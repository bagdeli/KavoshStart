# Classification — Tier × Runtime

Two independent axes. **Tier** decides how much process (ceremony) the project needs.
**Runtime** decides how it is built and delivered. The core rules (`standard/RULES.md`, column "All")
apply to every combination.

## Axis 1 — Tier (apply top-down, first match wins)

| Tier | Trigger (any one is enough) | Typical examples |
|---|---|---|
| **T2 — Platform** | `data.regulatedIntegrations` not empty · `data.sensitivity = financial` · `data.multiTenant = true` · `size.domains ≥ 4` · `size.parallelStreams ≥ 3` · `users.audience = customers` and `users.scale ≥ 100-1000` | KavoshERP, KavoshLicense |
| **T1 — Application** | `runtime = server` · `data.sensitivity = personal` · `size.domains 2–3` · `size.lifetime ≠ weeks` · `ui.kind ∈ {web, admin}` · the project is a library consumed by other Kavosh repos | KavoshSMS, KavoshWebManager, KavoshUI |
| **T0 — Tool** | none of the above | script, CLI, one-off importer, static landing page, prototype |

The owner may move a project **up** freely. Moving **down** requires an ADR in the project explaining why the trigger does not apply.

## Axis 2 — Runtime

| Runtime | Meaning | Delivery | Template overlay |
|---|---|---|---|
| `none` | library, CLI, script | GitHub Release assets / package; no server | — |
| `static` | only static files | own web server via `pull-build` (Pages needs a public repo on Free) | `runtime/server` (static profile) |
| `server` | always-on service(s) | pull-based deploy to Kavosh server (`standard/07-deployment.md`) | `runtime/server` |
| `desktop` | installable app | GitHub Release assets built on tag | — |

## What each tier gets

| | T0 Tool | T1 Application | T2 Platform |
|---|---|---|---|
| Planning | issues + labels | + milestone per release, Project board | + epics, **spec per feature** (`specs/`) |
| ADR | optional | required for architectural decisions | required + review in PR |
| Environments | none | test + production (if server) | test + production, prerelease channel |
| CI on PR | `make check` (lint+test) | `make check` + build | + contract/migration checks; heavy jobs only on `main`/label `ci:full` |
| AI review workflow | no | optional (`ai-review.yml`) | yes |
| Secret scan in CI | no (local hook) | yes | yes |
| Release | tag on demand | release-please, rc on test | release-please, rc → UAT → final |
| **Actions minutes budget / month** | **100** | **300** | **700** |
| Max concurrent open PRs (ready) | 2 | 3 | 3 |

## Budget rule (CI-3)
The Free plan gives the whole account **2,000 minutes/month**; every job is rounded **up** to a full minute.
Sum of budgets of all active projects must stay **≤ 1,600** (20 % reserve).
Before creating a new project, check `scripts/portfolio.py`. If there is no room: archive/pause a project,
lower a budget with the owner's approval, or classify CI jobs so that more run locally (`make check` before push).

Rough job costs (hosted Linux): governance ≈ 1 min per PR event · T0 CI ≈ 1–2 min · T1 CI ≈ 3–6 min · T2 CI ≈ 6–12 min.
Example: T1 with 25 PRs × 3 pushes × (1 + 5) ≈ 450 min — **too much**. Hence rule CI-6: push once per PR
when possible, CI does not run on draft PRs, and governance ignores label/edit noise.
