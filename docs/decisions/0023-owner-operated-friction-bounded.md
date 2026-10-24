# ADR-0023 — Optional formal team ceremony, fast owner-operated development

- **Status:** proposed; not an accepted migration or a released standard version
- **Decision authority:** standard owner; a merge and a published major are separate
- **Scope:** generic standards only, no details of any specific consumer or host

## Problem

v8 owner-operated acceptance removed mandatory attestation/reviewer infrastructure, but the current PR policy still returns FAIL for owner-only process metadata (branch naming, artificial Issue links, Conventional Commit title, risk/AI form text, breaking-ADR document and shallow-stack rule). The CI runner defaults also require a new custom label even when a private registered runner already has platform-supplied `self-hosted/linux/x64` labels. These fail-to-green requirements do not establish runtime safety; they can delay small jobs in disposable TEST work.

## Proposed design

- `review.teamProcess` is an **optional** boolean in the existing manifest `review` object. It defaults to false and **does not infer team membership from visibility, Tier, domain count or risk**. A collaborative team can explicitly opt into the existing structured PR conventions by setting true, independently of choosing a second reviewer.
- In owner-operated mode, formal ceremony is advisory, while a Ready human PR still needs real change context. Explicit understatements of sensitive source risk fail in every profile, including when other form fields are absent. Do not create Issue/Spec/extra PR merely to fill in a template. Real false attribution is not excused, and source/required CI, secret boundaries, exact-source release and non-bypassed protection rules still apply.
- For private owner-operated self-hosted CI, existing platform labels `self-hosted`, OS and architecture can route a real runner without registering a new custom label or provisioning another VM. Public or explicitly formal team profiles retain a custom selector. Route matching remains exact; static labels are not proof of isolation, host security or access restrictions.
- A disposable non-Production custom TEST adapter needs no document-specific ADR; actual installed release/source identity and health cannot be invented. A selected Production environment and an explicitly selected/claimed ADR retain the existing validation. UI customizations without a chosen Design System do not create a solo-owner ADR obligation, but real accessibility/licensing needs remain.
- Retain owner-only prior approval for metered private GitHub-hosted use, and existing explicit high-risk/Production/release decisions. No consumer hosts, secrets, service accounts or configured checks are changed by this proposal.

## Balanced implementation boundaries

A scoped outcome, existing canonical implementation owner, focused verification and truthful handoff remain the core.
Multi-step work uses a short plan in the existing record. No speculative service, duplicate data writer or silent fallback
is authorized by switching off team forms. Formatting caps are advisory for owner-led work; selected team rules remain.

Core unit/schema/generated-workflow/scaffold checks run on every executing required job. Only an exact documentation-only
PR diff omits cross-domain conformance. Source/workflow/dependency changes, unknown diffs, main integration and trusted
release verification keep full tests. Manual core-only runs explicitly say conformance NOT_RUN. No required job is replaced
with a success stub, and no private hosted dispatch is introduced.

Scaffolding keeps core project facts and guards, but omits unselected team forms/Specs and custom adapter infrastructure.
An absent applicable test/build target remains fail-closed; N/A requires a real scoped reason. The obsolete Runner installer
is removed, portfolio scheduling becomes explicit, and branch cleanup changes from deny to ask without allowing protected
branch deletion or credential use. Historical tags, selected continuous evidence and published contracts stay unchanged.

## Compatibility and verification

This alters default governance failure outcomes and private runner selection. It is a **breaking** semantics change: publish only after genuine PR governance, required CI, test scaffolding, and owner authorization for a new major; current consumers pinned to older releases stay unchanged. Document all versioned caller changes in the selected consumer's own PR. Positive/negative regressions must distinguish owner-operated from explicitly selected team process, and fail an actually invalid trust/release boundary in either mode.
