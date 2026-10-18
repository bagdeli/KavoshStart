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
| Planning | issues + labels | + milestone per release, Project board | + epics, **spec per feature** (`specs/`) |
| ADR | optional | required for architectural decisions | required + review in PR |
| Environments | none | test + production (if server) | test + production, prerelease channel |
| CI on PR | semantic `check` adapter (lint+test) | semantic `check` + build | + contract/migration checks; heavy jobs only on `main`/label `ci:full` |
| AI review workflow | no | optional (`ai-review.yml`) | yes |
| Secret scan in CI | no (local hook) | yes | yes |
| Release | gated release strategy (release-please is the scaffold default) | + rc on test | + rc → UAT → final |
| Runner (CI-1/2) | Private: existing isolated self-hosted allowed; hosted only with explicit per-run approval | Same; exact-head dispatch for private hosted only | Public standard GitHub-hosted minutes free; self-hosted requires CI-2 trust ADR and excludes untrusted fork code |
| **GitHub-hosted minutes authorization by default** | **0** | **0** | **0** |
| Max concurrent open PRs (ready) | 2 | 3 | 3 |

## Budget rule (CI-3)
Private GitHub Actions may run on an existing isolated self-hosted server runner with CI-2 trust ADR (ADR-0018). Private GitHub-hosted usage is prohibited without explicit prior owner/admin approval of **each exact run** after asking, even before free allowance is exhausted; only manual scoped dispatch may use it. Public standard GitHub-hosted minutes are free; larger runners/storage cost separately. 'monthlyMinutesBudget' is a planning hint, not spending authorization. T1/static may choose 'none' without Actions.
