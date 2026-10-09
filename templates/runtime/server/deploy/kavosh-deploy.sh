#!/usr/bin/env bash
# KavoshStart pull-based deploy (DEP-1…9). Run by a project-scoped kavosh-deploy-<project>.timer.
#
# CHANNEL=test       → newest SemVer tag, release candidates included.
# CHANNEL=production → only the exact tag written in $STATE_DIR/pin.
#
# Standard persistent environments use:
#   $BASE/repo.git/            bare mirror (fetch only)
#   $BASE/releases/<version>/  clean export of that tag
#   $BASE/shared/.env          runtime secrets/config outside releases
#   $BASE/current              symlink to the accepted running release
#
# VERSION_URL proves exact tag + SHA. HEALTH_URL proves application health. PUBLIC_BASE_URL proves the
# canonical reverse-proxy route reaches the same runtime. A green isolated CI runtime is not a substitute.
#
# Manual:
#   kavosh-deploy-<project> [--pin vX.Y.Z] [--dry-run]
#   kavosh-deploy-<project> --verify-environment
#   kavosh-deploy-<project> --print-target <git-dir>
set -euo pipefail

SEMVER_RE='^v[0-9]+\.[0-9]+\.[0-9]+(-rc\.[0-9]+)?$'

select_latest() {
  git -C "$1" -c versionsort.suffix=-rc. tag --list 'v*' --sort=-v:refname |
    { grep -E "$SEMVER_RE" || true; } | head -n1
}

if [ "${1:-}" = "--print-target" ]; then
  select_latest "$2"
  exit 0
fi

: "${PROJECT:?set in deploy.env}"
BASE="${BASE:-/opt/kavosh/$PROJECT}"
CHANNEL="${CHANNEL:-test}"
DEPLOY_METHOD="${DEPLOY_METHOD:-pull-build}"
REPO_URL="${REPO_URL:?set in deploy.env (read-only deploy key or approved mirror)}"
VERSION_URL="${VERSION_URL:-http://127.0.0.1:8080/version}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8080/health}"
PUBLIC_BASE_URL="${PUBLIC_BASE_URL:?set in deploy.env to the canonical environment origin}"
PUBLIC_BASE_URL="${PUBLIC_BASE_URL%/}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-90}"
KEEP_RELEASES="${KEEP_RELEASES:-3}"
ARTIFACT_VERIFY_CMD="${ARTIFACT_VERIFY_CMD:-}"
MIGRATE_CMD="${MIGRATE_CMD:-}"
BACKUP_CMD="${BACKUP_CMD:-}"
BACKUP_HEALTHCHECK_CMD="${BACKUP_HEALTHCHECK_CMD:-}"
RESTORE_TEST_CHECK_CMD="${RESTORE_TEST_CHECK_CMD:-}"
MIGRATION_MODE="${MIGRATION_MODE:-expand-contract}"
MIGRATION_RISK="${MIGRATION_RISK:-low}"
MAINTENANCE_STOP_CMD="${MAINTENANCE_STOP_CMD:-}"
STATE_DIR="${STATE_DIR:-/etc/kavosh/$PROJECT}"
LOG_FILE="${LOG_FILE:-/var/log/kavosh/$PROJECT-deploy.log}"
LOCK_FILE="${LOCK_FILE:-/run/lock/kavosh-deploy-$PROJECT.lock}"
DEPLOY_BIN="${DEPLOY_BIN:-/usr/local/bin/kavosh-deploy-$PROJECT}"
UNIT_DIR="${UNIT_DIR:-/etc/systemd/system}"
SYSTEMCTL="${SYSTEMCTL:-systemctl}"
CURL="${CURL:-curl}"
UNIT_PREFIX="${UNIT_PREFIX:-kavosh-deploy-$PROJECT}"
DRY_RUN=0
VERIFY_ENVIRONMENT=0

while [ $# -gt 0 ]; do
  case "$1" in
    --pin)
      [ $# -ge 2 ] && [ -n "$2" ] || { echo "--pin requires a version" >&2; exit 2; }
      PIN_OVERRIDE="$2"; shift 2 ;;
    --authorize-maintenance-window)
      [ $# -ge 2 ] && [ -n "$2" ] || { echo "--authorize-maintenance-window requires the exact target tag" >&2; exit 2; }
      MAINTENANCE_AUTH_TAG="$2"; shift 2 ;;
    --verify-environment) VERIFY_ENVIRONMENT=1; shift ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "unknown argument $1" >&2; exit 2 ;;
  esac
done

case "$CHANNEL" in test|production) ;; *) echo "unknown CHANNEL=$CHANNEL" >&2; exit 2 ;; esac
case "$DEPLOY_METHOD" in pull-build|pull-image) ;; *) echo "standard deployer requires DEPLOY_METHOD=pull-build or pull-image" >&2; exit 2 ;; esac
case "$MIGRATION_RISK" in low|high|destructive) ;; *) echo "unknown MIGRATION_RISK=$MIGRATION_RISK" >&2; exit 2 ;; esac
case "$MIGRATION_MODE" in expand-contract|maintenance-window) ;; *) echo "unknown MIGRATION_MODE=$MIGRATION_MODE" >&2; exit 2 ;; esac
if [ "$DEPLOY_METHOD" = pull-image ] && [ -z "$ARTIFACT_VERIFY_CMD" ]; then
  echo "pull-image requires ARTIFACT_VERIFY_CMD to prove immutable release artifact identity (DEP-9)" >&2
  exit 2
fi
if [ -n "${PIN_OVERRIDE:-}" ] && [ "$CHANNEL" != production ]; then
  echo "--pin is allowed only with CHANNEL=production" >&2
  exit 2
fi
if [ -n "${PIN_OVERRIDE:-}" ]; then
  echo "$PIN_OVERRIDE" | grep -Eq "$SEMVER_RE" || { echo "pin '$PIN_OVERRIDE' is not a SemVer tag" >&2; exit 2; }
fi

identity_ok() {
  local url="$1" version="$2" sha="$3"
  "$CURL" -fsS --max-time 5 "$url" 2>/dev/null |
    EXPECTED_VERSION="$version" EXPECTED_SHA="$sha" python3 -c 'import json,os,sys
try:
 d=json.load(sys.stdin)
 ok=d.get("version")==os.environ["EXPECTED_VERSION"] and d.get("sha")==os.environ["EXPECTED_SHA"]
 sys.exit(0 if ok else 1)
except (ValueError,TypeError): sys.exit(1)'
}

health_ok() {
  "$CURL" -fsS --max-time 5 "$1" >/dev/null 2>&1
}

runtime_ok_once() {
  local version="$1" sha="$2"
  identity_ok "$VERSION_URL" "$version" "$sha" &&
    health_ok "$HEALTH_URL" &&
    identity_ok "$PUBLIC_BASE_URL/version" "$version" "$sha" &&
    health_ok "$PUBLIC_BASE_URL/health"
}

target_from_local_state() {
  case "$CHANNEL" in
    test) select_latest "$BASE/repo.git" ;;
    production) cat "$STATE_DIR/pin" 2>/dev/null || true ;;
  esac
}

verify_environment() {
  local failed=0 target target_sha current_path expected_path
  verify() {
    if "$@"; then
      return 0
    fi
    printf 'ENVIRONMENT_CONFORMANCE=FAIL check=%s\n' "$1" >&2
    failed=1
    return 0
  }

  verify test -d "$BASE/repo.git"
  verify test -d "$BASE/releases"
  verify test -f "$BASE/shared/.env"
  verify test -f "$STATE_DIR/deploy.env"
  verify test -x "$DEPLOY_BIN"
  verify test -f "$UNIT_DIR/$UNIT_PREFIX.service"
  verify test -f "$UNIT_DIR/$UNIT_PREFIX.timer"
  verify "$SYSTEMCTL" is-enabled --quiet "$UNIT_PREFIX.timer"
  verify "$SYSTEMCTL" is-active --quiet "$UNIT_PREFIX.timer"
  [ "$failed" = 0 ] || return 1

  target="$(target_from_local_state)"
  [ -n "$target" ] && echo "$target" | grep -Eq "$SEMVER_RE" || {
    echo "ENVIRONMENT_CONFORMANCE=FAIL check=target-semver" >&2
    return 1
  }
  target_sha="$(git -C "$BASE/repo.git" rev-parse "refs/tags/$target^{commit}" 2>/dev/null || true)"
  [ -n "$target_sha" ] || { echo "ENVIRONMENT_CONFORMANCE=FAIL check=target-tag" >&2; return 1; }
  [ -d "$BASE/releases/$target" ] || { echo "ENVIRONMENT_CONFORMANCE=FAIL check=release-dir" >&2; return 1; }
  [ -L "$BASE/current" ] || { echo "ENVIRONMENT_CONFORMANCE=FAIL check=current-symlink" >&2; return 1; }
  current_path="$(readlink -f "$BASE/current")"
  expected_path="$(readlink -f "$BASE/releases/$target")"
  [ "$current_path" = "$expected_path" ] || {
    echo "ENVIRONMENT_CONFORMANCE=FAIL check=current-target expected=$target" >&2
    return 1
  }
  runtime_ok_once "$target" "$target_sha" || {
    echo "ENVIRONMENT_CONFORMANCE=FAIL check=runtime-drift expected=$target/$target_sha" >&2
    return 1
  }
  printf 'ENVIRONMENT_CONFORMANCE=PASS project=%s channel=%s version=%s sha=%s\n' "$PROJECT" "$CHANNEL" "$target" "$target_sha"
}

if [ "$VERIFY_ENVIRONMENT" = 1 ]; then
  verify_environment
  exit $?
fi

# A dry run is pure argument/config validation: no directories, locks, network, pins, Docker or systemd changes.
if [ "$DRY_RUN" = 1 ]; then
  if [ -n "${PIN_OVERRIDE:-}" ]; then
    echo "dry-run: would pin production to $PIN_OVERRIDE"
  else
    echo "dry-run: CHANNEL=$CHANNEL DEPLOY_METHOD=$DEPLOY_METHOD"
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
  test) target="$(select_latest "$BASE/repo.git")" ;;
  production) target="${PIN_OVERRIDE:-$(cat "$STATE_DIR/pin" 2>/dev/null || true)}" ;;
esac
[ -n "$target" ] || { log "no target version (no tags yet, or no pin for production)"; exit 1; }
echo "$target" | grep -Eq "$SEMVER_RE" || { log "target '$target' is not a SemVer tag"; exit 1; }
target_sha="$(git -C "$BASE/repo.git" rev-parse "refs/tags/$target^{commit}" 2>/dev/null || true)"
[ -n "$target_sha" ] || { log "tag $target not found"; exit 1; }

if [ -n "${PIN_OVERRIDE:-}" ]; then
  pin_tmp="$STATE_DIR/pin.tmp.$$"
  printf '%s\n' "$PIN_OVERRIDE" > "$pin_tmp"
  mv -f "$pin_tmp" "$STATE_DIR/pin"
fi

current="$(basename "$(readlink "$BASE/current" 2>/dev/null || echo none)")"
if [ "$target" = "$current" ]; then
  if runtime_ok_once "$target" "$target_sha"; then
    log "OK $target; no deployment drift"
    exit 0
  fi
  log "DRIFT $target; current release identity/health does not match canonical runtime"
  exit 1
fi
log "deploying $target (current: $current)"

prepare() {
  local v="$1" dir="$BASE/releases/$1"
  if [ ! -d "$dir" ]; then
    rm -rf "$dir.tmp" && mkdir -p "$dir.tmp"
    git -C "$BASE/repo.git" archive "refs/tags/$v" | tar -x -C "$dir.tmp"
    mv "$dir.tmp" "$dir"
  fi
  [ -f "$BASE/shared/.env" ] || { log "ABORT: missing $BASE/shared/.env"; return 1; }
  ln -sfn "$BASE/shared/.env" "$dir/.env"
}

start() {
  local v="$1" mode="${2:-build}"
  export KAVOSH_VERSION="$v" KAVOSH_SHA
  KAVOSH_SHA="$(git -C "$BASE/repo.git" rev-parse "refs/tags/$v^{commit}")"
  if [ "$mode" = cached ]; then
    (cd "$BASE/releases/$v" && docker compose -p "$PROJECT" up -d --remove-orphans --no-build --pull never)
  elif [ "$DEPLOY_METHOD" = pull-build ]; then
    (cd "$BASE/releases/$v" && docker compose -p "$PROJECT" build --pull &&
      { [ -z "$ARTIFACT_VERIFY_CMD" ] || eval "$ARTIFACT_VERIFY_CMD"; } &&
      docker compose -p "$PROJECT" up -d --remove-orphans)
  else
    (cd "$BASE/releases/$v" && docker compose -p "$PROJECT" pull &&
      eval "$ARTIFACT_VERIFY_CMD" &&
      docker compose -p "$PROJECT" up -d --remove-orphans --no-build --pull never)
  fi
}

healthy() {
  local v="$1" sha="$2" deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    if runtime_ok_once "$v" "$sha"; then
      return 0
    fi
    sleep 3
  done
  return 1
}

prepare "$target"

if [ -n "$MIGRATE_CMD" ]; then
  manifest_mode="$(python3 - "$BASE/releases/$target/kavosh.project.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f).get("deploy", {}).get("migrationMode", "expand-contract"))
PY
  )"
  [ "$MIGRATION_MODE" = "$manifest_mode" ] || { log "ABORT: MIGRATION_MODE does not match the release manifest"; exit 1; }
  if [ "$MIGRATION_MODE" = maintenance-window ]; then
    manifest_tier="$(python3 - "$BASE/releases/$target/kavosh.project.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f).get("tier", ""))
PY
    )"
    migration_adr="$(python3 - "$BASE/releases/$target/kavosh.project.json" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    print(json.load(f).get("deploy", {}).get("migrationADR", ""))
PY
    )"
    [ "$manifest_tier" = T1 ] || { log "ABORT: maintenance-window migrations are T1-only"; exit 1; }
    [ "${MAINTENANCE_AUTH_TAG:-}" = "$target" ] || { log "ABORT: direct per-run authorization requires --authorize-maintenance-window $target"; exit 1; }
    [ -n "$MAINTENANCE_STOP_CMD" ] || { log "ABORT: MAINTENANCE_STOP_CMD is required to enter the downtime window"; exit 1; }
    [ -n "$migration_adr" ] && [ -f "$BASE/releases/$target/$migration_adr" ] || { log "ABORT: release migration ADR is missing"; exit 1; }
    python3 - "$BASE/releases/$target/$migration_adr" <<'PY'
import pathlib, sys
text = pathlib.Path(sys.argv[1]).read_text(encoding="utf-8").lower()
required = ("migration and recovery", "maintenance window", "backup", "restore test", "rollback")
missing = [term for term in required if term not in text]
if missing:
    sys.exit("migration ADR missing required evidence: " + ", ".join(missing))
PY
    log "maintenance-window authorized by ${DEPLOY_ACTOR:-$(id -un)} for exact tag $target; stopping service after backup checks"
  fi
  [ -n "$BACKUP_HEALTHCHECK_CMD" ] || { log "ABORT: MIGRATE_CMD is set but BACKUP_HEALTHCHECK_CMD is empty (DEP-6)"; exit 1; }
  log "verify continuous backup/PITR before migration"
  (cd "$BASE/releases/$target" && eval "$BACKUP_HEALTHCHECK_CMD") || { log "ABORT: continuous backup/PITR is unhealthy — nothing changed (DEP-6)"; exit 1; }
  [ -n "$RESTORE_TEST_CHECK_CMD" ] || { log "ABORT: MIGRATE_CMD is set but RESTORE_TEST_CHECK_CMD is empty (DEP-6)"; exit 1; }
  log "verify recent successful restore rehearsal before migration"
  (cd "$BASE/releases/$target" && eval "$RESTORE_TEST_CHECK_CMD") || { log "ABORT: latest restore rehearsal is missing, stale, or failed — nothing changed (DEP-6)"; exit 1; }
  if [ "$MIGRATION_RISK" = high ] || [ "$MIGRATION_RISK" = destructive ]; then
    [ -n "$BACKUP_CMD" ] || { log "ABORT: high-risk migration requires BACKUP_CMD snapshot (DEP-6)"; exit 1; }
    log "take risk-based snapshot before migration"
    (cd "$BASE/releases/$target" && eval "$BACKUP_CMD") || { log "ABORT: snapshot failed — nothing changed (DEP-6)"; exit 1; }
  fi
  if [ "$MIGRATION_MODE" = maintenance-window ]; then
    log "enter planned maintenance window"
    (cd "$BASE/releases/$target" && eval "$MAINTENANCE_STOP_CMD") || { log "ABORT: could not stop service for maintenance window"; exit 1; }
  fi
  log "migrate to $target"
  (cd "$BASE/releases/$target" && export KAVOSH_VERSION="$target" KAVOSH_SHA="$target_sha" && eval "$MIGRATE_CMD") ||
    { log "ABORT: migration failed — inspect the database; restore only with separate authorization"; exit 1; }
fi

if start "$target" && healthy "$target" "$target_sha"; then
  ln -sfn "$BASE/releases/$target" "$BASE/current"
  log "OK $target"
  ls -1dt "$BASE"/releases/v* 2>/dev/null | tail -n +"$((KEEP_RELEASES + 1))" | while read -r old; do
    [ "$(readlink "$BASE/current")" = "$old" ] || rm -rf "$old"
  done
  exit 0
fi

if [ "${MIGRATION_MODE:-expand-contract}" = maintenance-window ] && [ -n "$MIGRATE_CMD" ]; then
  log "FAILED $target — maintenance-window migration is not assumed backward-compatible; service remains stopped for manual recovery"
  exit 1
fi

log "FAILED $target — rolling the APP back to $current; database is never automatically restored"
if [ "$current" != none ] && start "$current" cached &&
  healthy "$current" "$(git -C "$BASE/repo.git" rev-parse "refs/tags/$current^{commit}")"; then
  log "app rolled back to $current"
else
  log "ROLLBACK FAILED — manual action required (docs/runbooks/deploy.md)"
fi
exit 1
