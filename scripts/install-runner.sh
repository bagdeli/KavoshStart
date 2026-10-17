#!/usr/bin/env bash
# Retired legacy installer. KavoshStart no longer provisions GitHub Actions self-hosted runners.
set -euo pipefail
printf '%s\n' \
  'KavoshStart CI-1: private repositories MUST use standard GitHub-hosted Actions runners.' \
  'The old private self-hosted runner installer has been retired; it cannot register a runner.' \
  'Exceptional public self-hosted runners require a CI-2 isolation/fork/credential ADR and separate owner-approved provisioning.' >&2
exit 1
