# 13 — Composable Capability Profiles

قواعد: CAP-1…2، CR-3

## هدف

Tier، Runtime و Capability سه سؤال متفاوت را جواب می‌دهند:

- **Tier**: چه سطح assurance و ceremony برای کل پروژه لازم است؟
- **Runtime**: کد در چه شکل اجرایی زندگی می‌کند؟
- **Capability**: چه نوع contract/evidence ممکن است برای این پروژه معنا داشته باشد؟

Capability نام تکنولوژی نیست. `react`، `php`، `terraform` یا `fastapi` در `stack` می‌مانند؛ capability باید یک concern پایدار و قابل استفاده در policy باشد.

## Catalog اولیه

| Capability | Contract surface |
|---|---|
| `control-plane` | governance، استاندارد، orchestration و policy code |
| `package` | public/consumer API، installability، compatibility و versioning |
| `server` | long-lived service، runtime identity، health و deploy/rollback |
| `browser-ui` | render، responsive، RTL/Bidi، keyboard/focus، accessibility و visual evidence |
| `desktop` | installer/runtime desktop، upgrade/rollback/signing در صورت کاربرد |
| `persistent-data` | durable state، backup/restore و ownership |
| `migration` | schema/data migration، backfill، compatibility و rollback |
| `infrastructure` | IaC، plan/drift/apply/recovery و infrastructure ownership |
| `release-artifact` | immutable artifact/package bytes، provenance و integrity |
| `regulated` | financial/regulated/high-assurance integration boundary |
| `cms-wordpress` | WordPress/WooCommerce، theme/plugin lifecycle، Site Editor/DB override concerns |

Catalog باید کوچک و semantic بماند. اضافه‌کردن capability جدید یک تغییر استاندارد است و باید Rule/evidence ownership روشن داشته باشد.

## Derivation

KavoshStart فقط capabilityهایی را خودکار الزام می‌کند که از facts مانیفست قطعی‌اند:

- `projectKind=library` → `package`
- `runtime=server` → `server`
- `ui.kind=web|admin` → `browser-ui`
- `runtime=desktop` → `desktop`
- database غیر `none` → `persistent-data` + `migration`
- `deploy.method=release-artifact` → `release-artifact`
- financial sensitivity یا regulated integration → `regulated`
- WordPress/WooCommerce در framework facts → `cms-wordpress`

`control-plane` و `infrastructure` از نام فایل یا ابزار حدس زده نمی‌شوند؛ پروژه آنها را وقتی واقعاً در scope است صریح اعلام می‌کند.

## Extra capability مجاز است

CAP-2 یک **minimum consistency** است، نه closed-world inference. اگر پروژه‌ای runtime=none دارد ولی هم package و هم infrastructure tooling ارائه می‌کند، می‌تواند هر دو را اعلام کند. Capability اضافی نباید برای دور زدن Tier/Runtime یا کاهش assurance استفاده شود.

## Risk × Capability

CR-3 همچنان مالک evidence هر تغییر است. Capability project-level فقط context پایدار می‌دهد؛ PR باید capabilityهای متاثر را نیز در `Capabilities:` اعلام کند.

نمونه‌ها:

- `package` + medium public API change → API compatibility + package/install evidence
- `browser-ui` + medium behavior change → render/RTL/breakpoints/keyboard/focus/accessibility evidence
- `persistent-data,migration` + high schema change → migration/backup/restore/rollback evidence
- `infrastructure` + high apply-policy change → plan/drift/recovery evidence
- `regulated` + critical financial boundary → domain-specific owner decision + security/audit evidence

وجود capability به‌تنهایی هیچ evidence را «complete» اعلام نمی‌کند.

## Profile examples

### KavoshUI-like library

```json
{
  "tier": "T1",
  "runtime": "none",
  "projectKind": "library",
  "capabilities": ["package", "browser-ui", "release-artifact"]
}
```

`browser-ui` اینجا درست است حتی با `ui.kind=none`، چون خود repository یک UI contract/package تولید می‌کند؛ CAP-2 حداقل‌های derivable را enforce می‌کند و capability اضافی semantic مجاز است.

### Stateful web service

```json
{
  "tier": "T2",
  "runtime": "server",
  "capabilities": ["server", "browser-ui", "persistent-data", "migration", "regulated"]
}
```

### WordPress product

```json
{
  "runtime": "server",
  "capabilities": ["server", "browser-ui", "persistent-data", "migration", "cms-wordpress"]
}
```

WordPress-specific Ruleها در Core عمومی قرار نمی‌گیرند؛ profile فقط ownership/applicability را اعلام می‌کند و reusable WordPress controls باید در profile/tooling مناسب باقی بمانند.

## تکامل

این release axis و consistency contract را ایجاد می‌کند. Gate تخصصی جدید فقط وقتی به capability متصل می‌شود که:

1. invariant عمومی و تکرارشونده باشد؛
2. detector قابل‌اعتماد داشته باشد؛
3. positive/negative test داشته باشد؛
4. project-specific truth را از Core بیرون نگه دارد.

این همان مرز `Core + capability profiles + project truth` است.
