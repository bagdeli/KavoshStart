# KavoshStart

**استاندارد شروع، ساخت و نگهداری پروژه‌های Kavosh با همکاری انسان و عامل‌های هوش مصنوعی؛ مستقل از زبان، ابزار release و اندازهٔ diff، با policyهای platform/account به‌صورت overlay.**

KavoshStart برای «روش کار» همان نقشی را دارد که [KavoshUI](https://github.com/bagdeli/KavoshUI) برای «ظاهر» دارد: یک مرجع نسخه‌دار که همه‌ی پروژه‌ها از آن پیروی می‌کنند، به‌جای این‌که هر پروژه قواعد خودش را از نو بنویسد.

## چطور استفاده می‌شود

به عامل AI (Claude Code، Codex، …) فقط بگویید:

> پروژه‌ی **‹نام›** را با این مشخصات: ‹…› در **`bagdeli/‹repo›`** بساز.
> برای اصول و روند کار از **KavoshStart** و برای ظاهر از **KavoshUI** استفاده کن.

عامل موظف است [`START.md`](START.md) را اجرا کند:

```text
1 Intake     → پرسش‌نامه‌ی intake/QUESTIONNAIRE.md؛ هر چه نامعلوم است می‌پرسد، حدس نمی‌زند
2 Classify   → Tier (T0/T1/T2) و Runtime (none/static/server/desktop) طبق intake/CLASSIFICATION.md؛ مالک تأیید می‌کند
3 Manifest   → kavosh.project.json (ماشین‌خوان) + PROJECT.md (یک صفحه)
4 Scaffold   → scripts/scaffold.py: فایل‌های مشترک + فایل‌های Tier + فایل‌های Runtime
5 Backlog    → Milestone و Issueها در GitHub (نه در فایل)
6 Deliver    → هر Issue = یک تغییر coherent و reviewable؛ risk/evidence مستقل از اندازهٔ diff → ادغام فقط به main
7 Decide     → low/medium پس از gate کامل delegated merge؛ high/critical نیازمند تصمیم انسانی، نه کلیک مکانیکی Merge
8 Maintain   → گزارش سلامت، انتشار gated، و ارتقای KavoshStart/KavoshUI با PR
```

## محتوا

| مسیر | چیست | زبان |
|---|---|---|
| [`START.md`](START.md) | پروتکل اجرایی عامل AI (ساخت پروژه‌ی جدید / پذیرش پروژه‌ی موجود / ارتقا) | EN |
| [`intake/`](intake/) | پرسش‌نامه، قواعد رده‌بندی، schema فایل `kavosh.project.json` | EN/FA |
| [`standard/RULES.md`](standard/RULES.md) | **فهرست مرجع همه‌ی قواعد** با شناسه، سطح، Tier و مکانیزم اجرا | FA |
| [`standard/`](standard/) | توضیح قواعد: مدل پلن رایگان، شاخه/PR، CI و دقیقه‌ها، AI، استقرار، KavoshUI … | FA |
| [`templates/`](templates/) | فایل‌های آماده: `common/` + `tier/T0..T2` + `runtime/server` | EN |
| [`.github/workflows/`](.github/workflows/) | workflowهای مشترک که پروژه‌ها با tag دقیق `@vX.Y.Z` و نسخهٔ مانیفست فرا می‌خوانند | — |
| [`scripts/`](scripts/) | scaffold، راه‌اندازی ریپو، نصب محافظ‌های عامل، ممیزی، گزارش پرتفوی | — |
| [`docs/decisions/`](docs/decisions/) | ADRهای خود KavoshStart (چرا این قواعد) | EN |
| [`adoption/`](adoption/) | راهنمای عمومی پذیرش پروژه‌های موجود | FA |

## واقعیت platform/account (خلاصه‌ی [ADR-0003](docs/decisions/0003-free-plan-enforcement-model.md))

روی ریپوی private در GitHub Free **هیچ** branch protection، ruleset یا required check قابل اعمال نیست و GitHub Pages در دسترس نیست. GitHub-hosted Actions برای private از سهمیهٔ مشترک حساب استفاده می‌کند؛ KavoshStart هیچ private run را بدون dispatch مستقیم و محدود مالک اجرا نمی‌کند. انتخاب runner به trust، billing، شبکه و workload وابسته است: hosted با مجوز هر اجرا یا self-hosted ایزوله. برای public، runner استاندارد GitHub پیش‌فرض است (CI-1، [ADR-0009](docs/decisions/0009-human-authorized-operations.md)).

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

## نسخه‌بندی

KavoshStart خودش SemVer دارد و فقط از طریق دروازه‌ی REL-5 منتشر می‌شود. پروژه‌های مصرف‌کننده workflowها را با **tag دقیق** (`@vX.Y.Z`) فرا می‌خوانند، همان مقدار `kavosh.project.json` → `kavoshStart`؛ Dependabot ارتقا را به‌صورت PR پیشنهاد می‌کند (ADR-0006). مقدار `self` فقط در مانیفست خود `bagdeli/KavoshStart` معتبر است و به معنی checked-out canonical source است؛ هیچ consumer و هیچ workflow refای از `@self` استفاده نمی‌کند (ADR-0010). فایل example عمداً `vX.Y.Z` نامعتبر دارد تا قبل از scaffold به آخرین Release واقعی resolve شود. tag قدیمی `v1` و نسخه‌ی `v1.0.0` (pre-release) برای استفاده نیستند.

## پیش‌نیاز یک‌باره

مصرف‌کننده‌ها workflowهای عمومی KavoshStart را با tag دقیق release فرا می‌خوانند؛ هیچ دسترسی پرتفوی private به KavoshStart عمومی داده نمی‌شود.
