## What and why
<!-- 1–3 sentences about the actual change and scope. Link an existing Issue when relevant; use Closes only for real completion. No artificial Issue needed. -->

<!-- Record actual sensitive risk and its scoped owner decision whenever applicable. Formal risk metadata is required for the selected team process only; use real capability IDs and never understate risk.
Risk: low|medium|high|critical
Capabilities: affected capabilities
Rationale: why this level; line/file count is not a risk classifier.
-->

## How verified
<!-- Semantic check and affected tests, generated-change review, relevant rendered evidence only. For new/retired material requirements/tests cite the authoritative source/version/owner and unique integration risk or upstream-equivalent proof in the same Issue/Spec/PR. No extra receipt per inherited row. -->

## Acceptance mapping
<!-- For acceptance.mode=continuous: list AC-* IDs affected by this PR, or:
not-applicable: <specific reason>
-->

## Session handoff
- **Done:**
- **Remaining (same work record; new Issue only for independent, unowned work):**
- **Decisions (ADR if architectural):**

<!-- Formal team-process AI section when selected; otherwise genuine attribution may be recorded without this form. Never claim a human review that did not happen or leave a placeholder trailer in the submitted PR.
## AI involvement
- Agent / model: actual agent and model, or none
Co-Authored-By: Name <real@example.invalid> (only for genuine agent work)
-->

## Checklist (applicable items only)
- [ ] Actual risk and necessary owner decisions are recorded; formal fields only where applicable
- [ ] Change is coherent/reviewable; any generated or broad mechanical diff documents its generator and verification
- [ ] Searched for existing ownership before new code; material test/requirement changes have a scoped rationale when applicable
- [ ] Affected callers and tests are consistent (if a contract changed)
- [ ] Third-party changes reviewed for risk, licence/NOTICE and distribution/network obligations (TP-1/TP-2; N/A with reason if none)
- [ ] Docs / ADR / runbook updated (if behaviour changed)
