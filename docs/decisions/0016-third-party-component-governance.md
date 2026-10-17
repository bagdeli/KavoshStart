# 0016 — Risk-based third-party component policy

- Status: accepted
- Deciders: repository owner
- Tracking: issue #141
- Rules: TP-1 / TP-2, standard/15-third-party-components.md

## Decision

Favor mature third-party components over custom implementation when total ownership cost, security, support, maintainability and legal rights justify them. No blanket GPL/AGPL ban. Classify specific licence identifiers and compatibility using the *actual combination, modifications, distribution and relevant network-use terms*. Separate code libraries, build-only tools, independent services, fonts, assets, container layers, data and commercial contracts.

Apply a lightweight record to unchanged low-risk clearly licensed dependencies; use deeper diligence for modified copyleft, commercial/redistributed or network-obligation components. For any commercial release or relevant network offering, produce an output-scoped component inventory/SBOM and fulfil License/NOTICE/source/relinking and redistribution obligations. Unknown or conflicting material rights block only the affected delivery component until cleared. Qualified legal and owner decision is required for material ambiguity.

Product code licence, third-party component rights and product licensing/entitlement are distinct. Never publish consuming private-project inventory into this public standard.

## Enforcement boundary

TP-1 and TP-2 are explicit **human review** controls, not claims of automatic legal interpretation. PR checklists and a blank per-repository inventory template provide the operational hook. Machine tooling can detect missing metadata but cannot warrant licence compatibility or certify legal compliance.
