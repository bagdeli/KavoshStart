# 0015 — GitHub-hosted-only Actions in private repositories

- Status: accepted
- Deciders: repository owner
- Tracking: issue #141
- Supersedes: only the private runner-choice portions of ADR-0009 and the current CI-1/2 explanations; older ADR-0004 and ADR-0008 remain historical.

## Context and alternatives

GitHub supports self-hosted Actions runners in private repositories and cautions about persistence and untrusted PR access (see [Secure use](https://docs.github.com/en/actions/reference/security/secure-use)). A properly isolated disposable runner may be appropriate elsewhere. A total ban is therefore **a deliberate project governance boundary, not a GitHub requirement**. The trade-offs include hosted-minute billing, unavailable private-network access and insufficient evidence for protected integration/TEST environments.

## Decision

1. **Private GitHub Actions jobs run only on standard GitHub-hosted runners.** No registered self-hosted, ARC, private custom group or self-hosted reusable-workflow execution is allowed. An ADR, local consent or manifest label cannot grant an exception.
2. T1/static may use `ci.runner: none` with *no* Actions jobs and explicit local evidence; this is not a self-hosted GitHub Actions mode.
3. Private GitHub-hosted jobs that consume shared quota remain per-run, ref/head-bound, owner-dispatched (ADR-0009); runner restriction does not itself grant billing authorization. Validate actual visibility and reject dynamic/unknown runner labels in the static governance check.
4. Public repositories continue to prefer hosted. A public self-hosted exception follows CI-2 only after accepted isolation/fork-code ADR; official GitHub guidance strongly warns against public self-hosted use.
5. Protected server integration, canonical Test and Production work occurs under independent provenance, approval and deployment controls. Do not misreport local/server checks as GitHub-hosted CI or inferred acceptance.
6. Only versioned changes to KavoshStart are made here. Consumer repo runner removal or enforcement of enterprise settings requires separate owner action; this decision authorizes no consumer mutation.

## Enforcement and limitation

Manifest schema + governance, scaffold rejection, workflow static classification, generated reusable workflows and positive/negative offline regression tests implement the machine-checkable subset. GitHub settings and installed runner inventory need independent authorized operational review. YAML static checks cannot prove all possible dynamic Action execution paths safe; review is still required.
