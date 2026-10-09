#!/usr/bin/env python3
"""Layer O — public portfolio supervisor.

A repository cannot reliably report that its own enforcement was deleted or neutered, so Layer O checks adopted
PUBLIC repositories from outside. Private repositories are skipped before their name, metadata, files or findings
can enter the public report. Private-project monitoring belongs in a separate private control surface.

    python3 scripts/portfolio_guard.py bagdeli                  # public report to stdout, exit 1 if findings
    python3 scripts/portfolio_guard.py bagdeli --update-issue   # keep one public `kavosh:portfolio` issue

In CI use the repository-scoped GITHUB_TOKEN with only the Contents, Actions, Pull requests and Issues
permissions needed for this public repository. No account PAT or shared secret is required. Settings that require
administrative access are outside this monitor's authority and must be checked by the repository owner.

Trust boundary: public Layer O depends on this repository and GitHub Actions. If it stops running, only a human
notices (the portfolio issue stops updating). The standard does not claim visibility into private projects.
"""
import base64
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
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
PUBLIC_INVENTORY = Path(__file__).resolve().parents[1] / ".github" / "kavosh-public-repositories.json"


class Api:
    """GitHub REST via Python stdlib; tests replace this with fakes at the same trust boundary."""

    def request(self, path, method="GET", payload=None, allow_status=()):
        base = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
        token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
        if not token:
            raise PermissionError("GitHub API token is unavailable")
        url = path if path.startswith("https://") else f"{base}/{path.lstrip('/')}"
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={"Authorization": f"Bearer {token}",
                     "Accept": "application/vnd.github+json",
                     "X-GitHub-Api-Version": "2022-11-28",
                     "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                raw = response.read().decode("utf-8")
        except urllib.error.HTTPError as exc:
            if exc.code in set(allow_status):
                return None
            detail = exc.read().decode("utf-8", errors="replace")
            raise PermissionError(f"GitHub API {method} {path}: HTTP {exc.code} {detail[:200]}") from exc
        return json.loads(raw) if raw.strip() else None

    def get(self, path):
        return self.request(path, allow_status=(404,))

    def repos(self, owner):
        out = []
        for page in range(1, 4):
            batch = self.get(f"users/{owner}/repos?per_page=100&page={page}") or []
            out += [{"nameWithOwner": item.get("full_name"),
                     "isPrivate": item.get("private"),
                     "isArchived": item.get("archived"),
                     "defaultBranchRef": {"name": item.get("default_branch")}}
                    for item in batch]
            if len(batch) < 100:
                break
        return out


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
    for level, rule, title, detail in wiring_problems(workflows, m, repo):
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
    head = (api.get(f"repos/{repo}/branches/{branch}") or {}).get("commit", {}).get("sha")
    if head:
        runs = (api.get(f"repos/{repo}/commits/{head}/check-runs?per_page=100") or {}).get("check_runs", [])
        if not any(r.get("name") == "main-guard / main-guard" for r in runs):
            findings.append(("M", f"no main-guard check on the head of {branch} — the guard is not running"))

    issues = api.get(f"repos/{repo}/issues?labels=kavosh:health&state=all&per_page=100") or []
    latest_health = max(issues, key=lambda item: item["updated_at"], default=None)
    if latest_health is None:
        findings.append(("H", "no `kavosh:health` report — weekly health has not run"))
    elif days_since(latest_health["updated_at"]) > HEALTH_MAX_AGE_DAYS:
        age = days_since(latest_health["updated_at"])
        findings.append(("H", f"health report not updated for {age} days — weekly health stopped"))
    viol = api.get(f"repos/{repo}/issues?labels=kavosh:violation&state=open") or []
    if viol:
        findings.append(("PR-7", f"{len(viol)} open violation issue(s): " + ", ".join(f"#{i['number']}" for i in viol)))

    actual = "private" if private else "public"
    if m.get("visibility") and m["visibility"] != actual:
        findings.append(("CI-1", f"repository is {actual} but manifest says {m['visibility']}"))
    budget = m.get("ci", {}).get("monthlyMinutesBudget", 0) if private else 0
    return m, findings, {"adopted": True, "budget": budget, "tier": m.get("tier"), "pin": m.get("kavoshStart")}


def run(api, owner, inventory=None):
    rows, total_budget, total_findings = [], 0, 0
    frozen_v1 = []
    if inventory is None:
        try:
            registry = json.loads(PUBLIC_INVENTORY.read_text(encoding="utf-8"))
            inventory = registry["repositories"]
        except (OSError, ValueError, KeyError, TypeError):
            inventory = []
            total_findings += 1
            rows.append(("public inventory unavailable", "?", "?", [("O", "the governed public repository inventory cannot be read")]))
    for repo in inventory:
        # The curated public registry is independent from each consumer's manifest. Check current visibility
        # before fetching any file; recheck after inspection and suppress entries that became private/unknown.
        try:
            fresh = api.get(f"repos/{repo}")
        except PermissionError:
            fresh = None
        if not fresh:
            rows.append(("visibility unverifiable", "?", "?", [("O", "a registered public repository could not be revalidated; details withheld")]))
            total_findings += 1
            continue
        if fresh.get("private") is not False or fresh.get("archived"):
            continue
        branch = (fresh.get("default_branch") or "main")
        try:
            m, findings, info = inspect_repo(api, repo, branch, False)
        except PermissionError:
            try:
                still_public = (api.get(f"repos/{repo}") or {}).get("private") is False
            except PermissionError:
                still_public = False
            if not still_public:
                continue
            rows.append((repo, "?", "?", [("O", "cannot inspect this public repository")]))
            total_findings += 1
            continue
        try:
            still_public = (api.get(f"repos/{repo}") or {}).get("private") is False
        except PermissionError:
            still_public = False
        if not still_public:
            continue
        if not info.get("adopted"):
            rows.append((repo, "—", "manifest missing", [("SRC-5", "adopted repository has no kavosh.project.json")]))
            total_findings += 1
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


def update_issue(text, findings, api=None):
    """Keep one canonical public Layer O issue; green closes it, findings create/update it."""
    api = api or Api()
    api.request(f"repos/{HOME}/labels", method="POST",
                payload={"name": "kavosh:portfolio", "color": "5319E7",
                         "description": "Layer O portfolio findings"},
                allow_status=(422,))
    label = urllib.parse.quote("kavosh:portfolio", safe="")
    found = api.get(f"repos/{HOME}/issues?labels={label}&state=open&per_page=100") or []
    found = [item for item in found if "pull_request" not in item]
    if findings == 0:
        if found:
            number = found[0]["number"]
            api.request(f"repos/{HOME}/issues/{number}", method="PATCH",
                        payload={"state": "closed", "state_reason": "completed"})
            api.request(f"repos/{HOME}/issues/{number}/comments", method="POST",
                        payload={"body": "Latest Layer O report has zero findings."})
        return
    if found:
        api.request(f"repos/{HOME}/issues/{found[0]['number']}", method="PATCH", payload={"body": text})
    else:
        api.request(f"repos/{HOME}/issues", method="POST",
                    payload={"title": "Portfolio supervisor (Layer O)",
                             "labels": ["kavosh:portfolio"], "body": text})


def main(argv):
    if not argv or argv[0].startswith("-"):
        print(__doc__)
        return 2
    api = Api()
    text, findings = run(api, argv[0])
    print(text)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        Path(summary).open("a", encoding="utf-8").write(text)
    if "--update-issue" in argv:
        update_issue(text, findings, api)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
