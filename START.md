# START.md — agent protocol

You are an AI agent asked to create, adopt or maintain a Kavosh project "using KavoshStart".
Follow this protocol exactly. Rules are referenced by ID (e.g. `BR-1`); their canonical list is
[`standard/RULES.md`](standard/RULES.md). When this file and a rule disagree, the rule wins — report the conflict.

Pick the mode:

| Mode | Trigger | Go to |
|---|---|---|
| **NEW** | "build / create project X" | §1 |
| **ADOPT** | "bring existing repo X under KavoshStart" | §2 |
| **UPGRADE** | "update X to KavoshStart vN / KavoshUI vN" | §3 |
| **WORK** | "implement issue #n in X" (project already adopted) | §4 |

Never skip a step. Never invent an answer the owner has not given — ask.

---

## §1 NEW project

### Step 1 — Intake
1. Read [`intake/QUESTIONNAIRE.md`](intake/QUESTIONNAIRE.md).
2. Fill every question you can from the owner's request. For every **required** question you cannot
   answer with certainty, ask the owner. Ask all open questions **in one message**, grouped, in Persian,
   each with your suggested default so the owner can reply "OK".
3. Do not proceed while any required answer is missing.

### Step 2 — Classify
1. Apply [`intake/CLASSIFICATION.md`](intake/CLASSIFICATION.md) mechanically to get **Tier** (T0/T1/T2)
   and **Runtime** (none/static/server/desktop). Show the owner which criterion triggered the result.
2. Explain the GitHub Free cost boundary. Do not run private hosted CI without direct owner approval for one named
   execution; labels and a zero budget field are not authorization. Public standard hosted CI may run only where it
   draws on no shared allowance. A T1/static project may choose `ci.runner: none` to use the local-only profile.
3. The owner confirms or overrides. An override is recorded later as an ADR in the new repo.

### Step 3 — Manifest
1. Write `kavosh.project.json` conforming to [`intake/kavosh.project.schema.json`](intake/kavosh.project.schema.json).
   Pin `kavoshStart` to the latest KavoshStart release tag (`gh release view -R bagdeli/KavoshStart --json tagName`)
   and, if the project has a UI, `ui.kavoshui` to the latest KavoshUI release.
2. Write `PROJECT.md` from `templates/common/PROJECT.md` — one page, Persian, no status.
3. Show both to the owner. Continue only after confirmation.

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
4. If `ui.kind` is not `none`: follow [`standard/10-kavoshui.md`](standard/10-kavoshui.md). Do not copy
   KavoshUI components; consume the pinned version.
5. `make check` must pass locally.
6. First commit directly on `main` is allowed **only** for this initial scaffold of an empty repository:
   `chore: scaffold from KavoshStart <version>` with the agent `Co-Authored-By` trailer. Everything after it goes through PRs.
7. Run `bash <KavoshStart>/scripts/bootstrap-repo.sh bagdeli/<repo>` (dry-run), show the output, and run it
   with `--apply` only after the owner agrees. Then `bash scripts/install-agent-guards.sh` inside the repo.
8. **Runner (CI-1):** public repositories default to standard GitHub-hosted. Private repositories may choose hosted or
   isolated self-hosted based on trust, billing, network and workload. With this Free account, do not use private
   hosted Actions without the owner's direct approval for this run; run the `ci` and `kavosh` workflows by
   `workflow_dispatch`, naming the open PR and exact current head SHA. Stale heads fail closed. Self-hosted is optional;
   rootful Docker is root-equivalent, so use rootless Docker or a disposable VM destroyed after each job. The owner
   creates the registration token. Verify: `gh api repos/bagdeli/<repo>/actions/runners -q '.runners[] | [.name,.status] | @tsv'`.
   For T1/static, the owner may select `ci.runner: none`: scaffold omits all workflows. Run `make check` locally and
   attach its successful output to every PR. Bootstrap selects a PR-protected ruleset without CI status checks for
   this profile. Never merge a red result or bypass an actual required check.

### Step 5 — Backlog
1. Create milestone `v0.1.0` (first usable release).
2. Create issues with the repository's issue forms: epics (T2), features (T1/T2), tasks. Every issue gets a
   `type:*` label (`WK-1`), acceptance criteria, and — for tasks — "Where to look".
3. Prefer tasks small enough for focused review. Split work when that improves review or risk control (`WK-6`, `PR-3`).
4. Post the backlog summary to the owner (issue links only; do not write the backlog into a file — `SRC-1`).

### Step 6 — Hand over
Report: repository URL, tier/runtime, budget, the first 3 tasks you recommend, anything the owner must do
manually (e.g. the Actions access setting). Stop.

---

## §2 ADOPT an existing repository
1. Run `bash scripts/audit-repo.sh bagdeli/<repo>` (read-only). Summarise findings against `standard/RULES.md`.
2. Run the intake (§1 steps 1–3) using what the repository already shows; ask only what is missing.
3. Propose an adoption plan in phases using [`adoption/ADOPTION.md`](adoption/ADOPTION.md). Get owner approval per phase.
4. Scaffold with `scaffold.py --adopt`: existing files are never overwritten; the script writes
   `*.kavosh-new` next to them for you to merge in a PR.
5. Governance remains `enforce: true`. If the audit finds legacy failures, fix or document their scope; `enforce: false` is not a green-check shortcut.
6. Destructive steps (deleting branches, closing issues, rewriting docs) only with explicit owner approval, one phase at a time.

## §3 UPGRADE
1. Read the KavoshStart `CHANGELOG.md` between the pinned version and the target.
2. One PR (usually the Dependabot PR that bumps `bagdeli/KavoshStart/...@vX.Y.Z`): set `kavosh.project.json` → `kavoshStart`
   to the same tag (REL-6), apply template changes listed in the changelog, and adjust anything the new rules require. Title: `chore(kavosh): upgrade KavoshStart to vX.Y.Z`.
3. KavoshUI upgrades are separate PRs: `chore(ui): upgrade KavoshUI to vX.Y.Z`, with rendered screenshots (RTL + mobile).

## §4 WORK on an issue (every day)
1. `gh issue view <n>`; read its parent; read the project's `AGENTS.md`. Nothing else unless the issue points to it.
2. `git fetch origin && git switch -c <type>/<n>-<slug> origin/main` (`BR-2`).
3. Open a **draft PR early** with your plan (`PR-1`, `PR-2`). Body from the PR template. Draft stacks may be deep;
   health warns until the Ready stack is normalized.
4. Implement; run focused tests; run `make check`; push once. Heavy CI is off by default on Draft; early CI still
   needs direct approval if it consumes shared quota.
5. Update the PR body: Done / Remaining (as new issues) / Decisions / How verified / AI involvement.
6. Mark ready for review. An explicit owner authorization for this PR and current head permits an ordinary green
   squash merge after fresh preflight checks. Recheck base, mergeability, required green checks and unresolved review
   threads immediately before merge; bind it to the same SHA with `gh pr merge <number> --squash --match-head-commit <sha>`.
   It never permits `--admin`, protection bypass or a red/missing check.
7. If the branch is older than 3 days or `main` moved significantly: rebase on `origin/main` before asking for review (`BR-3`).

## Hard stops — ask the owner, do nothing else
- Creating/deleting repositories, deleting branches or tags, closing issues you did not create.
- Production data changes and credentials require direct authorization scoped to one action; SETAD/Moadian/bank
  credentials, OTP/CAPTCHA and signing keys are never handled by agents.
- A rule in `standard/RULES.md` would have to be broken to finish the task.
- A CI dispatch would consume shared quota without direct, bounded owner approval.
