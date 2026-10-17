# Migrating from v5 to v6 — private self-hosted runner choice

This is a prospective **major** policy change. No downstream repository is auto-upgraded or modified by KavoshStart.

1. Confirm repository visibility, existing runner inventory and permitted access with the owner. Do not infer that a manifest label proves an actual runner is available.
2. Where an isolated, approved server-installed GitHub Actions runner already exists, choose `ci.runner: self-hosted`, repo-specific `runnerLabels` such as `[self-hosted, linux, x64, example]`, and a real `ci.trustModelADR` in that consuming repository. Record isolation, untrusted PR policy, secret boundaries and actual registration. Such jobs do not consume GitHub-hosted minutes.
3. If private `ci.runner: github-hosted` is chosen, automatic cost-bearing triggers remain off. For every specific execution, ask the owner/admin and obtain explicit authorization **before** manual dispatch. Bind the dispatch to the current PR/ref/head SHA; free included private minutes are still subject to this policy.
4. On public repositories, standard hosted minutes remain free under current GitHub terms. Public self-hosted requires the same fork/isolation/credential review. Larger runners and storage have separate cost policies.
5. `ci.runner: none` remains limited to T1/static with local test evidence and no Actions workflow.
6. Re-run schema, scaffold and runner-positive/negative tests plus normal governance. Self-hosted server setup, live runner availability, environment access and genuine Test/Production checks need independent owner verification.
7. Preserve required CI/release contexts. Do not claim local/server-only checks are GitHub check runs. No release or consumer adoption without its own versioned PR and approvals.

Earlier consumers upgrading directly from v2, v3 or v4 must also review intermediate v3–v5 acceptance/schema/governance changes. The [v5 migration guide](v5-provider-neutral-and-hosted-only.md) remains the historical contract for v5.

Decision: [ADR-0018](../decisions/0018-private-self-hosted-and-hosted-consent.md).
