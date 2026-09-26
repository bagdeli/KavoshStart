# 0006 — Exact version pins for KavoshStart workflows; frozen `v1`

- Status: accepted (supersedes the floating-tag part of 0005)
- Deciders: bagdeli
- Issue: bagdeli/KavoshStart#2

## Context and problem
Product repositories called `@v1`, a tag moved on every release, while their manifest claimed an exact version.
Runtime behaviour could change without a PR in the product repository, and a tag ruleset (immutable `v*`) would
conflict with moving it. `v1` was also created before any green CI (see 0007 / REL-5).

## Decision
- Callers use `bagdeli/KavoshStart/.github/workflows/<name>.yml@vX.Y.Z`, equal to `kavosh.project.json` → `kavoshStart` (REL-6).
- Dependabot (`github-actions` ecosystem) proposes upgrades of these refs as PRs; the upgrade PR also updates the manifest.
- The tag `v1` is frozen: never moved again, never referenced; deleted once Layer O confirms no consumer uses it.
- Release workflows never force-move tags.

## Consequences
- Good: reproducible behaviour per project; upgrades are reviewed; compatible with immutable tag rulesets.
- Bad: every KavoshStart release produces one PR per product repository.

## Enforcement
Governance check of ref vs manifest (#6), Layer O portfolio check (#4), `kavosh-release` has no tag-moving step.
