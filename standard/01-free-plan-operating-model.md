# 01 — مدل اجرا، assurance و policy پلتفرم

## Core در برابر Portfolio/Account Policy

KavoshStart Core کیفیت و assurance را تعریف می‌کند: trust/isolation، checks، exact-source، release/deploy gates و evidence. هزینه، quota، plan و انتخاب تجاری runner یک **Portfolio/Account Policy overlay** است و نباید invariant کیفیت نرم‌افزار شود. این سند وضعیت فعلی GitHub را برای تصمیم عملی توضیح می‌دهد، اما تغییر billing نباید معنای Ruleهای مهندسی را عوض کند.

## چه چیزی روی ریپوی private در پلن Free وجود ندارد
| قابلیت | وضعیت | پیامد |
|---|---|---|
| Branch protection / Rulesets | ❌ (فقط public یا پلن پولی) | push مستقیم و force-push به `main` از سمت GitHub مسدود نمی‌شود |
| Required status checks | ❌ | PR قرمز قابل ادغام است |
| Required reviewers / CODEOWNERS اجباری | ❌ | CODEOWNERS فقط درخواست بازبینی است |
| Merge queue، Environments با reviewer | ❌ | — |
| GitHub Pages | ❌ برای private | سایت ایستا روی سرور خودمان |
| Actions | ✅ standard GitHub-hosted runner در **repo عمومی رایگان و نامحدود** است؛ private GitHub-hosted تابع سهمیهٔ پلن است | budget فقط برای مسیرهای billable؛ storage/cache/Packages و larger runners جدا |
| Issues، sub-issues، Projects، Milestones، Releases، Labels | ✅ | — |
| Issue Types | ❌ (فقط Organization) | برچسب `type:*` |
| Reusable workflow از ریپوی private دیگر همان کاربر | ✅ با تنظیم Access | KavoshStart مرکز workflowهاست |
| Squash-only، حذف خودکار شاخه | ✅ | لایه‌ی S |

## لایه‌های کنترل

```text
   عامل AI / توسعه‌دهنده
          │
   [A] محافظ عامل ─── .githooks/pre-push + agent deny rules
          ▼
   شاخه‌ی کوتاه ──► PR
          │
   [P] governance ── ساختار repo/PR/manifest/workflow
          │
   [R] بازبینی انسانی در نقاطی که ماشین context کافی ندارد
          ▼
        main
          │
   [M] main-guard ── merge/direct-push violations
          │
   [G] release gate ── exact-main required checks
          │
   [H] health ── repository drift / backlog / CI / release hygiene
          │
   [E] environment conformance ── روی host persistent:
       release layout + project-scoped deploy service/timer
       exact expected SemVer + SHA
       independent local /version + /health
       canonical /version + /health through the real proxy route
          │
   [O] portfolio ── public control surface only
```

**مرز مهم:** لایه‌های A/P/M/G/H کیفیت repository و release candidate را کنترل می‌کنند؛ آن‌ها ثابت نمی‌کنند canonical Test/Production واقعاً همان artifact را اجرا می‌کند. این وظیفه‌ی **E** است. یک Compose موقت، runner proof یا localhost smoke حتی با CI سبز، تا وقتی `ENVIRONMENT_CONFORMANCE=PASS` ندهد environment رسمی نیست.

- **A** خطاهای متداول عامل را قبل از GitHub می‌گیرد؛ bypass مجاز نیست.
- **P** ساختار PR/repo و ruleهای قابل مشاهده از GitHub را می‌سنجد.
- **M** merge ناسالم یا direct push را پس از وقوع آشکار می‌کند و release gate را می‌بندد.
- **G** فقط release از exact current `main` با checkهای required سبز می‌سازد.
- **H** سلامت repository را دوره‌ای گزارش می‌کند؛ H جای E را نمی‌گیرد.
- **E** توسط deployer استاندارد روی همان host اجرا می‌شود و fail-closed است. اگر `current`، service/timer، target، exact SHA/version، health یا canonical proxy با انتظار سازگار نباشند، environment پذیرفته نیست.
- **O** فقط repoهای public را از بیرون می‌بیند؛ metadata پروژه‌ی private وارد سطح عمومی نمی‌شود.
- **R** برای تصمیم‌هایی که نیازمند judgment انسانی‌اند باقی می‌ماند؛ وجود R مجوز نداشتن check ارزان و قابل‌اتکا نیست.

## لایه‌ی E — چرا لازم است

سه چیز مستقل‌اند و نباید با هم اشتباه شوند:

1. **CI proof:** کد/Artifact در محیط ایزوله تست شده است.
2. **Release proof:** tag/release immutable از exact main سبز ساخته شده است.
3. **Environment proof:** host canonical همان release را واقعاً اجرا می‌کند.

شکاف بین 2 و 3 همان جایی است که deployment drift، image قدیمی، reverse proxy متصل به runtime موقت یا service/timer نصب‌نشده می‌تواند هفته‌ها پنهان بماند. برای runtimeهای server/static استاندارد، `deploy/kavosh-deploy.sh --verify-environment` این شکاف را می‌بندد (DEP-7/8).

## لایه‌ی O — ناظر پرتفوی عمومی

هیچ ریپویی نمی‌تواند حذف شدن محافظ خودش را به‌طور قابل‌اتکا گزارش کند. برای repoهای **public**، KavoshStart یک ناظر بیرونی عمومی دارد:

- `scripts/portfolio_guard.py` و workflow روزانه‌ی `kavosh-portfolio` فقط repoهای public را بررسی می‌کنند.
- اگر credential به اشتباه repoهای private را هم ببیند، script آن‌ها را **پیش از inspection و report** نادیده می‌گیرد (SEC-5).
- نتیجه فقط درباره‌ی repoهای public در Issue عمومی `kavosh:portfolio` نوشته می‌شود.
- Layer O با `GITHUB_TOKEN` محدود به همان مخزن و مجوزهای حداقلی اجرا می‌شود؛ PAT مشترک یا secret حساب لازم نیست.
- نام، URL، هدف، audit، plan، finding یا runtime metadata پروژه‌ی private نباید وارد file، Issue، PR، commit message، Release یا log عمومی شود.

برای repoهای **private**، ناظر بیرونی باید در یک control surface private مستقل اجرا شود اگر سازمان می‌خواهد freshness/enforcement را portfolio-level تضمین کند. KavoshStart عمومی inventory خصوصی را نگه نمی‌دارد، اما contract آن ناظر را تعریف می‌کند: pin KavoshStart، enforce wiring، main/health freshness، acceptance profile و disabled/missing controlها را از بیرون بررسی کند و هیچ metadata خصوصی را وارد سطح عمومی نکند. target inventory و token فقط در سطح private نگه‌داری می‌شوند.

**مرز اعتماد:** Layer O عمومی به همین repo و GitHub Actions وابسته است. اگر خودش از کار بیفتد، فقط انسان متوجه می‌شود که Issue پرتفوی عمومی دیگر به‌روز نشده است. این لایه هیچ ادعایی درباره‌ی مشاهده یا سلامت پروژه‌های private ندارد.

## هزینه‌ی دقیقه‌ی خود KavoshStart

KavoshStart عمومی است و workflowهای خودش روی **standard GitHub-hosted runner** اجرا می‌شوند؛ این دقیقه‌ها طبق مدل billing GitHub رایگان/نامحدودند و نباید CI-3 را قرمز کنند. این معافیت فقط minute billing همان runner استاندارد عمومی است، نه larger runners، artifact/storage، cache یا Packages.

- `kavosh-governance`: یک job کوتاه روی رویدادهای PR.
- `kavosh-main-guard`: یک job پس از push/merge به main.
- `kavosh-health`: هفتگی.
- `kavosh-portfolio`: فقط در KavoshStart عمومی.
- **Layer E روی host خود پروژه اجرا می‌شود و GitHub-hosted minute مصرف نمی‌کند.**

## اگر روزی پلن پولی شد یا repo public شد

Rulesetها را می‌توان required کرد، ولی A/M/H/E همچنان لازم‌اند. Branch protection هرگز جای environment admission و exact runtime verification را نمی‌گیرد.
