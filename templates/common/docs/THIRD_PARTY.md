# Third-party component compliance — release-scoped inventory

Apply the upstream KavoshStart **TP-1/TP-2** policy before selecting a material component and before commercial distribution. This document is a **blank reusable template**, not a claim of licence approval. Keep real inventory and evidence only in the consuming repository.

Use an SBOM (SPDX/CycloneDX) appropriate for each release output and separately account for packaged images, fonts, assets, models, data and components missed by tooling. Link immutable release-specific evidence; do not store live backlog/status here.

| Component + exact version | Upstream / verified source | SPDX expression or contract | Use / linking / packaging / network / modifications | Distribution or network obligations (License / NOTICE / source / relinking) | Security + TCO rationale | Decision owner + review/evidence reference |
|---|---|---|---|---|---|---|
| (add only when applicable) | | | | | | |

## Release review

- [ ] Direct and relevant transitive components/containers/assets inventoried; SBOM scope and blind spots recorded
- [ ] Copyright, License, Notice, redistribution and any corresponding-source/network obligations fulfilled
- [ ] Unknown, conflicting or commercially restricted items blocked until resolved for the affected release
- [ ] High-risk ambiguity reviewed by qualified legal counsel and the owner; no unsupported licence-compatibility claim
- [ ] Product licensing and entitlement decisions remain separate from third-party rights

Record **evidence**, not a perpetual second source of truth for work status. If no third-party component is in scope, state N/A and why. Unchanged low-risk permissive dependencies need proportionate review, not mandatory legal sign-off on each PR.
