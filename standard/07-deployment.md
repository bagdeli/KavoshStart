# 07 — استقرار (Runtime: server / static)

قواعد: DEP-1…9، CI-2

## اصل: repository سبز با environment سالم یکی نیست

KavoshStart چهار وضعیت جدا دارد:

```text
source reviewed
  → CI candidate proven
  → immutable release/tag
  → persistent environment admitted
```

سبز بودن CI یا Compose موقت فقط candidate را اثبات می‌کند. فقط **محیط persistentِ انتخاب‌شده** هنگام ادعای استقرار محصول باید از لایهٔ E یا verifier بومیِ معادل همان adapter هویت و health واقعی بگیرد؛ هیچ Test دوم یا استقرار جدید به‌صورت خودکار ساخته نمی‌شود.

## مرز اول: نگهداری معمول upstream در برابر Release محصول

این راهنما **فقط** هنگامی قرارداد استقرار نسخهٔ محصول را تحمیل می‌کند که سورس/بستهٔ محصول واقعاً تغییر و Release/Deploy محصول انجام شود. **مسیر سبک native تنها زمانی معتبر است که در قرارداد استقرار همان پروژه انتخاب شده و نسخهٔ جزء در سورس، Lockfile یا Image محصول به‌صورت قابل‌استقرار پین نشده باشد.** اگر پین یا فایل محصول عوض می‌شود، همان PR/CI/Release معتبر محصول لازم است؛ updater بومی نباید نسخهٔ روی میزبان را بی‌خبر از سورسِ canonical تغییر دهد. برای نمونهٔ عمومی، به‌روزرسانی WordPress Core/Plugin با updater رسمی خود WordPress و بدون تغییر سورس محصول، **به‌خودی‌خود** به PR انتشار Kavosh، RC، GitHub App مستقل، Test host/VM دوم، اسکن کامل WordPress یا نصب سیستم استقرار جدید نیاز ندارد. ابزار بومی باید نسخهٔ واقعی را گزارش دهد و رفتارهای یکپارچه‌سازیِ واقعاً متاثر به اندازهٔ ریسک بررسی شوند. **پیش از هر آپدیتی که ممکن است داده یا فایل‌های ماندگار را تغییر دهد، وجود نسخهٔ پشتیبانِ مناسب و قابل‌بازیابی بررسی شود**؛ این لزوماً به معنی آزمون Restore تازه یا ذخیره‌ساز/ماشین جدید نیست. اگر Core واقعاً نیازمند به‌روزرسانی پایگاه داده باشد، ریسک و backup موجودِ قابل‌بازیابی در همان مرز سنجیده می‌شوند؛ اجرای migration محصول/دادهٔ حساس را با نگهداری بدون تغییر داده یکی نگیرید.

طبق [راهنمای رسمی WordPress](https://wordpress.org/documentation/article/updating-wordpress/)، بک‌آپ سایت قبل از به‌روزرسانی اقدام احتیاطی مناسبی است و minor/security updateهای زیادی به‌صورت بومی انجام می‌شوند. این راهنما **اجبار به Snapshot دوم یا تمرین Restore تازه در هر patch** را تعریف نمی‌کند. Product changes به مسیر Release خود محصول و کنترل‌های معتبر آن بازمی‌گردند. هیچ مرحله‌ای بدون اجرای واقعی PASS محسوب نمی‌شود.

## pull-based

پیش‌فرض این است که سرور release را می‌کشد؛ GitHub به سرور push/SSH نمی‌کند:

```text
GitHub                                  Kavosh server
──────                                  ─────────────
main → gated release → vX.Y.Z[-rc.N]    project-scoped systemd timer
                           ▲                         │
                           └──── fetch tags ─────────┘
                                                     │
                                                     ▼
 clean export → recovery gates → migrate → build/pull → start
                                                     │
                      local /version exact tag+SHA ──┤
                      local /health healthy ─────────┤
                  canonical /version exact tag+SHA ──┤
                  canonical /health healthy ─────────┤
                                                     ▼
                                            current = release
```

اگر target با `current` برابر باشد، timer باز هم identity و health را بررسی می‌کند. «چیزی برای deploy نیست» مجوز نادیده‌گرفتن drift نیست.

## دو روش استاندارد (`deploy.method`)

| روش | منبع artifact | رفتار استاندارد | شرط |
|---|---|---|---|
| **pull-build** | clean export از tag | build روی server، سپس start | پیش‌فرض ساده و قابل‌ردیابی |
| **pull-image** | registry | pull → provenance verification → no-build start | `ARTIFACT_VERIFY_CMD` اجباری |
| custom | ADR | روش جایگزین | باید REL/DEP معادل را ثابت کند |

برای `pull-image`، صرف تزریق `KAVOSH_SHA` یا tag محیطی به container قدیمی evidence نیست. verification باید artifact/image immutable را واقعاً به release مورد انتظار bind کند.

## کانال‌ها (DEP-2)

- **Test:** جدیدترین SemVer، شامل `vX.Y.Z-rc.N`.
- **Production:** فقط tag exact که مالک در pin همان server ثبت کرده.
- branch، working tree، label موقت و `v0.0.0` جایگزین release نیستند.
- نبود RC رسمی به معنی اجازهٔ deploy مستقیم `main` نیست.

فقط برای RC محصول و در پروژه‌ای که manifest تگ RC کلید `release.testStaging` دارد، adapter استاندارد سرور آن RC را روی `CHANNEL=production` پیش از تغییر pin یا runtime رد می‌کند (REL-7). `--verify-environment` نیز چنین نصب Production را نمی‌پذیرد. dry-run فقط policy موجود در mirror محلی را بررسی می‌کند و در نبود آن نتیجه را بررسی‌نشده گزارش می‌دهد. نبودن این کلید، رفتار RC قبلی را حفظ می‌کند؛ تغییر adapter و فعال‌سازی این قرارداد باید در rollout همان پروژه بازبینی شوند.

## identity و health دو قرارداد جدا هستند (DEP-3/4/8)

`VERSION_URL` فقط هویت runtime را ثابت می‌کند و باید exact version + SHA مورد انتظار را برگرداند.

`HEALTH_URL` سلامت application/dependencies لازم را ثابت می‌کند.

هر دو مسیر روی loopback **و** canonical origin بررسی می‌شوند. این تفکیک جلوی false greenهایی را می‌گیرد که در آن static/version endpoint سالم است اما application خراب است، یا reverse proxy به runtime دیگری اشاره می‌کند.

## Layer E — Server Admission (DEP-7)

یک server که **adapter pull-based استاندارد Kavosh** را انتخاب کرده، قبل از ادعای نصب در **محیط canonical از قبل انتخاب‌شده** باید حداقل این‌ها را machine-check کند؛ این فهرست به updater بومی یا host انتخاب‌نشده تعمیم ندارد:

- mirror/release/shared/current layout زیر `/opt/kavosh/<project>`;
- `shared/.env` بیرون release؛
- deploy env و deploy binary نصب‌شده؛
- service/timer با نام **project-scoped**؛
- timer enabled + active؛
- target معتبر SemVer؛
- `current` دقیقاً همان target؛
- exact local و canonical version/SHA؛
- local و canonical health.

فرمان استاندارد:

```sh
/usr/local/bin/kavosh-deploy-<project> --verify-environment
```

خروجی موفق `ENVIRONMENT_CONFORMANCE=PASS` است. failure یعنی environment پذیرفته نیست، حتی اگر CI سبز باشد.

## preview موقت ≠ Test رسمی

preview یا proof می‌تواند با Compose/project name، DB/uploads و port مستقل ساخته شود، اما:

- canonical Test/Production origin به آن bind نمی‌شود مگر DEP-7 پاس شود؛
- proof resource نباید volume persistent environment را reuse کند؛
- «فعلاً preview است» نباید بدون admission به deployment دائمی تبدیل شود.

این مرز از تبدیل‌شدن workaround به معماری دائمی جلوگیری می‌کند.

## فایل‌های قالب

| فایل | کار |
|---|---|
| `deploy/kavosh-deploy.sh` | selector، build/pull، migration، rollback، admission و drift |
| `deploy/kavosh-deploy.service/.timer` | template؛ هنگام نصب با نام project-scoped کپی می‌شوند |
| `deploy/deploy.env.example` | method، local identity/health، canonical origin و recovery settings |
| `compose.yaml` | skeleton runtime؛ پروژه باید TODOها را حذف کند |
| `docs/runbooks/deploy.md` | bootstrap، admission، rollback و drift diagnosis |

فایل‌های template unit generic هستند، ولی مقصد نصب باید `kavosh-deploy-<slug>.service/.timer` باشد تا چند پروژه روی یک host با هم برخورد نکنند.

## ساختار استاندارد host

```text
/opt/kavosh/<project>/
  repo.git/
  releases/vX.Y.Z[-rc.N]/
  shared/.env
  current -> releases/<accepted-tag>

/etc/kavosh/<project>/
  deploy.env
  pin                    # Production only
```

در کنار آن:

```text
/usr/local/bin/kavosh-deploy-<project>
/etc/systemd/system/kavosh-deploy-<project>.service
/etc/systemd/system/kavosh-deploy-<project>.timer
```

## دیتابیس (DEP-5/6)

### تشخیص مستقیم Head مهاجرت از سورس (اختیاری برای پروژهٔ دارای Migration)

برای یک محصول واقعاً دارای پایگاه داده، **نسخهٔ موردانتظار باید از Migration graph همان checkout/commit کاندید استخراج شود**؛ متغیر محیطیِ دستی، نام Tag برنامه یا یک متنِ PASS‌شده جای source-head نیست. `scripts/check_migration_revision.py` یک الگوی سبک و اختیاری با Python stdlib است: فرمان read-onlyِ native migration tool در checkout را اجرا و نتیجهٔ دقیق یک Head را می‌خواند. خروجی خالی/نامعتبر، چند Head مستقل، اجرای ناموفق، Timeout یا خروجی خارج از قرارداد => FAIL. مقایسه با نسخهٔ واقعاً اعمال‌شده در DB فقط وقتی فرمان read-onlyِ `current` مشخص و اجرا شده باشد، و پس از migration یا در admission محیط، معتبر است؛ اختلاف => FAIL. **اجرا نشدن/skip شدن هر کدام، اثبات موفقیت آن نیست.**

برای Alembic، از ابزار خود Framework (`alembic heads` و `alembic current`) در همان محیط dependency/کانفیگ کاندید استفاده شود؛ این helper جای اعتبارسنجی صحت migration، تست rollback، backup/restore یا مجوز اجرای DB نیست. مثال بدون اثرگذاری روی پایگاه داده:

```bash
python3 <KavoshStart>/scripts/check_migration_revision.py \
  --source-command '["alembic", "heads"]'
# After an actual authorized migration, verify read-only current == source:
python3 <KavoshStart>/scripts/check_migration_revision.py \
  --source-command '["alembic", "heads"]' \
  --applied-command '["alembic", "current"]'
```

برای جلوگیری از سوءاستفاده از آرگومان‌های فرمان، helper تنها `alembic heads` و `alembic current` (و تنظیمات محلیِ محدود) را می‌پذیرد؛ اجرای `upgrade`، `stamp` و shell را رد می‌کند. بااین‌حال اجرای `alembic current` می‌تواند `env.py` محصول را وارد کند؛ ابزار sandbox امنیتی نیست و محیط و credentialها باید مستقل بررسی شوند. این گزینه برای ابزارهای مهاجرت دیگر فقط با adapter رسمی و قابل بازبینی همان پروژه مناسب است؛ نه اینکه خروجی `echo PASS` یا فایل دست‌نویس را «اثبات سورس» بدانیم. داشتن چند Head ممکن است در بعضی پروژه‌ها عمداً پذیرفته شده باشد؛ در چنین معماری‌ای کنترل تک-Head **قابل اعمال نیست** و باید به‌جای ادعای PASS، قرارداد اختصاصی graph/merge migration با تست واقعی تعریف شود. نصب ابزار مهاجرت، اتصال به DB و اجرای migration به‌صورت خودکار توسط KavoshStart انجام نمی‌شود.


- برای migration واقعیِ Product، expand/contract پیش‌فرض است؛ در T1/T2 مسیر maintenance-window با تصمیم مالک و downtime پذیرفته‌شده و runbook بازیابی مجاز است.
- اگر updater بومی به دادهٔ پایدار دست نمی‌زند، migration gate اصلاً فعال نیست؛ اگر migration کم‌ریسک دارد، سلامت backup موجود کافی است و تمرین Restore تازه تحمیل نمی‌شود.
- فقط high-risk/destructive/irreversible نیازمند مشاهدهٔ Restore متناسب و Snapshot تازه هستند؛ اگر بازیابی نامعتبر است، همان عملیات متوقف می‌شود.
- application rollback خودکار می‌تواند مجاز باشد؛ database restore هرگز خودکار نیست.
- maintenance-window فقط در دامنهٔ مجاز rule و با ADR/authorization همان run.

## drift (DEP-8)

Drift یعنی expected release و محیط canonical همسان نیستند؛ مثال‌ها:

- `current` به vN اشاره می‌کند ولی `/version` SHA دیگری می‌دهد؛
- local runtime درست است ولی reverse proxy canonical runtime قدیمی را می‌دهد؛
- target همان `current` است اما health خراب است؛
- project-scoped timer حذف/غیرفعال شده است.

Timer در no-op deployment نیز identity + health را دوباره می‌سنجد و mismatch را failure می‌کند.

## artifact provenance (DEP-9)

برای pull-build، source یک clean export از exact tag است و build در همان release directory انجام می‌شود.

برای pull-image، registry artifact باید independently verify شود. Command پروژه باید failure را با exit non-zero اعلام کند. Environment label به‌تنهایی provenance نیست.

## ثبت و عیب‌یابی

- deploy log: `/var/log/kavosh/<project>-deploy.log`
- unit logs: `journalctl -u kavosh-deploy-<project>.service`
- timer: `journalctl -u kavosh-deploy-<project>.timer`
- verification: `--verify-environment`

اگر verification fail شد، اول expected tag/SHA، `current`، local endpoints، canonical route و unitها را مقایسه کنید. rebuild تصادفی image یا repoint دستی proxy راه‌حل استاندارد نیست.

## static

runtime static نیز اگر server-hosted persistent باشد همین admission/identity contract را دارد. اگر deployment واقعاً خارج از این مدل است، `custom` + ADR باید gateهای معادل را تعریف کند.
