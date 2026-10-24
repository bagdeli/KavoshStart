Closes #

## What and why
<!-- 1–3 sentences. The issue holds the context; do not repeat it. -->

## Change risk
Risk: <!-- low | medium | high | critical -->
Capabilities: <!-- e.g. docs, public-api, ui, data, migration, security, deploy, release, governance -->
Rationale: <!-- Why this level; line/file count is not a risk classifier. -->

## How verified
<!-- Semantic check and affected tests, generated-change review, relevant rendered evidence only. For new/retired material requirements/tests cite the authoritative source/version/owner and unique integration risk or upstream-equivalent proof in the same Issue/Spec/PR. No extra receipt per inherited row. -->

## Acceptance mapping
<!-- For acceptance.mode=continuous: list AC-* IDs affected by this PR, or:
not-applicable: <specific reason>
-->

## Session handoff
- **Done:**
- **Remaining (as new issues):**
- **Decisions (ADR if architectural):**

## AI involvement
<!-- Agent and model, or "none". If an agent wrote code keep the trailer line below: it becomes part of the squash commit. -->
- Agent / model:
- Human reviewed the full diff: [ ]

Co-Authored-By: <Agent> <noreply@example.com>

## Checklist
- [ ] Change risk and affected capabilities are declared
- [ ] Change is coherent/reviewable; any generated or broad mechanical diff documents its generator and verification
- [ ] Searched for existing ownership before new code; material test/requirement changes have a scoped rationale when applicable
- [ ] API + UI consumer + tests changed together (if an API changed)
- [ ] If an actually distributed/network-used third-party component changed, its applicable license/NOTICE/source obligations are met; otherwise N/A (no lawyer, second signer or new inventory needed)
- [ ] Docs / ADR / runbook updated (if behaviour changed)
