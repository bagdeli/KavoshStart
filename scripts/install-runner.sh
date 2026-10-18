#!/usr/bin/env bash
# The legacy runner installer stays retired. V6 permits separately provisioned
# self-hosted GitHub Actions runners; never register one implicitly.
set -euo pipefail
printf '%s\n' \
  'KavoshStart CI-1/2: existing isolated self-hosted GitHub Actions runners are allowed in private repositories.' \
  'This retired script neither registers a runner nor certifies isolation.' \
  'Provisioning needs a separate authorized operation, scoped runner labels and a CI-2 trust ADR.' \
  'Private GitHub-hosted runs require separate explicit approval for each exact run.' >&2
exit 1
