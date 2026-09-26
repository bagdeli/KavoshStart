# پذیرش KavoshStart در پروژه‌های موجود

پروتکل عامل: [START.md §2](../START.md). این سند فقط فازهای عمومی پذیرش را مشخص می‌کند و نباید حاوی نام، URL، هدف، معماری، آمار، ممیزی یا برنامه‌ی اختصاصی یک پروژه‌ی private باشد.

## فازهای عمومی (برای هر ریپوی موجود)
| فاز | کار | خروجی | تأیید مالک |
|---|---|---|---|
| 0 | `bash scripts/audit-repo.sh bagdeli/<repo>` | گزارش خط پایه؛ برای ریپوی private فقط در همان فضای private | — |
| 1 | intake + `kavosh.project.json` + `scaffold.py --adopt` در یک PR؛ `kavosh.yml` با `enforce: false` | PR پذیرش | ✅ |
| 2 | `bootstrap-repo.sh --apply` + `install-agent-guards.sh` روی همه‌ی ماشین‌ها | تنظیمات و محافظ‌ها | ✅ |
| 3 | یکی‌کردن حقیقت: هر شاخه‌ی بلندعمر به `main` ادغام یا بسته؛ پشتیبان bundle قبل از حذف شاخه‌ها | `main` = حقیقت | ✅ برای هر حذف |
| 4 | پاک‌سازی دانش: حذف فایل‌های وضعیت، کوچک‌کردن AGENTS.md، شکستن اسناد بزرگ به spec/Issue، ADR برای تصمیم‌ها | governance سبز | ✅ |
| 5 | بازسازی backlog: برچسب type، sub-issue، milestone | health سبز در WK | — |
| 6 | CI بر اساس visibility، `make check`، job `required` و بودجه | health سبز در CI | ✅ |
| 7 | `enforce: true` | پذیرش کامل | ✅ |

پشتیبان قبل از هر حذف:
```bash
git clone --mirror https://github.com/bagdeli/<repo> <repo>-backup.git
git -C <repo>-backup.git bundle create ../<repo>-all-refs.bundle --all
```

## ترتیب پیشنهادی
1. خود KavoshStart باید self-conforming و سبز بماند.
2. پروژه‌ها و کتابخانه‌های public را می‌توان با Layer O عمومی پایش کرد.
3. پروژه‌های private فقط از داخل فضای private خودشان پذیرفته و ممیزی می‌شوند. هیچ artifact اختصاصی آن‌ها در KavoshStart عمومی ذخیره نمی‌شود.
4. هر پروژه هنگام اولین کار واقعی خود، با همین فازهای عمومی adopt می‌شود؛ ترتیب و جزئیات آن در همان repository ثبت می‌شود.

## مرز محرمانگی
- KavoshStart عمومی فقط استاندارد، قالب و مثال‌های ساختگی مانند `example-private-app` نگه می‌دارد.
- نام، URL، اهداف، معماری، آمار، audit، adoption plan، runner status یا health یک پروژه‌ی private در فایل، Issue، PR، Release، commit message یا log عمومی KavoshStart نوشته نمی‌شود.
- Layer O عمومی فقط repositoryهای public را enumerate و گزارش می‌کند.
- نظارت cross-repository برای پروژه‌های private باید در یک control-plane خصوصی جدا اجرا شود؛ خروجی آن هرگز به Issue یا log عمومی ارسال نمی‌شود.
