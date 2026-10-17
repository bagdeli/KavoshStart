# Third-party component compliance — release-scoped inventory

Apply the upstream KavoshStart **TP-1/TP-2** policy before selecting a material component and before commercial distribution. This document is a **blank reusable template**, not a claim of licence approval. Keep real inventory and evidence only in the consuming repository.

Use an SBOM (SPDX/CycloneDX) appropriate for each release output and separately account for packaged images, fonts, assets, models, data and components missed by tooling. Link immutable release-specific evidence; do not store live backlog/status here.

| Component + exact version | Upstream / verified source | SPDX expression or contract | Use / linking / packaging / network / modifications | Distribution or network obligations (License / NOTICE / source / relinking) | Security + TCO rationale | Decision owner + review/evidence reference |
|---|---|---|---|---|---|---|
| (add only when applicable) | | | | | | |

## AGPL-specific decision (complete only when AGPL may apply)

- **Exact licence expression / variant:** `AGPL-3.0-only`, `AGPL-3.0-or-later` or a documented dual/mixed-licence expression; N/A with justification for other components
- **Integration and modifications:** combined/linked, independently served/API, changed/forked or unchanged; specify actual evidence (not a presumed process/container exception)
- **Network-use review:** users and interactions; whether modified AGPLv3 section 13 or combination requirements apply; relevant Corresponding Source scope
- **Fulfilment route:** required License/NOTICE, redistribution and applicable network source offer/location; or a substantiated not-applicable explanation
- **Compatibility decision:** can all licence and contract obligations be met without conflicting proprietary/confidentiality commitments? What was verified?
- **Outcome:** `approved` / `blocked` / `needs-legal-review` with decision owner and reviewed evidence/ADR or PR reference; **never treat a scanner result as approval**

AGPL is **not automatically forbidden**: use is permitted only after the applicable duties are explicitly assessed, any material conflict is resolved and the owner approves the risk decision. For material legal ambiguity, obtain qualified legal review before affected adoption, distribution or network service.

## Release review

- [ ] Direct and relevant transitive components/containers/assets inventoried; SBOM scope and blind spots recorded
- [ ] Copyright, License, Notice, redistribution and any corresponding-source/network obligations fulfilled
- [ ] AGPL components, if any, have explicit section-13/network/combined-work applicability and compatible-obligations review with recorded outcome
- [ ] Unknown, conflicting or commercially restricted items blocked until resolved for the affected release
- [ ] High-risk ambiguity reviewed by qualified legal counsel and the owner; no unsupported licence-compatibility claim
- [ ] Product licensing and entitlement decisions remain separate from third-party rights

Record **evidence**, not a perpetual second source of truth for work status. If no third-party component is in scope, state N/A and why. Unchanged low-risk permissive dependencies need proportionate review, not mandatory legal sign-off on each PR.
