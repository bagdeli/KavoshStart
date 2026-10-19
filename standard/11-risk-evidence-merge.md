# 11 — Change Risk, Evidence, Continuation and Merge

این سند توضیح قواعد CR، FLOW و PR-6 است. منبع رسمی Ruleها همچنان `standard/RULES.md` است.

## 1. دو محور مستقل

KavoshStart دو چیز را جدا می‌کند:

- **Project Tier**: میزان assurance و فرایند پایهٔ کل پروژه.
- **Change Risk**: خطر خود تغییر فعلی.

یک T1 می‌تواند PR کم‌ریسک documentation و در همان روز migration پرریسک داشته باشد. Line count و file count فقط telemetry هستند و risk classifier نیستند.

## 2. Risk levels

| Risk | نمونه | انتظار |
|---|---|---|
| low | typo، docs، refactor مکانیکی کاملاً محصور | verification متناسب و reviewability |
| medium | رفتار bounded، API/UI غیرحساس، dependency عادی | test/evidence متناسب با capability |
| high | governance/control-plane، auth/permission، migration، deploy/release policy، trust boundary | تصمیم انسانی صریح برای scope فعلی + evidence قوی |
| critical | destructive production/data، regulated/financial safety boundary، تغییر غیرقابل‌برگشت یا blast radius بسیار بالا | تصمیم انسانی صریح، runbook/rollback و gateهای خاص domain |

Machine checks می‌توانند برای path/capabilityهای شناخته‌شده حداقل risk تعیین کنند؛ semantic risk بالاتر همچنان مسئولیت عامل و reviewer است.

## 3. Coherent change به‌جای size gate

Batch کوچک برای feedback سریع مطلوب است، اما split فقط وقتی خوب است که هر بخش independently useful/testable/mergeable بماند. این‌ها مثال‌های معتبر برای یک PR بزرگ‌اند:

- generated rename با generator و verification مشخص؛
- formatting/API regeneration؛
- migration ساختاری که split آن atomicity را خراب می‌کند؛
- UI change منسجم که شکستن آن integration risk را بیشتر می‌کند.

یک PR کوچک می‌تواند critical باشد؛ یک PR چند هزار خطی می‌تواند low/medium باشد. هیچ hard limit جهانی بر اساس تعداد خط یا فایل وجود ندارد.

## 4. Continue ≠ Accept ≠ Merge ≠ Release

این چهار عمل مستقل‌اند:

1. **Continue**: اجازهٔ انجام گام بعدی.
2. **Accept**: تأیید outcome/evidence مشخص.
3. **Merge**: عملیات مکانیکی واردکردن exact head به main.
4. **Release/Production**: boundary جدا با gate و authorization خودش.

«ادامه بده» هیچ‌کدام از 2 تا 4 را به‌طور ضمنی اعطا نمی‌کند. اگر بخشی ناقص است، قبل از ادامه باید Issue/acceptance item canonical داشته باشد و بعداً نمی‌توان آن را complete گزارش کرد تا واقعاً بسته شود.

## 5. Delegated merge

برای risk=low/medium، agent می‌تواند بعد از این preflight merge را انجام دهد:

- exact current head تغییر نکرده؛
- base/mergeability سالم است؛
- required checks حاضر و green هستند؛
- blocker و unresolved review thread وجود ندارد؛
- acceptance mapping/evidence لازم کامل است؛
- merge فقط ordinary Squash است، بدون `--admin` یا bypass.

برای high/critical و control-plane/security/destructive/release-policy change، قبل از merge یک تصمیم انسانی صریح برای scope فعلی لازم است. بعد از آن خود کلیک/فرمان merge کار مکانیکی است و agent می‌تواند انجام دهد.

## 6. مرز اثبات انسانی

اگر agent با همان GitHub identity یا credential مالک کار می‌کند، comment/label/review ایجادشده توسط همان identity به‌تنهایی اثبات نمی‌کند که انسان تصمیم گرفته است. KavoshStart در این وضعیت ادعای machine-proof human approval نمی‌کند؛ authorization انسانی یک trust boundary واقعی و لایهٔ R/A است.

## 7. Evidence = risk × capability

Evidence باید از ماهیت تغییر بیاید، نه از یک checklist ثابت. نمونهٔ capabilityها:

- public-api / package-install / compatibility
- ui / accessibility / visual
- data / migration / backup / restore
- security / auth / permission
- deploy / runtime identity / rollback
- release / provenance / artifact integrity
- infrastructure / plan / drift / recovery

برای هر defect ابتدا مالک واقعی شکست (upstream، integration یا محصول) تعیین می‌شود؛ فقط detector موجود یا regression کوچکِ همان رفتار اصلاح می‌شود. حذف یک الزام تکراری یا بی‌مبنا هم با تصمیم مستند در همان Issue/Spec/PR مجاز است.

## منشأ قرارداد، هزینهٔ اثبات و بازنشستگی الزام

سؤال اول «چه چیزی باید به‌درستی کار کند؟» است؛ نه «چند تست/رسید جدید بسازیم؟». برای **معیار یا آزمون جدید/تغییر مؤثر** در همان Issue/Spec/PR یک توضیح کوتاه کافی است: هدف کاربر یا ریسک واقعی، مالک invariant (native/upstream، افزونه/adapter، محصول یا الزامات قانونی)، منبع/نسخه، مدرک پوشش موجود، کوچک‌ترین رفتار پوشش‌نیافته، زمان مناسب و هزینهٔ اجرای آن. پاسخ‌های intake یا هزاران ردیف نیازمندی به‌طور خودکار Issue، receipt و تست مستقل ایجاد نمی‌کنند.

| مالک رفتار | حداقل بررسیِ مصرف‌کننده |
| --- | --- |
| WordPress، WooCommerce، SDK، Framework و کتابخانهٔ بالغِ نسخه‌دار | قرارداد رسمی، منبع/نسخه، سازگاری و مصرف صحیح؛ تست داخلی upstream را بدون دلیل تکرار نکنید |
| ترکیب/Template/افزونه و adapter | آزمون focused رفتار واقعی integration، داده، خطایابی و مسیر کاربر؛ upstream به‌تنهایی composition را ثابت نمی‌کند |
| منطق اختصاصی محصول | regression/contract واقعی برای نتیجهٔ قابل مشاهده و خطاهای مؤثر؛ نه هر متد trivially delegated |
| هویت و مجوز، پرداخت، دادهٔ حساس، مهاجرت، انتشار و استقرار | آزمون منفی/بازگشت یا شاهد مستقل در همان Trust Boundary، متناسب با ریسک و مرحلهٔ لازم |

**بازبینی مجدد حق طبیعی هر الزام است.** یک معیار/آزمون قدیمی ممکن است duplicate، upstream-owned، منسوخ، نادرست یا خارج از نسخهٔ کنونی باشد. با مرجع و نسخهٔ واقعی، مالک و پیامد حذف/تغییر، در همان Issue/PR/Spec تصمیم `keep / narrow / merge / retire` ثبت کنید. قرارداد، acceptance scope و test مربوط را با هم اصلاح و provenance را نگه دارید. لازم نیست ماه‌ها تست بی‌هدف برای اثبات نبود نیاز انجام شود. این تغییر نه اجازهٔ پاک‌کردن finding واقعی، نه تبدیل FAIL به PASS، نه غیرفعال‌سازی CI required و نه حذف تعهد امنیتی/مالی بدون تصمیم صاحب اختیار است.

**امنیت و هزینه:** Risk acceptance می‌تواند متناسب با محیط و دارایی باشد؛ ابزار معینی مثل دو VM یک‌بارمصرف یا اسکن سنگین در هر PR، به‌خودی‌خود invariant عمومی نیست. یک Runner محدود روی Host موجود شاید با هویت غیرممتاز، کنترل فایل/socket، شبکهٔ محدود و بدون secrets حساس کافی باشد، ولی firewall تنها جای مهار محلی کد مخرب را نمی‌گیرد. درصدهای ذهنی «۹۸/۹۹٪» معیار اثبات نیستند. خطر با احتمال/پیامد، کنترل موجود، residual risk، نظر مالک و هزینهٔ واقعی سنجیده شود. کنترل جدید زمانی هزینهٔ بیشتری بگیرد که ریسک واقعاً آن را بخواهد؛ مشاهدهٔ منبعی معتبر برای چند criterion قابل بازاستفاده است.

این روش **به قواعد جاری CR-3/CR-4 اضافه می‌شود، نه به یک ماشین ارزیابی، قالب جدید برای هر الزام، یا Rule/Workflow تازه**. کیفیت end-to-end و رأی واقعی کاربر/مالک از تعداد تست مهم‌ترند.

## 8. Proportionate two-lane verification and product lifecycle

**A — deterministic, machine-observed:** build/typecheck, relevant behavior and negative authorization tests, bounded regression, baseline secret/dependency/unsafe-rendering checks, artifact/source identity and required environment gates. A red/missing required machine test cannot be replaced by a model's verbal assurance or visual approval.

**B — evaluative:** visual design, language, layout quality, UX and owner-selected outcomes may use a reviewed repeatable machine comparison **or** a genuine human review. For rendered changes UI-2 verifies a same-head GitHub Actions visual comparison with actual passing step, or an authenticated exact-head APPROVED GitHub review by a different human reviewer; a screenshot link or AI-written approval text is insufficient. One method is enough unless a material risk justifies both. A textual PR label/link alone is a pointer, not proof that a person reviewed or a browser ran; never use the agent's own action as independently human-reviewed evidence.

**Timing:** PR → fast impacted A and applicable B; integrated candidate → cross-component/e2e on representative routes and security baseline; initial release → required gates for that version; post-functional-release → scheduled deep/manual penetration or operational pilot when applicable. High-risk public-facing auth/payment/sensitive-data attack surfaces need focused verification before public exposure. Full manual penetration testing must not be a universal development or initial-release gate.

**No gate inflation:** a defect gets a focused regression on the affected behavior. Before adding a global MUST, the owner must approve its cross-project applicability, measurable safety value, lifecycle timing and operational cost. An agent cannot create a mandatory project-wide security test simply because it suggested one. Capability completion, test output and acceptance remain distinct; the same genuine observation may support multiple criteria without one receipt per row.

The legacy **v3 attested ACC-3 contract remains the default**; an explicit future-release `acceptance.assurance=risk-based` permits native source-bound required-CI proof **only** for low/medium CI-only items. High/critical, deferrals and specialist evidence retain independent source-bound receipts and decisions. Neither mode turns a missing test into PASS. This is a breaking control-plane release choice, never a silent upgrade.

## 9. Tool adapters

Core outcome را govern می‌کند، نه tool را:

- command contract: setup/lint/test/build/check؛ default scaffold می‌تواند Make باشد.
- release contract: SemVer + exact-source + changelog/release notes + gated immutable output؛ release-please، Changesets یا strategy معادل ممکن‌اند.
- account/billing policy: overlay جدا؛ budget به‌تنهایی quality gate یا authorization نیست.

