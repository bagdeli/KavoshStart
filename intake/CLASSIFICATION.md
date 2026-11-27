# Classification — Tier × Runtime × Capabilities

Three independent but related axes describe a project:

- **Tier** decides baseline assurance/process.
- **Runtime** describes the execution shape.
- **Capabilities** are composable applicability/evidence profiles.

Core rules (`standard/RULES.md`, column "All") apply to every combination. Capabilities do not create a new Tier per technology and never override Tier/Runtime facts.

## Axis 1 — Tier (apply top-down, first match wins)

| Tier | Trigger (any one is enough) | Typical examples |
|---|---|---|
| **T2 — Platform** | `data.regulatedIntegrations` not empty · `data.sensitivity = financial` · `data.multiTenant = true` · `size.domains ≥ 4` · `size.parallelStreams ≥ 3` · `users.audience = customers` and `users.scale ≥ 100-1000` | regulated or multi-domain customer platform |
| **T1 — Application** | `runtime = server` · `data.sensitivity = personal` · `size.domains 2–3` · `size.lifetime ≠ weeks` · `ui.kind ∈ {web, admin}` · `projectKind = library` (consumed by other Kavosh repos) | illustrative server app, versioned component library |
| **T0 — Tool** | none of the above | script, CLI, one-off importer, static landing page, prototype |

The owner may move a project **up** freely. Moving **down** requires an ADR in the project explaining why the trigger does not apply.

## Axis 2 — Runtime

| Runtime | Meaning | Typical delivery | Template overlay |
|---|---|---|---|
| `none` | no long-lived runtime: library, CLI, script, control-plane | `none` or `release-artifact` through the declared release adapter | — |
| `static` | only static files | `pull-build` or ADR-backed custom delivery | `runtime/server` (static profile) |
| `server` | always-on service(s) | `pull-build`, `pull-image` or ADR-backed custom delivery | `runtime/server` |
| `desktop` | installable app | normally `release-artifact` through the declared artifact adapter | — |

## Axis 3 — Composable capabilities

Capabilities answer **what contracts/evidence can apply**, not which language/framework is used.

| Capability | Meaning |
|---|---|
| `control-plane` | governance/standards/orchestration that controls other work |
| `package` | versioned consumable library/package/API surface |
| `server` | long-lived service/runtime behavior |
| `browser-ui` | browser-rendered product/UI behavior, including accessibility/RTL evidence |
| `desktop` | installable desktop application/runtime |
| `persistent-data` | durable database/state ownership |
| `migration` | schema/data migration, backfill, restore/rollback concerns |
| `infrastructure` | infrastructure-as-code/runtime infrastructure ownership |
| `release-artifact` | immutable downloadable/package artifact delivery |
| `regulated` | financial/regulated integration or equivalent high-assurance boundary |
| `cms-wordpress` | WordPress/WooCommerce lifecycle, Site Editor/DB override and theme/plugin concerns |

Some capabilities are derivable and therefore mandatory when the manifest proves the fact: library→`package`, server→`server`, web/admin UI→`browser-ui`, desktop→`desktop`, database→`persistent-data`+`migration`, release-artifact delivery→`release-artifact`, financial/regulated integration→`regulated`, WordPress/WooCommerce→`cms-wordpress`.

Other capabilities such as `control-plane` and `infrastructure` are explicit because Core should not guess them from incidental tool names. Additional valid capabilities are allowed when they genuinely describe project scope.

## What each tier gets

| | T0 Tool | T1 Application | T2 Platform |
|---|---|---|---|
| Planning | existing task/PR or Issue; labels as applicable | same; milestone/Project board only when useful | same; Epics and scoped Specs only for genuinely complex coordination (WK-1/3/5) |
| ADR | optional | for material architectural decisions | for material decisions, not one ADR per routine test or permission |
| Environments | none | only declared persistent environments | only the owner's declared persistent environments; a separate Test host/VM/channel is never inferred from T2 |
| CI on PR | semantic `check` adapter (lint+test) | semantic `check` + build | relevant contract/migration checks only when the changed capability needs them; no duplicated giant suite |
| AI review workflow | no | only by explicit opt-in | only by explicit opt-in; never scaffolded automatically |
| Secret scan in CI | no (local hook) | yes | yes |
| Release | gated product release when publishing code | optional RC only for an actually selected Test channel | optional RC/UAT only when an actual product release & risk requires them; routine upstream maintenance uses native controls |
| Runner (CI-1/2) | Private: existing isolated self-hosted allowed; private hosted only with exact-run billing-owner consent and manual dispatch | same; Trust ADR optional, actual isolation required | same; public standard GitHub-hosted minutes free, self-hosted follows CI-2 and excludes untrusted fork code |
| **Private metered GitHub authorization by default** | **none** | **none** | **none** |
| Max concurrent open PRs (ready) | 2 | 3 | 3 |

**Collaboration is separate from Tier.** A T2 project may be managed by one person: that does not create an independent reviewer, paid AI workflow, legal adviser, two attestation Apps, or a dedicated physical Test. Ask owner preferences once at intake (D3/G9); default is none. `continuous`, `review.teamProcess=true` and `review.independentHumanReview=true` are separately and explicitly selected, never inferred from Tier. WK-1 formal issue labels apply only to the selected team process.

## Budget rule (CI-3)
Private GitHub Actions may run on an existing approved and actually isolated self-hosted runner under CI-2; a Trust ADR is optional, and an existing private owner-operated runner may use its actual native labels. Public/team self-hosted profiles retain the dedicated custom selector. Private GitHub-hosted usage (including free allowance) requires prior explicit consent of the designated human billing owner for **each exact run**, then scoped manual dispatch; other admins, agents and budgets cannot authorize it (ADR-0019). Other metered private GitHub features require that same owner's specific prior consent. Public standard GitHub-hosted minutes are free; larger runners/storage may cost separately. `monthlyMinutesBudget` is a planning hint, not spending authorization. T1/static may choose `none` without Actions. See [CI guidance](../standard/04-ci-runners-minutes.md) for the actual trust and test-selection boundaries.
