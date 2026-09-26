# پذیرش KavoshStart در پروژه‌های موجود

پروتکل عامل: [START.md §2](../START.md). این سند فقط **فرآیند عمومی پذیرش** را مشخص می‌کند.
برنامه، ممیزی، هدف، نام و وضعیت پروژه‌های private باید فقط در سطح private همان پروژه نگه‌داری شود و نباید در KavoshStart عمومی ثبت شود.

## فازهای عمومی (برای هر ریپوی موجود)
| فاز | کار | خروجی | تأیید مالک |
|---|---|---|---|
| 0 | `bash scripts/audit-repo.sh bagdeli/<repo>` | گزارش خط پایه در همان سطح visibility پروژه | — |
| 1 | intake + `kavosh.project.json` + `scaffold.py --adopt` در یک PR؛ `kavosh.yml` با `enforce: false` | PR پذیرش | ✅ |
| 2 | `bootstrap-repo.sh --apply` + `install-agent-guards.sh` روی همه‌ی ماشین‌ها | تنظیمات و محافظ‌ها | ✅ |
| 3 | یکی‌کردن حقیقت: هر شاخه‌ی بلندعمر به `main` ادغام یا بسته؛ پشتیبان bundle قبل از حذف شاخه‌ها | `main` = حقیقت | ✅ برای هر حذف |
| 4 | پاک‌سازی دانش: حذف فایل‌های وضعیت، کوچک‌کردن AGENTS.md، شکستن اسناد بزرگ به spec/Issue، ADR برای تصمیم‌ها | governance سبز | ✅ |
| 5 | بازسازی backlog: برچسب type، sub-issue، milestone | health سبز در WK | — |
| 6 | CI مطابق visibility و runner policy، `make check`، job `required` | health سبز در CI | ✅ |
| 7 | `enforce: true` | پذیرش کامل | ✅ |

پشتیبان قبل از هر حذف:
```bash
git clone --mirror https://github.com/bagdeli/<repo> <repo>-backup.git
git -C <repo>-backup.git bundle create ../<repo>-all-refs.bundle --all
```

## ترتیب پیشنهادی
1. **KavoshStart** — ابتدا خود استاندارد باید self-conforming و سبز باشد.
2. **KavoshUI** — چون عمومی است، برای آزمون واقعی adoption و GitHub-hosted CI گزینه‌ی مناسب بعدی است.
3. **پروژه‌های private** — فقط با برنامه‌ی adoption داخل همان فضای private. KavoshStart عمومی نباید نام، URL، audit، هدف، backlog، وضعیت یا یافته‌های آن‌ها را ثبت کند.
4. سایر پروژه‌های public هنگام کار بعدی روی هرکدام.

## مرز اطلاعاتی public/private
- audit یک پروژه باید در همان پروژه یا یک control surface با همان سطح visibility ذخیره شود.
- KavoshStart عمومی فقط template، rule، مثال ساختگی و اطلاعات پروژه‌های public را نگه می‌دارد.
- Layer O عمومی فقط repoهای public را بررسی و گزارش می‌کند؛ repoهای private حتی اگر credential بتواند آن‌ها را ببیند، نادیده گرفته می‌شوند.
- نظارت پرتفوی private باید در یک control surface private مستقل اجرا شود.
- مثال‌ها باید generic باشند؛ از نام، URL، شناسه، هدف یا داده‌ی واقعی پروژه‌ی private استفاده نشود.
