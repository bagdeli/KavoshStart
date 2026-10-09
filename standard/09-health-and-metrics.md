# 09 — سلامت و سنجه‌ها

`kavosh-health` هر شنبه یک Issue ثابت با برچسب `kavosh:health` در هر ریپو را به‌روز می‌کند. **هر ❌ = یک Task در Backlog.**

| سنجه | هدف | قاعده |
|---|---|---|
| شاخه‌های غیر از main | ≤ 10 | BR-1 |
| شاخه‌های بی‌فعالیت > 7 روز | 0 | BR-3 |
| شاخه‌های > 50 commit جلوتر از main | 0 | BR-8 |
| PRهای باز غیر-Draft | ≤ حد مانیفست | PR-8 |
| Draft بی‌فعالیت > 7 روز | 0 | PR-9 |
| PRهای باز که به main نمی‌روند | ≤ 1 | BR-4 |
| Issueهای باز بدون **دقیقاً یک** `type:*` (به‌جز Issueهای خودکار `kavosh:*`) | 0 | WK-1 |
| Issue با > 30 کامنت | 0 | WK-2 |
| نرخ cancel CI (7 روز) | < 10٪ | CI-4, CI-6 |
| موفقیت CI روی main (7 روز) | > 90٪ | — |
| push مستقیم به main (7 روز) | 0 | BR-6 |
| Issueهای باز `kavosh:violation` | 0 | PR-7 |
| commitهای main با `Co-Authored-By` (30 روز) | اطلاعاتی | AI-3 |
| مصرف دقیقه‌ی ماه جاری / بودجه | ≤ 100٪ (هشدار از 80٪) | CI-3 |
| آخرین Release | وجود دارد؛ T1/T2: ≤ 30 روز | REL-1 |
| pin KavoshStart در برابر آخرین Release پایدار | current؛ عقب‌ماندگی = warning + review/upgrade | STD-1 |
| T2 با continuous acceptance | 100٪ | ACC-1, ACC-2 |
| tagهای غیر `v*` (به‌جز tag تاریخی immutable با allowlist صریح) | 0 | REL-3 |

## سطح پرتفوی
`python3 scripts/portfolio.py bagdeli --minutes` (محلی، با `gh`): همه‌ی ریپوهای دارای `kavosh.project.json`، tier، بودجه، مصرف تخمینی ماه، آخرین release، تعداد تخلف باز — و جمع بودجه‌ها در برابر 1,600.

## DORA (برای T1/T2، ماهانه)
فراوانی استقرار (release/هفته) · lead time (اولین commit شاخه تا ادغام) · نرخ شکست تغییر (release نیازمند hotfix) · زمان بازیابی. هدف نه عدد مطلق، بلکه روند.

## Freshness و بدهی پذیرش

Health هیچ dependency را خودکار ارتقا نمی‌دهد. STD-1 فقط اختلاف pin با آخرین release پایدار را visible می‌کند؛ تصمیم upgrade در PR مستقل و با CHANGELOG گرفته می‌شود. برای T2، نبودن continuous acceptance یک مشکل پیکربندی است، نه انتخاب دائمی.

هشدارهای ACC-2 برای closure کمتر از 80٪ یا acceptance debt قدیمی‌تر از 14 روز قرار نیست تست‌های سنگین را به هر PR تحمیل کنند؛ هدف این است که evidence debt دیده و در طول delivery مصرف شود، نه اینکه به release نهایی منتقل شود.
