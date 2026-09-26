# پذیرش KavoshStart در پروژه‌های موجود

پروتکل عامل: [START.md §2](../START.md). این سند ترتیب فازها و برنامه‌ی ریپوهای فعلی را مشخص می‌کند.

## فازهای عمومی (برای هر ریپوی موجود)
| فاز | کار | خروجی | تأیید مالک |
|---|---|---|---|
| 0 | `bash scripts/audit-repo.sh bagdeli/<repo>` | گزارش خط پایه | — |
| 1 | intake + `kavosh.project.json` + `scaffold.py --adopt` در یک PR؛ `kavosh.yml` با `enforce: false` | PR پذیرش | ✅ |
| 2 | `bootstrap-repo.sh --apply` + `install-agent-guards.sh` روی همه‌ی ماشین‌ها | تنظیمات و محافظ‌ها | ✅ |
| 3 | یکی‌کردن حقیقت: هر شاخه‌ی بلندعمر به `main` ادغام یا بسته؛ پشتیبان bundle قبل از حذف شاخه‌ها | `main` = حقیقت | ✅ برای هر حذف |
| 4 | پاک‌سازی دانش: حذف فایل‌های وضعیت، کوچک‌کردن AGENTS.md، شکستن اسناد بزرگ به spec/Issue، ADR برای تصمیم‌ها | governance سبز | ✅ |
| 5 | بازسازی backlog: برچسب type، sub-issue، milestone | health سبز در WK | — |
| 6 | CI: hosted، `make check`، job `required`، بودجه | health سبز در CI | ✅ |
| 7 | `enforce: true` | پذیرش کامل | ✅ |

پشتیبان قبل از هر حذف:
```bash
git clone --mirror https://github.com/bagdeli/<repo> <repo>-backup.git
git -C <repo>-backup.git bundle create ../<repo>-all-refs.bundle --all
```

## ترتیب پیشنهادی ریپوها
1. **KavoshStart** — خودش را از روز اول رعایت می‌کند.
2. **KavoshUI** (T1، کتابخانه) — کوچک، فقط 2 شاخه؛ مشکل اصلی CI خودمیزبان (173 شکست از 200) و حجم اسناد. انتقال CI به hosted و پاک‌سازی README/manifestها.
3. **KavoshERP** (T2) — بزرگ‌ترین کار؛ برنامه‌ی زیر.
4. بقیه (KavoshSMS، KavoshWebManager، KavoshLicense، …) هنگام کار بعدی روی هر کدام.

## برنامه‌ی KavoshERP
| فاز | جزئیات |
|---|---|
| 1 | مانیفست: T2 / server / pull-build / ui=web با KavoshUI پین‌شده / بودجه 700. PR پذیرش با `enforce: false`. |
| 3 | PR #231 آخرین PR بزرگ: مستقیم به `main` (یا یک PR یک‌باره‌ی integration → main با `size:exception`). سپس `vnext/integration-20260918` بسته. tag `v1.1.0` روی commit اعلام‌شده در Issue #234 + GitHub Release. حذف tag `develop`. حدود 130 شاخه: موارد ادغام‌شده حذف؛ بقیه پس از بررسی و bundle. هدف ≤ 5 شاخه. |
| 4 | AGENTS.md جدید از قالب (اصول Issue #236 در بخش Conventions). حذف `PROJECT_STATE.md`، `docs/STATUS.md`، `docs/HANDOFF.md`، `tasks/`. `IMPLEMENTATION_PLAN.md` و `ROADMAP.md` → epic و milestone. فایل prompt 169KB و قرارداد 313KB → specهای جدا. GLOSSARY برای LCCG/KCDS/KIPR. README هم‌خوان با مانیفست. |
| 5 | 37 Issue باز: برچسب type، sub-issue بومی به جای «parent #192»، milestone `v1.2.0`. Issue #48 → `docs/runbooks/test-runner.md`؛ #94 → runbook شبکه؛ #235/#236 → ADR + AGENTS.md و بسته. |
| 6 | 12 workflow → `ci.yml` (T2) + `kavosh.yml` + `release.yml`؛ rehearsal و clean-reset فقط روی main/tag/`ci:full`؛ حذف runner خودمیزبان از CI؛ استقرار TEST با `kavosh-deploy.sh`. |
| 7 | `enforce: true`. |

معیار موفقیت 4 هفته پس از شروع: شاخه‌ها ≤ 10 · `main` عقب از هیچ شاخه‌ای نیست · PR میانه ≤ 300 خط · cancel CI < 10٪ · همه‌ی Issueها typed · صفر Issue تخلف باز · مصرف دقیقه ≤ 700.
