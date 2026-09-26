# 0001 — Adopt KavoshStart

- Status: accepted
- Deciders: {{OWNER}}

## Context and problem
The project needs a defined way of planning, branching, reviewing, releasing and working with AI agents that is
enforceable on the GitHub Free plan.

## Decision
Follow KavoshStart {{KAVOSHSTART}} as tier {{TIER}} with runtime {{RUNTIME}}. Deviations require an ADR in this folder.

## Enforcement
`.github/workflows/kavosh.yml` (governance, main guard, weekly health), `.githooks/`, `.claude/settings.json`.
