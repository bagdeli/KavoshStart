# ADR 0014 — Risk-proportional source-bound acceptance evidence

## Status

Proposed breaking control-plane release, not part of published KavoshStart v3.0.2.

## Context

Dedicated independently credentialed Apps and short-lived artifacts for every low-risk CI-only item can make acceptance work scale with bookkeeping, not actual product quality. Removing all proof would permit false-positive readiness. The goal is evidence proportionate to risk, with continuous tracking and no parallel status registry.

## Decision

Retain T2 continuous mode and a release-scoped versioned acceptance contract; add opt-in `acceptance.assurance=risk-based`. Omission retains v3 strict attested semantics.

Only low/medium items declaring exactly `evidence=["ci"]`, `assertions.ci=["repository::required"]`, without defer, may use native proof: closed canonical Issue, declared owner, accepted merged source and actual successful required Actions workflow for the exact source or verified PR-head/squash bridge. Source/candidate trees must match or approved literal `evidencePaths` plus unchanged control-plane dependencies must establish safe reuse. A false, stale, skipped, wrong-source or unavailable check blocks the claim.

All high/critical, deferred and specialist `test`, `ui`, `security`, `migration` acceptance items continue to require fully typed independently published receipts and owner decisions. A reduced item evidence declaration is not a way to evade actual required tests; scope remains owner-reviewed and capability-based.

## Security and tradeoffs

Native proof demonstrates successful required engineering CI, **not** domain UAT or independent human acceptance. An editable `Accepted-By` marker is a declaration of the owner, not a signature. Real owner approval is still required for high-risk code, release and production operations. In unprotected private repositories, branch administrators may bypass checks, so this mode makes no claim of technical enforcement beyond the actual GitHub permissions.

## Compatibility and verification

This changes governance/release proof semantics and must be published only as a reviewed breaking major release with explicit consumer migration. There is no implicit relaxation for pinned v3 projects. Offline regression fixtures prove positive CI-only native acceptance without a publisher, and negative failed/stale/mismatched proof, false specialist claims, high-risk and deferred proof, while legacy attested fixtures stay green. Health and Release share the same evaluator; no additional tracking app or service is introduced.
