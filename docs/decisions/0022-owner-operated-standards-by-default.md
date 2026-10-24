# ADR 0022 — Owner-operated delivery by default; team assurance only by consent

## Status
Accepted and published in KavoshStart v8.0.0. Any further source corrections require their own reviewed PR/release; no consumer is auto-upgraded.

## Context
Project complexity, data sensitivity and repository tier do **not** measure how many humans manage delivery. A single owner may operate a complex T2 project without another person, a second model, dedicated App attestors, external counsel, a new Test VM or a second host. Defaulting to enterprise assurance creates uninstalled dependencies and release deadlocks rather than stronger real evidence.

The public standard remains independent of all consumer project identities and incidents. Historical ADRs about attested continuous acceptance and special trust profiles remain true **for the releases that adopted them**.

## Decision
- **Intake first, no extra form:** use existing D3/G9 decisions to learn whether the project is sole-owner or an actual sizeable team and ask **yes/no** to an independent human reviewer, continuous acceptance/App attestation, outside legal specialist, and dedicated Test capacity. Solo defaults are NO. Reuse previous explicit decisions.
- **Native owner-operated profile:** `acceptance.mode=none` is valid at T0/T1/T2 and does not generate an AC register, external publisher App or extra approvals. Existing required CI/checks and the owner's genuine risk/release decisions remain. No claimed CI or environment PASS may be inferred from the profile.
- **Team-only opt-in:** `review.independentHumanReview=true` is elective for sizeable collaborating teams. Continuous acceptance is likewise elective; it must explicitly select `assurance` and document real producer identity, credential boundaries and operational cost. In the currently selected attested protocol evidence/decision are different *technical* App identities; that is not two persons and is never imposed merely by T2.
- **UI:** the solo owner's actual visual judgement is valid when applicable, without an automatic second-person GitHub APPROVED review or expensive screenshot suite. An AI model does not impersonate the owner. In opted-in team review, the existing exact-head reviewer/actual comparison verifier remains authoritative.
- **Licences:** actual copyright, notice, source, network and contractual duties are not optional. The owner may elect counsel for unresolved material ambiguity but the public standard does not assume an outside lawyer or demand signatures per package. If duties remain genuinely incompatible, stop **that affected use/distribution** until resolved.
- **Test/CI:** an available restricted non-root self-hosted account on an owner-approved existing host can suffice. A separate physical server, VM, dedicated new Runner or ADR document is optional; never expose production credentials/root-equivalent capabilities to untrusted PR code.
- **Delivery efficiency:** no new global workflow, rule engine, second evidence ledger, review form, arbitrary per-PR heavy test or repeated upstream suite. Existing focused validators protect actual trust boundaries. Optional unused templates are not installed automatically.

## Consequences and compat
The T2 mandatory continuous profile, review-gate activation and scaffold defaults are deliberately **breaking**. Introduce only through a reviewed major-version Release PR after real required/governance checks. Previously published exact tags, attested consumers and signed evidence remain unchanged. Migration of an already opted-in consumer requires its own owner decision and source-scoped upgrade PR, preserving honest failures and irreversible duties.

This change neither issues legal advice for a specific product nor waives any applicable licence or owner authorization. It creates no service, App, new Runner, second reviewer or consumer change.

## Proportional upstream maintenance follow-up (under review)

Routine, well-understood upstream component maintenance is not automatically a product release or new deployment subsystem. Requiring a new physical Test environment, new timer/VM, another App, a new Issue per intermediate result, a fresh database-restore rehearsal and a new KavoshStart upgrade merely because an upstream version appeared conflicts with owner-operated delivery. Keep native component-version/health checks and the actual affected integration tests, but **never** waive a real failed required CI check, changed product source provenance or backup recovery when durable data is actually at risk.

If a project actually executes a high-risk/destructive migration, it must verify recovery and obtain current owner authorization; an unchanged low-risk/native update needs no performative fresh restore test. This refinement is not retroactively applied to consumers pinned to older releases.
