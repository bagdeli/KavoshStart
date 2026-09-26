#!/usr/bin/env python3
"""Layer O — public portfolio supervisor.

A repository cannot reliably report that its own enforcement was deleted or neutered, so Layer O checks adopted
PUBLIC repositories from outside. Private repositories are skipped before their name, metadata, files or findings
can enter the public report. Private-project monitoring belongs in a separate private control surface.

    python3 scripts/portfolio_guard.py bagdeli                  # public report to stdout, exit 1 if findings
    python3 scripts/portfolio_guard.py bagdeli --update-issue   # keep one public `kavosh:portfolio` issue

In CI use KAVOSH_PUBLIC_PORTFOLIO_TOKEN, a fine-grained read-only token scoped only to the governed public
repositories (Contents, Metadata, Actions, Issues and Administration: read). The skip is still enforced in code
so an accidentally broader credential does not make private repositories appear in a public report.

Trust boundary: public Layer O depends on this repository and GitHub Actions. If it stops running, only a human
notices (the portfolio issue stops updating). The standard does not claim visibility into private projects.
"""
import base64
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tooling" / "src"))
from governance import unpinned_uses, wiring_problems  # noqa: E402  (same rules as layer P)

HOME = "bagdeli/KavoshStart"
BUDGET_LIMIT = 1600
REQUIRED_FILES = [".githooks/pre-push", ".githooks/pre-commit", ".claude/settings.json", "AGENTS.md", "PROJECT.md",
                  ".github/dependabot.yml"]
WORKFLOWS = [".github/workflows/kavosh.yml", ".github/workflows/ci.yml", ".github/workflows/self-check.yml",
             ".github/workflows/release.yml"]
HEALTH_MAX_AGE_DAYS = 8
NOW = datetime.now(timezone.utc)


class Api:
    """Thin gh wrapper; tests replace it with a fake exposing the same two methods."""

    def get(self, path):
        r = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
        if r.returncode != 0:
            if "Not Found" in r.stderr or "404" in r.stderr:
                return None
            raise PermissionError(r.stderr.strip()[:200])
        return json.loads(r.stdout) if r.stdout.strip() else None

    def repos(self, owner):
        r = subprocess.run(["gh", "repo", "list", owner, "--limit", "300", "--json",
                            "nameWithOwner,isPrivate,isArchived,defaultBranchRef"],
                           capture_output=True, text=True, encoding="utf-8", check=True)
        return json.loads(r.stdout)


def content(api, repo, path, ref):
    data = api.get(f"repos/{repo}/contents/{path}?ref={ref}")
    if not data or "content" not in data:
        return None
    return base64.b64decode(data["content"]).decode("utf-8", errors="replace")


def days_since(ts):
    return (NOW - datetime.fromisoformat(ts.replace("Z", "+00:00"))).days


def inspect_repo(api, repo, branch, private):
    """Return (manifest or None, findings[list of (rule, text)], info dict)."""
    raw = content(api, repo, "kavosh.project.json", branch)
    if raw is None:
        return None, [], {"adopted": False}
    findings = []
    try:
        m = json.loads(raw)
    except ValueError:
        return {}, [("SRC-5", "kavosh.project.json is not valid JSON")], {"adopted": True}

    workflows = {w: content(api, repo, w, branch) or "" for w in WORKFLOWS}
    workflows = {k: v for k, v in workflows.items() if v}
    for level, rule, title, detail in wiring_problems(workflows, m):
        if level == "fail":
            findings.append((rule, f"{title}: {detail}"))
    for bad in unpinned_uses({k: v for k, v in workflows.items() if "kavosh" in v.lower() or k.endswith("release.yml")}, m):
        if "KavoshStart" in bad:
            findings.append(("REL-6", bad))

    tree = api.get(f"repos/{repo}/git/trees/{branch}?recursive=1") or {}
    paths = {t["path"] for t in tree.get("tree", [])}
    for f in REQUIRED_FILES:
        if f not in paths:
            findings.append(("AI-4" if f.startswith((".githooks", ".claude")) else "SRC-7" if f == "PROJECT.md" else
                             "SEC-4" if "dependabot" in f else "AI-1", f"required file missing: {f}"))

    info = api.get(f"repos/{repo}") or {}
    expected = {"allow_squash_merge": True, "allow_merge_commit": False, "allow_rebase_merge": False, "delete_branch_on_merge": True}
    drift = [f"{k}={info.get(k)}" for k, v in expected.items() if k in info and info.get(k) != v]
    if drift:
        findings.append(("PR-5/BR-5", "repository settings drift: " + ", ".join(drift)))
    try:
        perms = api.get(f"repos/{repo}/actions/permissions/workflow") or {}
        if perms and perms.get("default_workflow_permissions") != "read":
            findings.append(("SEC-3", f"default GITHUB_TOKEN permission is {perms.get('default_workflow_permissions')}, expected read"))
    except PermissionError:
        findings.append(("O", "cannot read Actions settings (token needs Administration: read)"))

    head = (api.get(f"repos/{repo}/branches/{branch}") or {}).get("commit", {}).get("sha")
    if head:
        runs = (api.get(f"repos/{repo}/commits/{head}/check-runs?per_page=100") or {}).get("check_runs", [])
        if not any(r.get("name") == "main-guard / main-guard" for r in runs):
            findings.append(("M", f"no main-guard check on the head of {branch} — the guard is not running"))

    issues = api.get(f"repos/{repo}/issues?labels=kavosh:health&state=open") or []
    if not issues:
        findings.append(("H", "no open `kavosh:health` issue — weekly health is not running"))
    elif days_since(issues[0]["updated_at"]) > HEALTH_MAX_AGE_DAYS:
        findings.append(("H", f"health issue not updated for {days_since(issues[0]['updated_at'])} days — weekly health stopped"))
    viol = api.get(f"repos/{repo}/issues?labels=kavosh:violation&state=open") or []
    if viol:
        findings.append(("PR-7", f"{len(viol)} open violation issue(s): " + ", ".join(f"#{i['number']}" for i in viol)))

    actual = "private" if private else "public"
    if m.get("visibility") and m["visibility"] != actual:
        findings.append(("CI-1", f"repository is {actual} but manifest says {m['visibility']}"))
    if actual == "private":
        try:
            runners = (api.get(f"repos/{repo}/actions/runners") or {}).get("runners", [])
            online = [r for r in runners if r.get("status") == "online"]
            need = 2 if m.get("tier") == "T2" else 1
            if len(online) < need:
                findings.append(("CI-2", f"{len(online)} online self-hosted runner(s) registered to the repository, need {need}"))
        except PermissionError:
            findings.append(("O", "cannot list self-hosted runners (token needs Administration: read)"))

    budget = m.get("ci", {}).get("monthlyMinutesBudget", 0) if private else 0
    return m, findings, {"adopted": True, "budget": budget, "tier": m.get("tier"), "pin": m.get("kavoshStart")}


def run(api, owner):
    rows, total_budget, total_findings = [], 0, 0
    frozen_v1 = []
    for r in api.repos(owner):
        if r.get("isArchived") or r.get("isPrivate"):
            # SEC-5: a public control surface must not inspect or report private repositories,
            # even when an accidentally broad credential can enumerate them.
            continue
        repo, branch = r["nameWithOwner"], (r.get("defaultBranchRef") or {}).get("name") or "main"
        try:
            m, findings, info = inspect_repo(api, repo, branch, r.get("isPrivate", True))
        except PermissionError as e:
            rows.append((repo, "?", "?", [("O", f"cannot inspect: {e}")]))
            total_findings += 1
            continue
        if not info.get("adopted"):
            rows.append((repo, "—", "not adopted", []))
            continue
        total_budget += info.get("budget", 0)
        total_findings += len(findings)
        if any("@v1\n" in (content(api, repo, w, branch) or "") or "@v1 " in (content(api, repo, w, branch) or "")
               for w in (".github/workflows/kavosh.yml", ".github/workflows/release.yml")):
            frozen_v1.append(repo)
        rows.append((repo, info.get("tier"), info.get("pin"), findings))
    budget_ok = total_budget <= BUDGET_LIMIT
    if not budget_ok:
        total_findings += 1
    lines = [f"# Public portfolio supervisor (Layer O) — {NOW:%Y-%m-%d %H:%M} UTC", "",
             f"**{total_findings} finding(s).** Budget sum {total_budget} / {BUDGET_LIMIT} {'✅' if budget_ok else '❌ CI-3'}. "
             f"Consumers of frozen tag `v1`: {', '.join(frozen_v1) or 'none'} (tag may be deleted when none).", "",
             "| Repository | Tier | KavoshStart | Findings |", "|---|---|---|---|"]
    for repo, tier, pin, findings in rows:
        cell = "<br>".join(f"❌ {rule}: {text}" for rule, text in findings) or ("—" if pin == "not adopted" else "✅")
        lines.append(f"| {repo} | {tier} | {pin} | {cell} |")
    lines += ["", "_Trust boundary: if this report stops updating, Layer O itself is down — only a human detects that._"]
    return "\n".join(lines) + "\n", total_findings


def update_issue(text):
    def gh(*a):
        return subprocess.run(["gh", *a], capture_output=True, text=True, encoding="utf-8")
    gh("label", "create", "kavosh:portfolio", "-R", HOME, "--color", "5319E7", "--description", "Layer O portfolio findings", "--force")
    found = json.loads(gh("issue", "list", "-R", HOME, "--label", "kavosh:portfolio", "--state", "open", "--json", "number").stdout or "[]")
    if found:
        gh("issue", "edit", str(found[0]["number"]), "-R", HOME, "--body", text)
    else:
        gh("issue", "create", "-R", HOME, "--title", "Portfolio supervisor (Layer O)", "--label", "kavosh:portfolio", "--body", text)


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    text, findings = run(Api(), argv[0])
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).open("a", encoding="utf-8").write(text)
    if "--update-issue" in argv:
        update_issue(text)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
