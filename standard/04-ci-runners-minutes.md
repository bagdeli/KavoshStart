# 04 — CI، runner و بودجه‌ی دقیقه

قواعد: CI-1…9

## runner و هزینه (CI-1…3 — ADR-0009)
| ریپو | پیش‌فرض | شرط |
|---|---|---|
| **private** | بر اساس اعتماد، شبکه و دسترسی: GitHub-hosted مجاز؛ self-hosted یک گزینهٔ اختیاریِ ایزوله است | هر hosted run که از سهمیهٔ مشترک استفاده کند فقط با dispatch مستقیم مالک برای PR/ref/SHA مشخص؛ trigger خودکار خاموش |
| **public** | runner استاندارد GitHub، مانند `ubuntu-latest` | self-hosted فقط با ADR ایزولیشن؛ PRهای fork/کد نامطمئن روی آن اجرا نمی‌شوند. runner بزرگ/custom پولی پیش‌فرض نیست |
| **T1/static, هر visibility** | انتخاب اختیاری `ci.runner: none`، بودجهٔ ماهانه صفر | فقط حالت local-only است؛ scaffold هیچ workflowی نمی‌سازد و خروجی موفق `make check` باید در PR ثبت شود |

### حالت local-only برای T1/static

مالک می‌تواند در intake، `ci.runner: "none"` را برای پروژهٔ T1/static انتخاب کند. این حالت هیچ فایل workflowی تولید نمی‌کند و هیچ دقیقهٔ GitHub Actions مصرف نمی‌کند. بودجه باید صفر باشد. عامل پیش از درخواست merge، `make setup` و `make check` را محلی اجرا می‌کند و در PR دستورها، کد خروجی، خلاصهٔ نتیجه و محیط اجرا را می‌نویسد. نتیجهٔ قرمز یا نبود شواهد مانع merge است. اگر یک status check واقعاً قرمز است، دورزدن آن ممنوع می‌ماند؛ این حالت فقط برای مخزنی است که عمداً CI status check ندارد و قواعد branch آن PR را همچنان الزامی می‌کنند.

برای smoke test مرورگر، Chromium/Chrome headless نصب‌شدهٔ محلی را استفاده کنید؛ اگر موجود نیست، تست را با `SKIP` روشن گزارش کنید. خروجی هر فایل تست را در مسیر جداگانه‌ای مانند `artifacts/smoke/<test-name>/` بنویسید. در Windows، پردازهٔ برنامه و همهٔ فرزندانش را در Job Object مدیریت کنید و در مسیر cleanup کل درخت پردازه را ببندید. وابستگی یا مرورگر را هنگام اعتبارسنجی آفلاین دانلود نکنید.

برای پروژهٔ private، اگر مالک نمی‌خواهد سهمیهٔ مشترک مصرف شود، workflow روی runner خودمیزبان ایزوله یا profile محلی واجدشرایط اجرا می‌شود؛ برای GitHub-hosted، تنها `workflow_dispatch` با PR number و head SHA جاری مجاز است. ثبت این انتخاب در مانیفست به‌تنهایی مجوز اجرا نیست.

قواعد runner خودمیزبان (یک runner مشترک می‌تواند به صف و لغوهای زیاد منجر شود):
- **برای هر ریپو** ثبت می‌شود، نه برای کل حساب؛ labelهای `self-hosted, linux, x64, <repo-slug>` دقیق‌اند.
- Core یک implementation واحد برای isolation تحمیل نمی‌کند. rootless container، sandbox، VM disposable/ephemeral و runner اختصاصیِ یک repo می‌توانند بخشی از trust model معتبر باشند، اما ADR باید isolation واقعی، مرز کد نامطمئن و credential boundary را توضیح دهد. rootful Docker بدون containment مستقل همچنان root-equivalent است و قابل‌قبول نیست. runner persistent/dedicated نباید credential تولید/production داشته باشد و workflowهای PR باید boundary کد نامطمئن را machine-enforce کنند.
- Runner capacity به صف و SLO بستگی دارد؛ تعداد ثابت برای همهٔ T2 الزام نیست.
- رازهای production هرگز روی ماشین runner نیستند (استقرار pull-based است — بخش 07).
- ظرفیت runner (`ci.runners`) براساس صف و SLO توسط مالک تعیین و در همان control surface بررسی می‌شود.
- نصب: `sudo bash scripts/install-runner.sh <owner/repo> <token> [n]`؛ token را مالک می‌گیرد:
  `gh api -X POST repos/<owner>/<repo>/actions/runners/registration-token -q .token`
- شبکه: runner داخل ایران باید به github.com، ghcr.io و مخازن بسته‌ها (یا mirror داخلی مثل KavoshRepo) دسترسی پایدار داشته باشد.
- تغییر visibility یک ریپو = تغییر runner در همان PR؛ governance ناهمخوانی را قرمز می‌کند.

حساب Free استفاده می‌شود و shared quota فقط پس از اجازهٔ مستقیم برای یک اجرای مشخص مصرف می‌شود. budget یا گزارش دقیقه توقف قطعی هزینه نیست. artifact، cache، Packages و انتقال داده جدا بررسی می‌شوند؛ runner بزرگ و AI API پولی وابستگی استاندارد نیستند.

## قواعد صرفه‌جویی (به ترتیب اثر)
1. **CI-6:** CI سنگین روی Draft خاموش است؛ اجرای زودهنگام باید درخواست صریح و، اگر سهمیه مصرف می‌کند، مجوز مستقیم همان اجرا داشته باشد.
2. **CI-5:** jobهای سنگین روی `main`/tag/برچسب `ci:full` یا dispatch صریح همان PR/SHA اجرا می‌شوند.
3. **CI-4:** `concurrency` با `cancel-in-progress` برای PR.
4. فیلتر مسیر و بررسی محلی مطابق `make check`.
5. هر job حداقل یک دقیقه حساب می‌شود → jobهای کوچک را در یک job ادغام کنید.
6. `timeout-minutes` برای هر job (پیش‌فرض 360 دقیقه است!).

## اجرای زودهنگام و workflowهای هر پروژه
روی Draft، CI سنگین خودکار اجرا نمی‌شود. در public یا self-hosted، افزودن `ci:full` اجرای زودهنگام را درخواست می‌کند؛ روی private GitHub-hosted، `workflow_dispatch` باید PR number و head SHA دقیق را بگیرد و برای suite سنگین ورودی `ci-full` هم صریحاً فعال شود. این عمل توسط صاحب ریپو انجام می‌شود و فقط همان run را مجاز می‌کند؛ SHA قدیمی یا PR بسته/تغییریافته fail-closed می‌شود.

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
