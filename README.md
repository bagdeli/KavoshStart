# KavoshStart

**استاندارد شروع، ساخت و نگهداری همه‌ی پروژه‌های Kavosh با همکاری انسان و عامل‌های هوش مصنوعی روی GitHub (پلن رایگان).**

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
6 Deliver    → هر Issue = یک شاخه‌ی کوتاه = یک PR کوچک → ادغام فقط به main، فقط توسط مالک
7 Maintain   → گزارش سلامت هفتگی، انتشار با tag، به‌روزرسانی نسخه‌ی KavoshStart/KavoshUI با PR
```

## محتوا

| مسیر | چیست | زبان |
|---|---|---|
| [`START.md`](START.md) | پروتکل اجرایی عامل AI (ساخت پروژه‌ی جدید / پذیرش پروژه‌ی موجود / ارتقا) | EN |
| [`intake/`](intake/) | پرسش‌نامه، قواعد رده‌بندی، schema فایل `kavosh.project.json` | EN/FA |
| [`standard/RULES.md`](standard/RULES.md) | **فهرست مرجع همه‌ی قواعد** با شناسه، سطح، Tier و مکانیزم اجرا | FA |
| [`standard/`](standard/) | توضیح قواعد: مدل پلن رایگان، شاخه/PR، CI و دقیقه‌ها، AI، استقرار، KavoshUI … | FA |
| [`templates/`](templates/) | فایل‌های آماده: `common/` + `tier/T0..T2` + `runtime/server` | EN |
| [`.github/workflows/`](.github/workflows/) | workflowهای مشترک که پروژه‌ها با `@v1` فرا می‌خوانند | — |
| [`scripts/`](scripts/) | scaffold، راه‌اندازی ریپو، نصب محافظ‌های عامل، ممیزی، گزارش پرتفوی | — |
| [`docs/decisions/`](docs/decisions/) | ADRهای خود KavoshStart (چرا این قواعد) | EN |
| [`adoption/`](adoption/) | راهنمای پذیرش پروژه‌ی موجود + برنامه‌ی KavoshERP | FA |

## واقعیت پلن رایگان (خلاصه‌ی [ADR-0003](docs/decisions/0003-free-plan-enforcement-model.md))

روی ریپوی private در GitHub Free **هیچ** branch protection، ruleset یا required check قابل اعمال نیست و GitHub Pages در دسترس نیست. روی این حساب jobهای GitHub-hosted ریپوهای private اصلاً اجرا نمی‌شوند (قفل Billing)؛ پس **ریپوی private همیشه runner خودمیزبانِ مخصوص خودش دارد و ریپوی public همیشه runner GitHub** (CI-1، [ADR-0008](docs/decisions/0008-runner-by-visibility.md)). KavoshStart با این واقعیت طراحی شده:

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

KavoshStart خودش SemVer دارد و فقط از طریق دروازه‌ی REL-5 منتشر می‌شود. پروژه‌ها workflowها را با **tag دقیق** (`@vX.Y.Z`) فرا می‌خوانند، همان مقدار `kavosh.project.json` → `kavoshStart`؛ Dependabot ارتقا را به‌صورت PR پیشنهاد می‌کند (ADR-0006). tag قدیمی `v1` و نسخه‌ی `v1.0.0` (pre-release) برای استفاده نیستند.

## پیش‌نیاز یک‌باره

مصرف‌کننده‌ها workflowهای عمومی KavoshStart را با tag دقیق release فرا می‌خوانند؛ هیچ دسترسی پرتفوی private به KavoshStart عمومی داده نمی‌شود.
