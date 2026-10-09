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
2. Draft PR زود (برنامه در بدنه). stack عمیق مجاز است و health هشدار می‌دهد؛ پیش از Ready به main یا یک والد بلافاصله قابل‌ادغام normalize می‌شود. CI سنگین روی Draft خاموش است؛ dispatch زودهنگام مجوز quota نیست.
3. کد + تست + `make check` محلی ← یک push.
4. Ready for review ← `kavosh` و `required` سبز، شاخه shallow، threadها resolved.
5. مالک برای PR و head فعلی مجوز merge می‌دهد؛ عامل بلافاصله پیش از merge، base، mergeability، checkهای سبز و threadهای حل‌نشده را دوباره بررسی می‌کند و **Squash merge** عادی را با تطبیق همان SHA انجام می‌دهد: `gh pr merge <number> --squash --match-head-commit <sha>`. `--admin` و bypass مطلقاً ممنوع‌اند.

## اندازه
| | هدف | هشدار | قرمز |
|---|---|---|---|
| خطوط تغییر (بدون lockfile/generated) | ≤ 200 | > `prMaxLines` (400) | > 2.5 × `prMaxLines` (1000) |
| فایل‌ها | ≤ 20 | > 20 | > 50 |
| عمق stack در Draft | آزاد | هشدار می‌گیرد | normalize پیش از Ready |
| عمق stack در Ready/Merge | 1 | یک والد بلافاصله قابل ادغام | ≥ 3 یا والد غیرقابل ادغام = قرمز |

برچسب `size:exception` فقط درخواست استثناست. عبور از سقف سخت نیازمند دلیل روشن و تأیید مالک روی همان head فعلی است.

## انتشار
```text
push به main → ci (required) + kavosh (main-guard) → ci موفق → release (workflow_run)
   → REL-5: checkهای الزامی همان commit موجود و موفق؟ و هنوز head main است؟
   → release-please: Release PR را به‌روز می‌کند / پس از ادغام آن: tag + Release (+ فایل‌های انتشار در همان اجرا)
```
- release-please یک «Release PR» باز نگه می‌دارد؛ ادغامش = نسخه + `CHANGELOG.md` + tag + Release.
- **Approve and run:** Release PR را `GITHUB_TOKEN` می‌سازد؛ اگر workflow action-required شد، فقط پس از مشاهدهٔ commit و هزینهٔ احتمالی اجرای مشخص را مجاز کنید، سپس سبز شدن را ببینید.
- اگر CI قرمز است یا اجرا نشده (مثلاً قفل Billing)، هیچ نسخه‌ای ساخته نمی‌شود (REL-5). دور زدن این دروازه با tag دستی تخلف است.
- tag `v1` قدیمی منجمد است و هرگز جابه‌جا نمی‌شود؛ پروژه‌ها فقط `@vX.Y.Z` دقیق (REL-6).
- نام tag برای انتشارهای جدید فقط `vX.Y.Z` یا `vX.Y.Z-rc.N` است. انتشار تاریخیِ immutable با نام `KavoshStart-v1.1.0` حفظ می‌شود: health فقط همین tag موجود را grandfather می‌کند، اما هیچ tag نام‌دار تازه‌ای مجاز نیست. هر tag تاریخی را حذف یا جابه‌جا نکنید.
- پیش‌انتشار: `vX.Y.Z-rc.N` ← سرور test خودکار آن را می‌کشد ← UAT ← نسخه‌ی نهایی ← مالک روی production پین می‌کند.
- hotfix نسخه‌ی قدیمی: شاخه‌ی `release/X.Y` **از روی tag** و فقط برای همان hotfix؛ بعد حذف.

## Conventional Commits
`feat(scope): …` `fix(scope): …` `docs:` `refactor:` `perf:` `test:` `ci:` `build:` `chore:` `revert:` — ناسازگار: `feat!:` یا `BREAKING CHANGE:`.
