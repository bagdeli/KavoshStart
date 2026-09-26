# 0007 — Release gate (REL-5)

- Status: accepted
- Deciders: bagdeli
- Issue: bagdeli/KavoshStart#2

## Context and problem
v1.0.0 was published before any CI had run (hosted jobs were blocked by account billing). REL-1 defined what a
release is, but nothing required green checks first.

## Decision
Releases are created only by the reusable `kavosh-release` workflow, triggered by `workflow_run` after CI succeeded
for a push to `main`. Its first step (`release_gate.py`) requires that every configured check (default `required`,
`main-guard / main-guard`) exists on that exact commit and concluded `success`, and that the commit is still the head
of `main`. Missing, pending after 5 minutes, failed, cancelled or skipped closes the gate. An API or CI outage closes it.

## Consequences
- Good: a release always corresponds to a verified commit; outages cannot produce unverified releases.
- Bad: while CI is unavailable, nothing can be released — by design.
- Release PRs are created with GITHUB_TOKEN; their CI needs "Approve and run" by the owner.

## Enforcement
`kavosh-release` (layer G); offline tests `tooling/tests/test_release_gate.py`; a manual tag is a REL-5 violation visible
in health (release without passing gate — planned in #6).
