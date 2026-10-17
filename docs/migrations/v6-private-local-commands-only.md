# v6 — Migrate a private project to owner-run local commands only

**Mandatory, breaking scope:** The owner's explicit rule is absolute. In a private repository, **no GitHub Actions jobs/runners of any kind** (GitHub-hosted or self-hosted) for any Tier/Runtime. The AI does not mutate a private repository or dispatch workflows; it only produces exact commands for the owner to run on a trusted machine with GitHub access.

## Order — never push before disabling Actions

1. On the **owner's machine**, use `gh repo view OWNER/REPO --json isPrivate,nameWithOwner` to confirm the repository is private. Do not share tokens/SSH keys/logs with AI.
2. In GitHub **Settings → Actions → General**, the **owner disables Actions** for that private repository **before any PR or push**. Then check by `gh api repos/OWNER/REPO/actions/permissions --jq '.enabled'` (must be `false`). Simply removing workflow YAML in a PR may still permit the base branch to schedule jobs.
3. On the owner's clean worktree and a review branch, set `kavosh.project.json.ci = {"runner":"none","monthlyMinutesBudget":0}`; remove all tracked `.github/workflows/*.yml|*.yaml` and deprecated runner labels/requiredWorkflow. Do not change repo visibility to bypass this ban. Set `kavoshStart` to the actual published new major release only after it exists.
4. Locally run `make setup`, `make check`, and risk-scoped integration/browser/security tests or project-specific `pnpm`/`pytest` commands. Capture true command, exit code, tool/browser version, source SHA and SHA-256 of any candidate artifact. Never relabel local proof as an Actions check or claim independent human approval.
5. If GitHub protection requires now-impossible Actions statuses, the owner **explicitly** changes rulesets to local-source/human-review rules (where supported), not `--admin`, protection bypass or fake-green status. Merge exact reviewed head using owner-run `gh pr merge --squash --match-head-commit ...` after reviewing local evidence and risk.
6. The owner creates releases and packages on the same trusted machine with inspected source, build/test results, immutable tarball digests and authorization. `gh release` and a package registry are distribution/storage, not CI. Production/Test conformance is still separately observed and recorded.
7. For missing downloads/uploads, give the owner sanitized URL/DNS/observed IP or unknown/port/error/attempts; never activate runner, proxy, mirror or relay to fix it.

Old v5 private hosted workflow guidance is **superseded**. Public GitHub Actions remain permitted with their own policy. Do not create a second tracker or unverified acceptance receipt to simulate CI.
