# برگه‌ی پروژه — KavoshStart

> ثابت و بدون وضعیت. تغییر این برگه = PR + تأیید مالک. وضعیت کارها در GitHub است (Issues، milestone، Releases).

## هدف
استاندارد مهندسی همه‌ی ریپوهای Kavosh: پرسش‌نامه‌ی شروع، رده‌بندی، قواعد با سازوکار اجرا، قالب‌ها و workflowهای مشترک GitHub برای پروژه‌هایی که انسان و عامل‌های AI با هم می‌سازند — روی پلن رایگان GitHub.

## کاربران
مالک (bagdeli) و عامل‌های AI (Claude Code، Codex) که پروژه‌های Kavosh را می‌سازند یا نگه می‌دارند. داخلی، 1–10 نفر.

## خروجی‌ها
- `START.md` — پروتکل عامل (NEW / ADOPT / UPGRADE / WORK)
- `intake/` — پرسش‌نامه، رده‌بندی، schema مانیفست
- `standard/RULES.md` — قواعد با شناسه، سطح و لایه‌ی اجرا
- `templates/` — فایل‌های پروژه برای T0–T2 و runtimeها
- workflowهای مشترک: governance، main-guard، health، release (با tag دقیق)

## خارج از محدوده
- کد محصول
- طراحی ظاهری (مرجع آن KavoshUI است)
- الزام به قابلیت‌های پولی GitHub

## مشخصات
| | |
|---|---|
| رده (Tier) | T1 — کتابخانه‌ی مصرف‌شده توسط ریپوهای دیگر |
| اجرا (Runtime) | none |
| روش استقرار | none (نسخه‌ها = tag + Release، فقط از طریق دروازه‌ی REL-5) |
| رابط کاربری | ندارد |
| بودجه‌ی دقیقه‌ی CI در ماه | 100 |

## فرض‌ها
- ریپو private می‌ماند؛ ریپوهای مصرف‌کننده با تنظیم Access «repositories owned by the user» به workflowها دسترسی دارند.
- GitHub-hosted runnerها در دسترس‌اند (پس از رفع قفل Billing، Issue #1).
