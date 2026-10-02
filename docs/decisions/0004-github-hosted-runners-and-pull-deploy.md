# 0004 — Hosted runners and pull-based deployment (superseded runner policy)

- Status: runner and minute-budget rules superseded by [ADR-0008](0008-runner-by-visibility.md) and [ADR-0009](0009-human-authorized-operations.md); pull-based deployment remains accepted
- Deciders: bagdeli

This ADR recorded the earlier hosted-only default and tier minute budgets. Those runner and budget decisions are
historical. The current Free-only, no-shared-quota-by-default policy and isolation requirements are in ADR-0009.

## Current deployment decision

Servers deploy themselves from approved immutable tags (`pull-build` default, `pull-image` optional); GitHub does
not connect to servers (DEP-1). Production actions, migration and restore each require their own scoped authorization.
