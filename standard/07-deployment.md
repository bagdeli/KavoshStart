# 07 — استقرار (Runtime: server / static)

قواعد: DEP-1…4، CI-2

## اصل: سرور می‌کشد، GitHub هل نمی‌دهد (pull-based)
runnerهای GitHub خارج از ایران‌اند و نباید (و معمولاً نمی‌توانند) به سرورهای داخلی وصل شوند. پس سرور خودش هر چند دقیقه یک‌بار بررسی می‌کند که نسخه‌ی جدیدی منتشر شده یا نه.

```text
GitHub                                   سرور Kavosh (test / production)
──────                                   ─────────────────────────────
main ── release-please ── tag v1.4.0-rc.1        systemd timer (هر 5 دقیقه)
                                 ▲                      │
                                 └──── git fetch --tags ┘   (یا docker pull)
                                                        │ نسخه‌ی هدف ≠ نسخه‌ی فعلی؟
                                                        ▼
                  export تمیز → backup → migrate → build/up → health-check ── ✗ → بازگشت «برنامه» به نسخه‌ی قبل
                                                        │ ✓
                                                        ▼
                                                /version = v1.4.0-rc.1 (sha)
```

## دو روش (`deploy.method`)
| روش | ساخت کجا | دقیقه‌ی Actions | نیاز سرور | پیشنهاد |
|---|---|---|---|---|
| **`pull-build`** | روی خود سرور از روی tag | صفر | دسترسی خواندن به ریپو (deploy key فقط‌خواندنی) + Docker | **پیش‌فرض در Free** |
| `pull-image` | GitHub Actions روی tag → GHCR | هر release چند دقیقه | دسترسی به ghcr.io + توکن read:packages | وقتی ساخت روی سرور سنگین است |
| `custom` | روش جایگزین در ADR پروژه | وابسته به روش | حداقل‌دسترسی و همان gateهای release | فقط استثنای بررسی‌شده؛ pull-based پیش‌فرض می‌ماند |

اگر دسترسی سرور به github.com ناپایدار است: ریپو را از طریق mirror/relay داخلی (KavoshRepo) بکشید — اسکریپت فقط آدرس remote را عوض می‌کند.

## کانال‌ها (DEP-2)
- **test:** همیشه آخرین tag (شامل `-rc`).
- **production:** فقط نسخه‌ای که مالک در فایل `/etc/kavosh/<project>/pin` روی سرور نوشته. ارتقا = عوض کردن همین یک خط (یا اجرای `kavosh-deploy.sh --pin vX.Y.Z`).
- هیچ شاخه‌ای مستقیم مستقر نمی‌شود.

## فایل‌های قالب (`templates/runtime/server/`)
| فایل | کار |
|---|---|
| `deploy/kavosh-deploy.sh` | منطق کامل: یافتن نسخه‌ی هدف، ساخت، migrate، up، health-check، rollback، نوشتن وضعیت |
| `deploy/kavosh-deploy.service` + `.timer` | اجرای دوره‌ای با systemd |
| `deploy/deploy.env.example` | متغیرهای هر سرور (کانال، مسیر، URL سلامت) — بدون راز |
| `compose.yaml` | اسکلت Docker Compose با برچسب نسخه |
| `docs/runbooks/deploy.md` | راه‌اندازی سرور جدید و بازگشت دستی |

هر روش غیر pull-based نیازمند ADR است که محل credential، least privilege، تأیید release از main، tag تغییرناپذیر، rollback برنامه و عدم restore خودکار DB را پوشش دهد. مجوز هر deploy همچنان جدا و محدود به همان مقصد/نسخه است.

## دیتابیس: آنچه خودکار است و آنچه نیست (DEP-4…6)
| مرحله | خودکار؟ | توضیح |
|---|---|---|
| recovery قبل از migration | طبق ریسک | سلامت continuous backup/PITR و مدرک تازه‌ی restore test با check شکست‌بسته بررسی می‌شود؛ برای migration مخرب، rewrite یا high-risk snapshot تازه لازم است |
| migration | ✅ | `MIGRATE_CMD`؛ فقط expand (اضافه کردن) در همان نسخه |
| بازگشت برنامه به نسخه‌ی قبل | ✅ | چون migrationها expand-only هستند، نسخه‌ی قبل روی schema جدید کار می‌کند |
| بازگرداندن دیتابیس | ❌ | عمداً دستی (runbook)؛ بازگرداندن خودکار می‌تواند داده‌ی ثبت‌شده بعد از backup را پاک کند |

قاعده‌ی production T2 همان expand/contract است: حذف ستون در نسخه‌ی N+1 فقط وقتی نسخه‌ی N دیگر از آن استفاده نمی‌کند. برای T1، ADR می‌تواند maintenance window محدود با downtime را تعریف کند؛ اجرای هر migration در این حالت نیازمند تأیید مستقیم مالک و backup/restore آزموده است.

`BACKUP_CMD` برای هر migration الزام دائمی نیست؛ snapshot پیش از migration لازم است اگر destructive/high-risk یا schema rewrite باشد. `BACKUP_HEALTHCHECK_CMD` و `RESTORE_TEST_CHECK_CMD` هر دو پیش از هر migration باید موفق شوند؛ دومی باید تازگی و موفقیت rehearsal را از سامانه‌ی پشتیبان‌گیری بررسی کند. نوشتن `PITR enabled` به‌تنهایی recovery را اثبات نمی‌کند: تازگی، retention و restore test باید ثبت باشند. بازگرداندن دیتابیس همچنان فقط دستی و با مجوز جداست.

## ساختار روی سرور
هر نسخه در `releases/vX.Y.Z/` با `git archive` استخراج می‌شود (بدون فایل‌های مانده از قبل)، `.env` در `shared/` و بیرون از نسخه‌هاست، و `current` به نسخه‌ی در حال اجرا اشاره می‌کند. سه نسخه‌ی آخر نگه داشته می‌شود.

## ثبت استقرار
اسکریپت پس از هر استقرار موفق یا ناموفق یک خط در `/var/log/kavosh/<project>-deploy.log` می‌نویسد. (اختیاری، بعداً: ارسال وضعیت به GitHub Deployments API با توکن محدود.)

## static
سایت ایستا از ریپوی private روی Free نمی‌تواند روی GitHub Pages باشد. همان `pull-build` با یک nginx روی سرور؛ یا اگر محتوا عمومی است، ریپو را public کنید تا Pages رایگان شود.
