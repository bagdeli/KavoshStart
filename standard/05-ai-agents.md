# 05 — همکاری با عامل‌های هوش مصنوعی

قواعد: AI-1…6، PR-4، PR-6، WK-5

## نقش‌ها
| نقش | چه کسی | کار |
|---|---|---|
| مالک | شما | دامنه، اولویت، تأیید رده و Spec، مجوزهای محدود برای ادغام، انتشار و production |
| مجری | Claude Code، Codex، Copilot، Gemini | برنامه، کد، تست، به‌روزرسانی PR و اجرای عمل صریحاً مجاز |
| بازبین | عامل دوم (ابزار یا مدل متفاوت) + شما | بازبینی diff؛ «Request changes» عامل الزام‌آور نیست ولی باید پاسخ داده شود |
| پلتفرم | workflowهای KavoshStart | اجرای قواعد، بی‌طرف |

## فایل‌های دستورالعمل
| فایل | محتوا |
|---|---|
| `AGENTS.md` | **تنها منبع**: پروژه (از مانیفست)، نقشه‌ی ریپو، فرمان‌ها، قراردادها، Definition of Done، مرزها |
| `CLAUDE.md` | `@AGENTS.md` + نکات مخصوص Claude |
| `GEMINI.md`، `.github/copilot-instructions.md` | یک خط ارجاع |
| `.claude/settings.json` | deny برای اعمال ممنوع و ask برای اعمال نیازمند اجازه (لایه‌ی A) |
| `.githooks/pre-push` | مسدودکردن push به main و force-push (لایه‌ی A) |
| `apps/*/AGENTS.md` | جزئیات هر بخش در monorepo (نزدیک‌ترین فایل اولویت دارد) |

AGENTS.md بر اساس الگوی تحلیل GitHub روی 2,500 ریپو: فرمان‌های دقیق، ساختار، سبک کد با مثال، مرزهای **Always / Ask first / Never**. هر بار که عامل اشتباهی تکرار کرد، یک خط به آن اضافه کنید — نه یک سند جدید.

## جریان Spec-Driven (T2 اجباری، T1 برای Featureهای بزرگ)
```text
Issue (feature) → PR#1: specs/<n>-<slug>/spec.md  (چه و چرا، ≤ 400 خط)  → مالک تأیید
                → PR#1 یا #2: plan.md  (چطور؛ owner‌های canonical؛ migration؛ tasks)
                → sub-issueهای type:task  (نه فایل tasks.md)
                → هر task یک PR
```
هم‌راستا با GitHub Spec Kit؛ استفاده از خود Spec Kit (`specify init`) مجاز است به شرط این‌که tasks به Issue تبدیل شوند.

## کنترل سرعت
- حداکثر PRهای باز غیر-Draft: 3 (PR-8). عامل‌ها می‌توانند موازی کار کنند، ولی بازبینی شما سریالی است.
- یک جلسه = یک Issue؛ برای Claude Code بین کارها `/clear`.
- شروع جلسه: `START.md §0` + `AGENTS.md` + Issue؛ pin KavoshStart را با آخرین release مقایسه کن و control-plane upgrade لازم را قبل از feature/gate جدید حل یا با owner محدود defer کن. پایان جلسه: بدنه‌ی PR و acceptance mapping را به‌روز کن.

## نسبت‌دهی
```text
Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Codex <noreply@openai.com>
Co-Authored-By: Copilot <copilot@github.com>
```
و بخش `## AI involvement` در PR. هویت git انسانی باید یکنواخت و قابل‌ردیابی بماند؛ از چند هویت نویسنده برای یک مالک استفاده نشود.

## جمله‌ی استاندارد برای شروع کار با هر عامل
```text
Use KavoshStart (bagdeli/KavoshStart, START.md §0 then the selected mode). Stay in bagdeli/<repo> only.
First verify repository identity, live main/task state, the project's exact KavoshStart pin, and the latest stable
KavoshStart release. If a newer control-plane release materially affects governance/acceptance/security/release/deploy/CI,
upgrade it in a separate PR before normal feature work unless the owner has recorded a bounded defer.
For WORK, handle exactly issue #<n>, branch <type>/<n>-<slug> from origin/main, open a draft PR, keep the diff reviewable,
run `make check`, map T2 acceptance IDs, and update the PR body. Merge only when the owner explicitly authorizes this
PR and current head after fresh base/check/review preflight. Never use `--admin`, report-only governance, or silent auto-upgrades.
```
