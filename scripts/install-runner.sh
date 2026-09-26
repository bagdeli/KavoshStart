#!/usr/bin/env bash
# KavoshStart CI-2: install a GitHub Actions self-hosted runner registered to ONE private repository.
# Run on the runner machine as root. Get a short-lived registration token on your own computer (owner only):
#   gh api -X POST repos/<owner>/<repo>/actions/runners/registration-token -q .token
# Usage:
#   sudo bash install-runner.sh <owner/repo> <registration-token> [instance-number]
# Installs under /opt/actions-runner/<repo>-<n>, runs as the unprivileged user "gha-<repo>" via systemd.
# Labels: self-hosted, linux, x64, <repo-slug>  (must equal kavosh.project.json → ci.runnerLabels).
# T2 projects: install at least two instances (instance-number 1 and 2).
set -euo pipefail

REPO="${1:?usage: install-runner.sh owner/repo registration-token [instance]}"
TOKEN="${2:?registration token required (gh api -X POST repos/$REPO/actions/runners/registration-token -q .token)}"
N="${3:-1}"
SLUG=$(echo "${REPO#*/}" | tr '[:upper:]' '[:lower:]' | sed 's/[^a-z0-9]\+/-/g; s/^-//; s/-$//')
USER_NAME="gha-$SLUG"
DIR="/opt/actions-runner/$SLUG-$N"
NAME="$(hostname -s)-$SLUG-$N"

[ "$(id -u)" = 0 ] || { echo "run as root" >&2; exit 1; }
command -v docker >/dev/null || echo "warning: Docker not found — most Kavosh CI jobs need it" >&2
command -v jq >/dev/null || { echo "jq is required (apt-get install -y jq)" >&2; exit 1; }

id "$USER_NAME" >/dev/null 2>&1 || useradd --system --create-home --shell /usr/sbin/nologin "$USER_NAME"
getent group docker >/dev/null && usermod -aG docker "$USER_NAME"

# Latest runner release + its published SHA-256 (from the release notes markers).
rel=$(curl -fsSL https://api.github.com/repos/actions/runner/releases/latest)
ver=$(echo "$rel" | jq -r .tag_name | sed 's/^v//')
sum=$(echo "$rel" | jq -r .body | sed -n 's/.*<!-- BEGIN SHA linux-x64 -->\([0-9a-f]\{64\}\)<!-- END SHA linux-x64 -->.*/\1/p' | head -n1)
[ -n "$sum" ] || { echo "could not read the published SHA-256 for linux-x64" >&2; exit 1; }
file="actions-runner-linux-x64-$ver.tar.gz"

mkdir -p "$DIR" && cd "$DIR"
curl -fsSL -o "$file" "https://github.com/actions/runner/releases/download/v$ver/$file"
echo "$sum  $file" | sha256sum -c -
tar -xzf "$file" && rm -f "$file"
chown -R "$USER_NAME:$USER_NAME" "$DIR"

sudo -u "$USER_NAME" ./config.sh --unattended --replace \
  --url "https://github.com/$REPO" --token "$TOKEN" \
  --name "$NAME" --labels "linux,x64,$SLUG" --work "_work"

./svc.sh install "$USER_NAME"
./svc.sh start
echo "runner $NAME online for $REPO with labels: self-hosted, linux, x64, $SLUG"
echo "check: gh api repos/$REPO/actions/runners -q '.runners[] | [.name,.status] | @tsv'"
