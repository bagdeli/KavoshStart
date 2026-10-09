# 11 — Change Risk, Evidence, Continuation and Merge

این سند توضیح قواعد CR، FLOW و PR-6 است. منبع رسمی Ruleها همچنان `standard/RULES.md` است.

## 1. دو محور مستقل

KavoshStart دو چیز را جدا می‌کند:

- **Project Tier**: میزان assurance و فرایند پایهٔ کل پروژه.
- **Change Risk**: خطر خود تغییر فعلی.

یک T1 می‌تواند PR کم‌ریسک documentation و در همان روز migration پرریسک داشته باشد. Line count و file count فقط telemetry هستند و risk classifier نیستند.

## 2. Risk levels

| Risk | نمونه | انتظار |
|---|---|---|
| low | typo، docs، refactor مکانیکی کاملاً محصور | verification متناسب و reviewability |
| medium | رفتار bounded، API/UI غیرحساس، dependency عادی | test/evidence متناسب با capability |
| high | governance/control-plane، auth/permission، migration، deploy/release policy، trust boundary | تصمیم انسانی صریح برای scope فعلی + evidence قوی |
| critical | destructive production/data، regulated/financial safety boundary، تغییر غیرقابل‌برگشت یا blast radius بسیار بالا | تصمیم انسانی صریح، runbook/rollback و gateهای خاص domain |

Machine checks می‌توانند برای path/capabilityهای شناخته‌شده حداقل risk تعیین کنند؛ semantic risk بالاتر همچنان مسئولیت عامل و reviewer است.

## 3. Coherent change به‌جای size gate

Batch کوچک برای feedback سریع مطلوب است، اما split فقط وقتی خوب است که هر بخش independently useful/testable/mergeable بماند. این‌ها مثال‌های معتبر برای یک PR بزرگ‌اند:

- generated rename با generator و verification مشخص؛
- formatting/API regeneration؛
- migration ساختاری که split آن atomicity را خراب می‌کند؛
- UI change منسجم که شکستن آن integration risk را بیشتر می‌کند.

یک PR کوچک می‌تواند critical باشد؛ یک PR چند هزار خطی می‌تواند low/medium باشد. هیچ hard limit جهانی بر اساس تعداد خط یا فایل وجود ندارد.

## 4. Continue ≠ Accept ≠ Merge ≠ Release

این چهار عمل مستقل‌اند:

1. **Continue**: اجازهٔ انجام گام بعدی.
2. **Accept**: تأیید outcome/evidence مشخص.
3. **Merge**: عملیات مکانیکی واردکردن exact head به main.
4. **Release/Production**: boundary جدا با gate و authorization خودش.

«ادامه بده» هیچ‌کدام از 2 تا 4 را به‌طور ضمنی اعطا نمی‌کند. اگر بخشی ناقص است، قبل از ادامه باید Issue/acceptance item canonical داشته باشد و بعداً نمی‌توان آن را complete گزارش کرد تا واقعاً بسته شود.

## 5. Delegated merge

برای risk=low/medium، agent می‌تواند بعد از این preflight merge را انجام دهد:

- exact current head تغییر نکرده؛
- base/mergeability سالم است؛
- required checks حاضر و green هستند؛
- blocker و unresolved review thread وجود ندارد؛
- acceptance mapping/evidence لازم کامل است؛
- merge فقط ordinary Squash است، بدون `--admin` یا bypass.

برای high/critical و control-plane/security/destructive/release-policy change، قبل از merge یک تصمیم انسانی صریح برای scope فعلی لازم است. بعد از آن خود کلیک/فرمان merge کار مکانیکی است و agent می‌تواند انجام دهد.

## 6. مرز اثبات انسانی

اگر agent با همان GitHub identity یا credential مالک کار می‌کند، comment/label/review ایجادشده توسط همان identity به‌تنهایی اثبات نمی‌کند که انسان تصمیم گرفته است. KavoshStart در این وضعیت ادعای machine-proof human approval نمی‌کند؛ authorization انسانی یک trust boundary واقعی و لایهٔ R/A است.

## 7. Evidence = risk × capability

Evidence باید از ماهیت تغییر بیاید، نه از یک checklist ثابت. نمونهٔ capabilityها:

- public-api / package-install / compatibility
- ui / accessibility / visual
- data / migration / backup / restore
- security / auth / permission
- deploy / runtime identity / rollback
- release / provenance / artifact integrity
- infrastructure / plan / drift / recovery

هر defect جدید باید یا invariant جدید را به contract+regression تبدیل کند یا detector قدیمی را با negative test تعمیر کند.

## 8. Tool adapters

Core outcome را govern می‌کند، نه tool را:

- command contract: setup/lint/test/build/check؛ default scaffold می‌تواند Make باشد.
- release contract: SemVer + exact-source + changelog/release notes + gated immutable output؛ release-please، Changesets یا strategy معادل ممکن‌اند.
- account/billing policy: overlay جدا؛ budget به‌تنهایی quality gate یا authorization نیست.

