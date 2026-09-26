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
# Order: export → BACKUP (mandatory when MIGRATE_CMD is set) → MIGRATE → build + up → health check.
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
STATE_DIR="/etc/kavosh/$PROJECT"
LOG_FILE="/var/log/kavosh/$PROJECT-deploy.log"
LOCK_FILE="/run/lock/kavosh-deploy-$PROJECT.lock"
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --pin) mkdir -p "$STATE_DIR"; echo "$2" > "$STATE_DIR/pin"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "unknown argument $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$(dirname "$LOG_FILE")" "$STATE_DIR" "$BASE/releases" "$BASE/shared"
log() { echo "$(date -u +%FT%TZ) [$PROJECT/$CHANNEL] $*" | tee -a "$LOG_FILE"; }

exec 9>"$LOCK_FILE"
flock -n 9 || { log "another deploy is running; skipping"; exit 0; }

[ -d "$BASE/repo.git" ] || git clone --quiet --mirror "$REPO_URL" "$BASE/repo.git"
git -C "$BASE/repo.git" remote set-url origin "$REPO_URL"
git -C "$BASE/repo.git" fetch --quiet --prune --tags origin

case "$CHANNEL" in
  test)       target=$(select_latest "$BASE/repo.git") ;;
  production) target=$(cat "$STATE_DIR/pin" 2>/dev/null || true) ;;
  *)          log "unknown CHANNEL=$CHANNEL"; exit 2 ;;
esac
[ -n "$target" ] || { log "no target version (no tags yet, or no pin for production)"; exit 0; }
echo "$target" | grep -Eq "$SEMVER_RE" || { log "target '$target' is not a SemVer tag"; exit 1; }
git -C "$BASE/repo.git" rev-parse -q --verify "refs/tags/$target" >/dev/null || { log "tag $target not found"; exit 1; }

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

start() {     # build and start a prepared release; the compose project name is stable, so volumes persist
  local v="$1"
  export KAVOSH_VERSION="$v" KAVOSH_SHA
  KAVOSH_SHA=$(git -C "$BASE/repo.git" rev-parse "refs/tags/$v^{commit}")
  (cd "$BASE/releases/$v" && docker compose -p "$PROJECT" build --pull && docker compose -p "$PROJECT" up -d --remove-orphans)
}

healthy() {
  local v="$1" deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    curl -fsS --max-time 5 "$HEALTH_URL" 2>/dev/null | grep -q "\"$v\"" && return 0
    sleep 3
  done
  return 1
}

prepare "$target"

if [ -n "$MIGRATE_CMD" ]; then
  [ -n "$BACKUP_CMD" ] || { log "ABORT: MIGRATE_CMD is set but BACKUP_CMD is empty (DEP-6)"; exit 1; }
  log "backup before migration"
  (cd "$BASE/releases/$target" && eval "$BACKUP_CMD") || { log "ABORT: backup failed — nothing changed (DEP-6)"; exit 1; }
  log "migrate to $target"
  (cd "$BASE/releases/$target" && export KAVOSH_VERSION="$target" && eval "$MIGRATE_CMD") \
    || { log "ABORT: migration failed — app still on $current; inspect the database, restore the backup if needed (runbook)"; exit 1; }
fi

if start "$target" && healthy "$target"; then
  ln -sfn "$BASE/releases/$target" "$BASE/current"
  log "OK $target"
  ls -1dt "$BASE"/releases/v* 2>/dev/null | tail -n +"$((KEEP_RELEASES + 1))" | while read -r old; do
    [ "$(readlink "$BASE/current")" = "$old" ] || rm -rf "$old"
  done
  exit 0
fi

log "FAILED $target — rolling the APP back to $current (database stays migrated; DEP-5 keeps $current compatible)"
if [ "$current" != none ] && start "$current" && healthy "$current"; then
  log "app rolled back to $current"
else
  log "ROLLBACK FAILED — manual action required (docs/runbooks/deploy.md)"
fi
exit 1
