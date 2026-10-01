# 04 — CI، runner و بودجه‌ی دقیقه

قواعد: CI-1…9

## runner و هزینه (CI-1…3 — ADR-0009)
| ریپو | پیش‌فرض | شرط |
|---|---|---|
| **private** | runner خودمیزبانِ همان repo یا آماده‌سازی محلی | private hosted فقط با اجازهٔ مستقیم مالک برای اجرای محدود و مشخص؛ نبود CI معتبر، merge/release را می‌بندد |
| **public** | runner استاندارد GitHub، مانند `ubuntu-latest` | runner خودمیزبان و runner بزرگ/custom ممنوع؛ اجرای استاندارد عمومی نباید سهمیهٔ مشترک یا هزینه بسازد |

قواعد runner خودمیزبان (یک runner مشترک می‌تواند به صف و لغوهای زیاد منجر شود):
- **برای هر ریپو** ثبت می‌شود، نه برای کل حساب؛ labelهای `self-hosted, linux, x64, <repo-slug>` دقیق‌اند.
- عضویت در گروه Docker روت‌فل دسترسی root-equivalent است. installer این مخزن Docker روت‌فل را رد می‌کند و فقط Docker روت‌لس را می‌پذیرد؛ runner یک‌بارمصرف است. VM اختصاصی disposable نیز باید پس از هر job بیرون از installer حذف شود.
- Runner capacity به صف و SLO بستگی دارد؛ تعداد ثابت برای همهٔ T2 الزام نیست.
- رازهای production هرگز روی ماشین runner نیستند (استقرار pull-based است — بخش 07).
- ظرفیت runner (`ci.runners`) براساس صف و SLO توسط مالک تعیین و در همان control surface بررسی می‌شود.
- نصب: `sudo bash scripts/install-runner.sh <owner/repo> <token> [n]`؛ token را مالک می‌گیرد:
  `gh api -X POST repos/<owner>/<repo>/actions/runners/registration-token -q .token`
- شبکه: runner داخل ایران باید به github.com، ghcr.io و مخازن بسته‌ها (یا mirror داخلی مثل KavoshRepo) دسترسی پایدار داشته باشد.
- تغییر visibility یک ریپو = تغییر runner در همان PR؛ governance ناهمخوانی را قرمز می‌کند.

حساب Free استفاده می‌شود و shared quota فقط پس از اجازهٔ مستقیم برای یک اجرای مشخص مصرف می‌شود. budget یا گزارش دقیقه توقف قطعی هزینه نیست. artifact، cache، Packages و انتقال داده جدا بررسی می‌شوند؛ runner بزرگ و AI API پولی وابستگی استاندارد نیستند.

## قواعد صرفه‌جویی (به ترتیب اثر)
1. **CI-6:** CI سنگین روی Draft خاموش است؛ dispatch زودهنگام مجوز سهمیه به‌شمار نمی‌رود.
2. **CI-5:** jobهای سنگین فقط روی `main`/tag/برچسب `ci:full`.
3. **CI-4:** `concurrency` با `cancel-in-progress` برای PR.
4. فیلتر مسیر و بررسی محلی مطابق `make check`.
5. هر job حداقل یک دقیقه حساب می‌شود → jobهای کوچک را در یک job ادغام کنید.
6. `timeout-minutes` برای هر job (پیش‌فرض 360 دقیقه است!).

## ساختار workflowهای هر پروژه
| فایل | رویداد | Tier |
|---|---|---|
| `kavosh.yml` | PR، push به main، هفتگی ← فراخوانی workflowهای KavoshStart با tag دقیق | All |
| `ci.yml` | PR (غیر Draft)، push به main ← `make check` + job `required` | All |
| `release.yml` | پس از موفقیت ci روی main ← `kavosh-release` (دروازه‌ی REL-5 + release-please + فایل‌های انتشار) | All |
| `ai-review.yml` | PR ready ← بازبینی AI (نیاز به کلید API) | T2 (T1 اختیاری) |

## قرارداد فرمان (CI-8)
CI هیچ‌وقت ابزار زبان خاصی را مستقیم صدا نمی‌زند؛ فقط `make setup` و `make check`. پس:
- عامل و CI دقیقاً یک کار را انجام می‌دهند (سبز محلی ≈ سبز CI).
- تغییر ابزار (ruff → x) فقط `Makefile` را عوض می‌کند.
