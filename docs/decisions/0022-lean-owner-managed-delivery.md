# ADR-0022 — Lean T2 delivery instead of mandatory acceptance infrastructure

- **Status:** proposed for a future versioned KavoshStart release
- **Scope:** generic public-standard behavior only; no consumer-specific details
- **Intent:** a small owner-run project must not inherit a compliance platform just to run tests and publish a server

## Complexity found in the existing default

A T2 scaffold had mandatory continuous acceptance, AC-* Issue/PR mapping, a second per-feature scope ledger, dedicated evidence and decision App services, detailed receipt-policy and JUnit artifact contracts, separate AI review, weekly health reporting and workflow-level blockers. The reusable governance and release workflows embed large generic verifiers even for projects that never require external attestation. Source labels and tier classifications were treated as reasons to add infrastructure rather than signals to prioritize real tests.

This complexity adds setup roles, secrets, App installation, maintenance and uncertainty over when a simple project is actually ready. **Repository size and workflow line count are inventory signals, not measured runtime slowness.**

## Adopt a lighter default

- A new T2 project may use `acceptance.mode=owner-managed` by default. It needs no AC IDs, acceptance scope file, producer App installation, receipt policy, per-PR Issue link, risk-field boilerplate, AI involvement field or independent visual attestation service.
- The source CI must still really run, pass on the exact source and be reported truthfully. Ordinary unit/integration/security tests are project-owned commands, not separate attestation products.
- Release must still refer to exact source and required successful checks; release authority rests with the actual owner. The new mode does **not** assert production deployment, backup recovery, licensing compliance or security approval without real work.
- Existing `continuous` remains **optional and backward compatible** for teams choosing granular/regulated attestation; no implicit opt-in or silent downgrade of existing consumers.
- Scaffold omits the unnecessary attestor documents and independent AI-review workflow in the lean mode. No new account, secret, runner or paid service is needed.

## Further reductions to evaluate separately

| Source of friction | Desired default | What stays necessary |
| --- | --- | --- |
| T2 classification → mandatory AC ledger | No ledger in owner mode | Tests and clear owner intent |
| Independent evidence/decision Apps | Not scaffolded, no cost | Genuine source CI checks |
| Repeated Issue/PR templates, AI trailers, risk tags | Optional for owner mode | Reviewable diff and actual result |
| Release-please PR + RC + main-guard complexity | Explore one explicit owner-driven tag release in a separate design | Immutable tag, exact main SHA and required CI |
| Weekly health and portfolio supervisors | Opt-in, not project delivery prerequisites | Manual inspectability |
| Massive generated governance + receipt-verifier bundle | Reduce default loading/building as a follow-up | Fail-closed checks for selected profiles |
| Staging, data restore, secrets policies | Based on actual operational need | No unauthorized network/data operations |

## Safety and migration

This first change adds a lean profile **without** breaking legacy consumers; it does not force-upgrade any pinned repository, weaken authentic required check conclusions or change another product's data. Promotion should follow the standard release/version/pin update, never a manual check bypass. Separate later changes can remove deprecated legacy implementation only after dependent projects are identified.

**Measure next:** generated file count for owner-managed vs continuous T2, number of required external services/credentials (target zero for owner-managed), number of reviewer/PR fields (target no mandated boilerplate) and time from source checkout to passing local `make check`.
