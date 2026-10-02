#!/usr/bin/env bash
# KavoshStart read-only audit of a GitHub repository. Reproduces the metrics in docs/audit/.
# Usage: bash scripts/audit-repo.sh <owner/repo> [workdir]
# Needs: gh (authenticated), git, python3. Changes nothing on GitHub.
set -euo pipefail
REPO="${1:?usage: audit-repo.sh owner/repo [workdir]}"
WORK="${2:-${TMPDIR:-/tmp}/kavosh-audit-$$}"
mkdir -p "$WORK"
echo "# KavoshStart audit — $REPO — $(date -u +%Y-%m-%d)"
echo

default=$(gh repo view "$REPO" --json defaultBranchRef -q .defaultBranchRef.name)
visibility=$(gh repo view "$REPO" --json visibility -q .visibility)
echo "## Platform"
echo "- default branch: $default · visibility: $visibility"
if gh api "repos/$REPO/rulesets" >/dev/null 2>&1; then
  echo "- rulesets: $(gh api "repos/$REPO/rulesets" -q 'length') configured"
else
  echo "- rulesets: NOT AVAILABLE (plan limitation or no permission) ❌"
fi
echo

echo "## Clone"
git -c core.longpaths=true clone --quiet --no-checkout "https://github.com/$REPO" "$WORK/repo"
cd "$WORK/repo"
git fetch --quiet origin '+refs/heads/*:refs/remotes/origin/*'

echo "## Branches"
total=$(git branch -r | grep -v HEAD | wc -l | tr -d ' ')
echo "- remote branches: $total"
echo "- by prefix:"; git branch -r | grep -v HEAD | sed 's#origin/##' | awk -F/ '{print $1}' | sort | uniq -c | sort -rn | head -12 | sed 's/^/    /'
merged=0; unmerged=0
for b in $(git branch -r | grep -v HEAD); do
  if git merge-base --is-ancestor "$b" "origin/$default" 2>/dev/null; then merged=$((merged+1)); else unmerged=$((unmerged+1)); fi
done
echo "- contained in $default: $merged · not in $default: $unmerged"
echo "- divergence of $default vs branches ahead by >50 commits:"
for b in $(git branch -r | grep -v HEAD | grep -v "origin/$default\$"); do
  read -r behind ahead < <(git rev-list --left-right --count "origin/$default...$b")
  [ "$ahead" -gt 50 ] && echo "    $b: $default is $ahead behind / $behind ahead"
done || true
echo

echo "## Commits"
echo "- total (all refs): $(git log --all --oneline | wc -l | tr -d ' ')"
cc=$(git log --all --format=%s | grep -cE '^(feat|fix|docs|chore|refactor|test|ci|build|perf|revert)(\(.+\))?!?:' || true)
echo "- Conventional Commit subjects: $cc"
echo "- with AI Co-Authored-By trailer: $(git log --all --format=%b | grep -ciE 'co-authored-by: .*(claude|codex|copilot|gemini|openai|anthropic)' || true)"
echo "- author identities:"; git log --all --format='%ae' | sort | uniq -c | sort -rn | head -5 | sed 's/^/    /'
echo "- busiest days:"; git log --all --format=%ad --date=short | sort | uniq -c | sort -rn | head -3 | sed 's/^/    /'
echo

echo "## Docs on $default"
git ls-tree -r -l "origin/$default" | awk '$5 ~ /\.md$/ {n++; s+=$4; if ($4>61440) big=big"\n    "$5" ("int($4/1024)"KB)"} END {printf "- markdown files: %d (%d KB)\n- over 60KB:%s\n", n, s/1024, big}'
echo "- commit SHAs inside markdown: $(git grep -cE '\b[0-9a-f]{40}\b' "origin/$default" -- '*.md' 2>/dev/null | awk -F: '{s+=$NF} END {print s+0}')"
if git cat-file -e "origin/$default:AGENTS.md" 2>/dev/null; then
  echo "- AGENTS.md: $(git show "origin/$default:AGENTS.md" | wc -l | tr -d ' ') lines; issue refs: $(git show "origin/$default:AGENTS.md" | grep -oE '#[0-9]{2,}' | sort -u | tr '\n' ' ')"
else
  echo "- AGENTS.md: missing ❌"
fi
echo

echo "## Issues & PRs"
gh issue list -R "$REPO" --state all --limit 1000 --json labels,comments,state -q '
  "- issues: \(length) · open: \([.[]|select(.state=="OPEN")]|length) · labelled: \([.[]|select(.labels|length>0)]|length) · >30 comments: \([.[]|select(.comments|length>30)]|length)"'
echo "- milestones: $(gh api "repos/$REPO/milestones?state=all" -q length)"
gh pr list -R "$REPO" --state all --limit 1000 --json state,baseRefName,additions,deletions,isDraft -q "
  \"- PRs: \(length) · merged: \([.[]|select(.state==\"MERGED\")]|length) · merged into $default: \([.[]|select(.state==\"MERGED\" and .baseRefName==\"$default\")]|length) · >1000 lines: \([.[]|select(.additions+.deletions>1000)]|length) · largest: \([.[]|.additions+.deletions]|max)\""
echo "- releases: $(gh release list -R "$REPO" --limit 100 | wc -l | tr -d ' ') · tags: $(git ls-remote --tags origin | grep -vc '\^{}' || true)"
echo

echo "## CI (last 500 runs)"
gh run list -R "$REPO" --limit 500 --json conclusion -q 'group_by(.conclusion)|map("- \(.[0].conclusion // "in_progress"): \(length)")|.[]'
echo
echo "_Workdir: ${WORK}_"
