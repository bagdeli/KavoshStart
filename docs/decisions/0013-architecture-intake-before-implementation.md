# ADR-0013 — Architecture choices before dependent implementation

- Status: Proposed
- Scope: agent intake and project/spec templates; no release/receipt-policy change

## Context

A project profile can name a dependency without deciding whether the product needs it. Late decisions about licensing, identity, tenancy, offline behavior, migration or acceptance infrastructure can create avoidable rework and late evidence debt. A source requirement is not automatically an independent delivery or review cycle.

## Decision

Use the existing questionnaire, PROJECT.md and feature Spec. Ask applicability and architecture-shaping choices early, including product licensing for every project. Reuse explicit answers and applicable owner-approved defaults; never infer a licence model from internal use or repository visibility. Only selected capabilities receive conditional detail and implementation work.

Settled choices are selected, explicitly not-needed, or inherited with a reference. Unresolved questions remain in the existing Issue/Spec with their owner and dependent work. Do not block unrelated authorized work or claim a finalized dependent architecture. Existing safety and acceptance gates are unchanged.

Keep machine facts in existing manifest fields, reference them from the compact project sheet, and do not add a manifest schema, decision registry, workflow, service or per-answer approval object. Identify the availability of the v3 independent receipt producer during planning; missing admission remains a prerequisite, not a reason to forge or relax receipts.

KavoshStart coordinates engineering choices and delivery. KavoshUI supplies UI contracts and presentation implementations. Product business models and chosen integrations stay in the product. Third-party/font licence administration and product entitlement enforcement are distinct concerns.

## Verification and limitations

Existing unittest discovery checks questionnaire/template/protocol consistency and regressions in contradictory instructions. These are documentation-contract tests, not proof that an arbitrary agent asks every question correctly or that a product's decisions are accepted. No source-bound receipt or observed product result is created by these tests.

## Compatibility

No workflow API, rule ID, manifest schema, receipt format or existing source approval changes. Existing consumers reuse decisions and fill only gaps when this protocol is explicitly adopted; it does not retroactively invalidate their releases. Canonical RULES.md still wins on conflict. This PR does not authorize merge, publication or rollout.

## Network incidents and proportional QA (owner-approved follow-up)

A failed upload/download is **not** authority to introduce a new relay or permanent service. The agent reports the private, sanitized URL, hostname/DNS, actually resolved IP or unknown, port, failure class and bounded attempts to the owner for unblock. This is an operational decision in the owning project, not a portfolio infrastructure requirement. The optional read-only diagnostic only resolves DNS; it does not perform a transfer or write durable state.

Quality uses deterministic machine-observed checks for measurable invariants and human **or** trusted machine comparison for evaluative UI; high-risk security boundaries remain tested. Full manual penetration tests are not a universal initial-release prerequisite. Existing v3 ACC-3 signed/typed receipt gates remain unchanged by this follow-up; any relaxation requires a separately reviewed versioned trust contract and tests. No private product environment is named in public standards.
