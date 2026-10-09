# 02 — منبع حقیقت و مدیریت کار

قواعد: SRC-1…6، WK-1…6

## چه چیزی کجا زندگی می‌کند
| اطلاعات | تنها محل | ممنوع در |
|---|---|---|
| کارهای باز، اولویت، مسئول | Issue + GitHub Project «Kavosh Delivery» | فایل‌های STATUS/HANDOFF/tasks |
| جزئیات و معیار پذیرش یک کار | **بدنه‌ی** Issue | کامنت‌های پراکنده، فایل |
| تغییر پیشنهادی و شواهد | PR + Checks | Issue |
| نسخه‌ی منتشرشده | tag + Release + `CHANGELOG.md` | Issue «closure record» |
| چرایی تصمیم | ADR (`docs/decisions/`) | کامنت Issue |
| «چه باید ساخته شود» برای یک Feature | `specs/<n>-<slug>/spec.md` | یک سند مرکزی چندصد KB |
| مشخصات ثابت پروژه | `kavosh.project.json` + `PROJECT.md` | README پراکنده |
| دستورالعمل عامل | `AGENTS.md` | Issue «handoff» |
| انتقال کار بین جلسات عامل | بدنه‌ی PR (Done / Remaining / Decisions) | Issue با 100 کامنت |

## سلسله‌مراتب کار
```text
Milestone  vX.Y.Z                 (T1, T2)
└─ type:epic      1–6 هفته         (T2)
   └─ type:feature  2–10 روز + spec (T1, T2)
      └─ type:task   معمولاً ≤ 1 روز؛ مرز PR بر اساس coherence، risk، testability و reviewability
type:bug · type:decision (→ ADR) · type:chore
```
- رابطه‌ی والد/فرزند با **sub-issue بومی** GitHub، نه متن «parent #192».
- Issue Types در حساب شخصی وجود ندارد؛ برچسب `type:*` جایگزین است و فرم‌های Issue آن را خودکار می‌گذارند.

## GitHub Project «Kavosh Delivery» (یکی برای همه‌ی ریپوها)
فیلدها: `Status` (Backlog, Ready, In Progress, In Review, Blocked, Done) · `Priority` (P0–P3) · `Size` (XS, S, M, L) · `Iteration` (دوهفته‌ای) · `Agent` (human, claude, codex, copilot, gemini) · `Repo`.
نماها: Board، Current iteration، By repo، Blocked، Roadmap by milestone.
خودکارسازی‌های بومی: Item closed → Done · PR merged → Done · auto-archive بعد از 14 روز.

**WIP:** حداکثر 3 آیتم In Progress در کل پرتفوی — ظرفیت بازبینی شما گلوگاه است، نه سرعت عامل.

## چرا
در یک پروژه‌ی بزرگ، «مرجع فعلی» چند بار عوض شده و در فایل‌های متعدد کپی شده بود؛ عاملی که از `main` شروع می‌کرد ممکن بود به Issue بسته هدایت شود. وضعیت در GitHub همیشه زنده است و با `gh` قابل خواندن.
## Immutable provenance versus live state

Source-of-truth rules distinguish evidence that must remain frozen from operational state that must stay live:

- exact source commit identifiers are valid in immutable release notes, audits and ADRs because they prove what was reviewed or released;
- ordinary explanatory Markdown must not freeze current repository state with a commit SHA;
- `AGENTS.md` must not depend on a specific current Issue/PR or status date;
- a standards citation such as `UTS #39`, RFC/section numbering or other non-GitHub citation is not a live Issue/PR reference;
- if an agent/contributor rule truly depends on a GitHub work item, put that state in GitHub and keep AGENTS generic.


