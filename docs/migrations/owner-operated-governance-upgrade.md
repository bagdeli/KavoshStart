# Owner-operated governance — future breaking release migration

This is an implementation guide for a proposed breaking standard change, **not a published tag**. Do not pin it in any consumer before the canonical GitHub Release exists.

## One existing owner decision (no new questionnaire)
Reuse intake D3/G9 or an existing approved project decision. Ask whether the work is managed by one human or a sizeable collaborating team and, separately, whether the owner *wants* another human reviewer, independent App attestation/continuous acceptance, an outside legal specialist, or dedicated physical Test capacity.

For a solo project, each answer defaults to **no/not selected**, not a hidden blocker or deferred YES. Use real source CI, risk-sized tests and one genuine owner decision. For a team with an accepted reason, opt into each requested service explicitly and review its cost.

## Proposed manifest examples
Owner-operated T2:
```json
{"acceptance":{"mode":"none"},"review":{"independentHumanReview":false}}
```
Selected team attestation (only where the owner has real producers and needs it):
```json
{"acceptance":{"mode":"continuous","assurance":"attested"},"review":{"independentHumanReview":true}}
```

The team example must meet the documented significant-team predicate for the second human reviewer; continuous may also choose risk-based if its actual requirement scope warrants that protocol.

## Release and safety boundaries
- Only an **actually published exact major** can be adopted. Update manifest and all version-pinned callers atomically in a project-owned PR.
- Previous continuous/attested selections, human/technical decisions and receipt histories remain immutable. Change to owner-operated only after checking that no applicable previous commitment is silently evaded; record the owner's actual release-scope decision. `none` is not an ACCEPTED status for historical items.
- No source CI PASS without a successful exact-source run; no Test environment health claim without actual identity/health checks. Prevent untrusted runner code from reading production secrets.
- For third-party use, satisfy actual License/NOTICE/Corresponding Source obligations; the optional external lawyer is not a substitute for compliance.
- Avoid new independent people, Apps, paid GitHub dispatches and Test VMs unless specifically selected and authorized. Keep scoped tests, reviewable diffs and owner-approved high-risk merges.

## Out of scope
No consumer repository changes, no retroactive migration, no built-in App service, no forced QA suite or new entitlement/legal subsystem. Historical standard decisions remain preserved by version.
