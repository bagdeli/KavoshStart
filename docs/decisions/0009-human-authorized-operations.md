# 0009 — Human-authorized operations and Free-only execution

- Status: accepted; enforced by the rules, templates and regression checks listed below
- Deciders: bagdeli
- Issue: bagdeli/KavoshStart#33

## Context

Absolute bans on every privileged operation prevent an agent from carrying out work the owner has explicitly approved. They also fail to distinguish ordinary authorization from protection bypass. GitHub Free and the owner's no-shared-quota-without-direct-approval constraint shape every CI path.

## Decision

- Authorization names one action, target, environment and current object/head where relevant. A material state change invalidates it. An issue, manifest, label, credential possession or general project policy does not itself authorize an action.
- A human may explicitly authorize an agent to squash-merge a specified PR after fresh checks, mergeability, base and review-thread preflight. The authorization never permits `--admin`, bypass, red/missing/skipped checks, direct main push or tag mutation.
- A human may authorize one credential for one login/action. Prefer execution that does not expose the value to the agent. Never log, commit, persist, upload or reuse the credential elsewhere. Regulated banking credentials, OTP/CAPTCHA and signing keys remain unavailable.
- GitHub Free and zero shared-quota consumption are the default. A private hosted run needs direct approval tied to one dispatch/ref/SHA and a bounded run. Public standard hosted runners are allowed only where they incur no shared quota or charge. Paid runners/features, required paid AI APIs and overage are not dependencies.
- Draft stacks may be arbitrarily deep while health warns. Ready PRs are normalized to main or one immediately mergeable parent. Merge requires a green shallow stack.
- Heavy Draft CI defaults off; a direct workflow dispatch may request early feedback only within the same execution authorization and cost rules.
- Runner isolation does not follow from a non-root account. Rootful Docker access is root-equivalent; this installer accepts rootless Docker only. A separately provisioned disposable worker VM must be destroyed after the job.
- Healthy continuous backup/PITR and a tested restore are the recovery baseline. A fresh snapshot is required for destructive/high-risk rewrites. A bounded T1 maintenance window may use downtime with verified backup and explicit authorization; production T2 keeps expand/contract as its default.
- Deployment/UI and PR-size exceptions require scoped owner authorization and evidence. Exception labels are requests, never authority.

## Unchanged boundaries

Required checks must exist and pass. No routine `--admin`, protection bypass, ordinary direct main push, mutable release tag, release from an unverified commit, secret disclosure/persistence, automatic database restore, publication of private data, or disabling security tests.

## Consequences

An explicit authorization record must be machine-verifiable for unattended/reusable checks; conversational approval is not silently converted into a long-lived manifest flag. If the authorization/cost proof or CI is absent, merge/release remains blocked. Local and GitHub-hosted free/public validation can establish code behavior; it cannot prove a private runner or an external backup service exists.

## Enforcement

`standard/RULES.md`, START and agent templates define the contract. Governance, main-guard, release-gate, public Layer O, runner installer and deployment templates must enforce the applicable machine-checkable boundaries with offline negative tests. Live repository settings and protected tags remain a separate operational gate.
