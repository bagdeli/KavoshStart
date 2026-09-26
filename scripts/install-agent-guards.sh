#!/usr/bin/env bash
# KavoshStart layer A: activate the committed git hooks in this clone (AI-4).
# Run once per clone, on every machine where a human or an AI agent works:
#   bash <KavoshStart>/scripts/install-agent-guards.sh [repo-dir]
set -euo pipefail
cd "${1:-.}"
[ -d .githooks ] || { echo "no .githooks/ here — scaffold the repository first" >&2; exit 1; }
chmod +x .githooks/* 2>/dev/null || true
git config core.hooksPath .githooks
git config push.default current
git config pull.rebase true
if [ -z "$(git config user.email)" ]; then
  echo "warning: git user.email is not set — use your GitHub noreply address (standard/05-ai-agents.md)" >&2
fi
echo "agent guards active: core.hooksPath=$(git config core.hooksPath)"
command -v gitleaks >/dev/null 2>&1 || echo "tip: install gitleaks for accurate secret scanning in pre-commit"
[ -f .claude/settings.json ] && echo "Claude Code deny rules: .claude/settings.json" || echo "warning: .claude/settings.json missing" >&2
