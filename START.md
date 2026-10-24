# START.md — agent protocol

You are an AI agent asked to create, adopt or maintain a Kavosh project "using KavoshStart".
Follow this protocol exactly. Rules are referenced by ID (e.g. `BR-1`); their canonical list is
[`standard/RULES.md`](standard/RULES.md). When this file and a rule disagree, the rule wins — report the conflict.

## Public/private boundary before every upstream write

KavoshStart is public: its files, issues, PR/review/comments, release notes, commits, logs and artifacts must contain **zero private consumer facts or identifying/indirect references**. Never copy the origin of a private project observation into an upstream bug explanation, sample, test fixture, error log or agent prompt. Abstract to a technology-neutral invariant and synthetic versioned example **before creating** any public GitHub object. Consumer-specific root causes, decisions and evidence stay inside the affected private repository or private communication. Locally preflight the exact public text with the checked-in `scripts/public_source_guard.py --stdin` when it helps; this does not replace human semantic review, does not check older history and never proves comprehensive non-disclosure. A public CI failure cannot undo an already submitted public leak. Do not construct a public private-name denylist.

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
4. A newer KavoshStart release is **an advisory input**, not a default prerequisite to routine product work. Read only the relevant CHANGELOG delta; continue on the exact pinned version unless the owner elects upgrade or an actual applicable security/compatibility defect requires a scoped action. No new defer Issue/form just because latest changed, and never silently upgrade.
5. A T2 project may be **owner-operated** with `acceptance.mode=none`; advanced continuous acceptance, attestation Apps and second-person review are separate owner opt-ins selected in intake. `adoptionPhase: true` remains invalid; no report-only bypass.
6. Refresh only the moving facts needed for the task: current `main`, related open PRs/checks/releases and, when runtime behavior matters, exact deployed version/SHA/schema/health. Do not turn routine continuation into an unrelated full audit.
7. Choose the mode below and complete one coherent packet. A genuine hotfix may proceed with an owner-approved bounded standard-upgrade defer, recorded in GitHub with its expiry/review trigger.

Pick the mode:

| Mode | Trigger | Go to |
|---|---|---|
| **NEW** | "build / create project X" | §1 |
| **ADOPT** | "bring existing repo X under KavoshStart" | §2 |
| **UPGRADE** | "update X to KavoshStart vN / its selected design-system package" | §3 |
| **WORK** | "implement or maintain X" (with an existing Issue when applicable) | §4 |

Apply only steps relevant to this task and the selected project profile. Do not turn team-only conventions, optional Apps, extra hosts or forms into a blocker. Never invent a material owner decision; reuse settled answers and ask only what truly matters.

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

### Evidence ownership before defining tests

At G6/G9 decide whether the proposed requirement is a unique product need, actual consumer integration or an inherited versioned native/upstream guarantee. For **new or materially changed** criteria/test suites note source/version, owning boundary, reason, smallest impacted verification and when needed in the same Issue/Spec; do not create an extra row, global detector or duplicate upstream suite. Revisit old requirements as keep/narrow/merge/retire where their owner/risk/source justify it. A security finding or broken required check is not cleared by retiring its name.

### Step 2 — Classify
1. Apply [`intake/CLASSIFICATION.md`](intake/CLASSIFICATION.md) mechanically to get **Tier** (T0/T1/T2),
   **Runtime** (none/static/server/desktop), and the minimum derivable **Capabilities**. Show the owner which facts triggered the Tier/Runtime and which capabilities were derived; ask only for additional non-derivable capabilities such as infrastructure/control-plane.
2. Explain the runner and cost boundary: in private, an existing
   **self-hosted runner on an existing accepted, least-privileged host** registered in GitHub Actions may
   be chosen without a second machine or mandatory trust ADR, and without an extra custom label for a private owner-operated TEST runner. Native `self-hosted/linux/x64` labels can suffice when they actually route to the intended repo-scoped Runner. Avoid giving untrusted code access to real secrets, writable main/release credentials or Production (CI-2).
   Private **GitHub-hosted** runs require **explicit prior authorization** from the
   designated human billing owner (the person who issued the policy; not another admin or agent)
   for each exact workflow/PR/ref/head SHA, even within included free minutes.
   No reply means no hosted dispatch; other metered GitHub features in private also require
   the same person's scoped prior consent (ADR-0019).
   Public standard GitHub-hosted minutes are free under current GitHub rules;
   larger runners and storage have separate terms. T1/static may select 'none'.
   Before selecting any material third-party component, apply `standard/15-third-party-components.md`.
   Record risk-sized licence, distribution, security and total-ownership-cost decisions in the consumer project.
3. The owner confirms or overrides. An override is recorded later as an ADR in the new repo.

### Step 3 — Manifest
1. Write `kavosh.project.json` conforming to [`intake/kavosh.project.schema.json`](intake/kavosh.project.schema.json).
   Pin `kavoshStart` to the latest KavoshStart release tag (`gh release view -R bagdeli/KavoshStart --json tagName`). Never copy the illustrative `vX.Y.Z` from the example and never use the reserved `self` value in a consumer project.
   For a UI project, record its selected exact package and version under `ui.designSystem`, or a scoped `ui.exceptionADR`.
   Never publish consumer-private package names, URLs or evidence in public KavoshStart.
2. For a single-owner project of **any tier**, default to `acceptance.mode: none` and omit `review.teamProcess` (or set it `false`); avoid a new Issue, PR-body form or artificial branch name solely for process. An explicitly collaborating team may opt into `review.teamProcess=true` separately from second-person review. Use `continuous` only if the owner specifically requested it during intake G9. Do not infer it from T2, data sensitivity or multiple domains. A large team may explicitly select `continuous` plus `assurance` only after learning the cost and real availability of separate evidence/decision Apps for attested outcomes. Missing elected producers block only the elected protocol; do not invent Apps or claim a fake receipt. Existing consumers retain their pinned profile until a separate reviewed upgrade.
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
8. **Runner (CI-1/2):** a private repository may select an available
   **self-hosted runner on an existing approved host** with non-root account/file/socket/credential containment; a second server/VM or separate ADR is not a default requirement.
   Reject untrusted fork/PR code and contain runner secrets and credentials.
   For private GitHub-hosted usage, **explicit authorization** must first be
   requested and received from the designated human billing owner for this exact run. Only after
   approval, manually dispatch 'ci' and 'kavosh' for the current PR/head SHA;
   stale heads fail closed. A budget field or generic permission to work is
   not a one-run spending approval. Public standard GitHub-hosted is free for
   Actions minutes; public self-hosted also requires CI-2 isolation review.
   Hosted does not imply private Test/Production access. T1/static 'none'
   creates no workflows: require real local 'make check' evidence, never
   bypass an existing failed required check.
9. **Only selected persistent Test/Production environments (DEP-7/8):** green CI is not an installed product release. With the default Kavosh pull deployer, use its existing project-scoped units and real `--verify-environment` identity/health check. For an owner-approved native/custom adapter, use its **actual equivalent** source/version/health and recovery checks; do not install Kavosh systemd units, a separate Test server or an extra VM just to do an ordinary upstream maintenance update. Temporary previews cannot impersonate a canonical environment.

### Step 5 — Backlog
1. For a sizeable team **if useful**, create a release milestone; a sole owner may deliver the first usable version with the existing Issue/PR/Release and no additional milestone.
2. Create issues for genuine independently trackable work, especially when a team needs coordination; a single owner does not need a new Issue, Epic or Spec per small change. Issues that do exist use one `type:*` label (`WK-1`) and their real acceptance scope. Do not inflate a template into a prerequisite for implementing the first small product slice.
3. If `acceptance.mode=continuous`, populate `acceptance/scope.json` for the first release from the approved scope: stable AC-* IDs, canonical GitHub issue, owner, risk and required evidence. The file declares scope only; never write live accepted/done status into it.
4. Use coherent, independently reviewable capability deliveries (`WK-6`, `PR-3`), not one PR per source requirement or intake answer. Plan criteria, assertions and risk-sized evidence with the implementation; reconcile them at capability closure. Shared evidence may cover multiple criteria only with actual traceability. Explicit not-needed decisions create no feature/test/receipt work.
5. Post the backlog summary to the owner (issue links only; do not write live backlog/status into a file — `SRC-1`).

### Step 6 — Hand over
Report: repository URL, tier/runtime/capabilities, budget, the first 3 tasks you recommend, anything the owner must do
manually (e.g. the Actions access setting). Stop.

---

## §2 ADOPT an existing repository
1. Run `bash scripts/audit-repo.sh bagdeli/<repo>` (read-only). Summarise findings against `standard/RULES.md`.
2. Run the intake (§1 steps 1–3) using existing answers and actual project choices; ask only missing or changed decisions. Explicitly recover D3/G9 owner-versus-team choices before suggesting second-person review, separate GitHub App attestation, external legal counsel or a second Test environment; default NO for solo ownership. Do not restart the project or re-approve unchanged choices. Examples from another product do not authorize work on that product.
3. Propose an adoption plan in phases using [`adoption/ADOPTION.md`](adoption/ADOPTION.md). Get owner approval per phase.
4. Scaffold with `scaffold.py --adopt`: existing files are never overwritten; the script writes
   `*.kavosh-new` next to them for you to merge in a PR.
5. Governance remains `enforce: true`. If the audit finds legacy failures, fix or document their scope; `enforce: false` is not a green-check shortcut.
6. Destructive steps (deleting branches, closing issues, rewriting docs) only with explicit owner approval, one phase at a time.

## §3 UPGRADE

For an **owner-selected upgrade** from any older stable major, use [the versioned compatibility matrix](docs/migrations/direct-upgrade-compatibility.md). Only an **actually published exact tag** can be adopted. Do not convert every legacy requirement or mature dependency's internal proof into new acceptance rows, new runners or heavy suites. Preserve accepted evidence only where actual source/version/environment coverage remains valid; reconcile obsolete requirements through their own approved scope, without forging PASS.

1. Read the KavoshStart `CHANGELOG.md` between the pinned version and the target and classify every change that affects governance, acceptance, security, release, deploy, CI, agent controls or templates.
2. Use one dedicated PR (usually the Dependabot PR that bumps `bagdeli/KavoshStart/...@vX.Y.Z`): set `kavosh.project.json` → `kavoshStart` to the same exact tag (REL-6), apply template changes listed in the changelog, and update all reusable workflow pins together. Title: `chore(kavosh): upgrade KavoshStart to vX.Y.Z`.
3. Remove legacy `adoptionPhase: true`; it is not a valid long-running operating mode. Governance stays enforcing. If a specific rule cannot yet be met, record a bounded exception with owner, risk, compensating control and review/expiry instead of disabling governance.
4. Ask whether the owner wants **solo-owner (`acceptance.mode=none`)** or intentionally **team-managed continuous acceptance**. Only for explicitly selected continuous, map release assertions, reviewed producers and actual evidence. If opting out of a previously chosen attested contract, review the risk/scope with the owner and preserve prior records; never silently mark missing receipts or previously failed tests PASS. No automatic second App, human, lawyer or test machine.
5. Run the repository audit/governance and `make check`; resolve new violations or explicitly disposition genuine external blockers. Do not bundle unrelated product features into the upgrade PR.
6. Design-system package upgrades use a separate PR and exact version. Capture actual rendered/RTL/mobile evidence only for relevant render or interaction changes; do not publish private consumer details in this public standard.

## §4 WORK on an issue (every day)

For a new or changed material test/requirement, state **why it exists**, which released upstream/native contract already covers it, which product integration gap remains and which focused observation detects that gap. Only run expensive/specialist tests at the relevant risk/lifecycle decision. For duplicated/stale criteria, propose a reviewed change to the existing owning Issue/Spec/PR, not a new test package. Do not bypass existing failed mandatory checks.

0. Complete the relevant §0 checks first. A newer standards tag alone does **not** route ordinary WORK to UPGRADE. Upgrade is a separate owner-selected action, unless a real applicable incompatibility/security blocker needs a scoped resolution.
1. Read the actual task request and the existing Issue/PR/Spec **if one exists**; use the project's `AGENTS.md` and affected settled architecture decisions. Do not manufacture an Issue, Epic or new decision record to start a bounded fix. Reopen only decisions affected by this scope.
2. Work from current source on a short-lived branch. Use `<type>/<n>-<slug>` if `review.teamProcess=true`; for owner-operated work any safe, descriptive branch name is sufficient (`BR-2`). No direct push to protected `main`.
3. Open a coherent PR once there is code to review. Draft-first, a specific PR-title format and extensive forms are **team-process options**, not prerequisites for owner-operated development.
4. Implement one coherent packet; run focused verification plus the project's actual required semantic `check` command. The scaffold uses `make check` by default, but adopted projects may provide a different documented adapter (CI-8). Do not force unrelated heavy suites to run for documentation-only work. Private hosted billing still requires prior owner consent.
5. Summarize the actual change, verification result and relevant outstanding decisions in the PR. `Risk`, `Capabilities`, Issue mapping and `AI involvement` are required only for the explicitly chosen team process or optional continuous-acceptance protocol, not for owner-operated work. Do not report an unverified outcome as done (FLOW-2).
6. Mark ready for review. Recheck base, mergeability, exact head, required green checks, unresolved review threads and blockers immediately before merge.
   - `low` / `medium`: when all required gates are complete, the agent may perform the ordinary Squash merge on the exact current head without asking the owner to click Merge.
   - `high` / `critical`, control-plane, security/trust-boundary, destructive-data or release-policy change: require an explicit human decision for the current scope first; after that decision the agent may perform the mechanical merge.
   - A generic "continue/proceed" is execution authority only; it is never acceptance, merge, release or waiver authority (FLOW-1).
   - Never use `--admin`, bypass protection, or merge a red/missing check.
7. If the branch is stale or `main` moved materially, refresh/rebase based on conflict and risk rather than a universal age threshold. Branch age remains a health signal, not proof that the change is unsafe (BR-3).

## Scoped hard stops — pause only the dependent unsafe operation
- Creating/deleting repositories, deleting branches or tags, closing issues you did not create.
- Production data changes and credentials require direct human authorization scoped to the current action/scope; high/critical **merge or release decisions** also require exact-scope human authorization, not a second person by default. Ordinary preparation, focused tests and safe edits can continue. SETAD/Moadian/bank credentials, OTP/CAPTCHA and signing keys are never handled by agents.
- A real security, source integrity, release or authorization gate would have to be bypassed to finish the dependent action. Report the exact blocker; **continue unrelated authorized development** without fabricating approval or PASS.
- A CI dispatch would consume shared quota without direct, bounded owner approval.
