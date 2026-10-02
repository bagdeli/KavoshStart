# 10 — ارتباط با KavoshUI

قواعد: UI-1…3

## تقسیم مسئولیت
| موضوع | مرجع |
|---|---|
| روند کار، ریپو، شاخه، CI، انتشار، عامل‌ها | **KavoshStart** |
| ظاهر، کامپوننت، تعامل، دسترس‌پذیری، RTL، اعداد/تاریخ فارسی در UI | **KavoshUI** |
| منطق کسب‌وکار، داده، API | خود پروژه |

## قواعد مصرف
1. `ui.kavoshui` در مانیفست نسخه‌ی **دقیق** را پین می‌کند (نه `latest`، نه `^`).
2. کامپوننت‌ها از بسته‌های نسخه‌دار KavoshUI مصرف می‌شوند، به همان روشی که KavoshUI در README و `CONSUMER_CONFORMANCE_STANDARD_FA.md` خودش تعریف می‌کند. کپی کد کامپوننت در پروژه ممنوع؛ کمبود = Issue در KavoshUI.
3. استثنای ظاهری فقط از طریق مکانیزم override که KavoshUI مجاز کرده (`CSS_PORTABILITY_STANDARD_FA.md`).
4. ارتقای KavoshUI = PR جدا `chore(ui): upgrade KavoshUI to vX.Y.Z` + تصاویر رندر (RTL، موبایل، تم تیره).
5. عامل پیش از هر کار UI این اسناد KavoshUI را می‌خواند: `AGENTS.md`، `docs/foundations/DESIGN_STANDARD_FA.md`، `docs/foundations/COMPONENT_SELECTION_STANDARD_FA.md`، `docs/architecture/CONSUMER_CONFORMANCE_STANDARD_FA.md` — و **نه** همه‌ی 91 سند.

## نکته برای خود KavoshUI
KavoshUI یک پروژه‌ی T1 (کتابخانه‌ی مصرف‌شده توسط دیگران) است و باید KavoshStart را بپذیرد. ممیزی آن باید فقط داده‌های خود KavoshUI را مبنا قرار دهد؛ پذیرش آن در [adoption/ADOPTION.md](../adoption/ADOPTION.md) پیشنهاد شده است.
