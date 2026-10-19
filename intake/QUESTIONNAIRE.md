# Intake questionnaire

A–F use existing `kavosh.project.json` fields. **R** = required before scaffolding; **R*** = required only when its condition applies.
G records architecture decisions in the existing `PROJECT.md` section, not new manifest fields or a new tracker.
Ask in Persian. A suggested default is a proposal, never an accepted answer. Reuse an explicit answer already supplied for this project; do not ask it again unless its scope changed.

## A. Identity
| # | R | Question (FA) | Field | Notes / default |
|---|---|---|---|---|
| A1 | R | نام پروژه و نام ریپو؟ | `name`, `repo` | use a project-owned repository name; public examples are synthetic |
| A2 | R | هدف پروژه در یک جمله؟ | `summary` | Must describe the product now, not the vision |
| A3 | R | چه کسانی از آن استفاده می‌کنند و تقریباً چند نفر؟ | `users.audience`, `users.scale` | `internal` / `customers` / `public`; `1-10`, `10-100`, `100-1000`, `1000+` |
| A4 | R | اولین خروجی قابل‌استفاده (v0.1.0) دقیقاً چه کاری انجام می‌دهد؟ | `firstRelease` | 1–5 bullet points; becomes milestone v0.1.0 |
| A5 | R | چه چیزهایی عمداً در این پروژه نیست؟ | `outOfScope` | Prevents scope drift when README and AGENTS.md describe different product boundaries |

## B. Runtime and deployment
| # | R | Question (FA) | Field | Notes / default |
|---|---|---|---|---|
| B0 | R | مخزن خصوصی است یا عمومی؟ Runner مستقل نصب‌شده روی سرور وجود دارد؟ | `visibility`, `ci.runner` | private → Self-hosted ایزوله در صورت وجود بلامانع؛ GitHub-hosted حتی در سهمیهٔ رایگان فقط پس از اجازهٔ قبلی و صریح شخص مالک اختیار مالی برای همان Run؛ سایر امکانات پولی/سهمیه‌ای GitHub در private نیز فقط با مجوز موردی او (ADR-0019). public → GitHub-hosted استاندارد رایگان؛ self-hosted با CI-2. T1/static → `none`. هرگز runner یا مجوز هزینه را حدس نزنید. |
| B0b | R* | اگر Self-hosted در private یا public انتخاب شد، trust model واقعی سرور، کنترل fork/کد نامطمئن، credential و ایزولیشن چیست؟ | `ci.runnerLabels`, `ci.runners`, `ci.trustModelADR` | ADR و label واقعی اختصاصی repo طبق CI-2 (از جمله ARM64/custom)؛ تفکیک کد نامطمئن از release/deploy/secrets و راستی‌آزمایی عملیاتی Runner ضروری است؛ ADR مجوز Hosted یا خدمت پولی نیست. |
| B1 | R | آیا برنامه باید روی سرور همیشه روشن اجرا شود؟ | `runtime` | No → `none` (library/CLI/script) or `desktop`; only static files → `static`; yes → `server` |
| B2 | R* | سرور کجاست؟ ایران / خارج / هر دو؟ | `deploy.location` | *if runtime=server |
| B3 | R* | آیا محیط اجرا می‌تواند به مقصدهای لازم برای دریافت/ارسال فایل متصل شود؟ اگر نه، محدودیت شبکه چیست؟ | `deploy.method` و تصمیم مستندِ اتصال | از `pull-image` یا `pull-build` فقط وقتی مسیر آن قابل اجراست استفاده شود. ابزار انتقال، proxy یا mirror خاصی به‌صورت عمومی اجباری نیست. شکست تکراری دانلود/آپلود با پروتکل گزارش URL/DNS/IP در `START.md` ثبت شود؛ مسیر جایگزین تنها با انتخاب مالک |
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
| E2 | R* | کدام بستهٔ Design System با چه نسخهٔ دقیقی انتخاب می‌شود؟ | `ui.designSystem` یا `ui.exceptionADR` | *if ui.kind≠none; انتخاب بسته و نسخهٔ دقیق و مستندات مصرف/حقوق فونت فقط در مخزن پروژه، بدون default اجباری |
| E3 | R* | زبان‌ها و جهت؟ | `ui.locales` | default `["fa-IR"]` RTL; add `en` only if needed |

## F. Engineering
| # | R | Question (FA) | Field | Notes / default |
|---|---|---|---|---|
| F1 | R | زبان/فریم‌ورک؟ محدودیتی هست؟ | `stack.languages`, `stack.frameworks` | defaults: API → Python 3.12 + FastAPI; Web → TypeScript + Next.js (subject to the selected UI package); CLI → Python |
| F2 | R | کدام عامل‌ها روی آن کار می‌کنند؟ | `agents` | `claude`, `codex`, `copilot`, `gemini` |
| F3 |   | وابستگی به ریپو یا سرویس دیگر هست؟ | `dependsOn` | منابع خصوصی تنها در مخزن مصرف‌کننده ثبت می‌شوند؛ نمونهٔ عمومی بدون وابستگی واقعی است |
| F4 | R | آیا این پروژه را ریپوهای دیگر Kavosh مصرف می‌کنند (کتابخانه/استاندارد)؟ | `projectKind` | `application` / `library` / `tool`; library ⇒ at least T1 |
| F5 | R | این پروژه چه capabilityهای پایدار دارد؟ | `capabilities` | choose from `control-plane`, `package`, `server`, `browser-ui`, `desktop`, `persistent-data`, `migration`, `infrastructure`, `release-artifact`, `regulated`, `cms-wordpress`; derive obvious entries from earlier answers, then ask only for non-derivable scope |

## G. Architecture decisions — ask applicability first

Review these subjects at initial intake for every project. **R** here means an explicit applicability/choice decision before dependent implementation, not mandatory implementation of the capability. A recorded answer can satisfy the question without asking it again. The **Record** column points to the existing project sheet; reference A–F fields rather than duplicating their values.

| # | R | Question (FA) | Record | Conditional detail / architectural effect |
|---|---|---|---|---|
| G1 | R | این محصول لایسنس می‌خواهد یا نه؟ اگر بله، از کدام سازوکار مصوب استفاده کند؟ | `PROJECT.md#architecture-decisions` | Ask regardless of internal/public audience. When needed, decide the licensing provider/contract, entitlement boundary (for example user, organization, installation or capability), enforcement location and disconnected/invalid behavior. Do not invent lease periods, cryptographic protocols or a licensing service. Product licensing is distinct from third-party/font usage rights. |
| G2 | R | ورود کاربر و کنترل دسترسی چگونه باشد؟ حساب محلی، ورود یکپارچه یا بدون ورود؟ | `PROJECT.md#architecture-decisions` | Decide identity provider, relevant roles and trusted authorization boundary before dependent routes/UI. Licensed capability does not grant a user permission. Reuse an approved authentication/authorization implementation instead of rebuilding it. |
| G3 | R | مرجع اصلی و مالک داده کیست و جداسازی سازمان‌ها چگونه انجام شود؟ | `PROJECT.md#architecture-decisions` | Reference `data.multiTenant` and `stack.database`; clarify authoritative systems, shared/private data and tenant boundaries only where applicable. Do not turn a UI value format into a product storage model. |
| G4 | R | کدام اتصال‌ها ضروری‌اند و هنگام قطع شبکه یا سرویس چه رفتاری لازم است؟ | `PROJECT.md#architecture-decisions` | Reference `dependsOn` and regulated integrations; distinguish required/optional services, offline needs, retry/queue needs and operator-visible failure. Ask channel/notification needs only when relevant; do not add an integration because it exists in the portfolio. |
| G5 | R | دادهٔ موجود یا مهاجرت داریم؟ نگهداری، حذف و بازیابی داده چه انتظاری دارد؟ | `PROJECT.md#architecture-decisions` | For persistent data, record the starting data source, migration/retention and recovery expectations; detailed rehearsal belongs before affected operations. No database means no invented database migration or backup work. Existing DEP/SEC safeguards remain applicable. |
| G6 | R | کدام روش پیاده‌سازی مصوب مناسب است و چه بخش‌هایی نباید دوباره ساخته شوند؟ | `PROJECT.md#architecture-decisions` | Reference `stack` and approved engineering decisions; prefer mature third-party options when risk, TCO and redistribution obligations allow. Review actual integration/distribution model per TP-1/TP-2; product licensing is separate. No universal framework is required. |
| G7 | R | رابط روی چه دستگاه‌ها و با چه زبان، تقویم و هویت بصری استفاده می‌شود؟ چاپ یا خروجی خاص لازم است؟ | `PROJECT.md#architecture-decisions` | If `ui.kind=none`, record not-needed and do not create UI tasks. Otherwise reuse `ui` choices; select supported typography, density, accessibility and responsive needs from the selected design system. Ask Help/search/print/export needs conditionally, not as universal product features. Known font licence administration remains with its recorded owner; do not ask it again. |
| G8 | R | محدودیت اجرا، هزینه، کارایی و مسئول نگهداری چیست؟ | `PROJECT.md#architecture-decisions` | Reference `deploy` and `ci`; decide relevant availability, recovery, observability and capacity expectations. Reuse approved operational profiles. A recorded budget or environment is not execution/credential/Production authorization. |
| G9 | R | اولین خروجی با چه معیار و شاهدی پذیرفته می‌شود و کدام تصمیم‌ها با مالک می‌ماند؟ | `PROJECT.md#architecture-decisions` | Reference `firstRelease`, approved scope and authority. Plan risk-sized evidence with the capability. For continuous acceptance, identify the existing admitted evidence/decision producer and its availability before promising delivery; a missing producer is an explicit prerequisite, not permission to invent receipts or build a new App by default. |

## Recording choices without a second source of truth

Use the compact G1–G9 table in `templates/common/PROJECT.md`. Store settled choices and a source/reference only: `selected`, `not-needed`, or `inherited` with an explicit approved profile/version/reference. These describe design intent, not acceptance or live work status. Reuse existing manifest fields through references; do not invent schema keys. Material rationale uses an existing project ADR/Spec, not one ADR per question.

An `unresolved` answer stays in the selected Issue/Spec **Open questions**, with the decision owner, the dependent work and when the answer is needed. Block only dependent implementation; unrelated authorized work may continue. Do not call the architecture finalized, scaffold a dependent implementation, or silently substitute a default. Repository identity and required scaffold inputs must still be known before scaffolding.

`not-needed` is not unanswered: it creates no implementation, test, evidence receipt or separate Issue. An inherited choice is reused, not re-approved on every session. A new scope or changed dependency can reopen only the affected decision; unchanged answers stay in force. Repository visibility and the fact that the standards are internal do not decide product licensing, identity or data sensitivity.

## Rules for asking
- Read existing project answers and explicit owner instructions first. Ask only missing decisions in one grouped message, with conditional follow-ups for selected capabilities.
- Never convert vague answers ("معمولی", "بعداً") into approval for licensing, identity, authorization, tenancy, data retention/deletion, paid operations or release authority. Offer alternatives and record unresolved dependent work. Explicit acceptance of an applicable pre-approved default is valid.
- Capture architecture-shaping choices early; leave reversible detail to the related capability before its acceptance. Do not conduct an exhaustive design of every possible feature at intake.
- Examples illustrate a decision class, not mandatory features or permission to inspect another project. Do not reopen an example product to apply this standard.
- Answers are not work items. Requirements, capability delivery and test observations are distinct; reuse one evidence source for all actually covered criteria with traceability. Never create one PR or receipt solely for every questionnaire/requirement row.
- Existing approval and operational safety rules are not waived by this questionnaire. Human review of these instructions is distinct from machine checks of their presence and consistency.
