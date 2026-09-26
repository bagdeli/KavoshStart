# 0008 — Runner by repository visibility

- Status: accepted (supersedes [0004](0004-github-hosted-runners-and-pull-deploy.md) for runners; its pull-deploy part stays)
- Deciders: bagdeli
- Issue: bagdeli/KavoshStart#17

## Context and problem
On this account GitHub-hosted jobs of **private** repositories do not start (failed-payment lock), while public
repositories run normally (probe on 2026-09-26). A standard that requires GitHub-hosted runners for private projects
therefore stops every private project — exactly the kind of delivery blockage this standard is designed to avoid. Self-hosted
runners on public repositories are a known risk: pull requests from forks would execute code on our machines.

## Decision
- Private repository → self-hosted runner registered to that repository, labels `self-hosted, linux, x64, <repo-slug>`.
- Public repository → GitHub-hosted runners only; self-hosted forbidden.
- The manifest records `visibility` and `ci.runner`; governance fails if the workflows, the manifest or the real
  repository visibility disagree; Layer O checks visibility and that enough runners are online (T2 ≥ 2).
- Reusable KavoshStart workflows take a `runs-on` input; templates fill it from the manifest.

## Consequences
- Good: private projects never depend on GitHub billing or hosted minutes; public projects never expose a server.
- Bad: each private project needs runner capacity and maintenance; one runner per T2 project is not enough
  (an anonymized private T2 project showed severe cancellation/queue pressure with a single runner).
- Making a private repository public requires switching the runner in the same change (governance fails otherwise).

## Enforcement
Governance CI-1/CI-2 (manifest, workflow `runs-on` values, PR event visibility), Layer O (visibility, online runners),
`scripts/install-runner.sh`, tests in `tooling/tests/test_coverage.py` and `test_portfolio_guard.py`.
