# KavoshStart

**استاندارد سریع و کم‌هزینه برای پروژهٔ تک‌مالک؛ کنترل‌های سازمانی چندنفره/دو App/وکیل/VM فقط با انتخاب صریح تیم بزرگ.** مهندسی، تست و انتشار واقعی محفوظ‌اند؛ ابزار/زبان و اندازهٔ diff قاعدهٔ عمومی نیست.

KavoshStart مرجع **عمومی و مستقل از مخازن مصرف‌کننده** برای استاندارد مهندسی، امنیت، CI و انتشار است. بستهٔ UI و اسناد خصوصی، فقط در مخزن خودِ مصرف‌کننده انتخاب و نگه‌داری می‌شوند.

## امنیت اطلاعات در مخزن عمومی

KavoshStart فقط استانداردهای مستقل از محصول و نمونه‌های کاملاً ساختگی دارد. نام، ساختار، نیاز، وضعیت، یافتهٔ تست/امنیت، مسیر مهاجرت، آدرس، شناسه، هزینه و هر نشانهٔ قابل‌استنتاج از مخازن خصوصی، **حتی در Issue، PR، Comment، Release و لاگ** نباید در این مخزن منتشر شود. بررسی منابع خصوصی برای الهام گرفتن مجاز است، اما نتیجه باید پیش از ثبت عمومی به یک اصل مستقل و بدون ردپای پروژه تبدیل شود (SEC-5). ابزار `scripts/public_source_guard.py` فقط نشانه‌های آشکار را می‌گیرد؛ مسئولیت بازبینی معنایی و عدم افشا همچنان با عامل و مالک است.

## مسیر پیش‌فرض سریع و بدون تشریفات

- یک **مالک انسانی** تصمیم‌های high-risk و انتشار را می‌گیرد؛ برای PR/UI به انسان دوم، مدل دوم یا اشتراک امضا نیاز نیست. T2 بودن به معنی داشتن تیم یا دو App نیست.
- **فرایند سریع تک‌مالک در نسخهٔ بعدی:** `review.teamProcess` پیش‌فرض `false` است؛ Issue-link، نام قالبی Branch، متن risk/AI و ADR صرفاً برای تشریفات، PR را قرمز نمی‌کند. این رفتار تا انتشار نسخهٔ major و ارتقای pin مصرف‌کننده فعال نیست. تیم بزرگ می‌تواند جداگانه `teamProcess=true` را انتخاب کند؛ CI و انتشار واقعی همچنان کنترل می‌شوند. یک Runner موجود خصوصی برای TEST کم‌ریسک با labelهای استاندارد کفایت می‌کند، به شرط جدابودن از اسرار/مجوز انتشار/Production.
- `acceptance.mode=none` برای پروژهٔ تک‌مالک در همهٔ Tierها معتبر است. Continuous Acceptance، attestation/GitHub Apps و reviewer مستقل فقط پس از سؤال و موافقت صریح مالک در intake فعال می‌شوند؛ فعال‌سازی قبلی consumer بدون PR خودش تغییر نمی‌کند.
- AGPL یا Licence روشن، وکیل یا پروندهٔ حقوقی اجباری برای هر PR ایجاد نمی‌کند؛ فقط تعهدات **واقعاً قابل‌اعمال** باید رعایت شوند، و عرضهٔ متعارض متوقف می‌ماند.
- Test/CI می‌توانند از میزبان موجودِ امن و کم‌دسترسی استفاده کنند؛ ماشین/VM دوم یا اسکن‌های سنگین و تکراری الزام عمومی نیستند. CI required قرمز/غایب، دسترسی ممتازِ ناامن، و تعهد واقعی قانونی با سرعت معامله نمی‌شوند.
- امکانات تیمی تنها وقتی خود مالک در [پرسش‌نامه](intake/QUESTIONNAIRE.md) انتخاب کند مطرح می‌شوند؛ به‌طور پیش‌فرض نصب نمی‌شوند.

## چطور استفاده می‌شود

به عامل AI (Claude Code، Codex، …) فقط بگویید:

> پروژه‌ی **‹نام›** را با این مشخصات: ‹…› در **`bagdeli/‹repo›`** بساز.
> از **KavoshStart** برای استاندارد مهندسی استفاده کن؛ بستهٔ UI نسخه‌دار متناسب را در مخزن خود پروژه انتخاب کن.

عامل موظف است [`START.md`](START.md) را اجرا کند:

```text
1 Intake     → پرسش‌نامه‌ی intake/QUESTIONNAIRE.md؛ هر چه نامعلوم است می‌پرسد، حدس نمی‌زند
2 Classify   → Tier + Runtime + composable Capabilities طبق intake/CLASSIFICATION.md؛ مالک facts و capabilityهای غیرقابل‌استنتاج را تأیید می‌کند
3 Manifest   → kavosh.project.json (ماشین‌خوان) + PROJECT.md (یک صفحه)
4 Scaffold   → scripts/scaffold.py: فایل‌های مشترک + overlayهای Tier/Runtime؛ capabilityها applicability/evidence را در manifest اعلام می‌کنند
5 Backlog    → Milestone و Issueها در GitHub (نه در فایل)
6 Deliver    → هر Issue = یک تغییر coherent و reviewable؛ risk/evidence مستقل از اندازهٔ diff → ادغام فقط به main
7 Decide     → low/medium پس از gate کامل delegated merge؛ high/critical نیازمند تصمیم انسانی، نه کلیک مکانیکی Merge
8 Maintain   → گزارش سلامت، انتشار gated، و ارتقای KavoshStart و بسته‌های انتخابی با PR
```

## محتوا

| مسیر | چیست | زبان |
|---|---|---|
| [`START.md`](START.md) | پروتکل اجرایی عامل AI (ساخت پروژه‌ی جدید / پذیرش پروژه‌ی موجود / ارتقا) | EN |
| [`intake/`](intake/) | پرسش‌نامه، قواعد رده‌بندی، schema فایل `kavosh.project.json` | EN/FA |
| [`standard/RULES.md`](standard/RULES.md) | **فهرست مرجع همه‌ی قواعد** با شناسه، سطح، Tier و مکانیزم اجرا | FA |
| [`standard/15-third-party-components.md`](standard/15-third-party-components.md) | سیاست انتخاب، یکپارچه‌سازی و توزیع اجزای شخص ثالث | FA |
| [`standard/`](standard/) | توضیح قواعد: مدل پلن رایگان، شاخه/PR، CI و دقیقه‌ها، AI، استقرار، کتابخانهٔ UI انتخابی … | FA |
| [`templates/`](templates/) | فایل‌های آماده: `common/` + `tier/T0..T2` + `runtime/server` | EN |
| [`.github/workflows/`](.github/workflows/) | workflowهای مشترک که پروژه‌ها با tag دقیق `@vX.Y.Z` و نسخهٔ مانیفست فرا می‌خوانند | — |
| [`scripts/`](scripts/) | scaffold، راه‌اندازی ریپو، نصب محافظ‌های عامل، ممیزی، گزارش پرتفوی | — |
| [`docs/decisions/`](docs/decisions/) | ADRهای خود KavoshStart (چرا این قواعد) | EN |
| [`adoption/`](adoption/) | راهنمای عمومی پذیرش پروژه‌های موجود | FA |

## واقعیت platform/account (خلاصه‌ی [ADR-0003](docs/decisions/0003-free-plan-enforcement-model.md))

در مخزن private با GitHub Free، کنترل‌های branch/ruleset قابل‌اعمال مانند مخزن public نیستند و باید محدودیت‌های پلن و وضعیت واقعی تنظیمات بررسی شوند. **در قرارداد نسخه ۶، Self-hosted GitHub Actions نصب‌شده روی میزبان موجودِ امن و محدود در Private در صورت وجود و کنترل واقعی CI-2 مجاز است.** اما GitHub-hosted در Private حتی از سهمیهٔ رایگان بدون اجازهٔ قبلی و صریح همان شخص مالک اختیار مالی برای همان Run ممنوع است؛ پس از مجوز فقط Dispatch دستی برای Workflow/PR/ref/SHA مشخص مجاز است. Public استاندارد GitHub-hosted از نظر دقیقه رایگان است؛ larger runners و storage ممکن است هزینه داشته باشند. Self-hosted عمومی با مدل اعتماد و منع کد fork نامطمئن قابل استفاده است. T1/static همچنان می‌تواند `ci.runner: none` بدون Actions داشته باشد ([ADR-0018](docs/decisions/0018-private-self-hosted-and-hosted-consent.md)، [ADR-0019](docs/decisions/0019-owner-only-github-metered-consent.md)، CI-1/2/3).

| لایه | کِی عمل می‌کند | چه چیزی |
|---|---|---|
| **A — محافظ عامل** (پیشگیری) | قبل از push | `.githooks/pre-push` + قواعد deny در `.claude/settings.json` |
| **P — بررسی PR** (قرمز شدن) | روی هر PR | workflow `kavosh-governance` — مالک هرگز PR قرمز را ادغام نمی‌کند |
| **G — دروازه‌ی انتشار** | قبل از هر نسخه | `kavosh-release` — بدون checkهای الزامی سبز، نسخه‌ای ساخته نمی‌شود |
| **M — نگهبان main** (کشف) | بعد از هر push به main | `kavosh-main-guard` — push مستقیم یا ادغام PR قرمز = Issue تخلف |
| **H — سلامت هفتگی** (اندازه‌گیری) | هر شنبه | `kavosh-health` — شاخه‌ها، دقیقه‌ها، Issueها، CI |
| **S — تنظیمات رایگان** | یک‌بار | squash-only، حذف خودکار شاخه، برچسب‌ها |
| **O — ناظر پرتفوی عمومی** | روزانه، از بیرون | `kavosh-portfolio` در KavoshStart — فقط repoهای public؛ privateها پیش از inspection نادیده گرفته می‌شوند |

مهم‌ترین قاعده‌ی انسانی: **«PR قرمز را ادغام نکن»** (PR-7) — نقضش را لایه‌ی M بعداً ثبت می‌کند. چند MUST دیگر فقط با بازبینی انسانی اجرا می‌شوند و در انتهای [RULES.md](standard/RULES.md) صریحاً فهرست شده‌اند؛ ادعای «اجرای کامل ماشینی» نداریم.

## اجزای شخص ثالث

اولویت با جزء بالغ و آماده است، اگر هزینهٔ کل مالکیت، امنیت، نگهداری و حقوق استفاده/توزیع آن قابل‌قبول باشد. Copyleft ممنوعیت مطلق ندارد؛ **AGPL نیز پس از بررسی صریح، رفع تناقض و توان اجرای تعهدات شبکه/سورس، قابل‌استفاده است.** نوع ترکیب، تغییر، توزیع و تعهد استفادهٔ شبکه‌ای تعیین‌کننده است. بررسی release-scoped شامل License/NOTICE، حقوق بازتوزیع، سورس لازم و SBOM متناسب است. این سیاست از مجوز خود محصول و سامانهٔ entitlement آن مستقل است؛ کنترل حقوقی انسانی را با CI سبز جایگزین نکنید ([TP-1/2](standard/RULES.md)، [راهنما](standard/15-third-party-components.md)).

## قرارداد عمومی و مهاجرت Major

این مخزن هیچ نام، URL، محتوا، شواهد یا وضعیت مخازن خصوصی را به‌عنوان نمونه یا dependency منتشر نمی‌کند. UI هر پروژه با نام بسته و نسخهٔ دقیق در همان مخزن انتخاب می‌شود؛ هیچ تأمین‌کنندهٔ مشخصی در Core الزامی نیست. مهاجرت از فیلدهای قدیمیِ وابسته به ارائه‌دهنده و سیاست جدید runner در private یک **تغییر ناسازگار (breaking)** است؛ [راهنمای مهاجرت v6](docs/migrations/v6-private-runner-choice.md) را بخوانید؛ [راهنمای v5](docs/migrations/v5-provider-neutral-and-hosted-only.md) صرفاً قرارداد تاریخی نسخهٔ ۵ است.

## نسخه‌بندی

KavoshStart خودش SemVer دارد و فقط از طریق دروازه‌ی REL-5 منتشر می‌شود. پروژه‌های مصرف‌کننده workflowها را با **tag دقیق** (`@vX.Y.Z`) فرا می‌خوانند، همان مقدار `kavosh.project.json` → `kavoshStart`؛ Dependabot ارتقا را به‌صورت PR پیشنهاد می‌کند (ADR-0006). مقدار `self` فقط در مانیفست خود `bagdeli/KavoshStart` معتبر است و به معنی checked-out canonical source است؛ هیچ consumer و هیچ workflow refای از `@self` استفاده نمی‌کند (ADR-0010). فایل example عمداً `vX.Y.Z` نامعتبر دارد تا قبل از scaffold به آخرین Release واقعی resolve شود. tag قدیمی `v1` و نسخه‌ی `v1.0.0` (pre-release) برای استفاده نیستند.

## پیش‌نیاز یک‌باره

مصرف‌کننده‌ها workflowهای عمومی KavoshStart را با tag دقیق release فرا می‌خوانند؛ هیچ دسترسی پرتفوی private به KavoshStart عمومی داده نمی‌شود.
