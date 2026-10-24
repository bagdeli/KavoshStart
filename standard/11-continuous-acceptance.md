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

## استیج Test برای RC

`release.testStaging` یک opt-in نسخه‌دار برای rehearsal روی Test است؛ هویت dispatch مالک، scope، CI موفق روی SHA دقیق و receiptهای test/security/migration را با REL-7 می‌سنجد. در صورت نیاز، producer با `mode=actions-external` برای CI همچنان باید App مستقل، workflow/run/attempt/job، منبع و chronology واقعی را تأیید و `externalEvidenceDigest` تغییرناپذیر صادر کند؛ verifier هیچ Actions artifact API یا URL دلخواهی را نمی‌خواند. خود App باید شواهد اصلیِ تحت مالکیت پروژه را بررسی و readback را تأیید کند. این مدرک فقط برای staging است: UI و approval مستقل نهایی همچنان pending می‌مانند و ACC-3 برای انتشار نهایی تغییر نمی‌کند.

این مسیر اولیه فقط برای `acceptance.mode=continuous`، `release.strategy=release-please` و runtime سروری با Test و `deploy.method=pull-build` یا `pull-image` پشتیبانی می‌شود؛ profileهای دیگر `NOT_SUPPORTED` هستند و adapter سفارشی را پوشش‌داده فرض نکنید.

## فعال‌سازی

برای هر T2 که این نسخه یا جدیدتر KavoshStart را می‌پذیرد:

```json
"acceptance": {"mode": "continuous"}
```

الزامی است. پروژه‌ای که روی KavoshStart قدیمی پین مانده retroactively تغییر نمی‌کند؛ اما upgrade به استاندارد جدید باید این profile را در همان PR فعال و scope واقعی نسخه را bootstrap کند.

## دو روش اثبات با ریسک واقعی (برای نسخهٔ جدید استاندارد)

T2 همچنان `acceptance.mode=continuous` دارد و تصمیم پذیرش باید همراه قابلیت بسته شود، نه در انتهای پروژه. انتخاب جدید و **اختیاری** در مانیفست:

```json
"acceptance": {"mode": "continuous", "assurance": "risk-based"}
```

- **`attested`** (پیش‌فرض سازگار با قرارداد قبلی): تمام آیتم‌ها به رسید و تصمیم مستقل قبلی نیاز دارند. نبود فیلد `assurance` همین روش است؛ مصرف‌کنندهٔ v3 در سکوت سبک‌تر نمی‌شود.
- **`risk-based`**: فقط آیتم با `risk=low|medium`، بدون defer، با `evidence=["ci"]` و `assertions.ci=["repository::required"]` از **GitHub Actions واقعی، موفق و هم‌منبع** استفاده می‌کند؛ Issue بسته، SHA ادغام، و کنترل تغییر منبع/وابستگی‌های مؤثر ضروری‌اند. بدون App جدید یا رسید مستقل برای این آیتم.
- آیتم با `risk=high|critical`، `deferredTo` یا شواهد تخصصی `test/ui/security/migration` همچنان **رسید و تصمیم مستقل attested** نیاز دارد. CI عمومی نمی‌تواند اثبات تخصصی را جایگزین کند.
- اگر سورس پس از اجرای CI تغییر کرده باشد، تنها با `evidencePaths` بازبینی‌شده و ثابت‌ماندن همهٔ مسیرهای کنترلی می‌توان مدرک را بازاستفاده کرد. نقص هویت منبع یا دادهٔ API مانع Release است.
- `Accepted-By` در مسیر native فقط مرجع مسئول ثبت‌شدهٔ Issue است، **نه اثبات مستقل تأیید انسان**. مجوز انتشار و عملیات حساس همچنان جداست.

انتخاب روش به معنای پذیرفتن هر هزاران ردیف با یک CI سبز نیست؛ واحد scope همان **قابلیت قابل پذیرش** است و هر ادعای آزمون تخصصی باید proof تخصصی داشته باشد.

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
      "evidence": ["ci", "test", "ui"],
      "assertions": {
        "ci": ["repository::required"],
        "test": ["document::denied-read"],
        "ui": ["document::rtl-denied-state"]
      }
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
  "assertions": {"ci": ["repository::required"]},
  "deferredTo": "v0.2.0",
  "deferIssue": 141
}
```

defer فقط با target آینده SemVer بالاتر، `deferIssue` بسته، marker مالک و رسید مستقل `Defer-Decision-Evidence` معتبر است؛ marker به‌تنهایی تصمیم انسانی را اثبات نمی‌کند.

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

## رسید قابل بررسی، نه صرفاً لینک (برای آیتم‌های attested)

برای آیتم‌های attested و هر نوع evidence، رسید شامل assertionهای دقیقِ مصوب در scope لازم است؛ یک job سبز عمومی مدرک UI یا migration نیست. `Acceptance-CI-Receipt` نیز در کنار `Acceptance-Evidence-Run` لازم است. مقدار markerهای تخصصی و تصمیم باید این قالب را داشته باشد:

```text
https://api.github.com/repos/<owner>/<repo>/check-runs/<id>#sha256:<64-hex>
```

marker تصمیم پذیرش `Acceptance-Decision-Evidence` و marker تعویق `Defer-Decision-Evidence` است. لینک از مخزن دیگر، URL دلخواه، JSON مبهم/تکراری، خروجی تغییرکرده، رسید منقضی یا check غیرموفق رد می‌شود. هیچ URL دلخواهی دنبال یا دانلود نمی‌شود.

قرارداد دقیق ناشر و payload در `templates/tier/T2/acceptance/README.md` است. ناشر شواهد باید artifact واقعی را بخواند؛ ناشر تصمیم باید هویت و تصمیم انسانی را بیرون از اختیار عامل احراز کند. قرارداد مرجع، GitHub App اختصاصی و بازبینی‌شده را از `acceptance/security/receipt-policy.json` می‌خواند. App مشترک Actions یا connector و marker قابل‌ویرایش مالک، مرجع مستقل نیستند. کلید/توکن ناشر تصمیم نباید در اختیار عامل یا job محصول باشد.

قالب policy عمداً `producers: {}` دارد: نه App خیالی می‌سازد، نه پذیرش را سبز می‌کند. پیکربندی یک ناشر واقعی، بررسی کنترل دسترسی آن و صدور رسید زنده شرط rollout است؛ وجود کد validator به معنی نصب این سرویس نیست. policy و تغییر مسیرهای پوشش، تغییر control-plane با حداقل ریسک high هستند. تغییر trust policy در مخزنِ بدون محافظ مستقل قابل دورزدن است؛ این adapter جای حفاظت از مسیر ادغام و credential را نمی‌گیرد.

**مرز اثبات:** gate هویت ناشر App و پیوند source/scope/job/artifact را بررسی می‌کند، اما خودش صحت معنایی تمام محصول یا هویت زیستی انسان را استنتاج نمی‌کند. به ناشر مستقلِ مصوب برای تفسیر artifact و احراز تصمیم اعتماد می‌شود. این App نباید سرویس «تبدیل JSON ارسالی عامل به مهر تأیید» باشد. UAT بیرونی فقط از مسیر attestation همین مرجع پذیرفته می‌شود؛ metadata خصوصی در خروجی عمومی قرار نمی‌گیرد.

## استفادهٔ مجدد و ابطال مدرک

پیش‌فرض محافظه‌کارانه، برابری کامل tree پذیرفته‌شده و کاندیداست. برای جلوگیری از اجرای بی‌دلیل آزمون پس از تغییر نامرتبط، item می‌تواند `evidencePaths` شامل مسیرهای literal، واقعی و مصوب داشته باشد. تغییر هرکدام از این مسیرها، یا قراردادهای `acceptance`، manifest و `.github`، رسید را باطل می‌کند. glob، parent traversal، مسیر غایب و اطلاعات tree ناقص پذیرفته نیست.

مالک باید پوشش وابستگی‌های مؤثر، lockfileها، پیکربندی و داده‌های آزمون را بازبینی کند؛ این فهرست ابزار حدس خودکار وابستگی نیست. مدارک قدیمی با وجود ancestor بودن، خودکار قابل reuse نیستند. تغییر scope یا policy و تعویض مدرک نیز تأیید قبلی را باطل می‌کند، چون تصمیم به digest همان محدوده و همان رسیدها متصل است.

## زمان مدرک ادغام — PR-7

Layer M کنترل‌های سرشاخهٔ PR را در مرز `merged_at` ارزیابی می‌کند، نه فقط رنگ فعلی آنها. نتیجه‌ای که پس از ادغام کامل شده، مجوز آن ادغام نیست؛ اجرای واقعاً جدیدِ پس از ادغام نیز سابقهٔ معتبر را به تخلف تبدیل نمی‌کند. تاریخچه یا زمان نامعلوم، «تأییدنشده» است و سبز فرض نمی‌شود.

برای Actions، زمان ایجاد workflow/attempt و هویت job/head خوانده می‌شود تا صف قبل از ساخته‌شدن job پنهان نماند. caller باید `actions: read` را همراه مجوزهای قبلی به main-guard بدهد؛ قالب مشترک این مجوز را دارد. API یا metadata ناقص، gate را باز نمی‌کند. این ممیزی پس از push است و جای کنترل دقیق سرشاخه و checkهای الزامی **پیش از merge** را نمی‌گیرد.

## health

Layer H تعداد scope items، open acceptance items، deferred items و موارد بسته‌ای که evidence markerهای پایه ندارند گزارش می‌کند. marker closure فقط declared است؛ `receipts.py` مشترک تعداد verified و مشکلات رسید را جدا گزارش می‌کند. هدف کشف debt است، نه auto-accept.

## release

برای profile continuous، REL-5 علاوه بر checkهای repository، ACC-3 را اجرا می‌کند؛ در risk-based، آیتم‌های CI-only واجد شرایط اثبات native می‌گیرند و بقیه مانند گذشته attested هستند. اگر acceptance API/evidence قابل خواندن نباشد، release بسته می‌ماند. unavailable evidence مجوز release نیست.

## حریم منبع حقیقت

`scope.json` فقط intent نسخه‌دار است. statusهایی مثل `accepted`, `done`, `passed` داخل آن ممنوع‌اند. state واقعی در GitHub Issue/PR/Actions و environment evidence باقی می‌ماند.

### اصل مالکیت evidence و اصلاح Scope

`acceptance/scope.json` یک مجموعهٔ **نتایج محصولِ همین Release** است، نه فهرست همهٔ تست‌های upstream، سؤال‌های intake یا قواعد تاریخی. یک آیتم می‌تواند چند الزام مرتبط را با صاحب اختیار و risk یکسان پوشش دهد. شواهد نسخه‌دارِ native/upstream برای همان قرارداد داخلی معتبرند، اما پذیرشِ رفتار اختصاصی مصرف‌کننده (theme، adapter، مجوز/داده، UX و Test/Production) هنوز به شاهد واقعی خودش نیاز دارد. نیازمند شدن به receipt جدید باید از claim مؤثر ناشی شود، نه شمار ردیف‌ها.

اگر معیار قبلی duplicate، منسوخ یا خارج از scope شناخته شود، تصمیم `keep / narrow / merge / retire` با مرجع source/version و ریسک در Issue/PR/Spec صاحب آن ثبت می‌شود. در یک PR قابل بازبینی، scope/assertions و testهای متأثر هم‌زمان اصلاح و گذشته برای audit حفظ می‌شود. آیتم releaseِ واقعاً لازم یا ریسک high/critical بدون تأیید و evidence معتبر محو نمی‌شود؛ قرمزشدن Required check، نبود ناشر مستقل واقعی یا رخنهٔ امنیتی با تغییر label/گزارش به PASS تبدیل نمی‌شود.

## migration برای T2 موجود

در upgrade، هدف ساختن tracker دوم یا تبدیل کورکورانهٔ هر requirement داخلی به AC مستقل نیست. acceptance item باید واحدی باشد که مالک بتواند برای release همان نسخه درباره‌اش تصمیم بگیرد. یک item می‌تواند چند requirement ریزتر را پوشش دهد فقط وقتی owner، risk tier و evidence آنها مشترک است و mapping requirement→evidence از بین نمی‌رود.

کد merge‌شدهٔ تاریخی بدون evidence معتبر خودکار accepted نمی‌شود. آن را به‌عنوان debt واقعی وارد scope کنید، evidence قابل‌استفاده را reuse کنید و فقط gapهای مادی را دوباره اجرا کنید. Health closure ratio و سن debt را برای feedback زودهنگام نشان می‌دهد؛ G/Release همچنان برای scope همان نسخه fail-closed است.

در ارتقای مصرف‌کننده، برای آیتم‌های attested باید policy ناشر واقعی فراهم باشد؛ برای CI-only native اپ مستقل ساخته نمی‌شود. assertionهای scope، `checks: read` برای Health و مدارک واقعی را در PR مربوط آماده کنید. receipt خالی/جعلی یا تغییر `continuous` به `none` راه مهاجرت نیست. هیچ tag منتشرنشده‌ای را در مصرف‌کننده pin نکنید.

این سخت‌گیری، قرارداد پذیرش مصرف‌کنندگان continuous را تغییر می‌دهد؛ rollout باید به‌عنوان تغییر ناسازگارِ نسخه‌دار برنامه‌ریزی شود، نه patch بی‌نیاز از مهاجرت. تغییر ناشر یا فعال‌سازی سرویس واقعی نیازمند تصمیم صریح مالک و کنترل دسترسی مستقل است.
