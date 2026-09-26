# 0002 — Every MUST has an enforcement mechanism

- Status: accepted
- Deciders: bagdeli
- Evidence: KavoshERP issue with twelve correct rules that were violated anyway (direct pushes to main, 100k-line PRs).

## Decision
A rule is only a MUST if `standard/RULES.md` names at least one enforcement layer (A agent guard, P PR check,
M main guard, H health, S repository setting, R human review). Without a mechanism it is a SHOULD.
Rules change in one PR together with their check and template.

## Enforcement
Review of `standard/RULES.md` changes (CODEOWNERS) and `tooling/test_templates.py` (templates must pass their own checks).
