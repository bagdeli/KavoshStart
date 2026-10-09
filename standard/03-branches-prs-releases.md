# 03 — شاخه، PR و انتشار

قواعد: BR-1…8، PR-1…9، REL-1…7

## مدل: Trunk-Based با شاخه‌های کوتاه‌عمر
```text
main   ●────●────●────●────●────●──── v0.3.0-rc.1 ── v0.3.0
        \  /      \  /  \  /
         ●         ●     ●        ← feat/12-login ، fix/15-sms-retry … (≤ 3 روز)
```
- **`main` همیشه حقیقت و همیشه قابل‌انتشار است.** کار ناتمامی که باید ادغام شود پشت feature flag می‌رود، نه در شاخه‌ی بلندعمر.
- وقتی کار روی شاخه‌های integration بلندعمر جمع شود، `main` می‌تواند صدها commit عقب بماند؛ این دقیقاً نقض BR-1 و BR-8 است. در این مدل، شاخه‌ی integration وجود ندارد؛ integration همان `main` است.

## چرخه‌ی یک PR
1. Issue در وضعیت Ready ← `git switch -c feat/<n>-<slug> origin/main`
2. Draft PR زود. stack عمیق در Draft مجاز است؛ پیش از Ready به main یا یک والد بلافاصله قابل‌ادغام normalize می‌شود.
3. **Change Risk** و capabilityهای متاثر را مستقل از Tier اعلام کنید. line/file/commit count فقط telemetry است و risk classifier یا hard gate نیست.
4. یک packet منسجم پیاده کنید و semantic `check` contract پروژه را اجرا کنید؛ Make فقط adapter پیش‌فرض scaffold است.
5. Ready for review ← `kavosh` و `required` سبز، exact head معلوم، blocker و thread حل‌نشده وجود ندارد.
6. `low/medium`: عامل می‌تواند پس از preflight کامل همان exact head را Squash merge کند. `high/critical` و control-plane/security/destructive/release-policy ابتدا تصمیم صریح انسانی برای scope فعلی می‌خواهند؛ سپس خود merge مکانیکی قابل واگذاری است.
7. «ادامه بده» فقط اجازهٔ گام بعدی است و Acceptance/Merge/Release یا waiver قبلی نیست. outcome ناقص باید Issue/acceptance item canonical داشته باشد.

## اندازه و split
Batch کوچک برای feedback سریع مطلوب است، اما **هیچ سقف عمومی بر اساس تعداد خط یا فایل وجود ندارد**. split فقط وقتی مطلوب است که هر بخش مستقل، قابل‌تست، قابل‌مرور و امن برای merge بماند. generated refactor یا تغییر منسجم بزرگ باید generator/روش بازبینی/verification خود را مستند کند؛ کوچک بودن diff نیز تغییر پرریسک را کم‌ریسک نمی‌کند.

## انتشار
Core نتیجه را govern می‌کند، نه ابزار را:

- هر strategy باید SemVer، tag immutable `vX.Y.Z[-rc.N]`، exact-source identity، changelog/release notes، provenance لازم و release gate معادل REL-5/6 را حفظ کند.
- `release.strategy=release-please` مسیر پیش‌فرض scaffold است و `release.workflow` پیش‌فرض `.github/workflows/release.yml`، که `kavosh-release.yml` را صدا می‌زند. اگر این مسیر asset منتشر می‌کند، `automation.interface=make` می‌تواند از adapter سازگار `make setup && make package` + `dist/*` استفاده کند؛ هر interface دیگر باید `release.artifact.command` و relative globهای `release.artifact.paths` را صریح اعلام کند. KavoshStart package manager یا task runner خاصی را invariant نمی‌کند.
- `changesets` یا `custom` باید workflow واقعی و `strategyADR` را در manifest اعلام کند؛ governance وجود adapter و قرارداد معادل را بررسی می‌کند. ابزار downstream حق ندارد با نام متفاوت gate ضعیف‌تری بسازد.
- `ci.requiredWorkflow` فایل workflow دارای job تجمیعی ثابت `required` را اعلام می‌کند؛ نام فایل invariant نیست.
- اگر checks همان exact candidate قرمز/غایب باشند هیچ نسخه‌ای ساخته نمی‌شود. tag دستی جای release gate نیست.
- تصمیم انسانی Release از اجرای مکانیکی CI/merge جداست. GitHub برای PR ساخته‌شده/به‌روزشده با `GITHUB_TOKEN` ممکن است runهای `pull_request` را approval-required کند و event قابل‌اتکای `pull_request_target` نیز برای همان bot update تضمین نمی‌شود. مسیر استاندارد به event bot وابسته نیست: workflow معتبر Release روی `main` فقط یک PR همان repo با actor دقیق `github-actions[bot]` و branch استاندارد `release-please--...` را می‌پذیرد، workflow واقعی `required` و `kavosh mode=pr-check` را روی exact head آن dispatch و تا نتیجه نهایی صبر می‌کند، سپس همان نتیجه را با Checks API و contextهای `required` و `kavosh / governance` روی همان SHA منتشر می‌کند. ruleset همچنان تصمیم نهایی merge است؛ owner click، no-op commit، PAT یا bypass جزو مسیر استاندارد نیستند.
- tag `v1` قدیمی منجمد است و هرگز جابه‌جا نمی‌شود؛ پروژه‌ها فقط `@vX.Y.Z` دقیق (REL-6).
- نام tag برای انتشارهای جدید فقط `vX.Y.Z` یا `vX.Y.Z-rc.N` است. انتشار تاریخیِ immutable با نام `KavoshStart-v1.1.0` حفظ می‌شود: health فقط همین tag موجود را grandfather می‌کند، اما هیچ tag نام‌دار تازه‌ای مجاز نیست. هر tag تاریخی را حذف یا جابه‌جا نکنید.
- پیش‌انتشار برای Test از workflow `rc` و فقط با dispatch مستقیم مالک ساخته می‌شود: مالک `vX.Y.Z-rc.N` و **SHA کامل current main** را وارد و همان creation را تأیید می‌کند. REL-7 دوباره required checks را روی همان SHA می‌سنجد، tag/release/final collision و RC عقب‌تر را رد می‌کند و سپس GitHub prerelease immutable می‌سازد. ساخت tag دستی، RC branch یا deploy مستقیم main جایگزین این مسیر نیست.
- پس از RC: سرور Test طبق DEP-2 آن release را می‌کشد، DEP-7/8 environment را با exact tag+SHA می‌پذیرد، UAT/acceptance انجام می‌شود؛ نسخه‌ی نهایی همچنان فقط از Release PR/release-please و REL-5 می‌آید و مالک همان final را روی Production پین می‌کند.
- hotfix نسخه‌ی قدیمی: شاخه‌ی `release/X.Y` **از روی tag** و فقط برای همان hotfix؛ بعد حذف.

## Conventional Commits
`feat(scope): …` `fix(scope): …` `docs:` `refactor:` `perf:` `test:` `ci:` `build:` `chore:` `revert:` — ناسازگار: `feat!:` یا `BREAKING CHANGE:`.
