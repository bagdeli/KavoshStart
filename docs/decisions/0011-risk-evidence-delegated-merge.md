# 0011 — Risk-based governance, continuation semantics and delegated merge

- Status: accepted
- Deciders: bagdeli
- Issue: bagdeli/KavoshStart#72
- Supersedes in part: ADR-0009 merge-authorization assumptions and universal size-exception language

## Context

KavoshStart 1.x improved lifecycle and acceptance enforcement, but several controls were still tied to implementation choices or universal numeric thresholds. In particular, PR line/file caps could force coherent changes into artificial stacks, release and command rules named specific tools, and every agent merge depended on a separate owner merge authorization. A conversational instruction such as “continue” could also be misread as approval of an earlier incomplete outcome.

The standard must apply across different project types and remain enforceable as agents, stacks and GitHub capabilities change.

## Decision

1. Project Tier and Change Risk are independent axes. Every non-bot PR declares low/medium/high/critical risk and affected capabilities.
2. Diff size is telemetry, not a universal merge gate. Split decisions are based on coherence, independent testability, reviewability and risk.
3. Continue, Accept, Merge, Release and Production are distinct authorities. Generic continuation never grants the later boundaries.
4. Low/medium-risk PRs may be mechanically Squash-merged by an agent after exact-head gates are green and blockers/review threads are clear.
5. High/critical, control-plane, security/trust-boundary, destructive-data and release-policy changes require an explicit human decision for the current scope first; after that decision the merge action itself may be delegated.
6. When agent and human share one GitHub identity/credential, a label/comment created through that identity is not claimed as cryptographic proof of human intent. Human authorization remains a real R/A trust boundary.
7. Core governance specifies outcomes. Make and release-please remain scaffold defaults, not universal invariants; equivalent adapters/strategies may be used when they preserve the same safety gates.
8. GitHub plan, billing and quota are portfolio/account policy overlays. They do not define software-quality invariants.
9. Every newly discovered defect asks why the existing gate missed it; the fix updates the contract or detector plus regression coverage when feasible.

## Consequences

- Large generated/mechanical or coherent changes no longer fail solely on line/file counts.
- Small changes can still be high/critical risk.
- The owner is no longer the mechanical merge bottleneck for routine green low/medium changes.
- Human attention is reserved for actual trust/risk decisions rather than the Merge button.
- Existing consumers remain pinned to their exact 1.x version until a dedicated v2 upgrade PR changes their manifest/workflow contract.
- Downstream release strategies such as Changesets can conform without pretending to use release-please.

## Enforcement

`standard/RULES.md` CR/FLOW/PR/REL/CI rules, `START.md`, the common agent and PR templates, `tooling/src/governance.py`, generated reusable workflows and offline positive/negative tests form one contract.

Breaking control-plane changes must themselves include an ADR in the same PR so architecture cannot silently change through prose/code alone.
