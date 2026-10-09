# ADR 0010 — KavoshStart self-hosting identity

## Status

Accepted.

## Context

Consumer repositories need an immutable, exact KavoshStart release tag so reusable workflows, rules and templates are reproducible. That is the meaning of `kavosh.project.json.kavoshStart = vX.Y.Z`.

The canonical KavoshStart repository is different: while developing and testing itself it executes the checked-out source and local reusable workflows. Making that repository claim it follows its previous release is stale immediately after the next release. Making release-please rewrite the same field would also overload a consumer tag pin as a self-version field and couples repository identity to release-file mutation.

The distinction must be explicit so humans and agents never infer that a consumer may follow an unreleased KavoshStart branch or that KavoshStart itself is governed by an older release.

## Decision

Reserve the manifest value `kavoshStart: "self"` exclusively for the canonical repository `bagdeli/KavoshStart`.

- The canonical standard repository uses `self` and local workflow references while testing its own source.
- Every other repository must use an exact stable release tag `vX.Y.Z`.
- Governance fails if a consumer uses `self`.
- Governance fails if the canonical KavoshStart repository uses a release tag instead of `self`.
- Scaffold fails before rendering if a consumer manifest contains `self`.
- Health freshness compares consumer pins with the latest stable release; it does not compare the self-hosting repository against itself.
- Release Please owns release versions, CHANGELOG, tags and GitHub Releases, but does not rewrite the self-hosting identity field.

## Consequences

The manifest field has one unambiguous meaning in each context: exact immutable dependency for consumers, current checked-out canonical source for the standard itself. A KavoshStart release can therefore contain `kavoshStart: "self"` without becoming stale in the next release.

The schema permits the sentinel so generic JSON/schema tooling can parse the canonical repository, while repository-aware governance enforces that no consumer can use it.

No consumer workflow may reference `@self`; REL-6 continues to require exact release tags for all consumers.
