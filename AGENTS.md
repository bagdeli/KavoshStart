# AGENTS.md — KavoshStart

## Project
KavoshStart is the engineering standard for all Kavosh repositories: intake, classification, rules, templates and
reusable GitHub workflows. It contains no product code. It follows itself (tier T1, runtime none — see `kavosh.project.json`).
Using KavoshStart for another project? Read `START.md`, not this file.

## Repository map
```text
START.md                 agent protocol for product projects (NEW / ADOPT / UPGRADE / WORK)
intake/                  questionnaire, classification, manifest schema + example
standard/RULES.md        canonical rule list — every rule has ID, level, tiers and enforcement layer
standard/0*.md           explanations (Persian)
templates/common|tier|runtime   files copied into product repos by scripts/scaffold.py
templates/labels.json, rulesets/ settings applied by scripts/bootstrap-repo.sh (not copied)
scripts/portfolio_guard.py Layer O (daily via .github/workflows/kavosh-portfolio.yml; reuses layer P checks)
tooling/src/*.py         source of the reusable workflows' logic
tooling/templates/*.yml  workflow skeletons; tooling/build_workflows.py writes .github/workflows/kavosh-*.yml
decisions/ audits/ adoption/  ADRs, dated audits, adoption plans
```

## Commands
```bash
make check                          # everything self-check runs
python3 tooling/build_workflows.py  # after editing tooling/src or tooling/templates or the schema
python3 tooling/test_templates.py   # scaffold every tier×runtime and run governance on it (+ negative test)
```

## Rules for changing KavoshStart
- A rule change touches, in the same PR: `standard/RULES.md`, the explaining doc, the template, and the check that enforces it.
- Every MUST names its enforcement layer (A/P/M/G/H/S/O/R). R-only MUSTs are listed as human-enforced in RULES.md.
- Never edit `.github/workflows/kavosh-*.yml` by hand — edit `tooling/` and rebuild. Self-check fails on drift.
- Reusable workflow inputs and job names are the public API (`@v1`). Breaking them = major version.
- Workflow logic uses python3 stdlib + gh only; third-party actions are pinned by SHA.
- Templates must pass `tooling/test_templates.py`. Placeholders: `{{NAME}}` style, defined in `scripts/scaffold.py`.
- Persian for explanations (`standard/`, `README.md`), English for anything agents execute (`START.md`, templates, ADRs).

## Boundaries
**Never:** push to `main` · merge · run `bootstrap-repo.sh --apply` or any GitHub-mutating command against another repository
without the owner's explicit request · put live status (SHAs, current issue numbers) in files.
**Ask first:** changing default limits or tier budgets · renaming workflow jobs or inputs · deleting a rule.
