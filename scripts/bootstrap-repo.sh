#!/usr/bin/env bash
# KavoshStart layer S: settings available on GitHub Free for a product repository.
# Dry-run by default. Usage: bash scripts/bootstrap-repo.sh <owner/repo> [--apply] [--main-ruleset|--rulesets] [--team-process] [--milestone NAME]
#   --main-ruleset OPTIONAL: only GitHub main-branch ruleset after G10=YES and separate owner approval.
#   --rulesets LEGACY BOTH: main + tags; tag rules require their own explicit owner approval.
#   Both require eligible public/paid private; dry-run/403 is never active protection.
set -euo pipefail
REPO="${1:?usage: bootstrap-repo.sh owner/repo [--apply] [--main-ruleset|--rulesets] [--team-process] [--milestone NAME]}"
shift
APPLY=0; RULESETS=0; RULES_MODE=""; TEAM=0; MILESTONE=""
while [ $# -gt 0 ]; do
  case "$1" in
    --apply) APPLY=1; shift ;;
    --main-ruleset) [ "$RULESETS" = 0 ] || { echo "choose only one ruleset mode" >&2; exit 2; }; RULESETS=1; RULES_MODE=main; shift ;;
    --rulesets) [ "$RULESETS" = 0 ] || { echo "choose only one ruleset mode" >&2; exit 2; }; RULESETS=1; RULES_MODE=both; shift ;;
    --team-process) TEAM=1; shift ;;
    --milestone) [ $# -ge 2 ] && [ -n "$2" ] || { echo "--milestone needs a name" >&2; exit 2; }; MILESTONE="$2"; shift 2 ;;
    *) echo "unknown $1" >&2; exit 2 ;;
  esac
done
HERE="$(cd "$(dirname "$0")/.." && pwd)"
run() { if [ "$APPLY" = 1 ]; then "$@"; else printf 'DRY-RUN:'; printf ' %q' "$@"; echo; fi; }

if [ "$RULES_MODE" = main ] && [ -n "$MILESTONE" ]; then echo "--main-ruleset cannot be combined with --milestone" >&2; exit 2; fi
if [ "$RULES_MODE" = main ] && [ "$TEAM" = 1 ]; then echo "--main-ruleset cannot be combined with --team-process" >&2; exit 2; fi

# Main-only owner choice must never silently mutate labels, merge settings or Actions permissions.
if [ "$RULES_MODE" != main ]; then
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
    if [ "$RULES_MODE" = main ] && [ "$f" = tags ]; then continue; fi
    template="$HERE/templates/rulesets/$f.json"
    [ "$f" != "main" ] || template="$HERE/templates/rulesets/$MAIN_RULESET.json"
    if [ "$APPLY" = 1 ] && [ "$RULES_MODE" = main ]; then
      # Inspect ONLY active server rules effective on main (including inherited
      # organization rules). Unrelated release/feature branch rules are not a blocker.
      # Also respect classic GitHub branch protection, which is not a ruleset.
      main_rules="$(gh api "repos/$REPO/rules/branches/main" | python3 -c 'import json,sys; rows=json.load(sys.stdin); assert isinstance(rows,list), "unexpected branch rules"; print(",".join(str(r.get("ruleset_id",r.get("type","unknown"))) for r in rows))')"
      main_protected="$(gh api "repos/$REPO/branches/main" --jq '.protected')"
      if [ "$main_protected" != false ] || [ -n "$main_rules" ]; then
        echo "main already has effective GitHub protection ($main_rules; protected=$main_protected): no duplicate or implicit update; inspect existing controls before mutation." >&2
        exit 1
      fi
      created="$(gh api -X POST "repos/$REPO/rulesets" --input "$template")"
      ruleset_id="$(printf '%s' "$created" | python3 -c 'import json,sys; x=json.load(sys.stdin); print(x["id"])')"
      # Confirm what GitHub actually accepted, not just the POST status.
      gh api "repos/$REPO/rulesets/$ruleset_id" | python3 -c '
import json, sys
expected = json.load(open(sys.argv[1], encoding="utf-8"))
actual = json.load(sys.stdin)
assert actual.get("name") == expected["name"], "ruleset name mismatch"
assert actual.get("target") == expected["target"] == "branch", "not a branch ruleset"
assert actual.get("enforcement") == expected["enforcement"] == "active", "not active"
assert actual.get("conditions", {}).get("ref_name") == expected["conditions"]["ref_name"], "unexpected branch scope"
assert actual.get("bypass_actors", []) == expected["bypass_actors"] == [], "unexpected bypass permissions"
actual_rules = {rule.get("type"): rule for rule in actual.get("rules", [])}
for rule in expected["rules"]:
    kind = rule["type"]
    assert kind in actual_rules, f"missing required rule: {kind}"
    parameters = rule.get("parameters", {})
    actual_parameters = actual_rules[kind].get("parameters", {})
    for key, value in parameters.items():
        if key == "required_status_checks":
            assert {item["context"] for item in value} == {
                item.get("context") for item in actual_parameters.get(key, [])
            }, "required status contexts differ"
        else:
            assert actual_parameters.get(key) == value, f"mismatched {kind}.{key}"
' "$template"
      echo "main ruleset $ruleset_id created and read back (server rules only; no claim about untested merge behavior)"
    elif [ "$APPLY" = 1 ]; then
      # Legacy both-main-and-tags path: requires separate broad-scope owner approval.
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
