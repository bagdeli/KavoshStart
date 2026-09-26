# Intake questionnaire

Every answer maps to a field of `kavosh.project.json` (column **Field**). **R** = required before scaffolding.
Ask the owner in Persian; the Persian wording is given for each question. Always offer a default.

## A. Identity
| # | R | Question (FA) | Field | Notes / default |
|---|---|---|---|---|
| A1 | R | نام پروژه و نام ریپو؟ | `name`, `repo` | repo = PascalCase like other Kavosh repos, e.g. `KavoshSMS` |
| A2 | R | هدف پروژه در یک جمله؟ | `summary` | Must describe the product now, not the vision |
| A3 | R | چه کسانی از آن استفاده می‌کنند و تقریباً چند نفر؟ | `users.audience`, `users.scale` | `internal` / `customers` / `public`; `1-10`, `10-100`, `100-1000`, `1000+` |
| A4 | R | اولین خروجی قابل‌استفاده (v0.1.0) دقیقاً چه کاری انجام می‌دهد؟ | `firstRelease` | 1–5 bullet points; becomes milestone v0.1.0 |
| A5 |   | چه چیزهایی عمداً در این پروژه نیست؟ | `outOfScope` | Prevents scope drift (KavoshERP README vs AGENTS.md conflict) |

## B. Runtime and deployment
| # | R | Question (FA) | Field | Notes / default |
|---|---|---|---|---|
| B1 | R | آیا برنامه باید روی سرور همیشه روشن اجرا شود؟ | `runtime` | No → `none` (library/CLI/script) or `desktop`; only static files → `static`; yes → `server` |
| B2 | R* | سرور کجاست؟ ایران / خارج / هر دو؟ | `deploy.location` | *if runtime=server |
| B3 | R* | سرور به github.com و ghcr.io دسترسی پایدار دارد؟ | `deploy.method` | yes → `pull-image` or `pull-build`; no → `pull-build` via mirror/relay (KavoshRepo) |
| B4 | R* | چه محیط‌هایی لازم است؟ | `deploy.environments` | default T1: `["test","production"]`; T0: `[]` |
| B5 |   | دامنه/آدرس هر محیط؟ | `deploy.urls` | never put credentials here |
| B6 | R* | اگر static: کجا منتشر شود؟ | `deploy.method` | GitHub Pages is **not** available for private repos on Free → own server (`pull-build`) or make the repo public |

## C. Data and risk
| # | R | Question (FA) | Field | Notes / default |
|---|---|---|---|---|
| C1 | R | چه داده‌ای نگه‌داری می‌کند؟ | `data.sensitivity` | `none` / `internal` / `personal` / `financial` |
| C2 | R | با سامانه‌ی بیرونی حساس وصل می‌شود؟ (مودیان، ستاد، بانک، پیامک، درگاه پرداخت) | `data.regulatedIntegrations` | list; any entry pushes tier to T2 unless read-only public data |
| C3 | R | چند مشتری/سازمان جدا از هم (multi-tenant)؟ | `data.multiTenant` | boolean |
| C4 |   | دیتابیس؟ | `stack.database` | `postgresql` default for server; `sqlite` for tools; `none` |

## D. Size and lifetime
| # | R | Question (FA) | Field | Notes / default |
|---|---|---|---|---|
| D1 | R | تقریباً چند ماژول/حوزه‌ی کسب‌وکاری مستقل دارد؟ | `size.domains` | e.g. CRM + Finance + HR = 3 |
| D2 | R | عمر مورد انتظار؟ | `size.lifetime` | `weeks` / `months` / `years` |
| D3 | R | چند عامل/نفر هم‌زمان روی آن کار می‌کنند؟ | `size.parallelStreams` | 1 = only you + one agent at a time |

## E. Interface
| # | R | Question (FA) | Field | Notes / default |
|---|---|---|---|---|
| E1 | R | رابط کاربری دارد؟ چه نوعی؟ | `ui.kind` | `none` / `web` / `admin` / `desktop` |
| E2 | R* | از KavoshUI استفاده شود؟ کدام نسخه؟ | `ui.kavoshui` | *if ui.kind≠none; default: latest KavoshUI release, pinned exactly |
| E3 | R* | زبان‌ها و جهت؟ | `ui.locales` | default `["fa-IR"]` RTL; add `en` only if needed |

## F. Engineering
| # | R | Question (FA) | Field | Notes / default |
|---|---|---|---|---|
| F1 | R | زبان/فریم‌ورک؟ محدودیتی هست؟ | `stack.languages`, `stack.frameworks` | defaults: API → Python 3.12 + FastAPI; Web → TypeScript + Next.js (KavoshUI compatible); CLI → Python |
| F2 | R | کدام عامل‌ها روی آن کار می‌کنند؟ | `agents` | `claude`, `codex`, `copilot`, `gemini` |
| F3 |   | وابستگی به ریپوهای دیگر Kavosh؟ | `dependsOn` | e.g. `KavoshLicense`, `KavoshUI` |

## Rules for asking
- Ask everything missing in **one** message. Number the questions with the IDs above.
- If the owner answers vaguely ("معمولی", "بعداً"), use the default and say so explicitly.
- Record assumptions in `PROJECT.md` → "Assumptions" so they can be revisited.
