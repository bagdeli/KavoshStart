# 06 — مستندات و تصمیم‌ها

قواعد: DOC-1…4، SRC-2، SRC-3

## ساختار استاندارد docs در هر پروژه
```text
README.md            یک صفحه: چیست (= summary مانیفست)، چطور اجرا کنم، لینک‌ها
PROJECT.md           برگه‌ی پروژه: هدف، کاربران، محدوده، خارج از محدوده، فرض‌ها (بدون وضعیت)
AGENTS.md            دستورالعمل عامل‌ها
CHANGELOG.md         خودکار (release-please)
docs/
  decisions/         ADRها (MADR)، شماره‌ی ترتیبی، تغییرناپذیر
  runbooks/          «چطور X را انجام دهم» عملیاتی (استقرار، بازیابی، پشتیبان)   T1+
  architecture/      توضیح معماری (نمودار، مرز ماژول‌ها)                          T2
  GLOSSARY.md        یک خط برای هر اصطلاح
specs/<n>-<slug>/    spec.md + plan.md                                           T1+ (T2 اجباری)
```
(نسخه‌ی ساده‌شده‌ی Diátaxis: tutorial در README، how-to در runbooks، reference در contracts/API، explanation در ADR/architecture.)

## قواعد حجم
- هیچ `.md` بزرگ‌تر از 60KB.
- `archive/` نداریم — تاریخچه در git است. سند منسوخ حذف می‌شود؛ اگر ارزش تاریخی دارد، یک ADR خلاصه‌اش را نگه می‌دارد.
- هیچ «prompt اصلی» یا «قرارداد تکمیل محصول» چندصد KB — این‌ها به Spec و Issue شکسته می‌شوند.

## ADR
- هر Issue `type:decision` با PR حاوی ADR بسته می‌شود.
- بخش **Enforcement** در قالب ADR اجباری است: کدام تست/lint این تصمیم را زنده نگه می‌دارد؟ «هیچ» یعنی تصمیم به‌زودی نقض می‌شود.

## زبان
- محصول و مستندات کاربر: فارسی.
- `AGENTS.md`، ADR، Spec، کامنت کد، commit: انگلیسی (دقت عامل‌ها، سازگاری ابزار).
- `PROJECT.md` و `README.md`: فارسی.
