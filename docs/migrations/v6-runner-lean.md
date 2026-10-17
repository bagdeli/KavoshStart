# Migration toward v6 — Runner authority and lean engineering

This is a **proposed major** contract; it is not effective for pinned v5 consumers until a stable v6 tag exists and each consumer separately adopts it with an authorized PR. Earlier v2/v3/v4 consumers must compare their intervening acceptance, UI/design-system, schema, CI and release contracts, not merely change a tag.

## Runner classification

1. Identify the real execution controller, not who owns the host. A GitHub-registered Actions runner is `self-hosted` even on your own server; a CI controller outside Actions is `external`.
2. For `external`, add `ci.externalCIADR`, `release.strategy: custom`, a reviewed `release.strategyADR` and `release.externalCommand` under `scripts/`. Remove GitHub Actions workflow files; do not delete existing workflows until independent trusted `required` and `kavosh / governance` source-bound check publishing is verified in the **consumer**. Verify SemVer tag/release gate and required check issuer on exact SHA. No auto-upgrade or invented green status.
3. For private Actions `self-hosted`, do **not** rely on a prior v5 label or an ADR as approval. Obtain actual scope-limited owner permission, add `ci.privateSelfHostedApprovalADR` and `ci.trustModelADR`, verify runner group isolation/ephemeral cleanup, prevent untrusted PR execution and restrict runs to separately authorized manual exact-SHA operations. An owner can deny or revoke this exception.
4. For private `github-hosted`, administrator approval for each billable run remains independent from manifest budget and `workflow_dispatch`. Confirm current account/actor permissions and actual usage boundary before starting.
5. For `none`, retain only T1/static with trustworthy locally recorded evidence; it is never a way around an existing failed Required Check.

## Lean guidance (no Ponytail runtime)

Agents trace callers/inputs/outputs outside the diff, reuse existing owner/native facilities, build the smallest complete change, and retain tests/security/data recovery/owner gates. No Ponytail hooks, telemetry, binaries, source snippets, coverage percentages or code-size quotas are installed.

## Review and rollout

- Validate schema/scaffold/governance, exact runner and reusable workflow selection, release strategy, both positive/negative CI tests, and real source-bound evidence for the chosen project. Human safety/credential review remains necessary.
- Resolve `required` and `kavosh / governance` with a trusted issuer for the exact candidate SHA and keep REL-5 protection; do not merge merely because a local script passed.
- Consumer activation or runner installation needs explicit separate project/repository authorization. No changes to any consumer are part of the public standard change.

## Version and privacy boundary

The standard change is **breaking**. It is planned for v6.0.0; no tag, release, private consumer rollout or runner registration occurs in this PR. Consumer identity, hostnames, metrics, audit outcomes and secrets must remain in their own private repository.
