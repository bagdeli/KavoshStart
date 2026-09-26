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
2. Show the CI minute budget from the classification table and the current account usage
   (`python3 scripts/portfolio.py bagdeli --minutes`, if available). If the budget does not fit, say so before continuing.
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
8. **Runner (CI-1):** private repository → ask the owner to register the self-hosted runner(s) with
   `scripts/install-runner.sh` (the owner creates the registration token; you never handle it). Verify:
   `gh api repos/bagdeli/<repo>/actions/runners -q '.runners[] | [.name,.status] | @tsv'`. Public repository → nothing to do.

### Step 5 — Backlog
1. Create milestone `v0.1.0` (first usable release).
2. Create issues with the repository's issue forms: epics (T2), features (T1/T2), tasks. Every issue gets a
   `type:*` label (`WK-1`), acceptance criteria, and — for tasks — "Where to look".
3. Tasks must be ≤ 1 day and ≤ 400 changed lines (`PR-3`). If you cannot size it, split it.
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
5. Governance starts with `enforce: false` (report-only) and switches to `true` when the audit is clean.
6. Destructive steps (deleting branches, closing issues, rewriting docs) only with explicit owner approval, one phase at a time.

## §3 UPGRADE
1. Read the KavoshStart `CHANGELOG.md` between the pinned version and the target.
2. One PR (usually the Dependabot PR that bumps `bagdeli/KavoshStart/...@vX.Y.Z`): set `kavosh.project.json` → `kavoshStart`
   to the same tag (REL-6), apply template changes listed in the changelog, and adjust anything the new rules require. Title: `chore(kavosh): upgrade KavoshStart to vX.Y.Z`.
3. KavoshUI upgrades are separate PRs: `chore(ui): upgrade KavoshUI to vX.Y.Z`, with rendered screenshots (RTL + mobile).

## §4 WORK on an issue (every day)
1. `gh issue view <n>`; read its parent; read the project's `AGENTS.md`. Nothing else unless the issue points to it.
2. `git fetch origin && git switch -c <type>/<n>-<slug> origin/main` (`BR-2`).
3. Open a **draft PR early** with your plan (`PR-1`, `PR-2`). Body from the PR template.
4. Implement; run focused tests; run `make check`; push once.
5. Update the PR body: Done / Remaining (as new issues) / Decisions / How verified / AI involvement.
6. Mark ready for review. **Never merge** (`AI-5`). If the `kavosh` check is red, fix it — never work around it.
7. If the branch is older than 3 days or `main` moved significantly: rebase on `origin/main` before asking for review (`BR-3`).

## Hard stops — ask the owner, do nothing else
- Creating/deleting repositories, deleting branches or tags, closing issues you did not create.
- Anything touching production data or credentials; SETAD/Moadian/bank credentials (never handle them at all).
- A rule in `standard/RULES.md` would have to be broken to finish the task.
- The CI minute budget of the project would be exceeded this month.
