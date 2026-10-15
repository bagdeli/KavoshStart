# 11 — جریان پیوستهٔ پذیرش و شواهد

قواعد: ACC-1…4، SRC-1، REL-5

## مسئله

ادغام code و سبز بودن CI به‌تنهایی به معنی «قابلیت پذیرفته شده» نیست. در پروژه‌های بزرگ، اگر mapping requirement→implementation→evidence تا انتهای نسخه عقب بیفتد، release با بدهی پذیرش سنگین مواجه می‌شود.

KavoshStart این سه حالت را جدا نگه می‌دارد:

```text
Engineering Complete  = کد merge + تست مهندسی
Acceptance Complete   = owner + evidence موردنیاز scope
Promotion Complete    = release/deploy/environment gates
```

هیچ مرحله‌ای مرحلهٔ بعد را خودکار فرض نمی‌کند.

## فعال‌سازی

برای هر T2 که این نسخه یا جدیدتر KavoshStart را می‌پذیرد:

```json
"acceptance": {"mode": "continuous"}
```

الزامی است. پروژه‌ای که روی KavoshStart قدیمی پین مانده retroactively تغییر نمی‌کند؛ اما upgrade به استاندارد جدید باید این profile را در همان PR فعال و scope واقعی نسخه را bootstrap کند.

## scope contract

`acceptance/scope.json` **tracker وضعیت نیست**. فقط قرارداد reviewable نسخه است:

```json
{
  "schemaVersion": 1,
  "targetRelease": "v0.1.0",
  "items": [
    {
      "id": "AC-001",
      "issue": 123,
      "owner": "github-login",
      "risk": "high",
      "evidence": ["ci", "test", "ui"]
    }
  ]
}
```

`risk`: `low|medium|high|critical`.
`evidence`: زیرمجموعهٔ `ci,test,ui,security,migration`.
`high/critical` باید `test` داشته باشد.

برای defer بررسی‌شده:

```json
{
  "id": "AC-009",
  "issue": 140,
  "owner": "github-login",
  "risk": "medium",
  "evidence": ["ci"],
  "deferredTo": "v0.2.0",
  "deferIssue": 141
}
```

defer فقط وقتی معتبر است که target آینده SemVer بالاتر باشد و `deferIssue` بسته و دارای `Defer-Approved-By: @<owner>` باشد.

## mapping در PR

هر PR غیررباتی در profile continuous باید بخش زیر را داشته باشد:

```markdown
## Acceptance mapping
- AC-001
- AC-004
```

یا برای maintenance واقعی:

```markdown
## Acceptance mapping
not-applicable: dependency-only maintenance; no product acceptance scope changes.
```

ID ناشناخته، duplicated scope ID یا دلیل خالی fail است.

## evidence در Issue canonical

وضعیت زنده در GitHub Issue می‌ماند. برای item قابل release، Issue باید closed باشد و markerهای machine-readable زیر را در body داشته باشد:

```text
Acceptance-Merged-SHA: <40-hex>
Acceptance-Evidence-Run: https://github.com/<owner>/<repo>/actions/runs/<id>
Accepted-By: @<owner>
```

برحسب scope:

```text
Acceptance-Test-Evidence: https://...
Acceptance-UI-Evidence: https://...
Acceptance-Security-Evidence: https://...
Acceptance-Migration-Evidence: https://...
```

Release gate بررسی می‌کند merged SHA ancestor کاندیداست و Actions run معرفی‌شده موفق، متعلق به همین repository و از `ci.requiredWorkflow` مانیفست کاندیدا باشد (پیش‌فرض: `.github/workflows/ci.yml`). `head_sha` اجرای مدرک باید همان `Acceptance-Merged-SHA` باشد؛ یک اجرای موفق ولی نامرتبط مدرک پذیرش نیست.

برای reuse مدرک سرشاخهٔ PR که با squash ادغام شده، marker اختیاری زیر را اضافه کنید:

```text
Acceptance-Evidence-PR: <positive PR number>
```

Gate باید ادغام همان PR به `main` همین repository، تطابق دقیق سرشاخهٔ آزمایش‌شده و commit ادغام، و برابری **کامل Git tree** آن دو را اثبات کند. ancestry یا توضیح «فقط مستندات تغییر کرده» کافی نیست؛ وقتی tree متفاوت است، مدرک CI روی source ادغام‌شده لازم است. marker خالی یا تکراری معتبر نیست.

**مرز اثبات:** این بررسی، provenance اجرای CI را کنترل می‌کند؛ پوشش معنایی requirement، محتوای لینک‌های تخصصی UI/security/migration و هویت انسانی پشت `Accepted-By` یا `Defer-Approved-By` را احراز نمی‌کند. لینک‌های تخصصی هنوز فقط از نظر قالب بررسی می‌شوند. تأیید انسانی و بازبینی ارتباط requirement→evidence همچنان لازم است؛ سبز بودن Gate یا Health جای آنها نیست. تغییرات بعدیِ مؤثر بر رفتار می‌توانند مدرک تاریخی را نامعتبر کنند و باید جدا بازبینی شوند.

## زمان مدرک ادغام — PR-7

Layer M کنترل‌های سرشاخهٔ PR را در مرز `merged_at` ارزیابی می‌کند، نه فقط رنگ فعلی آنها. نتیجه‌ای که پس از ادغام کامل شده، مجوز آن ادغام نیست؛ اجرای واقعاً جدیدِ پس از ادغام نیز سابقهٔ معتبر را به تخلف تبدیل نمی‌کند. تاریخچه یا زمان نامعلوم، «تأییدنشده» است و سبز فرض نمی‌شود.

برای Actions، زمان ایجاد workflow/attempt و هویت job/head خوانده می‌شود تا صف قبل از ساخته‌شدن job پنهان نماند. caller باید `actions: read` را همراه مجوزهای قبلی به main-guard بدهد؛ قالب مشترک این مجوز را دارد. API یا metadata ناقص، gate را باز نمی‌کند. این ممیزی پس از push است و جای کنترل دقیق سرشاخه و checkهای الزامی **پیش از merge** را نمی‌گیرد.

## health

Layer H تعداد scope items، open acceptance items، deferred items و موارد بسته‌ای که evidence markerهای پایه ندارند گزارش می‌کند. هدف آن کشف زودهنگام debt است، نه auto-accept.

## release

برای profile continuous، REL-5 علاوه بر checkهای repository، ACC-3 را اجرا می‌کند. اگر acceptance API/evidence قابل خواندن نباشد، release بسته می‌ماند. unavailable evidence مجوز release نیست.

## حریم منبع حقیقت

`scope.json` فقط intent نسخه‌دار است. statusهایی مثل `accepted`, `done`, `passed` داخل آن ممنوع‌اند. state واقعی در GitHub Issue/PR/Actions و environment evidence باقی می‌ماند.

## migration برای T2 موجود

در upgrade، هدف ساختن tracker دوم یا تبدیل کورکورانهٔ هر requirement داخلی به AC مستقل نیست. acceptance item باید واحدی باشد که مالک بتواند برای release همان نسخه درباره‌اش تصمیم بگیرد. یک item می‌تواند چند requirement ریزتر را پوشش دهد فقط وقتی owner، risk tier و evidence آنها مشترک است و mapping requirement→evidence از بین نمی‌رود.

کد merge‌شدهٔ تاریخی بدون evidence معتبر خودکار accepted نمی‌شود. آن را به‌عنوان debt واقعی وارد scope کنید، evidence قابل‌استفاده را reuse کنید و فقط gapهای مادی را دوباره اجرا کنید. Health closure ratio و سن debt را برای feedback زودهنگام نشان می‌دهد؛ G/Release همچنان برای scope همان نسخه fail-closed است.
