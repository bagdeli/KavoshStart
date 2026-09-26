# ممیزی مدیریت پروژه‌ی KavoshERP

- **ریپو:** `bagdeli/KavoshERP` (private، ساخته‌شده 2026-08-03)
- **تاریخ ممیزی:** 2026-09-26
- **دامنه:** شیوه‌ی مدیریت پروژه، GitHub، CI و همکاری با عامل‌های AI — نه کیفیت کد دامنه‌ی ERP.
- **روش:** خواندن مستقیم از GitHub API و تاریخچه‌ی git (قابل تکرار با [`scripts/audit-repo.sh`](../scripts/audit-repo.sh)).

## خلاصه‌ی مدیریتی

در 54 روز، **3,143 commit**، **233 PR/Issue**، **135 شاخه** و **~25,600 خط Markdown** تولید شده است (به‌علاوه‌ی دو سند 313KB و 169KB). همه‌چیز «در GitHub ثبت» شده، ولی **ثبت‌کردن با کنترل‌کردن یکی نیست**. پنج ریشه‌ی اصلی:

1. **منبع حقیقت چندپاره و متحرک** — مرجع «وضعیت فعلی» پنج بار عوض شده (#51 → #61 → #76 → #234/#235/#236 → PR #231) و در ده‌ها فایل Markdown کپی شده است؛ هر بار بخشی کهنه ماند.
2. **`main` حقیقت محصول نیست** — `main` از شاخه‌ی integration **537 commit عقب** و 11 commit جلوتر است؛ در کل عمر پروژه فقط **دو PR** در `main` ادغام شده.
3. **قواعد فقط به‌صورت نثر** — ریپو private روی پلن Free است؛ API برای rulesets و branch protection پاسخ **403** می‌دهد. هیچ قانونی («merge نکن»، «force-push نکن»، «required checks») توسط پلتفرم اجرا نمی‌شود.
4. **حجم تغییر بیش از ظرفیت بازبینی** — تا **285 commit در یک روز** و PRهای تا **+124,141 خط / 678 فایل** توسط یک انسان. بازبینی واقعی عملاً ممکن نیست؛ عامل AI کار خودش را تأیید می‌کند.
5. **CI ناسالم** — از 500 اجرای اخیر: **54٪ cancelled**، **14٪ success**؛ همه‌ی 24 job روی **یک runner خودمیزبان** صف می‌شوند.

این الگو دقیقاً همان چیزی است که گزارش DORA 2025 هشدار می‌دهد: AI «تقویت‌کننده» است و بدون کار در دسته‌های کوچک و پلتفرم کنترلی، ناپایداری و دوباره‌کاری را افزایش می‌دهد.

---

## یافته‌ها با شواهد

شدت: 🔴 بحرانی · 🟠 بالا · 🟡 متوسط

### الف) منبع حقیقت و مستندات

| # | شدت | یافته | شاهد |
|---|---|---|---|
| A1 | 🔴 | **AGENTS.md روی شاخه‌ی پیش‌فرض کهنه است.** هر عاملی که از `main` شروع کند دستور می‌گیرد «اول Issue #51 را بخوان» — در حالی که #51 بسته شده و مرجع فعلی #235/#236 است. نسخه‌ی اصلاح‌شده فقط روی شاخه‌ی PR #231 وجود دارد. | `main:AGENTS.md` خط «Read Issue #51 — CURRENT HANDOFF first» |
| A2 | 🔴 | **وضعیت زنده داخل فایل‌ها.** 49 SHA کامل 40 کاراکتری در فایل‌های `.md` شاخه‌ی فعال؛ 16 فایل هنوز به #51/#76 ارجاع می‌دهند. هر commit جدید این اسناد را کهنه می‌کند. | `git grep -E '[0-9a-f]{40}' -- '*.md'` |
| A3 | 🟠 | **شش ردیاب موازی وضعیت:** `PROJECT_STATE.md`، `IMPLEMENTATION_PLAN.md`، `docs/STATUS.md`، `docs/HANDOFF.md`، `docs/ROADMAP.md`، `tasks/active/*` + Issueهای master. | ساختار ریپو |
| A4 | 🟠 | **تضاد دامنه‌ی محصول:** README می‌گوید «تنها محصول فعال، پورتال جست‌وجوی ستاد است»؛ AGENTS.md می‌گوید «ERP یکپارچه، Release 1.0 بسته شد». | `README.md` در برابر `AGENTS.md` |
| A5 | 🟠 | **اسناد غول‌آسا به‌عنوان prompt:** `project_management_module_master_prompt_unified_crm.md` (6,841 خط، 169KB) در ریشه و `KAVOSHERP_PRODUCT_COMPLETION_CONTRACT.md` (313KB) در یک PR تک‌فایلی (+7,305). از پنجره‌ی context هر عاملی بزرگ‌تر است؛ عامل‌ها بخش‌هایی را می‌خوانند و بقیه را حدس می‌زنند. | `git ls-tree -l` |
| A6 | 🟡 | **واژگان اختراعی زیاد** (LCCG، KCDS، KIPR، Stage A–E، exact-head، Golden UAT، 100/100) که برای هر جلسه‌ی جدید عامل باید دوباره توضیح داده شود و خود-گواهی‌دهی را ممکن می‌کند (Release 1.0 «100/100» اعلام شد، ولی بعداً LCCG «FAIL» است). | #54، #235 |

### ب) Issue و برنامه‌ریزی

| # | شدت | یافته | شاهد |
|---|---|---|---|
| B1 | 🟠 | **صفر برچسب روی همه‌ی Issueها، صفر milestone.** Issue Type، sub-issue رسمی و Project استفاده نشده؛ سلسله‌مراتب با متن («parent #192») نوشته شده. | `gh issue list --json labels`، `milestones` = 0 |
| B2 | 🟠 | **Issue به‌عنوان لاگ گفتگو:** #51 = 100 کامنت، #44 = 85، #54 = 84، #48 = 81، #154 = 73. اطلاعات حیاتی در کامنت 60ام دفن می‌شود. | `comments` count |
| B3 | 🟡 | **Issue/PR تصادفی:** #52 «Accidental diagnostic no-op»، #97، #99، #100. | عنوان‌ها |
| B4 | 🟡 | **Issueهای «Superseded/Closure record»** به جای ابزار بومی (Release، Milestone، close-as-not-planned). | #37، #74، #75، #234 |

### پ) شاخه‌ها و PRها

| # | شدت | یافته | شاهد |
|---|---|---|---|
| C1 | 🔴 | **`main` واگرا:** 537 commit عقب از `vnext/integration-20260918`، 11 جلو. فقط #25 و #95 در `main` ادغام شده‌اند. | `git rev-list --left-right --count` |
| C2 | 🔴 | **135 شاخه‌ی remote، 80 تا در هیچ خط فعالی نیستند**، با 20 پیشوند مختلف (`vnext` 57، `prep` 23، `ops`، `diag`، `scratch`، `promote`، `codex`، …). | `git branch -r` |
| C3 | 🟠 | **زنجیره‌ی PR پشته‌ای:** PRهای #3 تا #35 هر یک روی قبلی — همه بسته و ادغام‌نشده؛ کار واقعی بعداً در PRهای غول‌آسا دوباره جمع شد. | `baseRefName` |
| C4 | 🟠 | **PRهای غیرقابل‌بازبینی:** #25 (+124,141/678 فایل)، #1 (+91,788)، #223 (+61,520)، #95 (+59,553)، #42 (+46,323)، #219 (+21,437 فقط سند). | `additions` |
| C5 | 🟠 | **PR به‌عنوان آرشیو/شواهد:** #42 «FROZEN EVIDENCE — do not merge»؛ وضعیت Draft برای معنای «منجمد» استفاده شده. | عنوان #42 |
| C6 | 🟡 | **Dependabot بی‌اثر:** تنها PR وابستگی (#105) بدون ادغام بسته شد. | #105 |
| C7 | 🔴 | **Push مستقیم به `main` بدون PR:** سه commit در 2026-09-23 (`c9b76c1`، `a9df0c9`، `b69cc2c` — اصلاح runbook بازیابی رمز TEST). در حالی که AGENTS.md می‌گوید «main را دستکاری نکن»، پلتفرم مانعی ندارد. | `reusable-hygiene-report` → commits/{sha}/pulls |
| C8 | 🟠 | **45٪ PRها (52 از 117) بیش از 1,000 خط** تغییر دارند. | `audit-repo.sh` |
| C9 | 🔴 | **PR فعال #231 در شش قانون از هفت قانون KavoshStart رد می‌شود:** عنوان غیر Conventional، شاخه‌ی `agent/…`، بدون `Closes #`، 16,315 خط / 148 فایل، هدف `vnext/integration` به جای `main`، بدون بخش AI involvement. | اجرای آزمایشی `reusable-pr-governance` |

### ت) نسخه‌بندی و انتشار

| # | شدت | یافته | شاهد |
|---|---|---|---|
| D1 | 🟠 | **انتشار v1.1.0 اعلام شده ولی Tag/Release ندارد**؛ فقط `v1.0.0` در GitHub Releases است. | `gh release list` |
| D2 | 🟡 | **Tag بی‌معنا به نام `develop`.** | `git tag` |
| D3 | 🟡 | **Conventional Commits نیمه‌کاره:** 2,622 از 3,143 (83٪). بدون آن، changelog و نسخه‌ی خودکار ممکن نیست. | `git log --format=%s` |

### ث) CI و زیرساخت

| # | شدت | یافته | شاهد |
|---|---|---|---|
| E1 | 🔴 | **هیچ ruleset/branch protection** — HTTP 403 «Upgrade to GitHub Pro or make this repository public». | `gh api .../rulesets` |
| E2 | 🔴 | **سلامت CI:** 500 اجرای اخیر → 269 cancelled، 139 skipped، 68 success، 19 failure، 5 startup_failure. workflow «CI»: 5 success در برابر 60 cancelled. در 7 روز اخیر: **75٪ از 704 اجرا cancelled** و **هیچ اجرای CI روی `main`**. | `gh run list`، `reusable-hygiene-report` |
| E3 | 🟠 | **یک runner خودمیزبان برای همه:** 24 job با `[self-hosted, linux, x64, kavosh-ci]`؛ Issue #48 (81 کامنت) و #232 «runner availability blocks closure». | `.github/workflows/*` |
| E4 | 🟡 | **workflowهای رویدادمحور** (`pilot-crm-final-test`، `platform-numbering-acceptance` …) که بیشتر اجراها skipped هستند؛ 12 workflow برای یک monolith. | `gh run list` |
| E5 | 🟡 | **اعتبارسنج خانگی جایگزین پلتفرم:** `scripts/validate_repo.py` (311 خط) وجود رشته‌هایی در Markdown را چک می‌کند — نشانه‌ی جبران نبود rulesets. | فایل |

### ج) همکاری با عامل‌های AI

| # | شدت | یافته | شاهد |
|---|---|---|---|
| F1 | 🔴 | **سرعت بالاتر از ظرفیت بازبینی انسانی:** 285 commit در 2026-09-20، 221 در 09-24، 186 در 09-25. | `git log --date=short` |
| F2 | 🟠 | **نسبت‌دهی ناقص:** فقط 27 commit trailer `Co-Authored-By: Claude` دارند؛ شاخه‌های `codex/*` بدون نسبت‌دهی؛ دو هویت نویسنده (`noreply` و یک ایمیل شخصی با 326 commit). مشخص نیست کدام تغییر را کدام عامل ساخته. | `git log --format=%an/%b` |
| F3 | 🟠 | **AGENTS.md پر از وضعیت زنده** (SHA، شماره‌ی PR، schema revision). طبق راهنمای رسمی AGENTS.md، این فایل برای دستورات ساخت/تست/قراردادهای پایدار است. | `AGENTS.md` |
| F4 | 🟠 | **حافظه‌ی جلسه در Issue:** «handoff»های طولانی در کامنت‌ها برای انتقال context بین جلسات عامل؛ هر جلسه‌ی جدید باید ده‌ها کامنت بخواند. | #51، #235 |
| F5 | 🟡 | **قواعد واکنشی:** #236 دوازده قانون درست را بعد از بروز مشکل نوشت — ولی باز هم بدون اجرای پلتفرمی. | #236 |

### چ) داده و Schema

| # | شدت | یافته | شاهد |
|---|---|---|---|
| G1 | 🟡 | **131 migration در 54 روز** و یک مورد revision تکراری Alembic (PR #230). نشانه‌ی کار موازی روی شاخه‌های بلندعمر. | `alembic/versions` |

---

## آنچه درست انجام شده (حفظ شود)

- وجود `AGENTS.md` با پل‌های `CLAUDE.md`/`GEMINI.md` — الگوی صحیح.
- CODEOWNERS، قالب PR، Issue forms، `.gitleaks.toml`، `SECURITY.md`، Dependabot.
- ADRها در `docs/decisions/`.
- اصول #236 (search before create، one writer، small changes، fitness functions، no bypass-to-green) — محتوای درست؛ فقط باید به ماشین منتقل شود.
- حساسیت امنیتی بالا (عدم ذخیره‌ی credential ستاد/مودیان).

## نگاشت یافته‌ها به قواعد KavoshStart

| یافته‌ها | قواعد ([RULES.md](../standard/RULES.md)) |
|---|---|
| A1, A2, A3, F3, F4 | SRC-1…4، AI-1 |
| A4 | SRC-6 |
| A5, A6 | DOC-1، DOC-3، DOC-4 |
| B1–B4 | WK-1…4 |
| C1, C2, C8 | BR-1، BR-8، BR-3 |
| C3, C4, C9 | BR-4، PR-3، PR-1، PR-2، PR-4 |
| C5 | REL-1 |
| C6 | SEC-4 |
| C7 | BR-6 (لایه‌های A و M) |
| D1–D3 | REL-1…4، PR-2 |
| E1 | مدل پلن رایگان ([01](../standard/01-free-plan-operating-model.md)) |
| E2–E5 | CI-1…8 |
| F1, F2, F5 | PR-8، AI-3، AI-5، CI-6 |
| G1 | BR-1، WK-5 |
