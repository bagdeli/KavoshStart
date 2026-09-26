#!/usr/bin/env bash
# KavoshStart pull-based deploy (DEP-1…4). Run by kavosh-deploy.timer on the server; safe to run by hand.
#   CHANNEL=test        → deploy the newest v* tag (including -rc)
#   CHANNEL=production  → deploy only the tag written in /etc/kavosh/$PROJECT/pin
# Flow: fetch tags → pick target → if different from current: checkout, build, up → health check → rollback on failure.
# Manual: kavosh-deploy.sh [--pin vX.Y.Z] [--dry-run]
set -euo pipefail

: "${PROJECT:?set in deploy.env}"
: "${APP_DIR:?set in deploy.env}"
CHANNEL="${CHANNEL:-test}"
HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8080/version}"
HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-90}"
STATE_DIR="/etc/kavosh/$PROJECT"
PIN_FILE="$STATE_DIR/pin"
CURRENT_FILE="$STATE_DIR/current"
LOG_FILE="/var/log/kavosh/$PROJECT-deploy.log"
LOCK_FILE="/run/lock/kavosh-deploy-$PROJECT.lock"
DRY_RUN=0

while [ $# -gt 0 ]; do
  case "$1" in
    --pin) mkdir -p "$STATE_DIR"; echo "$2" > "$PIN_FILE"; shift 2 ;;
    --dry-run) DRY_RUN=1; shift ;;
    *) echo "unknown argument $1" >&2; exit 2 ;;
  esac
done

mkdir -p "$(dirname "$LOG_FILE")" "$STATE_DIR"
log() { echo "$(date -u +%FT%TZ) [$PROJECT/$CHANNEL] $*" | tee -a "$LOG_FILE"; }

exec 9>"$LOCK_FILE"
flock -n 9 || { log "another deploy is running; skipping"; exit 0; }

cd "$APP_DIR"
if [ -n "${REPO_URL:-}" ] && [ "$(git remote get-url origin)" != "$REPO_URL" ]; then
  git remote set-url origin "$REPO_URL"
fi
git fetch --quiet --force --tags origin

case "$CHANNEL" in
  test)       target=$(git tag --list 'v*' --sort=-v:refname | head -n1) ;;
  production) target=$(cat "$PIN_FILE" 2>/dev/null || true) ;;
  *)          log "unknown CHANNEL=$CHANNEL"; exit 2 ;;
esac
[ -n "$target" ] || { log "no target version (no tags yet, or no pin for production)"; exit 0; }
git rev-parse -q --verify "refs/tags/$target" >/dev/null || { log "target $target is not a tag"; exit 1; }

current=$(cat "$CURRENT_FILE" 2>/dev/null || echo none)
[ "$target" = "$current" ] && exit 0
log "deploying $target (current: $current)"
[ "$DRY_RUN" = 1 ] && { log "dry-run: stop"; exit 0; }

deploy() {
  local version="$1"
  git -c advice.detachedHead=false checkout --quiet --force "refs/tags/$version"
  export KAVOSH_VERSION="$version" KAVOSH_SHA
  KAVOSH_SHA=$(git rev-parse HEAD)
  docker compose build --pull
  # TODO(kavosh): database migrations here if the project has them, e.g.
  # docker compose run --rm app <migrate command>
  docker compose up -d --remove-orphans
}

healthy() {
  local version="$1" deadline=$(( $(date +%s) + HEALTH_TIMEOUT ))
  while [ "$(date +%s)" -lt "$deadline" ]; do
    if curl -fsS --max-time 5 "$HEALTH_URL" 2>/dev/null | grep -q "\"$version\""; then
      return 0
    fi
    sleep 3
  done
  return 1
}

if deploy "$target" && healthy "$target"; then
  echo "$target" > "$CURRENT_FILE"
  log "OK $target ($(git rev-parse --short HEAD))"
  exit 0
fi

log "FAILED $target — rolling back to $current"
if [ "$current" != none ] && deploy "$current" && healthy "$current"; then
  log "rolled back to $current"
else
  log "ROLLBACK FAILED — manual action required (docs/runbooks/deploy.md)"
fi
exit 1
