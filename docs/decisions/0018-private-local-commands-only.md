# ADR-0018 — Private GitHub repositories run local commands only

- Status: accepted by owner; breaking CI/release governance change
- Supersedes: private runner/hosted options in ADR-0015, and older runner-specific history (0004, 0008, 0009)
- Enforcement: CI-1, PR-7, REL-5, schema/scaffolder, regression tests

## Decision

For any **private** repository, regardless of tier or runtime, GitHub Actions compute is forbidden: **no self-hosted runner, GitHub-hosted runner, ARC, reusable workflow, runner group, scheduled, dispatch, PR, push or release job**. `ci.runner=none`, budget=0 and **zero tracked workflow YAML files** are mandatory. No ADR, manual label, token, dispatch or agent request grants an exception.

The AI agent supplies reviewable commands **only**. The owner executes tests, lint, builds, browser checks, package checksums, `git`, `gh`, PR and release commands on an explicitly trusted workstation with GitHub access. The agent may not directly mutate a private repository, enable Actions, install or fix runners, register alternative infrastructure, or consume private account quota. Github Issues/PRs/Releases are metadata and artifact storage, not execution.

**Migration safety:** The owner first disables Actions at GitHub Settings → Actions → General (before creating a PR or pushing a branch that could still use legacy workflow files). Then removes all `.github/workflows/*.yml|yaml` and old private runner metadata from version control, runs local tests and reviews the diff. Removing YAML on the PR branch alone might not prevent a workflow from triggering. Old registered runners are handled by the owner separately.

## Proof and assurance

Record exact source SHA, commands, exit codes, tool/browser versions, relevant tests, authorized reviewers, and SHA-256 artifact digests in the **private** PR/Issue. Local evidence is not a GitHub Actions status and not independent human approval. Missing or failed tests cannot become PASS; specialist security/visual/release evidence remains scoped and real. The owner updates impossible old Actions-required branch rules explicitly and never invokes `--admin` or bypass to get a green result. Local `gh pr merge`, `gh release create` and package publication are explicit owner actions after verification.

Secrets remain exclusively on the owner's system. Network failures are reported with sanitized URL, DNS, observed IP or unknown and error category; no automatic proxy, mirror or relay. This is the owner's absolute policy, not a claim that GitHub disallows runners in private repositories.

Public repositories can continue using reviewed GitHub Actions under CI-2. Existing consumers must opt into the new breaking standard and migrate locally. No automatic private-repository mutation is authorized by this ADR.
