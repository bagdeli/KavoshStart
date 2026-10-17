# 0017 — Vendor-neutral UI contract for a public standard

- Status: accepted
- Deciders: repository owner
- Tracking: issue #141

## Decision

Public KavoshStart no longer names or links to private consumer repositories or private UI providers. Each consumer chooses `ui.designSystem: {package, version}`; `null` is permitted when the project has no UI or an appropriately reviewed UI exception ADR applies. Exact pinning, RTL, accessibility, consumer compatibility and observed render review remain governed by UI-1/2/3.

This is a **breaking schema change** combined with the separately approved private GitHub-hosted-only runner policy. Consumers require a versioned, separately authorized upgrade after publication of a major release, not an automatic rewrite from the public standard. No private project mutations are part of this ADR.

## Limits and evidence

Canonical schema, scaffold, governance, templates, synthetic examples, generated workflows and tests must agree. A forward-only PR removes current-tree references but does **not erase Git history**; rewriting immutable history would break release provenance and requires separate security/owner approval. Historical names alone are not evidence of leaked credentials.
