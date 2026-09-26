# 01 — مدل اجرا روی پلن رایگان GitHub

## چه چیزی روی ریپوی private در پلن Free وجود ندارد
| قابلیت | وضعیت | پیامد |
|---|---|---|
| Branch protection / Rulesets | ❌ (فقط public یا پلن پولی) | push مستقیم و force-push به `main` از سمت GitHub مسدود نمی‌شود |
| Required status checks | ❌ | PR قرمز قابل ادغام است |
| Required reviewers / CODEOWNERS اجباری | ❌ | CODEOWNERS فقط درخواست بازبینی است |
| Merge queue، Environments با reviewer | ❌ | — |
| GitHub Pages | ❌ برای private | سایت ایستا روی سرور خودمان |
| Actions | ✅ **2,000 دقیقه/ماه برای کل حساب**، هر job به دقیقه‌ی کامل گرد می‌شود | بودجه‌بندی اجباری (CI-3) |
| Issues، sub-issues، Projects، Milestones، Releases، Labels | ✅ | — |
| Issue Types | ❌ (فقط Organization) | برچسب `type:*` |
| Reusable workflow از ریپوی private دیگر همان کاربر | ✅ با تنظیم Access | KavoshStart مرکز workflowهاست |
| Squash-only، حذف خودکار شاخه | ✅ | لایه‌ی S |

## پنج لایه‌ی جایگزین

```text
   عامل AI / توسعه‌دهنده
          │
   [A] محافظ عامل ─── .githooks/pre-push  +  .claude/settings.json (deny)
          │              ✗ push به main   ✗ force-push   ✗ --no-verify   ✗ gh pr merge
          ▼
   شاخه‌ی کوتاه ──► PR
          │
   [P] kavosh-governance ── قرمز اگر: عنوان، شاخه، Issue، اندازه، base، AI، مانیفست، AGENTS.md، docs
          │
   [R] مالک: فقط PR سبز را Squash merge می‌کند   ← تنها نقطه‌ی کاملاً انسانی (PR-7)
          ▼
        main
          │
   [M] kavosh-main-guard ── بعد از هر push: commit بدون PR؟ PR با check قرمز؟ → Issue «kavosh:violation»
          │
   [H] kavosh-health (هفتگی) ── شاخه‌ها، دقیقه‌ها، Issueها، CI، releaseها → Issue «Repository health»
```

- **لایه‌ی A** جلوی ۹۰٪ خطاهای عامل را پیش از رسیدن به GitHub می‌گیرد. قابل دور زدن است (مثلاً `--no-verify`)، برای همین آن را هم در deny گذاشته‌ایم و لایه‌ی M پشتیبان است.
- **لایه‌ی M** چیزی را برنمی‌گرداند (revert خودکار روی `main` خودش خطرناک است)، بلکه **هیچ تخلفی را بی‌صدا نمی‌گذارد**: Issue تخلف باز می‌شود و تا رفع (معمولاً یک PR اصلاحی یا revert) باز می‌ماند.
- **قاعده‌ی انسانی واحد:** «PR قرمز را ادغام نکن» (PR-7). دکمه‌ی Merge در دسترس است؛ این تنها جایی است که به انضباط شما تکیه می‌کنیم — و اگر نقض شود، لایه‌ی M آن را ثبت می‌کند.

## هزینه‌ی دقیقه‌ی خود KavoshStart
- `kavosh-governance`: یک job، حدود 1 دقیقه به ازای هر رویداد PR (opened/synchronize/ready/edited عنوان-بدنه).
- `kavosh-main-guard`: یک job، حدود 1 دقیقه به ازای هر ادغام.
- `kavosh-health`: هفته‌ای یک job، حدود 1–2 دقیقه.
- جمع برای پروژه‌ای با 30 PR در ماه: حدود 30–60 دقیقه. در بودجه‌ی Tier حساب شده است.

## اگر روزی پلن پولی شد یا ریپو public شد
هیچ‌چیز دور ریخته نمی‌شود: `templates/rulesets/main.json` را اعمال کنید (`bootstrap-repo.sh --rulesets`) و check‌های `kavosh` و `required` را required کنید. لایه‌های A، M و H همچنان مفیدند.
