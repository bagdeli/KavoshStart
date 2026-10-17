# 0016 — Risk-based third-party component policy

- Status: accepted
- Deciders: repository owner
- Tracking: issue #141
- Rules: TP-1 / TP-2, standard/15-third-party-components.md

## Decision

Favor mature third-party components over custom implementation when total ownership cost, security, support, maintainability and legal rights justify them. No blanket GPL/AGPL ban. Classify specific licence identifiers and compatibility using the *actual combination, modifications, distribution and relevant network-use terms*. Separate code libraries, build-only tools, independent services, fonts, assets, container layers, data and commercial contracts.

Apply a lightweight record to unchanged low-risk clearly licensed dependencies; use deeper diligence for modified copyleft, commercial/redistributed or network-obligation components. For any commercial release or relevant network offering, produce an output-scoped component inventory/SBOM and fulfil License/NOTICE/source/relinking and redistribution obligations. Unknown or conflicting material rights block only the affected delivery component until cleared. Qualified legal and owner decision is required for material ambiguity.

Product code licence, third-party component rights and product licensing/entitlement are distinct. Never publish consuming private-project inventory into this public standard.

## Clarification — conditional AGPL acceptance

The policy **expressly permits** AGPL-3.0-only/-or-later when the consumer documents the actual software combination, modifications, distribution, network interaction (AGPLv3 section 13 where applicable), corresponding-source and notice delivery, and shows that all triggered duties can be fulfilled **without an unresolved licence or contract conflict**. AGPL detection is not an automatic ban or an automatic approval. Record the component-specific decision as `approved`, `blocked` or `needs-legal-review`; seek qualified legal and owner review for material ambiguity. This clarification preserves the original risk-proportionate TP-1/TP-2 human review boundary and creates no automated licence-compatibility certification.

## Enforcement boundary

TP-1 and TP-2 are explicit **human review** controls, not claims of automatic legal interpretation. PR checklists and a blank per-repository inventory template provide the operational hook. Machine tooling can detect missing metadata but cannot warrant licence compatibility or certify legal compliance.
