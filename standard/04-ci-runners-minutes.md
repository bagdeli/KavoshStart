# 04 — CI، runner و بودجه‌ی دقیقه

قواعد: CI-1…9

## Runtime contract for reusable controls

Reusable KavoshStart governance, main-guard, health, release-gate and RC-gate logic must not assume that a consumer runner has GitHub CLI installed. Core GitHub API access uses Python standard library plus the workflow-scoped `GITHUB_TOKEN`/`GITHUB_API_URL`; git remains the only repository CLI assumption. A project may install `gh` for its own tooling, but KavoshStart conformance cannot depend on that hidden host prerequisite.

## Runner و هزینه (CI-1…3 — ADR-0015)

| وضعیت ریپو | اجرای GitHub Actions | قید |
|---|---|---|
| **private** | **فقط GitHub-hosted استاندارد** مانند `ubuntu-latest` | runner خودمیزبان، runner group خودمیزبان، ARC و برچسب‌های سفارشیِ حل‌شونده به self-hosted ممنوع‌اند؛ هر run سهمیه‌دار نیازمند اجازه و `workflow_dispatch` محدود به ref/SHA است |
| **public** | GitHub-hosted استاندارد، پیش‌فرض و توصیه‌شده | self-hosted فقط با ADR مشخص و جداسازی واقعی؛ اجرای کد fork/نامطمئن بر آن ممنوع است |
| **T1/static با `ci.runner: none`** | هیچ GitHub Actions jobای تولید/اجرا نمی‌شود | فقط profile محلی با بودجهٔ صفر؛ شواهد موفق `make check` در PR لازم است |

فهرست نام‌های مجاز GitHub-hosted در Governance با [مستندات Runnerهای استاندارد GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) همگام می‌شود. برچسب رسمی جدید نباید به‌اشتباه رد شود، اما الگوی wildcard/prefix جای اثبات انتخاب GitHub-hosted را نمی‌گیرد. کنترل ایستا نیز جای بررسی تنظیمات واقعی GitHub را نمی‌گیرد.

این ممنوعیت private یک **سیاست سخت‌گیرانهٔ KavoshStart** است، نه ادعای اینکه GitHub استفاده از self-hosted در private را ممنوع کرده است. GitHub نسبت به خطر persistence و دسترسی کد نامطمئن هشدار می‌دهد؛ hosted نیز ایمنی خودکار کد شخص ثالث، تفکیک Secrets و حفاظت از شبکه را تضمین نمی‌کند.

### اجرای private (fail closed)

- انتخاب `ci.runner: self-hosted` یا باقی‌ماندن `ci.runnerLabels`، `ci.runners` و `ci.trustModelADR` برای private در schema، scaffold و governance رد می‌شود؛ ADR، label، بودجه یا وجود runner ثبت‌شده استثنا ایجاد نمی‌کند.
- Workflowهای reusable بیرونی می‌توانند runner مستقلی انتخاب کنند: در private فقط Workflow محلیِ واقعاً موجود (که همراه مخزن ممیزی می‌شود) یا Workflow پین‌شدهٔ KavoshStart مجاز است. سایر reusable workflowهای بیرونی تا ورود منطق آن‌ها به مخزن مصرف‌کننده و ممیزی مستقل fail-closed هستند؛ صرف SHA pin مجوز runner نیست.
- GitHub-hosted private در حساب دارای سهمیهٔ مشترک تنها پس از **مجوز مستقیم مالک برای همان اجرای مشخص** و با dispatch دستی برای PR باز و head SHA فعلی اجرا می‌شود. کنترل‌های `ci.yml` و workflowهای قابل‌استفادهٔ مجدد باید اعتبار ref/SHA را پیش از checkout/کار اصلی بررسی کنند. `push`، `pull_request`، `schedule` و `workflow_run` نباید job هزینه‌دار private را خودکار اجرا کنند.
- محیط‌های داخلی/داده‌های Test/Production با GitHub-hosted به‌صورت خودکار قابل دسترسی یا اثبات‌شده نیستند. build/validation محلی و pull-based deployment می‌توانند مستقل باشند، اما **نباید** به‌عنوان اجرای GitHub Actions یا شواهد Test/Production جا زده شوند. هر test/release باید provenance، سطح اعتماد و شواهد واقعی خود را داشته باشد.
- وجود self-hosted runner ثبت‌شده در GitHub به‌تنهایی اثبات نقض اجرای job نیست؛ خاموش‌کردن دسترسی، حذف ثبت/گروه و بازبینی workflows یک اقدام مدیریتی مالک در repositoryهای مصرف‌کننده است، نه کاری از داخل مخزن عمومی.

### حالت محلی T1/static

مالک می‌تواند در intake، `ci.runner: "none"` را فقط برای T1/static انتخاب کند. scaffold هیچ workflowی نمی‌سازد و بودجه صفر است. عامل `make setup` و `make check` را محلی اجرا می‌کند و فرمان، کد خروجی، محیط و نتیجه را در PR ثبت می‌کند. خروجی ناموفق یا غایب مانع merge است؛ required check موجود نباید دور زده شود. اعتبارسنجی مرورگر اگر محلی ممکن نبود با SKIP صریح گزارش می‌شود، نه PASS جعلی.

### public self-hosted (استثنا، نه توصیه)

اگر پروژهٔ public واقعاً نیازمند آن بود، ADR باید runner trust model، isolation/containment، boundary کد نامطمئن و credential boundary را با کنترل عملی بیان کند. rootful Docker دسترسی root-equivalent دارد و `--ephemeral` به‌تنهایی ایزولیشن host نیست. ظرفیت با صف/SLO تعیین می‌شود. نصب یا فعال‌سازی runner نیازمند فرایند مجزای مورد تأیید مالک است؛ installer قبلی private بازنشسته است.

دقیقه، storage، cache، Packages و larger runner هزینه‌های مستقل‌اند. مقدار `monthlyMinutesBudget` مجوز خرج‌کردن یا توقف قطعی هزینه نیست؛ policy حساب و بررسی billing معتبر است.

## قواعد صرفه‌جویی (به ترتیب اثر)
1. **CI-6:** CI سنگین روی Draft خاموش است؛ اجرای زودهنگام باید درخواست صریح و، اگر سهمیه مصرف می‌کند، مجوز مستقیم همان اجرا داشته باشد.
2. **CI-5:** jobهای سنگین روی `main`/tag/برچسب `ci:full` یا dispatch صریح همان PR/SHA اجرا می‌شوند.
3. **CI-4:** `concurrency` با `cancel-in-progress` برای PR.
4. فیلتر مسیر و بررسی محلی مطابق `make check`.
5. هر job حداقل یک دقیقه حساب می‌شود → jobهای کوچک را در یک job ادغام کنید.
6. `timeout-minutes` برای هر job (پیش‌فرض 360 دقیقه است!).

## اجرای زودهنگام و workflowهای هر پروژه
روی Draft، CI سنگین خودکار اجرا نمی‌شود. در public، افزودن `ci:full` اجرای زودهنگام را درخواست می‌کند؛ روی private GitHub-hosted، `workflow_dispatch` باید PR number و head SHA دقیق را بگیرد و برای suite سنگین ورودی `ci-full` هم صریحاً فعال شود. این عمل توسط صاحب ریپو انجام می‌شود و فقط همان run را مجاز می‌کند؛ SHA قدیمی یا PR بسته/تغییریافته fail-closed می‌شود.

| فایل | رویداد | Tier |
|---|---|---|
| `kavosh.yml` | PR، push به main، هفتگی ← فراخوانی workflowهای KavoshStart با tag دقیق | All |
| `ci.yml` | PR (غیر Draft)، push به main ← `make check` + job `required` | All به جز local-only |
| `release.yml` | پس از موفقیت ci روی main ← `kavosh-release` (دروازه‌ی REL-5 + release-please + فایل‌های انتشار) | All |
| `ai-review.yml` | PR ready ← بازبینی AI (نیاز به کلید API) | T2 (T1 اختیاری) |

## قرارداد فرمان (CI-8)
CI هیچ‌وقت ابزار زبان خاصی را مستقیم صدا نمی‌زند؛ فقط `make setup` و `make check`. پس:
- عامل و CI دقیقاً یک کار را انجام می‌دهند (سبز محلی ≈ سبز CI).
- تغییر ابزار (ruff → x) فقط `Makefile` را عوض می‌کند.
## pull_request_target برای Release PR

`pull_request_target` فقط برای حل محدودیت GitHub روی Release Please PR استفاده می‌شود و یک مسیر عمومی اجرای PR نیست. مسیر canonical باید هم‌زمان این شروط را machine-enforce کند: head repository همان repository، actor برابر `github-actions[bot]`، source branch با الگوی release-please، exact head checkout با `persist-credentials:false`، بدون Production secrets. برای PRهای دیگر job name باید context required تولید نکند. governance روی target از کد workflow پایه اجرا می‌شود و write-path اختیاری comment خاموش است.

