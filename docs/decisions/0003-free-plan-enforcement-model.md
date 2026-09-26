# 0003 — Enforcement model for GitHub Free with private repositories

- Status: accepted
- Deciders: bagdeli

## Context and problem
Paid plans are not an option now. On GitHub Free, private repositories get no branch protection, rulesets or required
checks (API returns 403), no GitHub Pages, and 2,000 Actions minutes per month for the whole account, each job rounded
up to a full minute.

## Considered options
1. Make repositories public to get rulesets and unlimited minutes.
2. Accept prose-only rules.
3. Layered enforcement without server-side protection.

## Decision
Option 3 by default; option 1 remains allowed per repository when its content is not sensitive.
Layers: A (git hooks via `core.hooksPath` + Claude Code deny rules) prevents; P (governance check + sticky comment)
makes violations red; the owner never merges red (PR-7, the single human-only rule); M (main guard) records any bypass
in a `kavosh:violation` issue; H (weekly health) measures drift and minutes; S applies the settings Free does allow
(squash-only, auto-delete branches, read-only default token).

## Consequences
- Good: every violation is either prevented or recorded; no silent drift like KavoshERP's 537-commit gap.
- Bad: a determined bypass is still possible; it is detected after the fact, not prevented.
- When a paid plan or public visibility arrives: apply `templates/rulesets/*.json`; nothing else changes.

## Enforcement
`kavosh-governance`, `kavosh-main-guard`, `kavosh-health`; `templates/common/.githooks/`, `.claude/settings.json`.
