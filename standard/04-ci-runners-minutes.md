# 04 — CI، runner و بودجه‌ی دقیقه

قواعد: CI-1…9

## Runtime contract for reusable controls

Reusable KavoshStart governance, main-guard, health, release-gate and RC-gate logic must not assume that a consumer runner has GitHub CLI installed. Core GitHub API access uses Python standard library plus the workflow-scoped `GITHUB_TOKEN`/`GITHUB_API_URL`; git remains the only repository CLI assumption. A project may install `gh` for its own tooling, but KavoshStart conformance cannot depend on that hidden host prerequisite.

## Runner و هزینه (CI-1…3 — ADR-0018 جایگزین تصمیم private در ADR-0015)

| ریپو و mode | اجرای GitHub Actions | مجوز و مرز |
|---|---|---|
| **private / self-hosted** | Runner متصل به GitHub و نصب‌شده روی سرور مستقل، اگر موجود و ایزوله است | CI-2 و Runner اختصاصی مخزن؛ **بدون نیاز به اجازهٔ مصرف دقیقه GitHub-hosted** |
| **private / github-hosted** | **بدون اجازهٔ قبلی و صریح شخص مالکِ اختیار مالی (صاحب این سیاست) برای همان اجرا ممنوع**، حتی از سهمیهٔ رایگان | فقط dispatch دستی محدود به workflow/PR/ref/SHA مصوب |
| **public / github-hosted استاندارد** | مجاز و طبق شرایط فعلی GitHub از نظر دقیقهٔ استاندارد رایگان | larger runner، storage و سایر خدمات ممکن است هزینهٔ جدا داشته باشند |
| **public / self-hosted** | با ایزولیشن و trust ADR مجاز | fork PR و کد نامطمئن نباید به runner/credential دسترسی پیدا کنند |
| **T1/static / `none`** | هیچ Actions workflow/job ندارد | فقط شواهد معتبر local check |

**تعریف:** Self-hosted Runner روی سرور خود مالک *همچنان* GitHub Actions Runner است، نه GitHub-hosted و نه Worker مستقل خارج از GitHub. در private استفاده از Runner موجود بلامانع است، ولی CI-2 مدل اعتماد، محدودیت دامنهٔ Runner و ایزولیشن را بررسی می‌کند؛ داشتن برچسب یا فایل ADR به‌تنهایی اثبات پیکربندی امن سرور نیست.

برای GitHub-hosted فقط برچسب‌های رسمی دقیق [مستندات GitHub](https://docs.github.com/en/actions/reference/runners/github-hosted-runners) مجازند؛ `runs-on` دینامیک یا ناشناخته انتخاب امن را اثبات نمی‌کند. برای Self-hosted، `[self-hosted, linux, x64, repo-slug]` فقط ترکیب پیش‌فرض است. `ci.runnerLabels` می‌تواند برچسب‌های **واقعی ثبت‌شده** مانند `[self-hosted, linux, ARM64, repo-slug, gpu]` را انتخاب کند. مجموعه و ترتیب باید در مانیفست، `runs-on` و callerهای reusable دقیقاً منطبق باشند. `self-hosted`، OS، معماری و یک label سفارشی و اختصاصیِ scope مخزن لازم‌اند؛ نام label اختصاصی ممکن است با slug مخزن تفاوت داشته باشد. مطابق CI-2، Trust ADR باید **پذیرفته شده** باشد، نه پیشنهادی/معوق. selector دینامیک، group مشترک یا برچسب hosted معتبر نیست. مالک مصرف‌کننده ثبت واقعی Runner، scope مخزن و ایزولیشن را عملیاتی و مستقل از مانیفست و ADR بررسی می‌کند.

### Private self-hosted: اجرای مجاز با جداسازی واقعی

- Runner می‌تواند در `push` و PR قابل‌اعتماد و رویدادهای دیگر استفاده شود؛ قبل از ثبت/اجرا، کنترل untrusted PR، credential boundary، جداسازی host و دسترسی Repo را تعیین کنید. GitHub اجرای کد fork روی Self-hosted عمومی را خطرناک می‌داند؛ حتی در Private، PRهای بدون اعتماد هم ممکن‌اند.
- Reusable workflowهای بیرونی می‌توانند Runner مستقل انتخاب کنند. در private فقط workflow محلی موجود و ممیزی‌شده یا workflow دقیقاً پین‌شدهٔ KavoshStart مجاز است. Caller روی private self-hosted باید `with.runs-on` متناظر با Runner مجاز را صریحاً مشخص کند؛ پیش‌فرض GitHub-hosted آن workflow مجوز استفاده نیست.
- KavoshStart نه Runner نصب می‌کند، نه وجود/ایزولیشن آن را از روی manifest اثبات می‌کند و نه اطلاعات Runner خصوصی را در مخزن عمومی ذخیره می‌کند. تأیید تنظیمات واقعی به مالک Repository مصرف‌کننده تعلق دارد.
- **مرز اعتماد:** اجرای PR/کد نامطمئن، CI کم‌مجوز، release، استقرار و secrets/production حوزه‌های متفاوت‌اند. label یا Runner مشترک دسترسی به همهٔ آن‌ها را مجاز نمی‌کند؛ ابتدا با trigger/permission/secret boundary و ایزولیشن موجود جداسازی کنید، نه ماشین یا مجوز جدید به‌طور پیش‌فرض.

### Private GitHub-hosted: ممنوع تا اجازهٔ مشخص

- **پیش از هر Run** سؤال مجوز مطرح می‌شود. بدون پاسخ صریح و مستقیم **همان شخص مالکِ اختیار مالی** برای همان Workflow، ریپو و PR/ref/SHA، اجرای hosted ممنوع است؛ GitHub Admin دیگر، عامل حتی با credential مالک، بودجه، سهمیهٔ رایگان، dispatch یا مجوز کلی کار تأیید نیستند.
- Templateهای `ci.yml`، `kavosh.yml` و release مسیر GitHub-hosted خصوصی را از trigger خودکار `push`/`pull_request`/`schedule`/`workflow_run` جدا می‌کنند و `workflow_dispatch` محدود به SHA فعلی دارند. اعتبارسنجی داخل Job پس از تخصیص ماشین انجام می‌شود؛ بنابراین نمی‌تواند جای **گرفتن مجوز پیش از Dispatch** را بگیرد یا هویت انسان تأییدکننده را خودبه‌خود اثبات کند.
- GitHub برای Private سهمیهٔ رایگان دارد و فراتر از آن ممکن است هزینه بگیرد؛ سیاست مالک حتی برای دقیقه‌های داخل سهمیه اجازهٔ پیشینی می‌خواهد. Self-hosted دقیقهٔ Actions GitHub را مصرف نمی‌کند، اما سرور/امنیت/نگهداری هزینه دارند.
- **دیگر امکانات پولی/سهمیه‌ای GitHub در private** شامل larger runner، ذخیره‌سازی Artifact/Cache/Packages و اعتبار سرویس‌های AI (در صورت شمول) فقط پس از تأیید شخص مالک اختیار مالی برای خدمت، repo، اقدام، سقف و مدت مشخص مجازند. مجوز یک مصرف به دیگری تعمیم نمی‌یابد. تأیید باید **قبل از تخصیص/خرید/اجرا** باشد؛ `GITHUB_ACTOR` یا کنترل بعد از شروع CI اثبات اجازهٔ انسانی نیست. [ADR-0019](../docs/decisions/0019-owner-only-github-metered-consent.md) دامنهٔ اختیار را نسبت به عبارت تاریخی «owner/admin» در ADR-0018 محدود می‌کند.

### مرز شواهد و محیط عملیاتی

GitHub-hosted به‌معنای دسترسی واقعی به Test/Production خصوصی نیست و اجرای Self-hosted نیز مجوز اتوماتیک استقرار یا دسترسی به Secrets نیست. شواهد `required`، `main-guard`، CI و release باید واقعاً از منبع دقیق و اجرای معتبر حاصل شوند؛ یک Self-server مستقل نمی‌تواند خود را GitHub Actions check جا بزند.

### حالت محلی T1/static

مالک می‌تواند در intake، `ci.runner: "none"` را فقط برای T1/static انتخاب کند. scaffold هیچ workflowی نمی‌سازد و بودجه صفر است. عامل `make setup` و `make check` را محلی اجرا می‌کند و فرمان، کد خروجی، محیط و نتیجه را در PR ثبت می‌کند. خروجی ناموفق یا غایب مانع merge است؛ required check موجود نباید دور زده شود. اعتبارسنجی مرورگر اگر محلی ممکن نبود با SKIP صریح گزارش می‌شود، نه PASS جعلی.

### public self-hosted (مشروط به مدل اعتماد و حفاظت از PR نامطمئن)

Self-hosted عمومی با CI-2 و کنترل واقعی fork/credential/isolation مجاز است؛ اجرای کد نامطمئن روی Runner پایدار ممنوع است. rootful Docker دسترسی root-equivalent دارد و `--ephemeral` به‌تنهایی ایزولیشن host نیست. ظرفیت براساس صف/SLO است. نصب Runner یک فرایند عملیاتی جداست؛ installer قدیمی بازنشسته است.

دقیقه، storage، cache، Packages و larger runner هزینه‌های مستقل‌اند. مقدار `monthlyMinutesBudget` مجوز خرج‌کردن یا توقف قطعی هزینه نیست؛ policy حساب و بررسی billing معتبر است.

## قواعد صرفه‌جویی (به ترتیب اثر)
1. **CI-6:** CI سنگین روی Draft خاموش است؛ اجرای زودهنگام باید درخواست صریح و، اگر سهمیه مصرف می‌کند، مجوز مستقیم همان اجرا داشته باشد.
2. **CI-5:** jobهای سنگین روی `main`/tag/برچسب `ci:full` یا dispatch صریح همان PR/SHA اجرا می‌شوند.
3. **CI-4:** `concurrency` با `cancel-in-progress` برای PR.
4. فیلتر مسیر و بررسی محلی مطابق `make check`.
5. هر job حداقل یک دقیقه حساب می‌شود → jobهای کوچک را در یک job ادغام کنید.
6. `timeout-minutes` برای هر job (پیش‌فرض 360 دقیقه است!).

## اجرای زودهنگام و workflowهای هر پروژه
روی Draft، CI سنگین خودکار اجرا نمی‌شود. در public، افزودن `ci:full` اجرای زودهنگام را درخواست می‌کند؛ روی private GitHub-hosted، `workflow_dispatch` باید PR number و head SHA دقیق را بگیرد و برای suite سنگین ورودی `ci-full` هم صریحاً فعال شود. این عمل فقط پس از مجوز مستقیم مالک اختیار مالی انجام می‌شود و فقط همان run را مجاز می‌کند؛ SHA قدیمی یا PR بسته/تغییریافته fail-closed می‌شود.

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

