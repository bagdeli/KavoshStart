#!/usr/bin/env bash
# Public isolated test dependencies only; no product/service installation.
set -euo pipefail
: "${KAVOSH_CONFORMANCE_DEPS:?set an empty disposable dependency directory}"
mkdir -p "$KAVOSH_CONFORMANCE_DEPS"
cd "$KAVOSH_CONFORMANCE_DEPS"
if [ -n "$(find . -mindepth 1 -maxdepth 1 -print -quit)" ]; then
  echo 'dependency directory must be empty; existing data will not be removed' >&2
  exit 1
fi
curl --fail --location --proto '=https' --tlsv1.2 --max-time 120 \
  https://releases.hashicorp.com/terraform/1.9.8/terraform_1.9.8_linux_amd64.zip -o terraform.zip
printf '%s  terraform.zip\n' 186e0145f5e5f2eb97cbd785bc78f21bae4ef15119349f6ad4fa535b83b10df8 | sha256sum --check
unzip -q terraform.zip terraform
curl --fail --location --proto '=https' --tlsv1.2 --max-time 120 \
  https://wordpress.org/wordpress-6.8.3.tar.gz -o wordpress.tar.gz
# Exact archive pin published by WordPress; historical hook-engine fixture,
# never a production version recommendation. No WordPress installer is run.
printf '%s  wordpress.tar.gz\n' fd56bcdc15f1877e45dce67942ea75949ed650e8 | sha1sum --check
# Only the two core hook implementation files are needed; never unpack a site.
tar -xzf wordpress.tar.gz wordpress/wp-includes/plugin.php wordpress/wp-includes/class-wp-hook.php
printf 'Terraform: '; ./terraform version | sed -n '1p'
printf 'WordPress fixture: 6.8.3 pinned core hook engine\n'
