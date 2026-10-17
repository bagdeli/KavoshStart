# START.md — agent protocol
> **Private GitHub repositories — ADR-0018:** no GitHub Actions runners/jobs, hosted **or** self-hosted, under any circumstances. The AI supplies instructions only. The owner executes tests and `git`/`gh` commands on a trusted GitHub-connected machine, with genuine exit codes and source hashes. Disable Actions at repository settings **before** any PR/push with legacy workflow files.


You are an AI agent asked to create, adopt or maintain a Kavosh project "using KavoshStart".
Follow this protocol exactly. Rules are referenced by ID (e.g. `BR-1`); their canonical list is
[`standard/RULES.md`](standard/RULES.md). When this file and a rule disagree, the rule wins — report the conflict.

## Network transfer failure — per-project operator escalation

For a download or upload that fails repeatedly (normally no more than three bounded attempts for transient errors), **stop retrying that endpoint** and report the exact blocker to the owner. Do not silently introduce a relay, proxy, alternate registry, paid service, DNS override, TLS bypass, credential, or global infrastructure task. If the URL was never attempted, do not invent an outage.

Give a compact, operator-actionable report from the **environment where the transfer failed**:
- operation (download/upload), requested artifact and source environment, sanitized URL (`scheme://host[:port]/safe-path`, **without userinfo, query, fragment, signed tokens or secrets**), hostname/DNS name, port;
- the IP addresses resolved **from that environment** (IPv4/IPv6, with observation time/source), or exactly `IP unknown — DNS resolution failed/not checked`; never guess an IP or reuse one from another environment;
- observed failure category (DNS, timeout, TCP/TLS, HTTP status, authorization, rate limit, missing artifact), failed attempt count, and whether the failure is transient or reproducible;
- the smallest unblock request (host/domain/IP/port/protocol), distinguishing a routing/firewall failure from HTTP 401/403/404, expired token or certificate errors. CDN IPs can change; prefer domain-level diagnosis when appropriate.

Use existing logs or `python3 <KavoshStart>/scripts/network_failure_report.py --url 'https://host.example/' --operation download|upload --attempts N --reason <code>` **locally** for safe DNS/IP observations. **Sanitize URL before putting it in a command or log** (raw signed links may leak through process arguments or shell history); this optional read-only helper performs name resolution only, without download, upload or persistent state. Never paste signed URLs, headers, access tokens or private environment endpoints into public KavoshStart Issues/PRs. For private projects, report only in their private conversation/repository. A response from the owner that changes connectivity authorizes only the named unblock action, not a new platform dependency.

## §0 Session bootstrap — every conversation/session

Before choosing NEW / ADOPT / UPGRADE / WORK:
1. Verify the exact repository, default branch, workspace/remote when available, approved environments and task scope. Never infer authority from access.
2. Read the project's root `AGENTS.md`, `kavosh.project.json`, `PROJECT.md` architecture decisions, and the selected Issue/Spec/plan. Reuse settled answers and their recorded scope; ask again only for a missing or materially changed decision. Treat old reports as provenance, not live status.
3. For a consumer project, read its exact `kavoshStart: vX.Y.Z`, query the latest stable KavoshStart Release, and compare them. If behind, read the CHANGELOG between the pin and latest. The reserved value `self` is valid only when the repository is exactly `bagdeli/KavoshStart`; there it means the checked-out canonical source and is never used as a workflow ref.
4. If the newer release changes governance, acceptance, security, release, deploy, CI or agent-control semantics, perform UPGRADE before starting a new feature/gate packet unless the owner has recorded a bounded, traceable defer. Never silently auto-upgrade a dependency in the middle of unrelated work.
5. For T2 on this standard, `acceptance.mode=continuous` is mandatory and `adoptionPhase: true` is invalid. Do not continue ordinary feature work by treating report-only governance as success.
6. Refresh only the moving facts needed for the task: current `main`, related open PRs/checks/releases and, when runtime behavior matters, exact deployed version/SHA/schema/health. Do not turn routine continuation into an unrelated full audit.
7. Choose the mode below and complete one coherent packet. A genuine hotfix may proceed with an owner-approved bounded standard-upgrade defer, recorded in GitHub with its expiry/review trigger.

Pick the mode:

| Mode | Trigger | Go to |
|---|---|---|
| **NEW** | "build / create project X" | §1 |
| **ADOPT** | "bring existing repo X under KavoshStart" | §2 |
| **UPGRADE** | "update X to KavoshStart vN / its selected design-system package" | §3 |
| **WORK** | "implement issue #n in X" (project already adopted) | §4 |

Never skip a step. Never invent an answer the owner has not given — ask.

---

## §1 NEW project

### Step 1 — Intake
1. Read [`intake/QUESTIONNAIRE.md`](intake/QUESTIONNAIRE.md).
2. Reuse explicit project answers and approved applicable defaults from their recorded source. Review A–F facts
   and G1–G9 architecture decisions, including product licensing, for every new project. Ask only missing
   decisions in one grouped Persian message. Suggestions are not accepted defaults; internal use does not
   imply no licensing, no login or unrestricted data access.
3. Decide applicability first: selected, explicitly not-needed, or inherited from an approved reference.
   Keep unresolved questions in the selected Issue/Spec with the owner and dependent work. Block only
   dependent implementation; unrelated authorized work may continue. Do not claim architecture completion
   while shaping decisions are unresolved. Required identity/scaffold inputs must be known before scaffolding.

### Step 2 — Classify
1. Apply [`intake/CLASSIFICATION.md`](intake/CLASSIFICATION.md) mechanically to get **Tier** (T0/T1/T2),
   **Runtime** (none/static/server/desktop), and the minimum derivable **Capabilities**. Show the owner which facts triggered the Tier/Runtime and which capabilities were derived; ask only for additional non-derivable capabilities such as infrastructure/control-plane.
2. Explain the absolute **private local-only** boundary (ADR-0018): no GitHub Actions whatsoever,
   hosted or self-hosted, for any private Tier/Runtime. Set `ci.runner=none`, budget 0; no workflow
   files or runner metadata. AI supplies commands only; the owner executes them on a trusted GitHub-connected
   workstation. The owner disables Actions in GitHub settings before any push/PR that could trigger old
   workflows. Public CI retains its separate reviewed runner/cost policy.
   Before selecting any material third-party component, apply `standard/15-third-party-components.md`.
   Record risk-sized licence, distribution, security and total-ownership-cost decisions in the consumer project.
3. The owner confirms or overrides. An override is recorded later as an ADR in the new repo.

### Step 3 — Manifest
1. Write `kavosh.project.json` conforming to [`intake/kavosh.project.schema.json`](intake/kavosh.project.schema.json).
   Pin `kavoshStart` to the latest KavoshStart release tag (`gh release view -R bagdeli/KavoshStart --json tagName`). Never copy the illustrative `vX.Y.Z` from the example and never use the reserved `self` value in a consumer project.
   For a UI project, record its selected exact package and version under `ui.designSystem`, or a scoped `ui.exceptionADR`.
   Never publish consumer-private package names, URLs or evidence in public KavoshStart.
2. For a new T2 project set `acceptance.mode: continuous` as required by ACC-1; T0/T1 may opt in. Plan source-bound assertions and the availability of real admitted evidence/decision producers from `templates/tier/T2/acceptance/README.md` before promising delivery. Missing producer setup is a visible prerequisite, not a marker-only workaround or permission to create a new service by default.
3. Write `PROJECT.md` from `templates/common/PROJECT.md` — compact, Persian, no live status. Its architecture-decision table records settled G1–G9 choices/source references; detailed rationale and unresolved questions stay in the existing Spec/Issue. Do not add unsupported manifest keys or a parallel decision tracker.
4. Show both to the owner. Continue only after confirmation.

### Step 4 — Repository and scaffold
1. If the repository does not exist, **ask** the owner before creating it (`gh repo create bagdeli/<repo> --private`).
2. Clone it, put `kavosh.project.json` at the root, then run:
   ```bash
   python3 <KavoshStart>/scripts/scaffold.py <path-to-repo>
   ```
   The script copies `templates/common` + `templates/tier/<Tier>` + `templates/runtime/<Runtime>` (if present),
   fills placeholders from the manifest and refuses to overwrite existing files.
3. Replace every remaining `TODO(kavosh)` marker. Create the project code skeleton for the chosen stack and make
   the **command contract** work (`make setup | lint | test | build | check`, rule `CI-8`).
4. If `ui.kind` is not `none`: follow [`standard/10-design-systems.md`](standard/10-design-systems.md).
   Select an appropriate existing versioned design-system package in the **consumer repository** and comply with its licence/consumer contract; do not copy components without authority.
5. `make check` must pass locally.
6. First commit directly on `main` is allowed **only** for this initial scaffold of an empty repository:
   `chore: scaffold from KavoshStart <version>` with the agent `Co-Authored-By` trailer. Everything after it goes through PRs.
7. Run `bash <KavoshStart>/scripts/bootstrap-repo.sh bagdeli/<repo>` (dry-run), show the output, and run it
   with `--apply` only after the owner agrees. Then `bash scripts/install-agent-guards.sh` inside the repo.
8. **Private execution (CI-1):** for every private repository and any Tier/Runtime, select `ci.runner=none`,
   `monthlyMinutesBudget=0`. No GitHub Actions YAML, GitHub-hosted, self-hosted, ARC, reusable call or
   dispatch is ever used. The agent supplies an explicit command list only; the **owner** uses local `make
   check`, targeted tests and `git`/`gh` commands on an authorized GitHub-connected workstation and
   records exact SHA, exit code and evidence in the private PR. The owner must disable Actions in repository
   settings before old workflow files could be triggered, and reconcile incompatible required-status branch
   rules without bypass. For public, prefer standard hosted; self-hosted requires CI-2 ADR and fork isolation.
9. **Persistent server/static environment (DEP-7/8):** a green CI candidate is not a Test/Production deployment.
   Follow `docs/runbooks/deploy.md` on the target host, use only an immutable SemVer target, install project-scoped
   deploy units, configure distinct version/health plus the canonical origin, and require
   `kavosh-deploy-<slug> --verify-environment` to emit `ENVIRONMENT_CONFORMANCE=PASS` before representing that host
   as canonical Test/Production. Temporary runner/Compose previews stay non-canonical and isolated.

### Step 5 — Backlog
1. Create milestone `v0.1.0` (first usable release).
2. Create issues with the repository's issue forms: epics (T2), features (T1/T2), tasks. Every issue gets a
   `type:*` label (`WK-1`), acceptance criteria, and — for tasks — "Where to look".
3. If `acceptance.mode=continuous`, populate `acceptance/scope.json` for the first release from the approved scope: stable AC-* IDs, canonical GitHub issue, owner, risk and required evidence. The file declares scope only; never write live accepted/done status into it.
4. Use coherent, independently reviewable capability deliveries (`WK-6`, `PR-3`), not one PR per source requirement or intake answer. Plan criteria, assertions and risk-sized evidence with the implementation; reconcile them at capability closure. Shared evidence may cover multiple criteria only with actual traceability. Explicit not-needed decisions create no feature/test/receipt work.
5. Post the backlog summary to the owner (issue links only; do not write live backlog/status into a file — `SRC-1`).

### Step 6 — Hand over
Report: repository URL, tier/runtime/capabilities, budget, the first 3 tasks you recommend, anything the owner must do
manually (e.g. for private: disabling Actions before any push, running local checks, and GitHub CLI changes). Stop.

---

## §2 ADOPT an existing repository
1. Run `bash scripts/audit-repo.sh bagdeli/<repo>` (read-only). Summarise findings against `standard/RULES.md`.
2. Run the intake (§1 steps 1–3) using existing answers and actual project choices; ask only missing or changed architecture decisions. Do not restart the project or re-approve unchanged choices. Examples from another product do not authorize work on that product.
3. Propose an adoption plan in phases using [`adoption/ADOPTION.md`](adoption/ADOPTION.md). Get owner approval per phase.
4. Scaffold with `scaffold.py --adopt`: existing files are never overwritten; the script writes
   `*.kavosh-new` next to them for you to merge in a PR.
5. Governance remains `enforce: true`. If the audit finds legacy failures, fix or document their scope; `enforce: false` is not a green-check shortcut.
6. Destructive steps (deleting branches, closing issues, rewriting docs) only with explicit owner approval, one phase at a time.

## §3 UPGRADE
1. Read the KavoshStart `CHANGELOG.md` between the pinned version and the target and classify every change that affects governance, acceptance, security, release, deploy, CI, agent controls or templates.
2. Use one dedicated PR (usually the Dependabot PR that bumps `bagdeli/KavoshStart/...@vX.Y.Z`): set `kavosh.project.json` → `kavoshStart` to the same exact tag (REL-6), apply template changes listed in the changelog, and update all reusable workflow pins together. Title: `chore(kavosh): upgrade KavoshStart to vX.Y.Z`.
3. Remove legacy `adoptionPhase: true`; it is not a valid long-running operating mode. Governance stays enforcing. If a specific rule cannot yet be met, record a bounded exception with owner, risk, compensating control and review/expiry instead of disabling governance.
4. For every T2 consumer, enable `"acceptance": {"mode": "continuous"}` and migrate release-scoped assertions, source-bound receipts and real admitted producers using `templates/tier/T2/acceptance/README.md`. Identify missing prerequisites before claiming the upgrade complete. Existing requirement ledgers remain supporting traceability; do not turn every row into a new acceptance Issue or mark historical code accepted without evidence.
5. Run the repository audit/governance and `make check`; resolve new violations or explicitly disposition genuine external blockers. Do not bundle unrelated product features into the upgrade PR.
6. Design-system package upgrades use a separate PR and exact version. Capture actual rendered/RTL/mobile evidence only for relevant render or interaction changes; do not publish private consumer details in this public standard.

## §4 WORK on an issue (every day)
0. Complete §0 first. If §0 routes this session to UPGRADE, finish or explicitly defer that upgrade before opening a normal feature branch.
1. `gh issue view <n>`; read its parent, the project's `AGENTS.md` and the relevant settled architecture decisions from §0. Reopen only decisions affected by this scope. Read additional material only when the issue or those decisions require it.
2. `git fetch origin && git switch -c <type>/<n>-<slug> origin/main` (`BR-2`).
3. Open a **draft PR early** with your plan (`PR-1`, `PR-2`). Body from the PR template. Draft stacks may be deep;
   health warns until the Ready stack is normalized.
4. Implement one coherent packet; run focused verification plus the project's semantic `check` command. The default scaffold exposes this through `make check`, but an adopted project may use another documented adapter (CI-8). Heavy CI is off by default on Draft; early CI still needs direct approval if it consumes shared quota.
5. Update the PR body: Change risk / affected capabilities / Done / Remaining (as canonical issues) / Decisions / How verified / AI involvement. A remaining required outcome is never silently converted into "done" by starting the next task (FLOW-2).
6. Mark ready for review. Recheck base, mergeability, exact head, required green checks, unresolved review threads and blockers immediately before merge.
   - `low` / `medium`: when all required gates are complete, the agent may perform the ordinary Squash merge on the exact current head without asking the owner to click Merge.
   - `high` / `critical`, control-plane, security/trust-boundary, destructive-data or release-policy change: require an explicit human decision for the current scope first; after that decision the agent may perform the mechanical merge.
   - A generic "continue/proceed" is execution authority only; it is never acceptance, merge, release or waiver authority (FLOW-1).
   - Never use `--admin`, bypass protection, or merge a red/missing check.
7. If the branch is stale or `main` moved materially, refresh/rebase based on conflict and risk rather than a universal age threshold. Branch age remains a health signal, not proof that the change is unsafe (BR-3).

## Hard stops — ask the owner, do nothing else
- Creating/deleting repositories, deleting branches or tags, closing issues you did not create.
- High/critical risk decisions, Production data changes and credentials require direct human authorization scoped to the current action/scope; SETAD/Moadian/bank credentials, OTP/CAPTCHA and signing keys are never handled by agents.
- A rule in `standard/RULES.md` would have to be broken to finish the task.
- A CI dispatch would consume shared quota without direct, bounded owner approval.
