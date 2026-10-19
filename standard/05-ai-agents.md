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

## الزام/آزمون تازه باید دلیل داشته باشد؛ الزام قدیمی قابل بازبینی است

عامل پیش از ساختن الزام، تست یا چک تازه در همان کار مشخص می‌کند که رفتار واقعاً در مالکیت **پلتفرم/upstream، integration یا محصول** است، چه نسخه‌ای از قرارداد موجود آن را تضمین می‌کند، چه خطر/نتیجه‌ای واقعاً بدون آزمون مانده و ارزان‌ترین مدرک معتبر چیست. تست‌های داخلی کتابخانهٔ شناخته‌شده را در مصرف‌کننده بازنسازی نکند؛ ولی ترکیب واقعی، RTL/UX، auth/payment و سایر مرزهای محصول باید به‌قدر ریسک بررسی شوند. برای الزام/تست زائد، منسوخ یا بی‌مبنا مسیر حذف یا ادغام در Issue/Spec/PR **همان مالک** باز است؛ نیاز به دفتر تازه یا چند ماه اثبات منفی نیست، و اصلاح نباید CI قرمز را دور بزند یا تعهد امنیتی حقیقی را پنهان کند.

## کمترین تغییر کامل، نه کمترین خط کد

این یک روش بازبینی **توصیه‌ای** زیر قواعد موجود AI-1، CR-3/4، PR-3 و TP-1/2 است؛ Rule، معیار عددی یا دروازهٔ جدیدی اضافه نمی‌کند.

1. **اثر واقعی تغییر را بشناسید:** مسیر داده و مصرف‌کنندگان متاثر از جمله callerها، قرارداد API، UI، config، تست و fixture را بخوانید؛ Diff به‌تنهایی مرز مسئله نیست.
2. **راه موجود را زودتر بررسی کنید:** آیا کد تازه لازم است؟ اول الگوی مالک همان مفهوم در مخزن، بعد قابلیت بومی/stdlib، سپس وابستگی موجود و مناسب با بررسی TP-1/2، و سرانجام کوچک‌ترین پیاده‌سازی **کامل و خوانا**. نصب‌بودن dependency یا کم‌بودن خطوط به‌تنهایی دلیل انتخاب نیست.
3. **کامل اصلاح کنید:** ریشهٔ مشکل و تمام مصرف‌کنندگان متاثر را یکجا سازگار نگه دارید؛ wrapper، config و abstraction فرضی نسازید. کوتاه‌شدن Diff مجوز حذف کنترل امنیتی، اعتبارسنجی، مدیریت خطا، جلوگیری از اتلاف داده یا accessibility نیست.
4. **با شواهد بازبینی کنید:** ابتدا خطا/امنیت/بار واقعی و آزمون رگرسیون منطق غیرساده را بسنجید و بعد کد اضافی را حذف کنید. یک اشکال باید نمونهٔ شکست مشخص داشته باشد؛ آزمون یا gate سراسری تازه فقط طبق CR-4.
5. **ریسک را گزارش کنید:** در PR روشن کنید چه چیزی بررسی شده، چه چیزی *بررسی نشده* و ریسک باقی‌مانده چیست. تأیید مالک، CI، مستندات و تعهدات حقوقی همچنان معتبرند.

الهام مفهومی: [Ponytail v5.3.2](https://github.com/DietrichGebert/ponytail/tree/v5.3.2) (MIT). این متن مستقل نوشته شده و هیچ prompt، کد، Hook یا تله‌متریِ Ponytail کپی یا نصب نمی‌شود. [نتایج بنچمارک خود Ponytail](https://github.com/DietrichGebert/ponytail/blob/v5.3.2/benchmarks/results/2026-10-07-agentic.md) به‌معنای اثبات صرفه‌جویی برای KavoshStart نیست.

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
