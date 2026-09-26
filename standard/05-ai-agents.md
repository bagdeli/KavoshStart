# 05 — همکاری با عامل‌های هوش مصنوعی

قواعد: AI-1…6، PR-4، PR-6، WK-5

## نقش‌ها
| نقش | چه کسی | کار |
|---|---|---|
| مالک | شما | دامنه، اولویت، تأیید رده و Spec، **ادغام**، انتشار، تصمیم‌های قانونی و production |
| مجری | Claude Code، Codex، Copilot، Gemini | برنامه، کد، تست، به‌روزرسانی PR |
| بازبین | عامل دوم (ابزار یا مدل متفاوت) + شما | بازبینی diff؛ «Request changes» عامل الزام‌آور نیست ولی باید پاسخ داده شود |
| پلتفرم | workflowهای KavoshStart | اجرای قواعد، بی‌طرف |

## فایل‌های دستورالعمل
| فایل | محتوا |
|---|---|
| `AGENTS.md` | **تنها منبع**: پروژه (از مانیفست)، نقشه‌ی ریپو، فرمان‌ها، قراردادها، Definition of Done، مرزها |
| `CLAUDE.md` | `@AGENTS.md` + نکات مخصوص Claude |
| `GEMINI.md`، `.github/copilot-instructions.md` | یک خط ارجاع |
| `.claude/settings.json` | قواعد deny (لایه‌ی A) |
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
- شروع جلسه: `gh issue view` + `AGENTS.md`؛ پایان جلسه: به‌روزرسانی بدنه‌ی PR.

## نسبت‌دهی
```text
Co-Authored-By: Claude <noreply@anthropic.com>
Co-Authored-By: Codex <noreply@openai.com>
Co-Authored-By: Copilot <copilot@github.com>
```
و بخش `## AI involvement` در PR. هویت git انسانی باید یکنواخت و قابل‌ردیابی بماند؛ از چند هویت نویسنده برای یک مالک استفاده نشود.

## جمله‌ی استاندارد برای شروع کار با هر عامل
```text
Use KavoshStart (bagdeli/KavoshStart, START.md §4). Work on issue #<n> in bagdeli/<repo> only.
Branch <type>/<n>-<slug> from origin/main, open a draft PR with your plan first, keep it under the
project's prMaxLines, run `make check` before a single push, update the PR body, never merge.
```
