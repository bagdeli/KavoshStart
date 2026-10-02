# Classification — Tier × Runtime

Two independent axes. **Tier** decides how much process (ceremony) the project needs.
**Runtime** decides how it is built and delivered. The core rules (`standard/RULES.md`, column "All")
apply to every combination.

## Axis 1 — Tier (apply top-down, first match wins)

| Tier | Trigger (any one is enough) | Typical examples |
|---|---|---|
| **T2 — Platform** | `data.regulatedIntegrations` not empty · `data.sensitivity = financial` · `data.multiTenant = true` · `size.domains ≥ 4` · `size.parallelStreams ≥ 3` · `users.audience = customers` and `users.scale ≥ 100-1000` | regulated or multi-domain customer platform |
| **T1 — Application** | `runtime = server` · `data.sensitivity = personal` · `size.domains 2–3` · `size.lifetime ≠ weeks` · `ui.kind ∈ {web, admin}` · `projectKind = library` (consumed by other Kavosh repos) | KavoshSMS, KavoshWebManager, KavoshUI |
| **T0 — Tool** | none of the above | script, CLI, one-off importer, static landing page, prototype |

The owner may move a project **up** freely. Moving **down** requires an ADR in the project explaining why the trigger does not apply.

## Axis 2 — Runtime

| Runtime | Meaning | Delivery | Template overlay |
|---|---|---|---|
| `none` | library, CLI, script | `make package` → assets on the gated release; no server | — (release.yml `package: true`) |
| `static` | only static files | own web server via `pull-build` (Pages needs a public repo on Free) | `runtime/server` (static profile) |
| `server` | always-on service(s) | pull-based deploy to Kavosh server (`standard/07-deployment.md`) | `runtime/server` |
| `desktop` | installable app | `make package` → installer assets on the gated release | — (release.yml `package: true`) |

## What each tier gets

| | T0 Tool | T1 Application | T2 Platform |
|---|---|---|---|
| Planning | issues + labels | + milestone per release, Project board | + epics, **spec per feature** (`specs/`) |
| ADR | optional | required for architectural decisions | required + review in PR |
| Environments | none | test + production (if server) | test + production, prerelease channel |
| CI on PR | `make check` (lint+test) | `make check` + build | + contract/migration checks; heavy jobs only on `main`/label `ci:full` |
| AI review workflow | no | optional (`ai-review.yml`) | yes |
| Secret scan in CI | no (local hook) | yes | yes |
| Release | gated release-please (REL-5) | + rc on test | + rc → UAT → final |
| Runner (by visibility, CI-1) | private: hosted with per-run authorization or isolated self-hosted · public: standard hosted | private: hosted with per-run authorization or isolated self-hosted · public: standard hosted | capacity based on queue/SLO; same privacy/cost rules |
| **GitHub-hosted minutes authorization by default** | **0** | **0** | **0** |
| Max concurrent open PRs (ready) | 2 | 3 | 3 |

## Budget rule (CI-3)
Runner choice is not determined by visibility alone: public defaults to standard hosted; private may use hosted or isolated self-hosted.
Private hosted runs use shared quota and therefore require a direct, one-run authorization and manual dispatch. Every manifest keeps `monthlyMinutesBudget` at **0**: that field never authorizes
shared quota. A private hosted run needs direct owner authorization for one bounded dispatch; the shared Free allowance is never consumed automatically. Keep pushes per PR low anyway (CI-6): self-hosted
capacity is finite too.
