# 0019 — Only the designated human owner may authorize metered GitHub use in private repositories

- Status: accepted owner decision (2026-10-19); implementation, merge and release are separate
- Decider: the human owner who issued this policy; not another GitHub admin or agent
- Tracking: issue #157; runner portability #156
- Rules: CI-1, CI-3 (and unchanged CI-2)
- Supersedes: only the authorizer wording "owner/admin" of ADR-0018 for metered/private GitHub use; the four-way runner availability and trust policy remain unchanged

## Context

GitHub charges or meters certain services through plan allowances, credits and usage. Standard GitHub-hosted Actions jobs in private repositories consume included minutes before possible charges. Larger runners, Actions artifact/cache storage, Packages and some AI services have distinct costs or credits. A platform account's permission to dispatch a workflow is not consent from the designated human budget owner.

## Decision

1. Private GitHub use that incurs charges **or consumes a metered/billable allowance or credit** requires prior, direct, explicit authorization by **the human owner who issued this policy**. Included private hosted minutes are in scope even before the quota is exhausted. Other GitHub admins and agents cannot grant or delegate this person's permission.
2. Authorization names the repository, service/product, intended operation/workflow, exact PR/ref/current head SHA where applicable, duration/usage and budget/cap when applicable. It is a single scoped approval, not ongoing permission. No authorization is inferred from silence, a generic "continue", a plan/budget, unused free quota, write/admin access, an AI agent using the owner's credentials, a workflow actor, or a green check.
3. A private GitHub-hosted workflow is only manually dispatched **after** this exact approval. In-job SHA verification occurs after resource allocation and cannot prove prior human consent or retroactively authorize minutes already spent.
4. An existing isolated, repository-scoped **self-hosted GitHub Actions runner** on an independent server is still permitted under ADR-0018/CI-2 without authorization to consume GitHub-hosted minutes. That is not permission to buy a GitHub paid feature, extend infrastructure, expose secrets or deploy to production.
5. Standard GitHub-hosted minutes on **public** repositories remain permitted under current GitHub terms; paid add-ons are a separate authorization decision. An independent server worker outside GitHub Actions is not an Actions check.
6. Billing authority is an account/portfolio human decision expressed through existing CI-1/CI-3, not a new mandatory workflow, general specialist test, account secret, expanded default permission or provisioned server. Do not publish identifying private-repository or billing information in public KavoshStart.

## Enforcement and limitations

Keep existing private-hosted automatic triggers disabled and manual PR/ref/SHA scope checks; keep CI-2 trust, untrusted-code and credential isolation. The human owner must verify approval **before execution or metered feature activation**. Static checks and the GitHub actor/dispatch identity do not independently prove that human decision. No policy approval is conveyed by this ADR to execute a paid operation, alter a consumer repository, merge a PR or publish a release.

## References

- [ADR-0018 — four-way runner policy](0018-private-self-hosted-and-hosted-consent.md)
- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/concepts/runners/larger-runners
