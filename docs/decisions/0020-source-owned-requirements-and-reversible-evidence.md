# 0020 — Source-owned requirements, proportionate verification, reversible test obligations

- Status: proposed for owner-reviewed high-risk policy PR
- Tracking: issue #159
- Rules: existing CR-3, CR-4; intake G6/G9, TP-1/TP-2, ACC acceptance
- Scope: future new/changed product requirements/tests and review of inherited historical obligations
- Compatibility: no new rule ID, automated workflow, manifest key, receipt type or mandatory infrastructure

## Context

Consumer products have repeatedly recertified mature dependency internals while their own integrations and actual user journeys received insufficient attention. Requirements should not become irrevocable simply because an agent wrote them, nor should removing an unnecessary test require weeks of repeated runs. At the same time, upstream test quality never proves a consumer's customized trust or composition boundary.

## Decision

1. Identify the user outcome/risk, authoritative contract owner and version before proposing a new material requirement/test. Inherited native/upstream behavior is not duplicated by default. Focus on actual product logic, extension/integration and exposed trust boundaries.
2. Choose the smallest honest evidence at its lifecycle decision. PR fast checks, candidate integration/UX, release safety, operational acceptance and later deep assurance are different moments. Do not require every specialized suite for every PR.
3. A historical requirement/test is reviewable: keep, narrow, merge or retire it when an affected owner can demonstrate duplication, obsolete source/version, no longer in scope or no real invariant. Make one reviewable decision in its existing Issue/Spec/PR and change affected contract/scope/tests together, with historical evidence preserved.
4. No automatic deletion of a true defect, financial/security/data obligations, red required check, independently authorized high-risk decision or release gate. Source-bound acceptance still requires actual proof where the product owns a claim; never claim a missing test is PASS.
5. Select controls by practical risk reduction and real cost. For example, an existing bounded and correctly isolated self-hosted CI server may meet a consumer need without a universal demand for disposable VMs, while network firewall alone does not block local host/socket exposure. Risk acceptance requires appropriate human authority and real operational truth; percentages like 98/99 cannot be claimed from intuition.
6. Older pinned consumers are unchanged until a separate exact-tag, authorized upgrade. Migrate only materially changed contract axes and actual release outcomes, not thousands of historical rows.

## Enforcement and limits

This is an existing CR-3/CR-4 human-review/source-ownership clarification. The existing machine checks continue to enforce real required test success and source-bound evidence; static CI cannot certify the economic value of a proposed requirement. The companion focused documentation test checks that intake and agent guidance remain consistent, not that all future requirements are correct. No generic new workflow is introduced.

## Migration

Use the versioned direct-upgrade guide published with the future accepted policy; until then do not pin a planned release or silently upgrade private consumers.
