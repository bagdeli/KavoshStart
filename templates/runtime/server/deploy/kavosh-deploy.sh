#!/usr/bin/env bash
# KavoshStart pull-based deploy (DEP-1…6). Run by kavosh-deploy.timer on the server; safe to run by hand.
#
#   CHANNEL=test        → newest SemVer tag, release candidates included (v1.2.0 > v1.2.0-rc.3 > v1.1.9)
#   CHANNEL=production  → only the tag written in $STATE_DIR/pin
#
# Layout under $BASE (default /opt/kavosh/$PROJECT):
#   repo.git/            bare mirror (fetch only)
#   releases/<version>/  clean export of that tag — never reused, never contains untracked leftovers
#   shared/.env          runtime configuration and secrets — outside every release directory
#   current              symlink to the running release
#
# Order: export → verify continuous recovery → optional risk-based snapshot → MIGRATE → build + up → health check.
# On failure the APP rolls back to the previous release automatically. The DATABASE is never rolled back
# automatically: releases use expand/contract migrations (DEP-5) so the previous app still works on the
# migrated schema; restoring the backup is a manual runbook step (docs/runbooks/deploy.md).
#
# Manual: kavosh-deploy.sh [--pin vX.Y.Z] [--dry-run] | --print-target <git-dir>
set -euo pipefail

SEMVER_RE='^v[0-9]+\.[0-9]+\.[0-9]+(-rc\.[0-9]+)?$'

# Highest SemVer tag in a git dir. versionsort.suffix makes v1.2.0-rc.3 sort BELOW v1.2.0 (plain v:refname does not).
select_latest() {
  git -C "$1" -c versionsort.suffix=-rc. tag --list 'v*' --sort=-v:refname | { grep -E "$SEMVER_RE" || true; } | head -n1
}

if [ "${1:-}" = "--print-target" ]; then   # used by KavoshStart offline tests
  select_latest "$2"
  exit 0
fi

: "${PROJECT:?set in deploy.env}"
BASE="${BASE:-/opt/kavosh/$PROJECT}"
CHANNEL="${CHANNEL:-test}"
REPO_URL="${REPO_URL:?set in deploy.env (read-only deploy key or KavoshRepo mirror)}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8080/version}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-90}"
KEEP_RELEASES="${KEEP_RELEASES:-3}"
MIGRATE_CMD="${MIGRATE_CMD:-}"   # e.g. "docker compose -p $PROJECT run --rm app alembic upgrade head"
BACKUP_CMD="${BACKUP_CMD:-}"     # e.g. "/usr/local/bin/kavosh-pg-backup $PROJECT" — must exit non-zero on failure
BACKUP_HEALTHCHECK_CMD="${BACKUP_HEALTHCHECK_CMD:-}" # verify healthy PITR/continuous backup before migration
MIGRATION_RISK="${MIGRATION_RISK:-high}" # low | high | destructive; high/destructive requires a fresh snapshot
STATE_DIR="/etc/kavosh/$PROJECT"
LOG_FILE="/var/log/kavosh/$PROJECT-deploy.log"
LOCK_FILE="/run/lock/kavosh-deploy-$PROJECT.lock"
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --pin)
      [ $# -ge 2 ] && [ -n "$2" ] || { echo "--pin requires a version" >&2; exit 2; }
      PIN_OVERRIDE="$2"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "unknown argument $1" >&2; exit 2 ;;
  esac
done

case "$CHANNEL" in test|production) ;; *) echo "unknown CHANNEL=$CHANNEL" >&2; exit 2 ;; esac
if [ -n "${PIN_OVERRIDE:-}" ] && [ "$CHANNEL" != production ]; then
  echo "--pin is allowed only with CHANNEL=production" >&2
  exit 2
fi
case "$MIGRATION_RISK" in low|high|destructive) ;; *) echo "unknown MIGRATION_RISK=$MIGRATION_RISK" >&2; exit 2 ;; esac

if [ -n "${PIN_OVERRIDE:-}" ]; then
  echo "$PIN_OVERRIDE" | grep -Eq "$SEMVER_RE" || { echo "pin '$PIN_OVERRIDE' is not a SemVer tag" >&2; exit 2; }
fi

# A dry run is a pure argument/plan check: do not create directories, acquire server
# locks, contact GitHub, write pins, or touch Docker/systemd resources.
if [ "$DRY_RUN" = 1 ]; then
  if [ -n "${PIN_OVERRIDE:-}" ]; then
    echo "dry-run: would pin production to $PIN_OVERRIDE"
  else
    echo "dry-run: CHANNEL=$CHANNEL (target lookup requires a real deploy)"
  fi
  exit 0
fi

mkdir -p "$(dirname "$LOG_FILE")" "$STATE_DIR" "$BASE/releases" "$BASE/shared"
log() { echo "$(date -u +%FT%TZ) [$PROJECT/$CHANNEL] $*" | tee -a "$LOG_FILE"; }

exec 9>"$LOCK_FILE"
flock -n 9 || { log "another deploy is running; skipping"; exit 0; }

[ -d "$BASE/repo.git" ] || git clone --quiet --mirror "$REPO_URL" "$BASE/repo.git"
git -C "$BASE/repo.git" remote set-url origin "$REPO_URL"
git -C "$BASE/repo.git" fetch --quiet --prune --tags origin

case "$CHANNEL" in
  test)       target=$(select_latest "$BASE/repo.git") ;;
  production) target="${PIN_OVERRIDE:-$(cat "$STATE_DIR/pin" 2>/dev/null || true)}" ;;
  *)          log "unknown CHANNEL=$CHANNEL"; exit 2 ;;
esac
[ -n "$target" ] || { log "no target version (no tags yet, or no pin for production)"; exit 0; }
echo "$target" | grep -Eq "$SEMVER_RE" || { log "target '$target' is not a SemVer tag"; exit 1; }
git -C "$BASE/repo.git" rev-parse -q --verify "refs/tags/$target" >/dev/null || { log "tag $target not found"; exit 1; }

if [ -n "${PIN_OVERRIDE:-}" ]; then
  pin_tmp="$STATE_DIR/pin.tmp.$$"
  printf '%s\n' "$PIN_OVERRIDE" > "$pin_tmp"
  mv -f "$pin_tmp" "$STATE_DIR/pin"
fi

current=$(basename "$(readlink "$BASE/current" 2>/dev/null || echo none)")
[ "$target" = "$current" ] && exit 0
log "deploying $target (current: $current)"
[ "$DRY_RUN" = 1 ] && { log "dry-run: stop"; exit 0; }

prepare() {   # clean export of a tag into its own directory
  local v="$1" dir="$BASE/releases/$1"
  if [ ! -d "$dir" ]; then
    rm -rf "$dir.tmp" && mkdir -p "$dir.tmp"
    git -C "$BASE/repo.git" archive "refs/tags/$v" | tar -x -C "$dir.tmp"
    mv "$dir.tmp" "$dir"
  fi
  ln -sfn "$BASE/shared/.env" "$dir/.env"
}

start() {     # mode=build for new releases; mode=cached for rollback with no network/build dependency
  local v="$1" mode="${2:-build}"
  export KAVOSH_VERSION="$v" KAVOSH_SHA
  KAVOSH_SHA=$(git -C "$BASE/repo.git" rev-parse "refs/tags/$v^{commit}")
  if [ "$mode" = cached ]; then
    (cd "$BASE/releases/$v" && docker compose -p "$PROJECT" up -d --remove-orphans --no-build --pull never)
  else
    (cd "$BASE/releases/$v" && docker compose -p "$PROJECT" build --pull && docker compose -p "$PROJECT" up -d --remove-orphans)
  fi
}

healthy() {
  local v="$1" sha="$2" deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    if curl -fsS --max-time 5 "$HEALTH_URL" 2>/dev/null | \
      EXPECTED_VERSION="$v" EXPECTED_SHA="$sha" python3 -c 'import json,os,sys
try:
 d=json.load(sys.stdin)
 ok=d.get("version")==os.environ["EXPECTED_VERSION"] and d.get("sha")==os.environ["EXPECTED_SHA"]
 ok=ok and ("status" not in d or d["status"] in ("ok","healthy","ready"))
 sys.exit(0 if ok else 1)
except (ValueError,TypeError): sys.exit(1)'; then return 0; fi
    sleep 3
  done
  return 1
}

prepare "$target"

if [ -n "$MIGRATE_CMD" ]; then
  [ -n "$BACKUP_HEALTHCHECK_CMD" ] || { log "ABORT: MIGRATE_CMD is set but BACKUP_HEALTHCHECK_CMD is empty (DEP-6)"; exit 1; }
  log "verify continuous backup/PITR before migration"
  (cd "$BASE/releases/$target" && eval "$BACKUP_HEALTHCHECK_CMD") || { log "ABORT: continuous backup/PITR is unhealthy — nothing changed (DEP-6)"; exit 1; }
  if [ "$MIGRATION_RISK" = high ] || [ "$MIGRATION_RISK" = destructive ]; then
    [ -n "$BACKUP_CMD" ] || { log "ABORT: high-risk migration requires BACKUP_CMD snapshot (DEP-6)"; exit 1; }
    log "take risk-based snapshot before migration"
    (cd "$BASE/releases/$target" && eval "$BACKUP_CMD") || { log "ABORT: snapshot failed — nothing changed (DEP-6)"; exit 1; }
  fi
  log "migrate to $target"
  (cd "$BASE/releases/$target" && export KAVOSH_VERSION="$target" && eval "$MIGRATE_CMD") \
    || { log "ABORT: migration failed — app still on $current; inspect the database, restore the backup if needed (runbook)"; exit 1; }
fi

target_sha=$(git -C "$BASE/repo.git" rev-parse "refs/tags/$target^{commit}")
if start "$target" && healthy "$target" "$target_sha"; then
  ln -sfn "$BASE/releases/$target" "$BASE/current"
  log "OK $target"
  ls -1dt "$BASE"/releases/v* 2>/dev/null | tail -n +"$((KEEP_RELEASES + 1))" | while read -r old; do
    [ "$(readlink "$BASE/current")" = "$old" ] || rm -rf "$old"
  done
  exit 0
fi

log "FAILED $target — rolling the APP back to $current (database stays migrated; DEP-5 keeps $current compatible)"
if [ "$current" != none ] && start "$current" cached && healthy "$current" "$(git -C "$BASE/repo.git" rev-parse "refs/tags/$current^{commit}")"; then
  log "app rolled back to $current"
else
  log "ROLLBACK FAILED — manual action required (docs/runbooks/deploy.md)"
fi
exit 1
