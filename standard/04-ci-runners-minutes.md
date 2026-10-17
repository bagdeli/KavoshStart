# 04 — CI، runner و بودجه‌ی دقیقه

قواعد: CI-1…9

## Runtime contract for reusable controls

Reusable KavoshStart governance, main-guard, health, release-gate and RC-gate logic must not assume that a consumer runner has GitHub CLI installed. Core GitHub API access uses Python standard library plus the workflow-scoped `GITHUB_TOKEN`/`GITHUB_API_URL`; git remains the only repository CLI assumption. A project may install `gh` for its own tooling, but KavoshStart conformance cannot depend on that hidden host prerequisite.

## Runner و هزینه (CI-1…3 — ADR-0018)

**Runner ثبت‌شدهٔ GitHub Actions با CI مستقلی که روی سرور شخصی اجرا می‌شود یکی نیست.** نام سرور، مالکیت ماشین یا استفاده از Container این تفاوت را تغییر نمی‌دهد.

| انتخاب `ci.runner` | مخزن خصوصی | مخزن عمومی | خروجی و مجوز |
|---|---|---|---|
| `external` (SelfServer مستقل) | مجاز | مجاز | **هیچ GitHub Actions workflowی وجود ندارد.** ADR واقعی برای اجرای `make check`، گزارش معتبر `required`/`kavosh / governance` روی exact SHA و انتشار مستقل لازم است |
| `self-hosted` (ثبت‌شده در GitHub Actions) | پیش‌فرض **ممنوع**، استثنای موردی فقط با **تأیید صریح مالک/ناظر** و CI-2 | مجاز با CI-2 | ADR ایزولیشن، منع کد نامطمئن، جداسازی Secrets و گروه/برچسب مخزن؛ private فقط اجرای دستی و محدوده‌دار |
| `github-hosted` (سهمیه GitHub) | فقط با **اجازه مدیر حساب/مخزن برای هزینه همان اجرا** | Runner استاندارد پیش‌فرض | در private اجرای دستی، محدود به PR/SHA فعلی و با بررسی مجوز مدیر؛ مقدار Budget اثبات اجازه نیست |
| `none` | فقط T1/static | فقط T1/static | هیچ Actions workflow؛ `make check` و نتیجه محلی ثبت می‌شود؛ جای Required Check قرمز را نمی‌گیرد |

این **سیاست KavoshStart** است؛ GitHub خودِ self-hosted در مخزن خصوصی را به‌طور کلی ممنوع نمی‌کند. حتی در public نیز خطر اجرای PR نامطمئن روی runner دائم وجود دارد. مخزن public اجازه استفاده با کنترل‌های CI-2 را دارد، نه مجوز حذف آنها. [امنیت GitHub Actions](https://docs.github.com/en/actions/reference/security/secure-use)؛ [Runnerهای موقت](https://docs.github.com/en/actions/reference/runners/self-hosted-runners).

### SelfServer مستقل: اثبات واقعی، نه CI ظاهری

- `ci.runner: external` باید `ci.externalCIADR` واقعی را معرفی کند؛ مدیر همان مخزن به‌طور مستقل مسئول راه‌اندازی CI و publisher است. هیچ Runner در Actions ثبت، هیچ `.github/workflows/` ایجاد و هیچ مزیت مخفی‌ای از GitHub-hosted فرض نمی‌شود.
- کنترل‌های Core از طریق همان **semantic command contract** (مثلاً `make setup && make check` و ممیزی KavoshStart) روی exact commit اجرا شوند. نتیجه از GitHub App/سرویس معتبر با `required` و `kavosh / governance` و در صورت لزوم `main-guard / main-guard` روی SHA دقیق گزارش شود. خود فایل ADR، لاگ محلی یا متن PR **check سبز ایجاد نمی‌کند**؛ publisher باید واقعاً کار کند. کنترل App identity و plan/ruleset بسته به حساب در GitHub به‌طور جداگانه بررسی می‌شود.
- انتشار external فقط با `release.strategy: custom`، `release.strategyADR` و `release.externalCommand` به یک فایل واقعی در `scripts/` انجام می‌شود؛ tag immutable، بررسی آخرین SHA `main` و Required Check/پذیرش همان Commit طبق REL-5/6 لازم‌اند. `release-please` که به Actions وابسته است، با وجود نداشتن Actions workflow یک مسیر انتشار پنهانی نیست.
- انتخاب محصول مستقل (Woodpecker، Jenkins، Dagger یا ابزار موجود سرور) تصمیم هر مصرف‌کننده است، نه dependency هسته. [Woodpecker](https://woodpecker-ci.org/docs/administration/general) فقط نمونهٔ الگوی server/agent و GitHub status reporting است.

### GH Actions خودمیزبان: استثنای خصوصی سخت‌گیرانه

`ci.privateSelfHostedApprovalADR` باید به **تصمیم واقعی و دامنه‌دار مالک** اشاره کند؛ `ci.trustModelADR` جداگانه runner trust model، isolation، untrusted code، credential boundary و containment را اثبات کند. یک PR یا ADR ویرایش‌پذیر **اثبات رمزنگاری‌شدهٔ رضایت مالک نیست**: بازبین باید اصل مجوز و وضعیت تنظیمات GitHub را بررسی کند. استثنا برای هر Repository مستقل است، نه برای همهٔ محصولات یا همهٔ Runnerها.

در private، GH Actions خودمیزبان نیز مانند GitHub-hosted فقط از مسیر dispatch دستیِ مربوط به ref/SHA اجرا می‌شود؛ `pull_request`، `push`، `schedule` و `workflow_run` نباید خودکار job بسازند. runnerهای ephemeral/disposable بر persistent ترجیح دارند؛ جداسازی واقعی host، عدم persistence راز، least-privilege و محدودکردن runner group به repo/workflow باید در review بررسی شود. rootful Docker یا جدا بودن Container به‌تنهایی boundary معتبر نیست.

در public، fork PR یا کد ناشناس حق دسترسی به Runner خودمیزبان ندارد. CI-2 حتی وقتی انتخاب self-hosted برای public مجاز است لازم می‌ماند. [مدیریت runner group](https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/manage-access).

### GitHub-hosted خصوصی: مجوز سهمیه قابل استنتاج نیست

فقط **ادمین حساب/مخزن** می‌تواند برای مصرف سهمیه اجازه دهد و مالک باید این اجازه را برای همان اجرا/ref/SHA تأیید کند. `workflow_dispatch` صرفاً ابزار اعمال محدوده SHA است، نه اثبات اینکه actor ادمین یا صاحب بودجه بوده است؛ بدون سیاست واقعی دسترسی/approval در GitHub، سطح این کنترل انسانی (R) باقی می‌ماند. `monthlyMinutesBudget` فقط راهنمای برنامه‌ریزی است. برای ربات‌های دارای write access نیز trigger دستی لزوماً به معنی تأیید صاحب بودجه نیست. [صورتحساب Actions](https://docs.github.com/en/actions/concepts/billing-and-usage).

در private، reusable workflowهای خارجی می‌توانند `runs-on` مستقل انتخاب کنند؛ فقط نسخه پین‌شده و ممیزی‌شدهٔ استاندارد یا Workflow محلی واقعاً موجود قابل قبول است. Scanner استاتیک نمی‌تواند امنیت همهٔ مسیرهای dynamic Actions را ثابت کند.

### انتخاب local-only

`none` فقط برای T1/static بدون GitHub Actions است. شواهد `make check` محلی در PR ثبت می‌شوند. از آن برای دورزدن CI شکست‌خورده، release gate یا پروژه بزرگ‌تر استفاده نکنید.

## قواعد صرفه‌جویی (به ترتیب اثر)
1. **CI-6:** CI سنگین روی Draft خاموش است؛ اجرای زودهنگام باید درخواست صریح و، اگر سهمیه مصرف می‌کند، مجوز مستقیم همان اجرا داشته باشد.
2. **CI-5:** jobهای سنگین روی `main`/tag/برچسب `ci:full` یا dispatch صریح همان PR/SHA اجرا می‌شوند.
3. **CI-4:** `concurrency` با `cancel-in-progress` برای PR.
4. فیلتر مسیر و بررسی محلی مطابق `make check`.
5. هر job حداقل یک دقیقه حساب می‌شود → jobهای کوچک را در یک job ادغام کنید.
6. `timeout-minutes` برای هر job (پیش‌فرض 360 دقیقه است!).

## اجرای زودهنگام و workflowهای هر پروژه
روی Draft، CI سنگین خودکار اجرا نمی‌شود. در public، افزودن `ci:full` اجرای زودهنگام را درخواست می‌کند؛ روی private GitHub Actions، `workflow_dispatch` باید PR number و head SHA دقیق را بگیرد و برای suite سنگین ورودی `ci-full` هم صریحاً فعال شود. این عمل توسط صاحب ریپو انجام می‌شود و فقط همان run را مجاز می‌کند؛ SHA قدیمی یا PR بسته/تغییریافته fail-closed می‌شود.

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

