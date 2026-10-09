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

سبز بودن CI یا Compose موقت فقط candidate را اثبات می‌کند. Test/Production رسمی فقط وقتی پذیرفته می‌شود که **لایه E (Environment)** روی همان host و canonical route قرارداد deployment را پاس کند.

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

## identity و health دو قرارداد جدا هستند (DEP-3/4/8)

`VERSION_URL` فقط هویت runtime را ثابت می‌کند و باید exact version + SHA مورد انتظار را برگرداند.

`HEALTH_URL` سلامت application/dependencies لازم را ثابت می‌کند.

هر دو مسیر روی loopback **و** canonical origin بررسی می‌شوند. این تفکیک جلوی false greenهایی را می‌گیرد که در آن static/version endpoint سالم است اما application خراب است، یا reverse proxy به runtime دیگری اشاره می‌کند.

## Layer E — Server Admission (DEP-7)

یک server استاندارد قبل از اینکه Test/Production رسمی نامیده شود باید حداقل این‌ها را machine-check کند:

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

- migrationهای T2 production expand/contract هستند.
- قبل از migration، continuous recovery/PITR و restore rehearsal تازه fail-closed بررسی می‌شوند.
- high-risk/destructive rewrite snapshot تازه لازم دارد.
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
