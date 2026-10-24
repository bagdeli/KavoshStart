# ADR-0021: Owner-authorized Test staging for release candidates

## Status

Proposed — pending owner review.

## Context

Some products need a bounded Test rehearsal before they can finish the final
acceptance process. A release candidate must not be treated as final acceptance:
the existing ACC-3 UI and independent owner-approval requirements remain
unchanged. Staging must be opt-in, bound to exact current main, and use the
existing REL-7 caller and receipt verifier rather than a parallel workflow or
weaker acceptance path.

## Decision

An optional `release.testStaging` object in the exact main manifest activates the
staging checks. Its versioned schema fixes `target` to `test`, declares the
caller workflow and maps `full`, `originals`, `recovery`, and `capacity` to
declared `test` assertions by acceptance ID. One integrated assertion may cover
all four only when its actual test contract checks all four conditions;
repeating one ID in the map does not create coverage. Invalid mappings and
deferred items fail closed.

The gate verifies the live workflow-dispatch run and attempt through the GitHub
API. The run must be on `main`, use the declared caller, and have both actor and
triggering actor equal to the manifest owner. The candidate is still required to
be exact current main with the existing required checks. The RC base must equal
`acceptance/scope.json`'s `targetRelease`.

For every scope item, the gate verifies each declared `test`, `security`, and
`migration` receipt through the canonical Issue's `Staging-*` marker and the
reviewed receipt policy. Canonical Issues may remain open during staging; they
must not be pull requests. CI must reference a successful required-workflow run
on the exact staging SHA. UI and approval evidence remain pending. No staging
marker satisfies the final ACC-3 gate, which continues to require its existing
closed Issue, UI evidence, and independent decision.

`actions-external` is an optional producer mode for CI where Actions artifact
storage is unavailable. It preserves the dedicated-App, exact workflow/run/
attempt/job/source/status and chronology checks; it requires an immutable
`externalEvidenceDigest` and does not fetch an arbitrary URL or call the Actions
artifact API. The trusted App must inspect the exact run, verify owner-held
original evidence custody and readback, and attest the digest. Existing
`actions` mode is unchanged.

## Consequences

Projects without `release.testStaging` retain the existing RC flow. Staging can
create only the existing immutable RC prerelease; it does not create a final
release, update a Production pin, deploy, or grant Production eligibility. The
runtime deployment gate independently rejects opt-in Test-staging RCs on
Production while retaining legacy behavior for manifests without the opt-in.

The receipt verifier authenticates App identity and exact source bindings, not
the truth of a dishonest attestor. Repository administration, policy review,
App credentials, and the human decision channel therefore remain trusted
control planes.
