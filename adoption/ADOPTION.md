# پذیرش KavoshStart در پروژه‌های موجود

پروتکل عامل: [START.md §2](../START.md). این سند فقط **فرآیند عمومی پذیرش** را مشخص می‌کند.
برنامه، ممیزی، هدف، نام و وضعیت پروژه‌های private باید فقط در سطح private همان پروژه نگه‌داری شود و نباید در KavoshStart عمومی ثبت شود.

## فازهای عمومی (برای هر ریپوی موجود)
| فاز | کار | خروجی | تأیید مالک |
|---|---|---|---|
| 0 | `bash scripts/audit-repo.sh bagdeli/<repo>` | گزارش خط پایه در همان سطح visibility پروژه | — |
| 1 | intake + `kavosh.project.json` + `scaffold.py --adopt` در یک PR؛ governance با `enforce: true` (هیچ پذیرش report-only مجاز نیست) | PR پذیرش | ✅ |
| 2 | `bootstrap-repo.sh --apply` + `install-agent-guards.sh` روی همه‌ی ماشین‌ها | تنظیمات و محافظ‌ها | ✅ |
| 3 | یکی‌کردن حقیقت: هر شاخه‌ی بلندعمر به `main` ادغام یا بسته؛ پشتیبان bundle قبل از حذف شاخه‌ها | `main` = حقیقت | ✅ برای هر حذف |
| 4 | پاک‌سازی دانش: حذف فایل‌های وضعیت، کوچک‌کردن AGENTS.md، شکستن اسناد بزرگ به spec/Issue، ADR برای تصمیم‌ها | governance سبز | ✅ |
| 5 | بازسازی backlog: برچسب type، sub-issue، milestone | health سبز در WK | — |
| 6 | CI با GitHub-hosted-only برای private و CI-1/2، `make check` و `required`؛ ثبت نیازهای مهاجرت runner جدا از شواهد Test/Production | health سبز و انتخاب runner سازگار | ✅ |
| 7 | اثبات سبز بودن همهٔ gateها روی SHA فعلی | پذیرش کامل | ✅ |

پشتیبان قبل از هر حذف:
```bash
git clone --mirror https://github.com/bagdeli/<repo> <repo>-backup.git
git -C <repo>-backup.git bundle create ../<repo>-all-refs.bundle --all
```

## ترتیب پیشنهادی
1. **KavoshStart** — ابتدا خود استاندارد باید self-conforming و سبز باشد.
2. **مصرف‌کنندهٔ عمومی با اطلاعات کاملاً ساختگی** — نمونهٔ مناسبی برای آزمایش workflow و الگوهای پذیرش بدون افشای مخزن خصوصی است.
3. **پروژه‌های private** — پذیرش فقط داخل فضای private همان پروژه؛ نام، URL، audit، backlog و runtime در KavoshStart عمومی قرار نمی‌گیرد.
4. سایر پروژه‌های public به‌شکل مستقل و نسخه‌دار.

## مرز اطلاعاتی public/private
- audit یک پروژه باید در همان پروژه یا یک control surface با همان سطح visibility ذخیره شود.
- KavoshStart عمومی فقط template، rule، مثال ساختگی و اطلاعات پروژه‌های public را نگه می‌دارد.
- Layer O عمومی فقط repoهای public را بررسی و گزارش می‌کند؛ repoهای private حتی اگر credential بتواند آن‌ها را ببیند، نادیده گرفته می‌شوند.
- نظارت پرتفوی private باید در یک control surface private مستقل اجرا شود.
- مثال‌ها باید generic باشند؛ از نام، URL، شناسه، هدف یا داده‌ی واقعی پروژه‌ی private استفاده نشود.
