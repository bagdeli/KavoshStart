# Spec: <feature>

- Issue: #<n> · Status: draft | approved

## Problem
<Who has which problem? Why now?>

## User stories
- As a <role>, I want <capability>, so that <benefit>.

## Architecture decisions used
<Reference relevant settled choices in PROJECT.md#architecture-decisions or the existing ADR. Reuse unchanged answers. Identify only decisions this capability changes. Do not copy the entire project questionnaire.>

## Acceptance criteria
- [ ] Given … when … then …

## Evidence plan
For each material criterion identify its user/risk purpose, source/version and actual owner: native/upstream, consumer integration or product logic. Reuse supported upstream internal guarantees instead of mirroring their test suite; add the smallest real consumer check for affected composition, authorization, data, locale and UX. An old duplicated/stale/out-of-scope criterion may be retired through the same owning Issue/PR/Spec with reviewed risk, relevant test adjustment and preserved history; never hide a required FAIL. No extra evidence tracker or receipt per inherited platform row.

<For each actual criterion, name its test/assertion or proportionate review method and where its observed result will be linked. Reuse shared evidence with traceability. This is a plan, not a pass, a receipt or human approval. Close evidence with the capability, not a separate routine telemetry PR.>

## Out of scope
<Include explicitly not-needed capabilities; do not create tasks or receipts for them.>

## Open questions
- [ ] <question> — owner: @<who>; dependent work: <scope>; needed before: <decision point>.

Only dependent implementation is blocked by an unresolved architecture choice. Unrelated authorized work can continue; never silently convert an unanswered question into a default.
