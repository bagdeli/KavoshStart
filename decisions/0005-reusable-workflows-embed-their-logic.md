# 0005 — Reusable workflows embed their logic; floating major tag

- Status: accepted
- Deciders: bagdeli

## Context and problem
A reusable workflow from private KavoshStart runs with the caller repository's token, which cannot read KavoshStart files.

## Decision
Logic lives in `tooling/src/*.py` (testable) and is embedded into `.github/workflows/kavosh-*.yml` by
`tooling/build_workflows.py`; self-check fails if generated files are stale. Product repositories call `@v1`, a tag moved
by the release workflow to the newest v1.x.y; the exact version each project follows is recorded in `kavosh.project.json`.

## Enforcement
`make lint` → `build_workflows.py --check`.
