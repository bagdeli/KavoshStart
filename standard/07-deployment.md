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

## دیتابیس: آنچه خودکار است و آنچه نیست (DEP-4…6)
| مرحله | خودکار؟ | توضیح |
|---|---|---|
| backup قبل از migration | ✅ | `BACKUP_CMD`؛ اگر شکست بخورد، هیچ تغییری اعمال نمی‌شود |
| migration | ✅ | `MIGRATE_CMD`؛ فقط expand (اضافه کردن) در همان نسخه |
| بازگشت برنامه به نسخه‌ی قبل | ✅ | چون migrationها expand-only هستند، نسخه‌ی قبل روی schema جدید کار می‌کند |
| بازگرداندن دیتابیس | ❌ | عمداً دستی (runbook)؛ بازگرداندن خودکار می‌تواند داده‌ی ثبت‌شده بعد از backup را پاک کند |

قاعده‌ی expand/contract: حذف ستون در نسخه‌ی N+1، فقط وقتی نسخه‌ی N دیگر از آن استفاده نمی‌کند. این تنها چیزی است که «بازگشت خودکار» را واقعاً امن می‌کند.

## ساختار روی سرور
هر نسخه در `releases/vX.Y.Z/` با `git archive` استخراج می‌شود (بدون فایل‌های مانده از قبل)، `.env` در `shared/` و بیرون از نسخه‌هاست، و `current` به نسخه‌ی در حال اجرا اشاره می‌کند. سه نسخه‌ی آخر نگه داشته می‌شود.

## ثبت استقرار
اسکریپت پس از هر استقرار موفق یا ناموفق یک خط در `/var/log/kavosh/<project>-deploy.log` می‌نویسد. (اختیاری، بعداً: ارسال وضعیت به GitHub Deployments API با توکن محدود.)

## static
سایت ایستا از ریپوی private روی Free نمی‌تواند روی GitHub Pages باشد. همان `pull-build` با یک nginx روی سرور؛ یا اگر محتوا عمومی است، ریپو را public کنید تا Pages رایگان شود.
