#!/usr/bin/env bash
# KavoshStart layer S: settings available on GitHub Free for a product repository.
# Dry-run by default. Usage: bash scripts/bootstrap-repo.sh <owner/repo> [--apply] [--rulesets] [--team-process] [--milestone NAME]
#   --rulesets  only for public repositories or paid plans (Free + private returns 403)
set -euo pipefail
REPO="${1:?usage: bootstrap-repo.sh owner/repo [--apply] [--rulesets] [--team-process] [--milestone NAME]}"
shift
APPLY=0; RULESETS=0; TEAM=0; MILESTONE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --rulesets) RULESETS=1; shift ;;
    --team-process) TEAM=1; shift ;;
    --milestone) [ $# -ge 2 ] && [ -n "$2" ] || { echo "--milestone needs a name" >&2; exit 2; }; MILESTONE="$2"; shift 2 ;;
    *) echo "unknown $1" >&2; exit 2 ;;
  esac
done
HERE="$(cd "$(dirname "$0")/.." && pwd)"
run() { if [ "$APPLY" = 1 ]; then "$@"; else printf 'DRY-RUN:'; printf ' %q' "$@"; echo; fi; }

echo "== Labels (WK-1 and KavoshStart automation)"
python3 - "$HERE/templates/labels.json" "$TEAM" <<'PY' | while IFS=$'\t' read -r name color desc; do run gh label create "$name" -R "$REPO" --color "$color" --description "$desc" --force; done
import json, sys
for l in json.load(open(sys.argv[1], encoding="utf-8")):
    if sys.argv[2] != "1" and l["name"] not in {"type:bug", "ci:full", "blocked", "kavosh:health", "kavosh:violation"}:
        continue
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

if [ -n "$MILESTONE" ]; then
  echo "== Owner-selected milestone"
  run gh api -X POST "repos/$REPO/milestones" -f title="$MILESTONE"
fi

if [ "$RULESETS" = 1 ]; then
  echo "== Rulesets (paid plan or public repository only)"
  CI_RUNNER="$(gh api "repos/$REPO/contents/kavosh.project.json" --jq '.content' | base64 --decode | python3 -c 'import json,sys; print(json.load(sys.stdin)["ci"]["runner"])')"
  MAIN_RULESET=main
  if [ "$CI_RUNNER" = "none" ]; then
    MAIN_RULESET=main-local-only
    echo "Local-only validation: retain PR and branch protections without CI status checks."
  fi
  for f in main tags; do
    template="$HERE/templates/rulesets/$f.json"
    [ "$f" != "main" ] || template="$HERE/templates/rulesets/$MAIN_RULESET.json"
    if [ "$APPLY" = 1 ]; then
      gh api -X POST "repos/$REPO/rulesets" --input "$template" >/dev/null && echo "ruleset $f applied" \
        || echo "ruleset $f NOT applied (GitHub Free + private?) — see standard/01-free-plan-operating-model.md"
    else
      echo "DRY-RUN: gh api -X POST repos/$REPO/rulesets --input $template"
    fi
  done
fi

echo
echo "Next, inside the clone: bash $HERE/scripts/install-agent-guards.sh"
[ "$APPLY" = 1 ] || echo "(nothing changed — re-run with --apply)"
