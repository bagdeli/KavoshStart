# 04 — CI، runner و بودجه‌ی دقیقه

قواعد: CI-1…9

## Runtime contract for reusable controls

Reusable KavoshStart governance, main-guard, health, release-gate and RC-gate logic must not assume that a consumer runner has GitHub CLI installed. Core GitHub API access uses Python standard library plus the workflow-scoped `GITHUB_TOKEN`/`GITHUB_API_URL`; git remains the only repository CLI assumption. A project may install `gh` for its own tooling, but KavoshStart conformance cannot depend on that hidden host prerequisite.

## PRIVATE — local commands only; no GitHub Actions (CI-1, ADR-0018)

**بدون استثنا:** هر مخزن `private`، در هر Tier/Runtime، `ci.runner=none` و بودجه صفر دارد. هیچ GitHub Actions job روی self-hosted یا GitHub-hosted، ARC، گروه runner، reusable workflow، dispatch، trigger خودکار یا محیط دیگری اجرا نمی‌شود. عامل نمی‌تواند runner را روشن، نصب یا حذف کند، Actions را dispatch کند یا مخزن خصوصی را با ابزار متصل mutate کند. فقط **دستورهای مشخص** می‌دهد و **مالک** آن‌ها را در سیستم مورداعتماد دارای دسترسی GitHub اجرا می‌کند.

**پیش‌شرط حیاتی:** مالک **قبل از هر push/PR** در Settings → Actions → General، Actions مخزن خصوصی را غیرفعال می‌کند. تا آن زمان ایجاد PR در مخزن دارای workflow قدیمی ممکن است runner را trigger کند. حذف YAMLها در PR به‌تنهایی خاموشی مطمئن نیست. ثبت runner قدیمی مجوز اجرا نیست؛ مالک وضعیت آن را جداگانه بررسی می‌کند.

- Manifest private: فقط `runner=none` و `monthlyMinutesBudget=0`؛ هیچ `runnerLabels`، `runners`، `trustModelADR`، `requiredWorkflow` یا `.github/workflows/*.yml|yaml` نباید باقی بماند. GitHub Issues/PR/Releases همچنان برای metadata و توزیع قابل استفاده‌اند، **نه compute**.
- کار واقعی: عامل دستورهای `make setup/check`، آزمون حوزهٔ اثر، ساخت بسته، `git` و `gh` می‌نویسد؛ مالک اجرا می‌کند و HEAD SHA، command، exit code، نسخهٔ ابزار و hash artifact را در private PR گزارش می‌کند؛ token/secret داخل خروجی نمی‌آید.
- Code/test/security/UAT/انتشار هنوز gate دارند. غیاب GitHub Actions status **به معنی سبزشدن خودکار** نیست. مالک قوانین branch protection requiring legacy Actions checks را به مدل انسانی/محلی اصلاح می‌کند؛ `--admin` و bypass ممنوع‌اند.
- `gh pr merge`, `gh release create` و انتشار package تنها از سیستم مالک با تأیید SHA، ورودی واقعی و مجوزهای لازم انجام می‌شوند. هیچ Actions publishing job یا attestation جعلی ایجاد نمی‌شود.
- خطای تکراری download/upload: URL امن، DNS، IP واقعاً مشاهده‌شده یا unknown و خطا برای رفع محدودیت به مالک گزارش می‌شود؛ proxy/mirror/relay خودکار ممنوع است.

این انتخاب سیاست مالک (ADR-0018) است، نه محدودیت GitHub. ADR-0015 که private GitHub-hosted را مجاز می‌دانست **منسوخ** شده است.

## PUBLIC — allowed GitHub Actions with bounded risk (CI-2/3)

Public: standard hosted runner پیش‌فرض، self-hosted فقط با ADR جداسازی، منع fork code و کنترل credential. Public T1/static می‌تواند local-only `runner=none` باشد. Budget و quota تابع policy حساب‌اند و هیچ manifestی خودبه‌خود مجوز مصرف منابع نمی‌دهد. نمونهٔ `ci.yml`، `kavosh.yml` و `release.yml` فقط برای public scaffold می‌شوند؛ برای private هیچ workflow تولید نمی‌شود.

## قواعد صرفه‌جویی در GitHub Actions مخازن public (به ترتیب اثر)
1. **CI-6:** CI سنگین روی Draft خاموش است؛ اجرای زودهنگام باید درخواست صریح و، اگر سهمیه مصرف می‌کند، مجوز مستقیم همان اجرا داشته باشد.
2. **CI-5:** jobهای سنگین روی `main`/tag/برچسب `ci:full` یا dispatch صریح همان PR/SHA اجرا می‌شوند.
3. **CI-4:** `concurrency` با `cancel-in-progress` برای PR.
4. فیلتر مسیر و بررسی محلی مطابق `make check`.
5. هر job حداقل یک دقیقه حساب می‌شود → jobهای کوچک را در یک job ادغام کنید.
6. `timeout-minutes` برای هر job (پیش‌فرض 360 دقیقه است!).

## اجرای زودهنگام و workflowهای **public**
**فقط در public**، اجرای زودهنگام CI ممکن است پس از بررسی PR/ref/SHA و بودجهٔ مجاز انجام شود. در private اجرای GitHub Actions برای Draft، PR، push یا dispatch **همیشه ممنوع** است؛ عامل فقط دستورهای تست/merge/release را می‌دهد و مالک در سیستم مورداعتماد اجرا می‌کند. گام CI سنگین در private فقط یک command محلیِ واقعاً اجراشده با exit code است.

**جدول زیر صرفاً برای public است؛ private هیچ‌یک از این workflowها را ندارد.**

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

