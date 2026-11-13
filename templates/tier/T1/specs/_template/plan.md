# Plan: <feature>

## Approach
<Which existing owners are extended? Why no existing module fits, if a new one is added?>

## Data and contracts
<Tables and migrations (expand → migrate → contract), API changes, events.>

## UI
<If this change affects UI, identify the actor/task, route or local navigation, affected screens/states, content/fields/actions/operator settings, authoritative read/write source and authorization boundary. Reuse the selected package's pinned UI components/layout contracts when applicable, or the project's recorded custom UI contract; describe only page-specific differences.>
<Track materially unresolved design decisions, their owner and the dependent work they block. Scoped design completion is separate from package installation, rendered review, product acceptance and release. For no-UI, unchanged surfaces or a bounded text/style fix, keep this brief or N/A; no whole-product design freeze is required.>

<Only if this change actually needs a selected UI redesign or reference artifact: reuse the existing work item to clarify affected actor/task, route/state/navigation, source-of-truth permissions, selected UI contract and the smallest relevant fidelity evidence. A Product that explicitly selects human-approved image references records real decisions on those exact image versions; other Projects may use existing UI-2 machine comparison or authentic human review of rendered UI as applicable. No mandatory screenshot, separate source copy, approval form, independent reviewer, all-pages freeze, extra task, runner or CI gate for no-UI, small edits or unrelated engineering. Preserve valid existing evidence and revisit only genuinely affected references. This is optional design guidance until a separately approved versioned rule exists.>

## Tasks (reuse the existing Issue/Spec; split only independently meaningful work)
<Make a coherent plan. A small owner-operated change needs no sub-issue or extra PR just to fill this template; independent sub-issues are optional when their ownership and acceptance differ.>
1.
2.

## Risks and rollout
<Feature flag? Backfill? Rollback?>
