# Plan: <feature>

## Approach
<Which existing owners are extended? Why no existing module fits, if a new one is added?>

## Data and contracts
<Tables and migrations (expand → migrate → contract), API changes, events.>

## UI
<If this change affects UI, identify the actor/task, route or local navigation, affected screens/states, content/fields/actions/operator settings, authoritative read/write source and authorization boundary. Reuse the selected package's pinned UI components/layout contracts when applicable, or the project's recorded custom UI contract; describe only page-specific differences.>
<Track materially unresolved design decisions, their owner and the dependent work they block. Scoped design completion is separate from package installation, rendered review, product acceptance and release. For no-UI, unchanged surfaces or a bounded text/style fix, keep this brief or N/A; no whole-product design freeze is required.>

## Tasks (each becomes a sub-issue, each ≤ one PR)
1.
2.

## Risks and rollout
<Feature flag? Backfill? Rollback?>
