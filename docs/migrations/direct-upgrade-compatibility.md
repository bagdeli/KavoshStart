# Direct upgrade compatibility for KavoshStart v1–v6

This guide does not announce a new release. The target must be an **actually published exact stable** `vX.Y.Z` tag. Older pinned consumers remain unchanged until their own authorized PR. Direct major upgrades are possible without installing each intermediate version, but all applicable **breaking contracts** must be reviewed.

## One bounded consumer-owned migration PR

1. Read the real default branch's `kavosh.project.json`, `AGENTS.md`, CI/release callers, required check names, accepted ADRs and runtime. If no manifest exists on main, use **ADOPT**, not UPGRADE. A Draft or Issue is not live adoption.
2. Compare the existing tag with the published target using `CHANGELOG.md`, versioned schema and major migration guides. List affected contracts, source/runner trust, exact pins, custom tool adapters, provider ownership and relevant release/acceptance outcomes. Do **not** restart all historical requirements.
3. Confirm real runner labels and accepted CI-2 trust model on the existing host: repository/workload scoping, restricted account, file/socket/credential separation, network boundary, untrusted-code policy. Existing correctly controlled self-hosted is allowed. No two disposable VMs, JIT registration or new server is a blanket requirement. A firewall alone is not local host isolation.
4. Change the manifest tag, **all pinned reusable workflow references** and only the affected consumer-owned template/configuration/command adapters together. Preserve least privilege, exact jobs/contexts, required `enforce:true`, release identity and no unauthorized private-hosted fallback. `scaffold.py --adopt` prepares reviewable `*.kavosh-new` files, never silently overrides.
5. For T2 use `acceptance.mode=continuous`; missing `assurance` means strict `attested`, whereas `risk-based` is an explicit versioned option for qualified low/medium CI-only items. High/critical or specialist evidence still needs real independent source-bound proof. Keep actual release outcomes, not one AC for every upstream library or legacy requirement; reuse valid equivalent evidence, or `keep/narrow/merge/retire` a stale criterion through its owning Issue/Spec/PR with preserved history and actual owner decision.
6. Verify **changed** manifest/schema/caller/runner/acceptance contracts plus existing semantic check/required CI on exact source. Additional specialist, performance, UI and destructive tests only when their changed risk/integration/release boundary warrants it. Static green cannot prove physical runner isolation, customer Production or a human consent decision.
7. High-risk merge requires its own owner authorization for exact current head and normal green gates. Consumer release/Production are separate actions. In **private** GitHub, paid or metered service use including included GitHub-hosted minutes needs prior explicit **designated human billing owner** authorization for the exact action; another admin, AI or remaining quota never approves it.

## Starting-version review

| Existing pin | Material forward changes to reconcile | Do not automatically require |
| --- | --- | --- |
| **v1.x** | v2 change risk/approval/command contract replaces universal PR-size gates; v2.1 capabilities and rule registry; then later major contracts. | New tests per historical requirement, a replacement of still-functional product architecture. |
| **v2.x** | v3 continuous T2 source-bound receipt/decision integrity, v2.1 capability profiles, then v4–v6. | Fake attestors/receipts or re-certifying every upstream internal method. |
| **v3.x** | v4 optional `acceptance.assurance=risk-based`, strict default `attested`, real source-bound UI review; then v5–v6. | Silent waiver of high/critical specialist evidence or claiming screenshots as independent human approval. |
| **v4.x** | v5 provider-neutral `ui.designSystem` exact package/version or justified `ui.exceptionADR`, followed by v6 runner correction. | Treating v5's historical private hosted-only restriction as v6 policy; forcing UI package for non-UI products. |
| **v5.x** | v6 allows appropriately isolated private Self-hosted GitHub Actions again; check `ci.runner`, actual labels/ADR, nested caller selection and explicit private-hosted consent. | Provisioning new runners or enabling private hosted minutes automatically. |
| **v6.x** | Future **published** source-owned requirement/retirement guidance and flexible real self-hosted labels/owner-only metered consent; read that release's precise notes. | Retroactive invalidation of current pins, global specialist suites, more VMs or a second acceptance ledger. |

## Minimal evidence matrix

| Changed boundary | Right-sized proof |
| --- | --- |
| Documentation/agent instructions | Current approved contract/source and targeted doc/agent checks, not runtime revalidation. |
| Manifest, CI adapter, runner | Schema/governance, exact pinned caller/job/runs-on, actual runner configuration and bounded operational check **when trust changes**. |
| Upstream package/design-system | Exact version, compatibility and real consumer integration; not upstream's entire suite again. |
| User journey, role/tenant/financial behavior | Focused observed behavior and negative authorization/data checks at affected boundary. |
| Migration/release/environment | Real source-bound rollback, artifact and environment identity/evidence where affected; no inferred Production access. |

**Stop rules:** Do not fabricate PASS, remove an effective safety obligation without scoped owner decision, bypass an actually red required check, auto-upgrade another repository, publish a planned tag, grant secrets, create new infrastructure or dispatch paid private GitHub capacity. Historical [v5](v5-provider-neutral-and-hosted-only.md) and [v6](v6-private-runner-choice.md) migrations are provenance and context; the latest accepted rules require the future **published tag**.
