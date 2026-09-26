#!/usr/bin/env bash
# KavoshStart layer S: settings available on GitHub Free for a product repository.
# Dry-run by default. Usage: bash scripts/bootstrap-repo.sh <owner/repo> [--apply] [--rulesets]
#   --rulesets  only for public repositories or paid plans (Free + private returns 403)
set -euo pipefail
REPO="${1:?usage: bootstrap-repo.sh owner/repo [--apply] [--rulesets]}"
shift
APPLY=0; RULESETS=0
for a in "$@"; do
  case "$a" in --apply) APPLY=1 ;; --rulesets) RULESETS=1 ;; *) echo "unknown $a" >&2; exit 2 ;; esac
done
HERE="$(cd "$(dirname "$0")/.." && pwd)"
run() { if [ "$APPLY" = 1 ]; then "$@"; else printf 'DRY-RUN:'; printf ' %q' "$@"; echo; fi; }

echo "== Labels (WK-1 and KavoshStart automation)"
python3 - "$HERE/templates/labels.json" <<'PY' | while IFS=$'\t' read -r name color desc; do run gh label create "$name" -R "$REPO" --color "$color" --description "$desc" --force; done
import json, sys
for l in json.load(open(sys.argv[1], encoding="utf-8")):
    print(f"{l['name']}\t{l['color']}\t{l['description']}")
PY

echo "== Merge settings: squash only, PR title/body as commit, delete merged branches (PR-5, BR-5)"
run gh api -X PATCH "repos/$REPO" \
  -F allow_squash_merge=true -F allow_merge_commit=false -F allow_rebase_merge=false \
  -f squash_merge_commit_title=PR_TITLE -f squash_merge_commit_message=PR_BODY \
  -F delete_branch_on_merge=true -F allow_update_branch=true -F has_wiki=false

echo "== Actions: default token read-only; allow Actions to create PRs (required by release-please, REL-4)"
# GitHub has one switch for "create and approve pull requests". Approving has no effect on GitHub Free
# (no required reviews), and PR-7 keeps merging a human decision.
run gh api -X PUT "repos/$REPO/actions/permissions/workflow" \
  -f default_workflow_permissions=read -F can_approve_pull_request_reviews=true

echo "== First milestone"
run gh api -X POST "repos/$REPO/milestones" -f title=v0.1.0 -f description="First usable release (PROJECT.md)"

if [ "$RULESETS" = 1 ]; then
  echo "== Rulesets (paid plan or public repository only)"
  for f in main tags; do
    if [ "$APPLY" = 1 ]; then
      gh api -X POST "repos/$REPO/rulesets" --input "$HERE/templates/rulesets/$f.json" >/dev/null && echo "ruleset $f applied" \
        || echo "ruleset $f NOT applied (GitHub Free + private?) — see standard/01-free-plan-operating-model.md"
    else
      echo "DRY-RUN: gh api -X POST repos/$REPO/rulesets --input templates/rulesets/$f.json"
    fi
  done
fi

echo
echo "Next, inside the clone: bash $HERE/scripts/install-agent-guards.sh"
[ "$APPLY" = 1 ] || echo "(nothing changed — re-run with --apply)"
