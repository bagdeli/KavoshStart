# 0004 — GitHub-hosted runners by default; pull-based deployment

- Status: accepted
- Deciders: bagdeli
- Evidence: KavoshERP 75 % cancelled runs in 7 days on one self-hosted runner; network/TLS registry issue; KavoshUI 173 failures in 200 runs, also self-hosted.

## Decision
- All CI jobs run on `ubuntu-latest` (CI-1). Self-hosted only for a T2 deploy job with an ADR, ephemeral, repository-scoped (CI-2).
- Minutes are budgeted per tier (T0 100, T1 300, T2 700; total ≤ 1,600) and measured weekly (CI-3).
- Servers deploy themselves from tags (`pull-build` default, `pull-image` optional); GitHub never connects to servers (DEP-1).

## Consequences
- Good: no runner maintenance, no internal-network exposure, public package registries reachable from CI.
- Bad: minutes are scarce → CI does not run on drafts, heavy suites only on main/tags/label, agents run `make check` locally.
- The December 2025 announcement of a per-minute fee for self-hosted runners (later postponed) shows self-hosting is not guaranteed free either.

## Enforcement
Governance CI-1/CI-2 (fails on self-hosted `runs-on` without manifest + ADR), health minutes metric, `scripts/portfolio.py`.
