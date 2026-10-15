# ADR 0012 — Source-bound receipts and independent acceptance decisions

## Status

Proposed; human acceptance and operational rollout are separate from passing tests.

## Context

Issue closure, editable approval markers, arbitrary HTTPS links and a successful
but unrelated workflow cannot establish product acceptance. Historical merge
safety also depends on evidence available at merge time, not later success.
Health and Release must not disagree about the same receipt's validity.

## Decision

Use one read-only source and receipt evaluator for Health and Release. Preserve
current required check names and reusable workflow inputs. Evaluate historical
merge evidence at the actual merge time; unavailable history is unverified.

For continuous acceptance, retain the versioned scope and live canonical Issues,
but require explicit assertion IDs and digest-bound receipts from reviewed,
dedicated GitHub App publishers. Automated receipts bind exact source/tree,
workflow, job, run attempt, retained artifact identity/digest, outcomes and expiry.
Manual evidence binds an external evidence digest through a trusted attestor;
no arbitrary Issue URL is fetched. Recheck the current head and required checks
after receipt verification before allowing release.

A separate decision publisher authenticates the human and binds the actual
accept/defer decision to the owner, release scope, policy and exact evidence.
Product Actions tokens, agent connector identities and editable owner markers
are not independent approval. Evidence and decision publishers cannot share
the same App identity. The gate verifies these identities and bindings; the
attestors must independently inspect evidence and authenticate decisions.

Evidence reuse defaults to complete Git-tree equality. A reviewed literal
`evidencePaths` contract may restrict the dependency boundary, but control-plane,
manifest and acceptance-contract changes always invalidate old evidence.

## Alternatives and tradeoffs

Keeping marker-only compatibility would retain the reproduced false-acceptance
path. Trusting the product's own automation to approve its work would not separate
execution from acceptance. Requiring every test after every source edit would
waste evidence while still not prove authentic human decisions. The chosen
protocol instead makes trust, provenance and reuse explicit and testable.

Dedicated attestors add real operational cost and ownership. This implementation
is the verifier/protocol and an offline JUnit assertion adapter, not a deployed
attestation service. An owner must review and admit actual producer services,
protect their credentials outside product/agent execution, and verify their
behavior. The default empty producer policy fails closed; example or fabricated
App IDs must never activate it. Repository administration and policy review
remain part of the trust boundary; bypassing them can replace the policy.

## Compatibility and migration

This is a breaking continuous-acceptance contract and must not ship as a silent
patch upgrade. Publish only through the normal reviewed major-version release
path. Existing pinned consumers remain on their exact version until a dedicated
upgrade supplies genuine scope assertions, reviewed producer policy, receipts
and independently authenticated decisions. Non-continuous profiles do not gain
an implicit acceptance requirement. Do not promote historical work automatically.

The producer protocol and migration fields are specified in
`templates/tier/T2/acceptance/README.md`. Policy is versioned intent, not a second
live acceptance tracker. No paid service, new App installation, consumer upgrade,
Release, deployment or product acceptance is authorized by this ADR proposal.

## Verification boundary

Positive/negative offline fixtures exercise publisher identity, digest and source
bindings, assertion outcomes, run/job/artifact identity, expiration, dependency
invalidation and final-check refresh. A real SQLite negative fixture proves that
a missing schema column fails and cannot be serialized as a passing assertion.
These fixtures do not certify PostgreSQL, rendered UI or deployed product UAT.
Real producer integration and product-specific evidence remain rollout gates.
