# 0001 — GitHub is the single source of live state

- Status: accepted
- Deciders: bagdeli
- Evidence: anonymized audit of a large private project (details retained only in its private workspace)

## Context and problem
A large private project kept live status (current head, schema and active work references) across many Markdown files and long handoff issues. Every commit made part of it stale; agents starting on `main` could be routed to obsolete work.

## Considered options
1. Keep status files and validate them with a script.
2. Keep live state only in GitHub objects (issues, project, PRs, checks, releases); files hold stable knowledge only.

## Decision
Option 2. Prose validation cannot keep up with agent commit rates; GitHub objects are always current and queryable with `gh`.

## Consequences
- Good: no drift, small precise agent context (`gh issue view`).
- Bad: status is not visible offline in a clone — acceptable.

## Enforcement
Governance rules SRC-2, SRC-3, SRC-4 (layer P) and weekly health (layer H).
