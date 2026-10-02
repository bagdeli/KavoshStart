# 0002 — Every MUST has an enforcement mechanism

- Status: accepted
- Deciders: bagdeli
- Evidence: a prior project had correct written rules that were still violated in practice; prose alone did not enforce them.

## Decision
A rule is only a MUST if `standard/RULES.md` names at least one enforcement layer (A agent guard, P PR check,
M main guard, G release gate, H health, S repository setting, O portfolio supervisor, R human review).
MUSTs whose only layer is R are listed explicitly at the end of RULES.md as human-enforced: no automatic detection is
claimed for them. Without any layer, a rule is a SHOULD.
Rules change in one PR together with their check and template.

## Enforcement
Review of `standard/RULES.md` changes (CODEOWNERS) and `tooling/test_templates.py` (templates must pass their own checks).
