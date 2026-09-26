# 03 — شاخه، PR و انتشار

قواعد: BR-1…8، PR-1…9، REL-1…4

## مدل: Trunk-Based با شاخه‌های کوتاه‌عمر
```text
main   ●────●────●────●────●────●──── v0.3.0-rc.1 ── v0.3.0
        \  /      \  /  \  /
         ●         ●     ●        ← feat/12-login ، fix/15-sms-retry … (≤ 3 روز)
```
- **`main` همیشه حقیقت و همیشه قابل‌انتشار است.** کار ناتمامی که باید ادغام شود پشت feature flag می‌رود، نه در شاخه‌ی بلندعمر.
- مشکل KavoshERP («main خیلی عقب‌تر از branchها») دقیقاً نقض BR-1 و BR-8 بود: کار روی `vnext/integration-*` جمع شد و `main` 537 commit عقب ماند. در این مدل، شاخه‌ی integration وجود ندارد؛ integration همان `main` است.

## چرخه‌ی یک PR
1. Issue در وضعیت Ready ← `git switch -c feat/<n>-<slug> origin/main`
2. Draft PR زود (برنامه در بدنه) — CI روی Draft اجرا نمی‌شود (CI-6)، فقط governance سبک.
3. کد + تست + `make check` محلی ← یک push.
4. Ready for review ← `kavosh` و `required` سبز.
5. مالک بازبینی و **Squash merge** ← شاخه خودکار حذف ← Issue بسته.

## اندازه
| | هدف | هشدار | قرمز |
|---|---|---|---|
| خطوط تغییر (بدون lockfile/generated) | ≤ 200 | > `prMaxLines` (400) | > 2.5 × `prMaxLines` (1000) |
| فایل‌ها | ≤ 20 | > 20 | > 50 |
| عمق stack | 1 | 2 | ≥ 3 |

## انتشار
```text
push به main → ci (required) + kavosh (main-guard) → ci موفق → release (workflow_run)
   → REL-5: checkهای الزامی همان commit موجود و موفق؟ و هنوز head main است؟
   → release-please: Release PR را به‌روز می‌کند / پس از ادغام آن: tag + Release (+ فایل‌های انتشار در همان اجرا)
```
- release-please یک «Release PR» باز نگه می‌دارد؛ ادغامش = نسخه + `CHANGELOG.md` + tag + Release.
- **Approve and run:** Release PR را `GITHUB_TOKEN` می‌سازد؛ طبق قاعده‌ی GitHub، CI آن PR تا تأیید مالک اجرا نمی‌شود. در تب Checks روی «Approve and run» بزنید، سبز شدن را ببینید، بعد ادغام کنید.
- اگر CI قرمز است یا اجرا نشده (مثلاً قفل Billing)، هیچ نسخه‌ای ساخته نمی‌شود (REL-5). دور زدن این دروازه با tag دستی تخلف است.
- tag `v1` قدیمی منجمد است و هرگز جابه‌جا نمی‌شود؛ پروژه‌ها فقط `@vX.Y.Z` دقیق (REL-6).
- پیش‌انتشار: `vX.Y.Z-rc.N` ← سرور test خودکار آن را می‌کشد ← UAT ← نسخه‌ی نهایی ← مالک روی production پین می‌کند.
- hotfix نسخه‌ی قدیمی: شاخه‌ی `release/X.Y` **از روی tag** و فقط برای همان hotfix؛ بعد حذف.

## Conventional Commits
`feat(scope): …` `fix(scope): …` `docs:` `refactor:` `perf:` `test:` `ci:` `build:` `chore:` `revert:` — ناسازگار: `feat!:` یا `BREAKING CHANGE:`.
