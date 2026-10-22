# ADR-0021 — Base-first acceptance and dependency-aware Feature release units

- **Status:** Proposed — requires owner review before any new standard release
- **Scope:** Generic T1/T2 project delivery; existing pinned consumers unchanged
- **Tracking:** Public standards Issue #173
- **Related rules:** BASE-1…3, TRN-1…5; existing WK-3/5/6, REL-1…7, ACC-1…4, CR-3 and SRC-1

## Context

A product may have architecture, many merged code changes, an operational Pilot and a long Milestone roadmap but still no independently accepted first usable Base. Feature work then becomes an ambiguous backlog rather than a chain of testable release outcomes. A milestone can also group independent features and mask incomplete dependent behavior. Conversely, demanding the complete final product before any feature engineering would freeze useful bounded progress.

A generic standard must not copy consumer-specific product priorities, secrets, environment proof or acceptance into a public standard repository. No universal CI workflow can infer whether a particular runtime is ready or whether two business capabilities really must be delivered together.

## Decision

1. **Base-first:** Prioritize one smallest safe, usable vertical Base contract before activation of dependent feature expansion: B0 scoped, B1 architecture reviewed, B2 implemented, B3 independently candidate-verified, B4 accepted initial release in its explicitly stated channel. A Test RC never authorizes Production.
2. **No global freeze:** Continue true security repairs, independent research, documentation and safely default-off preparation while downstream prerequisites are blocked. Only the affected Feature or release unit is HOLD.
3. **Per-feature plan:** Reuse the existing canonical Feature Issue plus Spec/Plan; record outcome, reuse-first decision, dependency classification, risk/verification, stage exits, owner and compatibility/rollback. Do not create a second mutable status registry or one PR for every requirement.
4. **Dependency-aware releases:** Independently usable prerequisite first; inseparable features one atomic acceptance/release unit; unrelated features independent candidates. Resolve graph cycles through architecture and owner decision rather than inventing a release order. Weight measures integration scope, not security priority, velocity, or acceptance.
5. **Version/trace:** An Issue, PR, accepted Feature and official Release are distinct. Frozen RC corrections advance rc.N only when a new candidate is actually issued; stable SemVer PATCH/MINOR/MAJOR follow compatible fix/new compatible feature/breaking contract. Honor pre-1.0 contract and migration decisions, exact-main tags, ACC verification, immutable provenance and original Product authority. No approved capability disappears because unslotted or blocked.
6. **Bounded adoption:** Introduce human-reviewed BASE/TRN process rules on a new exact KavoshStart release and its opt-in consumer upgrade. Do not retroactively invalidate prior Production releases, change required workflow names, receipts, schema or runner trust, or auto-assign a Base Gate from the presence of a file.

## Alternatives considered

- **Enforce a universal global freeze until all target features ship:** rejected; confuses Base with Product scope, blocks unrelated repairs and adds unnecessary delivery delays.
- **One enormous feature-catalog milestone with release only at the end:** rejected; hides independent acceptance and produces avoidable operational coupling.
- **Release each PR as a product version:** rejected; source changes are not necessarily accepted user-visible capabilities.
- **Machine-declare Base readiness from a JSON flag:** rejected; falsifiable without current environment and independent acceptance.
- **New private portfolio release service or permanent second status ledger:** rejected; GitHub already owns live state and release/acceptance evidence.

## Consequences

- T1/T2 initial Base and next-features planning become a clear prerequisite review workflow. A prior accepted Base counts when authentic and relevant; it is never built again merely to satisfy a new template.
- The public scaffold may include a Base contract and Feature decision form. Current maintained consumers upgrade only with pinned Release and deliberate migration; an old tag remains unaffected.
- `tooling/feature_delivery.py` can reject structural cycles, unknown dependencies and fake independent groups in a **user-provided plan**; it cannot decide priority, security, architecture, acceptance, deployment, support or release authorization.
- Introducing additional hard machine-enforced project gates later is a separate release/migration compatibility decision. This proposal tentatively targets the next compatible minor after the current stable line; actual version is determined and verified at release time, not assumed by a draft.

## Enforcement and verification

- BASE/TRN are **MUST / R (human review)**, explicitly listed under R-only MUST rules. A machine cannot establish the truth of a Base or Feature just by seeing its file.
- The T2 Base contract template and Feature Issue form give stable decision fields; `START.md` handles NEW/ADOPT/UPGRADE/WORK routing.
- Focused offline positive/negative tests validate unique feature owner assignment, required dependency reasons, topological waves, explicit atomic co-release, unknown prerequisite and cycle denial. Template/rule consistency tests prevent silent drift. These tests certify only structure, not consumer product Gate success.
- Existing REL, ACC, PR, runner and public SEC-5 controls remain mandatory; no workflow or release bypass is introduced.

## Rollout and rollback

First obtain independent source/policy review and exact-head CI in the public repository. Merge only with the current owner's authorization and let Release Please and the regular tagged-release workflow handle SemVer. If compatibility review finds a genuine consumer contract break, move the rule introduction metadata and release target to an approved **major** before merge. For a consumer, use UPGRADE with a bounded Issue and chosen Base checkpoint; rollback is to its prior immutable pinned standard version, not mutation of a released tag.
