# 16 — Base-first delivery, Feature Dependency Graph و Release Units

**قواعد:** BASE-1…3، TRN-1…5، WK-3/5/6، CR-3، REL-1…7 و ACC-1…4.
این متن **روش عمومی** است، نه وضعیت یک مصرف‌کننده یا استاندارد جدید برای یک دامنهٔ محصول. تصمیم، پذیرش و شواهد واقعی هر پروژه در مخزن خودش می‌مانند.

## چرا ابتدا Base؟

دو شکست متقابل رخ می‌دهد: (۱) معماری و کد بسیار تولید می‌شود ولی هنوز یک مسیر واقعی و امن از نصب تا رفتار کاربر ثابت نشده؛ (۲) قابلیت‌ها صرفاً بر اساس زمان یا Milestone در یک Release اجباری بسته می‌شوند، درحالی‌که مسیرهای واقعاً وابسته ناتمام باقی می‌مانند.

**Base** = کوچک‌ترین محصول/کتابخانهٔ قابل استفاده با «یک مسیر عمودی واقعی» (Walking Skeleton). Base عبارت نیست از تمام قابلیت‌های مصوب و همچنین فقط ساختار پوشه، Mock، صفحهٔ Login، Demo بدون حفاظ، سبزی CI، یا طراحی پذیرفته‌شده نیست. Base با T1/T2 و Runtime تناسب می‌یابد: برای سرویس، build/deploy/health/version/one real end-to-end use case و recovery؛ برای Library، بستهٔ قابل نصب، API مصرف‌کنندهٔ واقعی، compatibility و rollback/revert release؛ برای UI، یک رندر/interaction قابل‌استفاده با آزمون مرتبط. هر کجا auth/tenant/license/audit/offline/storage/trust جزو invariant همان Runtime است، Base آنها را در محدودهٔ واقعی تست می‌کند؛ هیچ subsystem ساختگی صرفاً برای چک کردن Base اضافه نشود.

## پنج وضعیت طراحی و ساخت Base (هر کدام یک Gate واقعی، نه workflow جدید)

| مرحله | خروجی | شرط خروج و مرجع |
|---|---|---|
| **B0 — Scope/Decision** | outcome اولیهٔ کوچک، نیازمندی‌های پذیرفته‌شده، عدم‌قطعیت‌ها و مسئول تصمیم | تصمیم محصول، constraints، موارد انتخاب/عدم‌نیاز صریح؛ در Issue/Spec |
| **B1 — Design Contract** | معماری، trust/data/API boundaries، reuse، حداقل supported tuple، سناریوی کاربر/اپراتور و rollback | بازبینی طراحی و ADR تنها وقتی تصمیم جدید لازم است؛ قرارداد پایدار در `docs/architecture/` |
| **B2 — Implemented Base** | سورس یک مسیر واقعی + تست مرتبط + artifact قابل ساخت | PRهای منسجم و checks موفق روی exact head؛ هنوز Accepted یا Released نیست |
| **B3 — Verified Base Candidate** | Candidate نسخه‌دار روی کانال مجاز Test/consumer، E2E متناسب، negative/security/recovery/upgrade evidence | پذیرش مستقل/انسانی لازم مطابق ریسک، همان source/artifact و سناریو؛ فقدان شاهد = HOLD |
| **B4 — Accepted Initial Base** | نخستین Base واقعاً قابل استفاده در **کانال اعلام‌شده**، با شناسهٔ immutable و trace کامل | owner sign-off و tag + GitHub Release معتبر طبق REL؛ Test RC برابر Production نیست؛ قبل از Production باید Gates آن نیز پاس شوند |

یک پروژهٔ موجود باید **اولین Gate اثبات‌نشده** را بر اساس GitHub و اجرای واقعی مشخص کند؛ B0/B1 تصویب‌شده از نو انجام نمی‌شود. اگر B2 سورس موجود ولی B3/4 پذیرش نشده، راه صحیح تکمیل شواهد Base و Gate است، نه بازنویسی Base یا اعلام «همه چیز کامل». اگر Base در محیط مجاز Test پذیرفته شد، Feature development می‌تواند برای کانال Test آغاز شود؛ هیچ ادعای Production از آن نتیجه نمی‌شود. مسیر security fix و research مستقل طبق BASE-3 باز می‌ماند.

## انتخاب اینکه چه چیزی Base است

در قرارداد معماری (قالب زیر `templates/tier/T2/docs/architecture/base-contract.md`) فقط **پایدارترین هدف و معیار پذیرش** نوشته می‌شود: outcome اولیه، مرزهای امنیتی و داده، وابستگی‌های حقیقی، موجودیِ اجزا، source owners، migration و recovery، target runtime/channel و معیارهای قابل تکرار. وضعیت روز مانند `current phase`، اجرای CI، SHA موردنظر، زمان تخمینی، blockers و decision approval در GitHub Issue/PR/Run ثبت می‌شود، نه در سند دوم.

فقط مسیر کوچک اما کامل Base را انتخاب کنید. نیازمندی مهمی که خارج از اولین Base است در Scope رسمی محصول و Issue canonical **حفظ** می‌شود؛ نه Accepted جعلی، نه DROP پنهانی. هنگام بستن نخستین Baseline، scope ابتدایی مستند شود و اگر تعهد نسخهٔ نهایی/Production باید تغییر کند، تصمیم صریح مالک در منبع محصول لازم است.

## برای هر Feature یک طرح توسعهٔ مستقل

**Feature Decision Packet** در Issue و `specs/<issue>-<slug>/{spec,plan}.md`، با استفاده از ظرفیت موجود مدیریت کار:

- **Outcome/Owner:** کاربر چه رفتار قابل مشاهده‌ای می‌گیرد؟ مسئول business writer و قراردادهای دقیق چیست؟
- **Reuse decision:** اول قابلیت موجود/Native/Provider/نسخهٔ تثبیت‌شده؛ بعد extend و فقط در صورت اثبات gap، build جدید.
- **Dependency:** hard prerequisite، atomic co-release، optional integration یا independent؛ Issue/Unit ارجاع‌شده، دلیل و اثر بلوکه‌شدن.
- **Priority/readiness:** ارزش واقعی، risk، critical security، position on dependency path و Gate قبلی؛ وزن نسبی فقط پیچیدگی تحویل است، نه مدت یا اولویت امنیت.
- **Plan:** Design/decision → one bounded slice → contract+tests → PR review → integration observation → acceptance → rollout/rollback. شرط ورود/خروج هر مرحله روشن باشد.
- **Release Unit:** شناسهٔ یکتا، Featureها و Issueها، نسخهٔ کاندید پس از Freeze، سازگاری و supported tuple، acceptance owner و evidence.
- **Non-goals:** چه چیزهایی برای این Unit وعده داده نشده‌اند؟ چه مورد مصوبی به واحد بعدی موکول شده و Issue معتبر دارد؟

### قانون تصمیم دربارهٔ وابستگی

| رابطه | تصمیم توسعه | تصمیم انتشار |
|---|---|---|
| **B یک خروجی مستقل و مورد نیاز A است** | اول B را با owner/contract خودش کامل و قبول کنید؛ طراحی A در صورت ثبات API می‌تواند موازی بماند | B می‌تواند جدا منتشر شود؛ A فقط با نسخهٔ پذیرفته‌شدهٔ B |
| **A+B فقط با هم خروجی امن/قابل استفاده می‌دهند** | چند PR کوچک در دو owner مجاز است، ولی integration/negative acceptance یک واحد است | **یک Release Unit اتمیک** روی artifact/contract سازگار و منجمد |
| **A و B واقعاً مستقل‌اند** | backlog/PR و Gate مستقل، بدون ایجاد dependency مصنوعی | جداگانه در اولین Candidate مجاز و موردنیاز |
| **وابستگی اختیاری است** | interface و fallback/flag امن تعریف کنید | فقط در صورتی مستقل که absence/B failure آن را نقض نکند |
| **A↔B چرخهٔ hard ایجاد می‌کند** | به طراحی و مرزبندی مالکیت برگردید؛ cycle را حل/یکپارچه کنید | تا حل/اثبات چرخه نه ترتیب ادعایی بسازید نه Acceptance |

ابزار اختیاری آفلاین `python3 tooling/feature_delivery.py <file.json>` فقط **ساختار DAG و واحدهای تحویل** را با یک نمونهٔ کاملاً مصنوعی اعتبارسنجی و موج‌های وابستگی را پیشنهاد می‌کند؛ نه مالک، اولویت، تاریخ، محیط، صحت معماری یا پذیرش را کشف می‌کند و نه به GitHub وصل می‌شود. خود سند JSON ورودی وضعیت زنده یا مدرک Release نیست؛ می‌تواند موقت/در Spec مورد بررسی باشد.

## Release/Version policy — بدون نسخه‌سازی برای هر PR

1. **کد/Issue/Feature version با Product release یک چیز نیست.** PR واحد منسجم engineering است؛ Release Unit رفتار و پذیرش محصول؛ نسخهٔ Product فقط یک هویت رسمی exact-tag+Release برای source/artifact دارد. نسخهٔ dependency مستقل باید در compatibility matrix یا قرارداد مؤثر ثبت شود.
2. **قبل از Freeze:** تغییرهای PR کوچک و تست تناسبی ادامه دارد؛ هر commit شمارهٔ نسخه نمی‌گیرد. فریز هر Candidate، فهرست include/exclude Unit و requirements، artifact، tests، rollback و نسخه‌های وابسته را ثابت می‌کند.
3. **Test RC:** با فرمان و Gate معتبر `vX.Y.Z-rc.1`، سپس برای تصحیح همان scope در Candidate جدید `rc.2` و بالاتر. tag صادرشده تغییر نمی‌کند، مشکل نسخهٔ قبلی پنهان نمی‌شود و ویژگی مستقل به عنوان «fix» وارد همان scope نمی‌شود.
4. **Stable >=1.0.0:** اصلاح سازگارِ امن = PATCH؛ قابلیت مستقلِ سازگار = MINOR؛ ناسازگاری قراردادی = MAJOR همراه migration/transition با تصمیم مالک. **قبل از 1.0.0** معنا/تضمین API و ارتقای minor/patch طبق SemVer و قرارداد پذیرفته‌شدهٔ خود پروژه صریح می‌شود؛ شماره را از یک جدول ثابتِ بدون شواهد حدس نزنید.
5. **Release Gate:** REL-5/6/7، ACC-3، signed/offline/version/provenance، محیط و اختیار owner پابرجا هستند. milestone فقط برنامهٔ کار است؛ ممکن است چند Unit مستقل در RCهای مختلف قرار گیرند. چند اصلاح در یک Unit می‌تواند چند PR داشته باشد و فقط یک RC پس از Freeze بسازد.
6. **Production:** Base پذیرفته‌شده در Test مجوز GF/Production نیست؛ انتشار Production همچنان اثبات واقعی privacy/security/HA/DR/support/installation لازم را در scope مصوب می‌خواهد. شرط‌های خاموش مانع ادعای release هستند، نه دلیلی برای حذف Featureهای مصوب.

## قواعد جلوگیری از بدهی و گزارشِ ادعایی

- در پایان هر واحد، خط قابل ردیابی: `Feature Issue → Spec/contract → PR+SHA → actual CI / negative tests → independent acceptance → tag/Release → deployed identity (if relevant)`. **Blank evidence = HOLD** و Critical boundary failure = STOP.
- وابستگی بلاک‌شده فقط downstream خودش را متوقف می‌کند. اولویت مستقل R3/R4/امنیت و عملیات با ضرورت واقعی تعریف می‌شود.
- حالت‌های `Designed / Implemented / Tested / Environment-verified / Accepted / Merged / Released / Deployed` به هم تبدیل خودکار نمی‌شوند.
- برای کارهای هنوز آماده نشده دستهٔ Backlog کافی است؛ انبوهی از Issue/PRهای speculative ساخته نشود. وضعیت و اولویت همیشه از GitHub خوانده شود، نه گزارشی در این فایل.
- Ruleهای BASE/TRN در این مرحله **R-only human review** هستند. تست محلی فقط consistency قالب و صحت ساختار یک نمونه را ثابت می‌کند؛ نه تکمیل واقعی Base یا Feature در یک محصول را. اگر روزی Gate ماشینی معتبری ساخته شد، Rule و پوشش مثبت/منفی با PR/نسخهٔ بعدی تغییر می‌کنند.

## نمونهٔ مصنوعی از تصمیم Release Unit

```json
{
  "schemaVersion": 1,
  "units": [
    {"id": "U-FOUND", "featureIds": ["F-001"], "mode": "independent", "weight": 3, "acceptance": "A verified public API works", "dependsOn": []},
    {"id": "U-WORK", "featureIds": ["F-002", "F-003"], "mode": "atomic", "weight": 8, "acceptance": "An authorized full journey passes", "dependsOn": [{"unit": "U-FOUND", "reason": "Consumes the accepted API contract"}]},
    {"id": "U-HELP", "featureIds": ["F-004"], "mode": "independent", "weight": 2, "acceptance": "Documentation renders offline", "dependsOn": []}
  ]
}
```

الگوریتم موج می‌تواند U-FOUND و U-HELP را مستقل نشان دهد و U-WORK را بعد از U-FOUND. هیچ عدد W، وضعیت نرم‌افزاری یا قبول Gate از این داده‌ها استنتاج نمی‌شود.

## مهاجرت و دامنهٔ اثر استاندارد

نسخهٔ جدید KavoshStart پس از review/release رسمی و ارتقای **اختیاری/مجاز consumer exact pin** اثر می‌کند. پروژهٔ موجود از اولین B Gate اثبات‌نشده ادامه می‌دهد و وضعیتِ گذشته یا انتشار موجودش با این سند ابطال نمی‌شود. اگر تبدیل این راهنما به Gate اجباری و خودکار برای همهٔ مصرف‌کننده‌های موجود مدنظر شد، هزینهٔ migration و SemVer major جداگانه بررسی شود؛ این سند Workflow یا CI جدید ایجاد نمی‌کند.
