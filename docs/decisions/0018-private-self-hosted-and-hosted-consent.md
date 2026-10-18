# 0018 — Permit private self-hosted GitHub Actions; require consent for private GitHub-hosted

- Status: accepted (owner runner-policy decision; PR merge and release are separate)
- Deciders: repository owner
- Tracking: issue #153
- Rules: CI-1, CI-2, CI-3
- Supersedes: private hosted-only restriction in ADR-0015 for future major-version adopters; no history rewrite

## Context

Self-hosted and GitHub-hosted are both GitHub Actions runners. A self-hosted runner can be installed on a server controlled by the repository owner. A separate local server job without an Actions registration is not a third GitHub runner type and is not a GitHub check run.

GitHub currently offers standard GitHub-hosted minutes for public repositories without minute charges and plan-specific included minutes for private repositories, with charges possible beyond the allowance. Self-hosted Actions runner minutes are not billed by GitHub, although server, security, support and storage still have costs. Larger hosted runners and some Actions storage are billed separately.

## Owner decision

1. **Private self-hosted:** allowed when a correctly restricted/isolated server-installed Actions runner is available. Require a real in-repository CI-2 trust ADR, repository-specific runner labels, containment, untrusted-code/fork exclusions and credential boundaries; no special authorization to use *GitHub-hosted minutes* is required for that self-hosted mode.
2. **Private GitHub-hosted:** default **deny** even while included free plan minutes remain. Before every proposed run, **ask the owner/admin and receive explicit approval for this exact repo, workflow, PR/ref, head SHA and scope**. Only a manual, bounded workflow dispatch after this approval is permitted. A budget field, generic 'proceed' instruction, agent assertion or presence of write access is not consent.
3. **Public standard GitHub-hosted:** permitted and currently free for standard runner minutes. This is not a promise that larger runners, caching/storage, packages or other services are free.
4. **Public self-hosted:** allowed subject to CI-2 isolation/credential boundaries and excluding untrusted fork PR code, following GitHub's secure use recommendations.
5. **T1/static none:** preserve no-GitHub-Actions local evidence profile.
6. **Reusable workflows:** review local reusable workflows and explicitly forward the self-hosted selection to pinned standard calls; unknown external/dynamic runner choices do not prove compliance.
7. **Versioning:** the change breaks the v5 runner selection contract and requires the next major release. Existing consumers pinned to v5 remain unchanged; each consumer migration needs separate owner authorization.

## Limitations and evidence

Static schema, scaffold and workflow checks cannot prove whether a physical runner exists, is isolated, or holds unapproved credentials; those must be verified operationally. They also cannot independently prove human consent for an Actions dispatch: the question and approval must precede job allocation. A CI check after the job starts does not authorize the minutes already consumed.

The trust ADR describes the physical control, not a GitHub-hosted spending exception. Continue to enforce exact source/ref, normal PR gates and release evidence. No operations, installation or changes to other repositories are authorized by this decision.

## External references

- https://docs.github.com/en/billing/concepts/product-billing/github-actions
- https://docs.github.com/en/actions/reference/runners/github-hosted-runners
- https://docs.github.com/en/actions/reference/runners/self-hosted-runners
- https://docs.github.com/en/actions/how-tos/manage-runners/self-hosted-runners/manage-access
