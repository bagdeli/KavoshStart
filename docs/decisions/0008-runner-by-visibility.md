# 0008 — Runner by repository visibility (superseded)

- Status: superseded by [ADR-0009](0009-human-authorized-operations.md)
- Deciders: bagdeli
- Issue: bagdeli/KavoshStart#17

This ADR recorded the original incident-specific rule that private repositories always use self-hosted runners.
That rule is historical and no longer defines the standard. The current Free-only and no-shared-quota-by-default
policy, Docker root-equivalent warning, runner-isolation requirements, and cost boundary are in ADR-0009 and
`standard/04-ci-runners-minutes.md`.
