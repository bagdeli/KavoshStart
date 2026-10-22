# Initial Base Contract — stable design and acceptance scope

> Architecture contract for the first **usable** project Base. No live status, current SHA, open PR list or fabricated gate result belongs here. Approval/evidence live in project GitHub Issues, PRs, checks and releases. Never copy this example verbatim as an accepted product decision.

## Intended Base outcome
- **First observable consumer/admin/operator journey:** Describe one actually useful vertical path, including entry, decision/enforcement, result and diagnostic recovery.
- **Runtime and supported channel:** Specify which Test/consumer context is in-scope; a Test RC is not Production.
- **In scope:** Only necessary foundational modules, contracts and trust boundaries.
- **Not in the initial Base (retained approved product scope):** Link existing Feature Issues; do not silently mark them done or delete them.
- **Owner/decision source:** Identify the product/architecture authority in the private consuming project.

## Base architecture
- Existing/native components to reuse, owning modules, providers and one-writer boundaries:
- Actual trust, identity, tenant, data, licensing, logging and secrets invariants applicable to this Base:
- API/DB/migration/dependency and deployed artifact identity:
- Build/install/run/health/version from clean environment; supported configurations:
- Safe rollback, upgrade/recovery, operational diagnosis and support:
- Required independent decisions/ADR or allowed non-applicability with rationale:

## B0–B4 acceptance contract (criteria only, not current status)
| Stage | Checkable outcome | Evidence source / required reviewer |
|---|---|---|
| B0 scope | Smallest meaningful Base and dependencies explicitly decided | Product owner Issue / accepted requirement |
| B1 design | Contracts and security boundaries reviewed | Design/ADR link as applicable |
| B2 implemented | Build and focused native tests on exact source | PR, required checks, provenance |
| B3 verified | Reproducible real journey and applicable negative/recovery checks on one candidate | Accepted independent evidence in GitHub |
| B4 initial release | Versioned and accepted Base artifact in stated channel; support/rollback identified | Immutable main-derived tag + GitHub Release + decision |

An existing consumer starts at the **first unproven stage**. No row is self-certifying. Before feature activation, resolve dependencies, delivery units and the exact supported channel through the canonical GitHub Feature Issue/Spec and `standard/16-base-first-feature-delivery.md` of the pinned KavoshStart version.
