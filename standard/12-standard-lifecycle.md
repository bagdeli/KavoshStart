# 12 — چرخهٔ استاندارد و پیش‌پرواز جلسه

قواعد: STD-1…2، ACC-1، AI-4، REL-6

## مسئله

پین دقیق KavoshStart برای تکرارپذیری و امنیت لازم است، اما «پین دقیق» نباید به معنی «بی‌خبری از نسخهٔ جدید» باشد.
یک پروژهٔ بزرگ می‌تواند ماه‌ها روی نسخهٔ قدیمی بماند، adoption موقت را به وضعیت دائمی تبدیل کند، و در عین
سبز بودن PR/CI بدهی پذیرش جمع کند. این سند مرز بین **ثبات نسخه** و **تازگی استاندارد** را روشن می‌کند.

## قرارداد نسخه

- مصرف‌کننده همیشه workflowها و مانیفست را به یک tag دقیق `vX.Y.Z` پین می‌کند؛ tag متحرک ممنوع است.
- Health آخرین release پایدار KavoshStart را با pin پروژه مقایسه می‌کند و عقب‌ماندگی را آشکار می‌کند.
- هشدار freshness به‌تنهایی مجوز ارتقای خودکار نیست. ارتقا یک PR مستقل با خواندن CHANGELOG و اجرای UPGRADE است.
- اگر نسخهٔ جدید قواعد governance، acceptance، security، release، deploy، CI یا agent-control را تغییر دهد،
  عامل پیش از شروع feature/gate جدید ارتقا را انجام می‌دهد یا یک defer محدود و صریحِ مالک ثبت می‌کند.
- hotfix واقعی می‌تواند با defer محدود ادامه یابد؛ defer نباید به سکوت دائمی دربارهٔ استاندارد تبدیل شود.

## پایان adoption

`adoptionPhase` فقط یک مفهوم تاریخی برای migration پروژه‌های قدیمی بود. در استاندارد جدید:

- `adoptionPhase: true` معتبر نیست؛
- `enforce: false` هیچ‌گاه check سبز تولید نمی‌کند؛
- deviation واقعی با Issue/ADR، مالک، ریسک، کنترل جبرانی و trigger بازبینی ثبت می‌شود؛
- پروژه پس از bootstrap باید با همان governance اجباری که برای کار عادی استفاده می‌کند ادامه دهد.

یعنی adoption یک **مسیر انتقال محدود** است، نه operating mode بلندمدت.

## T2 و continuous acceptance

هر T2 که این نسخه یا جدیدتر را می‌پذیرد باید `acceptance.mode=continuous` داشته باشد.
این الزام به معنی E2E سنگین برای هر PR نیست. هدف بستن حلقهٔ زیر است:

```text
approved scope → implementation → risk-sized evidence → owner acceptance → promotion
```

قواعد تست همچنان هرم ریسک را حفظ می‌کنند: focused/unit زیاد، integration به‌اندازهٔ invariant، و تعداد محدود
journey/end-to-end روی مرز مناسب. چیزی که ممنوع است انتقال نامرئی acceptance debt به انتهای پروژه است.

برای پروژهٔ T2 موجود هنگام upgrade:

1. scope نسخهٔ هدف را در `acceptance/scope.json` تعریف کنید؛
2. acceptance item را بر اساس واحد قابل‌پذیرش release بسازید، نه لزوماً یک ردیف برای هر requirement داخلی؛
3. requirementهای ریزتر می‌توانند زیر یک acceptance item مشترک باشند فقط اگر owner/risk/evidence آنها واقعاً مشترک است
   و traceability جداگانه حفظ می‌شود؛
4. بدهی موجود را واقعی ثبت کنید؛ mergeهای قدیمی را صرفاً به‌خاطر وجود کد accepted اعلام نکنید؛
5. Health نسبت closure و سن قدیمی‌ترین debt را نشان می‌دهد؛ debt قدیمی باید قبل از feature expansion جدید کاهش یابد
   یا با تصمیم owner به gate بعدی/defer مشخص منتقل شود؛
6. Release همچنان 100٪ scope in-release را طبق ACC-3 لازم دارد.

## پیش‌پرواز هر جلسهٔ عامل

قبل از اجرای NEW / ADOPT / UPGRADE / WORK:

1. repository، remote/default branch، scope و محیط‌های مجاز را تثبیت کن.
2. `AGENTS.md`، `kavosh.project.json` و Issue/Spec مربوط را بخوان.
3. pin KavoshStart را با آخرین release پایدار مقایسه کن.
4. اگر عقب است، CHANGELOG بین pin و latest را بخوان و impact را طبقه‌بندی کن.
5. تغییرات governance/acceptance/security/release/deploy/CI/agent-control را قبل از feature/gate جدید upgrade کن،
   مگر owner یک defer محدود و traceable داده باشد.
6. وضعیت زندهٔ GitHub را تازه کن: main، PRهای باز مرتبط، checks و release؛ runtime را فقط وقتی برای task لازم است بررسی کن.
7. mode را انتخاب کن و فقط یک packet منسجم را اجرا کن.

این پیش‌پرواز جای prompt طولانی را نمی‌گیرد؛ آن را کوتاه می‌کند، چون facts و controls در repository و ماشین enforce می‌شوند.

## معیار معماری

KavoshStart باید این تعادل را حفظ کند:

- **prompt کم، guard زیاد**؛
- **pin دقیق، freshness قابل‌مشاهده**؛
- **تست متناسب با ریسک، acceptance پیوسته**؛
- **GitHub به‌عنوان live source of truth**؛
- **بدون auto-upgrade، auto-accept یا bypass-to-green**.
