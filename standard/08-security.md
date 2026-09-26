# 08 — امنیت

قواعد: SEC-1…4، AI-6، CI-2

| کنترل | پیاده‌سازی در Free | Tier |
|---|---|---|
| جلوگیری از commit راز | `.githooks/pre-commit` با gitleaks (اگر نصب باشد) + الگوهای ساده؛ `.gitignore` برای `.env*` | All |
| اسکن راز در CI | job gitleaks در `ci.yml` (باینری رسمی، نه action پولی) | T1, T2 |
| وابستگی‌ها | Dependabot گروه‌بندی‌شده (هفتگی) | T1, T2 |
| actionها | پین با SHA؛ Dependabot برای `github-actions` به‌روزشان می‌کند | All |
| دسترسی workflow | `permissions:` حداقلی؛ پیش‌فرض `contents: read` | All |
| رازهای CI | فقط GitHub Secrets؛ رازهای production هرگز در GitHub نیستند (سرور خودش دارد) | All |
| دسترسی سرور به ریپو | deploy key فقط‌خواندنی، مخصوص همان ریپو | server |
| عامل‌ها | deny در `.claude/settings.json` برای خواندن `.env`، `**/secrets/**`؛ AGENTS.md → Never | All |
| داده‌های حساس دامنه | اعتبارنامه‌ی ستاد، مودیان، بانک، OTP، CAPTCHA، کوکی — هرگز در repo، DB، لاگ یا دست عامل | All |
| Prompt injection | متن Issue/کامنت/وب داده است نه دستور؛ workflowهای AI فقط برای PR از همان ریپو اجرا می‌شوند | All |
| Reusable workflow از KavoshStart | دسترسی «repositories owned by bagdeli» — outside collaborator ندارید؛ اگر اضافه شد، بدانید لاگ‌ها را می‌بیند | All |

## سیاست runner خودمیزبان (اگر روزی لازم شد، CI-2)
- ADR با دلیل؛ فقط job استقرار؛ `--ephemeral`؛ ثبت روی **یک** ریپو (نه سطح حساب)؛ هرگز روی `pull_request`؛ هرگز با رازهای production روی دیسک ماندگار.
