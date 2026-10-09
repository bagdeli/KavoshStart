# 14 — Private portfolio supervisor

این سند reference implementation لایهٔ بیرونی برای consumerهای **private** را تعریف می‌کند. Ruleهای canonical همچنان در `RULES.md` هستند؛ این سطح، SEC-5 و BR-9 را برای private repoها قابل‌اجرا می‌کند.

## مرز محرمانگی

کد supervisor در KavoshStart عمومی است، اما inventory و report خصوصی نیستند و **نباید** وارد KavoshStart عمومی شوند.

- target list فقط از configuration موجود در private control surface خوانده می‌شود.
- token فقط به همان private control surface داده می‌شود.
- report می‌تواند نام repo و finding خصوصی داشته باشد، بنابراین فقط همان‌جا ذخیره/نمایش داده می‌شود.
- هیچ workflow عمومی KavoshStart این script را اجرا نمی‌کند.
- script در GitHub Actions عمومی خود KavoshStart عمداً refuse می‌کند.

## اجرا

```bash
KAVOSH_PRIVATE_CONTROL_SURFACE=1 \
GH_TOKEN=... \
python3 scripts/private_portfolio_guard.py \
  --inventory /secure/kavosh-private.json \
  --report /secure/kavosh-private-report.md
```

نمونهٔ **shape** inventory (بدون target واقعی):

```json
{
  "schemaVersion": 1,
  "repositories": ["owner/private-repository"]
}
```

این نمونه catalog نیست و نباید با repositoryهای واقعی در KavoshStart commit شود.

## چه چیزهایی بررسی می‌شوند

Reference implementation همان detectorهای Layer O عمومی را برای target خصوصی reuse می‌کند و حداقل این موارد را می‌سنجد:

- وجود `kavosh.project.json` و exact stable pin؛
- wiring واقعی governance/main-guard/health و invalid بودن `enforce:false`؛
- نبود main-guard روی head؛
- stale/missing health؛
- guard/dependabot/project files و repository merge settings؛
- open `kavosh:violation`؛
- T2 → `acceptance.mode=continuous` و scope غیرخالی.

## Freshness

اختلاف pin با آخرین stable **هشدار freshness** است، نه upgrade خودکار و نه failure کور. Consumer preflight باید changelog/control-plane delta را طبقه‌بندی کند:

- docs-only / non-material → warning می‌تواند تا upgrade برنامه‌ریزی‌شده باز بماند؛
- material control-plane → قبل از feature/gate جدید upgrade یا defer محدود و صریح مالک لازم است.

pin غیرSemVer، wiring غیرفعال، missing guard/health یا acceptance نامعتبر failure است.

## خروجی و exit code

- exit 0: هیچ failure؛ freshness warning ممکن است وجود داشته باشد.
- exit 1: حداقل یک failure conformance/assurance.
- exit 2: configuration/trust-boundary error، مثل نبود private-control-surface guard یا inventory نامعتبر.

این script Issue عمومی ایجاد نمی‌کند و هیچ target خصوصی را به Layer O عمومی اضافه نمی‌کند.
