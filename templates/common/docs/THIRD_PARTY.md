# Third-party component compliance — release-scoped inventory

**OPTIONAL — not installed by default.** Select this blank inventory only if the owner actually ships a material third-party component with nontrivial distribution/network obligations, or deliberately chooses a team compliance register. It is not legal approval, a required second sign-off or a checklist for unchanged low-risk libraries. Keep records only in the consumer repository.

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

AGPL is **not automatically forbidden**: use is permitted only after the applicable duties are explicitly assessed, any material conflict is resolved and the owner approves the risk decision. For material unresolved ambiguity, stop the **affected** adoption/distribution until documented terms, an architecture/license change or **optional qualified legal review** resolves it. No automatic outside lawyer or second human approver.

## Release review

- [ ] Direct and relevant transitive components/containers/assets inventoried; SBOM scope and blind spots recorded
- [ ] Copyright, License, Notice, redistribution and any corresponding-source/network obligations fulfilled
- [ ] AGPL components, if any, have explicit section-13/network/combined-work applicability and compatible-obligations review with recorded outcome
- [ ] Unknown, conflicting or commercially restricted items blocked until resolved for the affected release
- [ ] High-risk ambiguity actually resolved with authoritative terms, a compatible route or optional specialist advice selected by the owner; unresolved use stays blocked, not the entire project
- [ ] Product licensing and entitlement decisions remain separate from third-party rights

Record **evidence**, not a perpetual second source of truth for work status. If no third-party component is in scope, state N/A and why. Unchanged low-risk permissive dependencies need proportionate review, not mandatory legal sign-off on each PR.
