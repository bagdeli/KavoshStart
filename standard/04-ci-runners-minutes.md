# 04 — CI، runner و بودجه‌ی دقیقه

قواعد: CI-1…9

## runner بر اساس visibility (CI-1، CI-2 — ADR-0008)
| ریپو | runner | چرا |
|---|---|---|
| **private** | خودمیزبان، ثبت‌شده برای همان ریپو: `[self-hosted, linux, x64, <repo-slug>]` | روی این حساب، jobهای GitHub-hosted در ریپوهای private به‌خاطر قفل Billing اجرا نمی‌شوند؛ کار نباید به صورت‌حساب GitHub وابسته باشد |
| **public** | GitHub-hosted (`ubuntu-latest`) | رایگان و نامحدود؛ runner خودمیزبان روی ریپوی public یعنی اجرای کد PRهای fork روی ماشین ما — ممنوع |

قواعد runner خودمیزبان (درس یک پروژه‌ی خصوصی T2: یک runner مشترک می‌تواند به صف و cancellation شدید منجر شود):
- **برای هر ریپو** ثبت می‌شود، نه برای کل حساب؛ label چهارم نام ریپوست تا jobها قاطی نشوند.
- کاربر بدون دسترسی root، Docker نصب، workspace تمیز در هر job؛ ephemeral در صورت امکان.
- رازهای production هرگز روی ماشین runner نیستند (استقرار pull-based است — بخش 07).
- T2 حداقل **دو** runner آنلاین (`ci.runners` در مانیفست)؛ لایه‌ی O تعداد آنلاین را می‌شمارد.
- نصب: `sudo bash scripts/install-runner.sh <owner/repo> <token> [n]`؛ token را مالک می‌گیرد:
  `gh api -X POST repos/<owner>/<repo>/actions/runners/registration-token -q .token`
- شبکه: runner داخل ایران باید به github.com، ghcr.io و مخازن بسته‌ها (یا mirror داخلی مثل KavoshRepo) دسترسی پایدار داشته باشد.
- تغییر visibility یک ریپو = تغییر runner در همان PR؛ governance ناهمخوانی را قرمز می‌کند.

## بودجه (CI-3)
بودجه فقط به دقیقه‌های GitHub-hosted ریپوهای **private** مربوط است. با CI-1 این مقدار برای پروژه‌های private صفر است
(`monthlyMinutesBudget: 0`) و ریپوهای public دقیقه‌ی نامحدود رایگان دارند. بودجه فقط برای استثناهای ثبت‌شده با ADR معنا دارد؛
جمع کل ≤ 1,600.

`kavosh-health` مصرف ماه جاری هر ریپو را از روی jobها (گرد به دقیقه‌ی بالا، فقط hosted) تخمین می‌زند و با `ci.monthlyMinutesBudget` مقایسه می‌کند. `scripts/portfolio.py` جمع کل حساب را نشان می‌دهد.
با حساب Free و spending limit صفر، پس از اتمام دقیقه‌ها jobهای private تا اول ماه بعد **اجرا نمی‌شوند** — هزینه‌ی مالی ندارد ولی تحویل متوقف می‌شود.

## قواعد صرفه‌جویی (به ترتیب اثر)
1. **CI-6:** عامل `make check` را محلی اجرا می‌کند و یک‌بار push می‌کند؛ CI روی Draft اجرا نمی‌شود.
2. **CI-5:** jobهای سنگین فقط روی `main`/tag/برچسب `ci:full`.
3. **CI-4:** `concurrency` با `cancel-in-progress` برای PR.
4. فیلتر مسیر: تغییر فقط در `docs/` → فقط governance.
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
