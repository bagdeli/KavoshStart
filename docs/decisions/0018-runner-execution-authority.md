# 0018 — Independent CI execution authority and scoped GitHub Actions exceptions

- Status: **proposed for KavoshStart v6** — subject to explicit owner review of the high-risk v6 PR and its exact SHA
- Deciders: repository owner (control-plane authority); individual consumer exceptions decided only inside their own authorized repository
- Tracking: #152
- Supersedes on acceptance: ADR-0015 for runner choice; ADR-0015 remains intact as the historical v5 decision. Per-run human authorization from ADR-0009 remains applicable.
- Rules: CI-1, CI-2, CI-3, CI-7, AI-4, REL-4/5/6

## Problem

KavoshStart v5 imposed GitHub-hosted-only Actions in private repos. That excluded both owner-authorized isolated GitHub-registered runner exceptions and genuinely independent CI executed on a privately managed server. These are technically and trust-wise different arrangements. A privately hosted machine that runs the GitHub Actions runner app is **not** an external independent runner, regardless of container/VM/hostname.

Official GitHub guidance recognizes private self-hosted Actions runners as supported, warns about persistent compromise and untrusted PRs, and recommends ephemeral clean hosts for stronger isolation. External CI can post status/check results for the exact SHA through an independently trusted publisher; this must not be reduced to an unverified PR statement.

## Decision: separate execution authority from host ownership

| `ci.runner` | Execution system | Private | Public |
|---|---|---|---|
| `external` | independent SelfServer CI, not GitHub Actions | allowed with verified CI evidence, explicit externalCIADR and custom release contract | allowed with same source/permission checks |
| `self-hosted` | GitHub Actions registered self-hosted runner (including ARC) | **denied by default**; only an actual owner-approved **repository-specific exception** plus CI-2 isolation and restricted manual dispatch | allowed subject to real CI-2 untrusted-code, isolation, credential and fork boundary |
| `github-hosted` | GitHub-hosted Actions | administrator must authorize use of account quota for one exact run/ref/SHA; no private automatic runs | preferred standard CI when no account-cost exposure |
| `none` | focused local-only evidence, no Actions | T1/static only | T1/static only |

A budget field, label, ADR, repository write permission or manual `workflow_dispatch` event is **not proof** of the administrator's spending consent or the owner's private self-hosted exception. Human validation of actual owner approval and account/runner settings is necessary; independent approval must not be fabricated by an agent's comment or mutable branch file.

## Fail-closed external CI adapter

An `external` manifest declares `ci.externalCIADR` describing independent CI, exact SHA checkout, trusted publisher identity, the real required and `kavosh / governance` checks, credential boundary and release gate. The consuming owner installs/configures the publisher separately. Scaffold emits **zero** GitHub Actions workflow files. Local logs or passing scripts without a genuine source-bound, publisher-verified check do not authorize PR merge.

External release uses `release.strategy: custom`, `release.externalCommand` (a consumer-owned `scripts/*.sh` or `scripts/*.py` executable) and a separate `release.strategyADR` explaining SemVer immutable tags, exact-main SHA, required passing checks, acceptance provenance and authorized release. The release command may not masquerade as `.github/workflows/*`; file presence alone never proves that a release was actually executed. This mode may run an existing engine (Jenkins/Woodpecker/locally owned tooling) but KavoshStart installs none and names no required vendor. It does not silently continue using Actions-only release-please.

## Private GitHub Actions self-hosted exception

Before any exception becomes effective, the project-specific owner records a real, reviewable scope decision referenced by `ci.privateSelfHostedApprovalADR` and security design referenced by `ci.trustModelADR`. The isolation ADR covers runner trust model, isolation/disposability, untrusted code, credential boundary, actual execution control, teardown, and no persistent production secrets. A submitted ADR is evidence for **human checking**, not automatic verification that a human granted a live exception.

Private GitHub Actions jobs (both hosted and excepted self-hosted) remain behind scoped manual `workflow_dispatch` paths and are not automatically run on PR, push, schedule or workflow_run. A token and actor with GitHub write access do not automatically become a budget administrator. Actual GitHub access policy, runner registration and allowlisted workflow paths must be verified outside static GitHub-file scans. A GitHub-hosted private run also requires administrator quota authorization for that exact execution.

Public self-hosted is permitted but must still exclude untrusted fork code and use isolated trust boundaries. The option to use a public runner is **not** a recommendation to execute public fork PRs on a persistent trusted machine.

## Security and limitations

- Reusable called workflows select jobs in their own code, so a calling file's `runs-on` cannot prove a distant runner choice; retain fail-closed external reusable workflow policy in private.
- Exact-SHA GitHub status evidence requires a trusted GitHub App where supported; workflow_dispatch-created job checks may not satisfy protected-branch requirements. Private Free accounts may lack server-side branch enforcement. If a check is missing, red, unverifiable or unavailable, block merge/release rather than accepting a text claim.
- `none` remains limited to T1/static and is not a loophole for networked services.
- Reject runner mode masquerading (`external` combined with GH Actions runner labels/workflow files), unjustified new tools and vendor-specific runtime assumptions.
- Do not modify or identify downstream private consumers in this public repo; pinned old versions continue operating until separately authorized upgrade.

## Sources

- [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use)
- [Self-hosted runner reference](https://docs.github.com/en/actions/reference/runners/self-hosted-runners)
- [Required status checks](https://docs.github.com/en/pull-requests/how-tos/merge-and-close-pull-requests/troubleshooting-required-status-checks)
- [Reusable workflow runner authority](https://docs.github.com/en/actions/how-tos/reuse-automations/reuse-workflows)
- [SelfServer CI example, not a dependency](https://woodpecker-ci.org/docs/administration/general)
