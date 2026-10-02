# KavoshStart main guard (layer M). Embedded into .github/workflows/kavosh-main-guard.yml.
# Runs on every push to the default branch. It never rewrites history; it records violations in ONE
# open issue labelled `kavosh:violation` so nothing is silently lost (BR-6, BR-7, PR-7).
# A merged PR must have every required check PRESENT and SUCCESSFUL on its head commit:
# missing, pending, failed, cancelled or skipped are all violations.
import json
import os
import subprocess
import sys
from datetime import datetime, timezone

SCAFFOLD_PREFIX = "chore: scaffold from KavoshStart"
DEFAULT_REQUIRED = ["kavosh / governance", "required"]
MAX_COMMITS = 20  # GitHub push payloads list at most 20 commits


def gh_api(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(f"gh api {path}: {r.stderr.strip()}")
    return json.loads(r.stdout) if r.stdout.strip() else None


def check_state(runs, required):
    """Newest run per name wins. Returns a list of problems for the required checks."""
    latest = {}
    pending_runs = {}
    for r in runs:
        name = r.get("name", "")
        if r.get("status") != "completed":
            pending_runs[name] = r
        stamp = r.get("started_at") or r.get("created_at") or ""
        previous = latest.get(name, {})
        previous_stamp = previous.get("started_at") or previous.get("created_at") or ""
        pending = r.get("status") != "completed"
        previous_pending = previous.get("status") != "completed"
        if (name not in latest or stamp > previous_stamp or
                (pending and not previous_pending and (not stamp or stamp == previous_stamp))):
            latest[name] = r
    # An ambiguous in-flight rerun must never inherit an older green result. Once a
    # run completes, conclusion and run timestamps determine which result is newest.
    latest.update(pending_runs)
    problems = []
    for name in required:
        r = latest.get(name)
        if r is None:
            problems.append(f"'{name}' missing")
        elif r.get("status") != "completed":
            problems.append(f"'{name}' {r.get('status')}")
        elif r.get("conclusion") != "success":
            problems.append(f"'{name}' {r.get('conclusion')}")
    return problems


def manual_dispatch_event(repo, expected_sha, actor, api):
    """Build a bounded main-push audit only if the owner dispatched against the current main SHA."""
    if not expected_sha:
        raise RuntimeError("manual main-guard dispatch needs an exact authorized SHA")
    branch = api(f"repos/{repo}/branches/main") or {}
    current = (branch.get("commit") or {}).get("sha", "")
    if current != expected_sha:
        raise RuntimeError(f"authorization expired: main is {current or '<unavailable>'}, expected {expected_sha}")
    commit = api(f"repos/{repo}/commits/{expected_sha}") or {}
    message = (commit.get("commit") or {}).get("message", "")
    parents = commit.get("parents") or []
    return {"ref": "refs/heads/main", "before": (parents[0] if parents else {}).get("sha", "0" * 40),
            "after": expected_sha, "forced": False, "pusher": {"name": actor or "?"},
            "commits": [{"id": expected_sha, "message": message}]}


def inspect(event, repo, required, api):
    violations = []
    required = list(dict.fromkeys(required or []))
    if not set(DEFAULT_REQUIRED).issubset(required):
        violations.append(f"**PR-7 configuration error** required checks must include {', '.join(DEFAULT_REQUIRED)}")
    if event.get("forced"):
        violations.append(f"**BR-7 force-push** to `{event.get('ref')}` by @{(event.get('pusher') or {}).get('name', '?')} "
                          f"(`{(event.get('before') or '')[:7]}` → `{(event.get('after') or '')[:7]}`)")
    commits = event.get("commits") or []
    if len(commits) > 1:
        violations.append(f"**BR-6** one push added {len(commits)}{'+' if len(commits) >= MAX_COMMITS else ''} commits to main "
                          f"— a squash merge always adds exactly one")
    for c in commits[:MAX_COMMITS]:
        sha, msg = c["id"], (c.get("message") or "").splitlines()[0]
        pulls = api(f"repos/{repo}/commits/{sha}/pulls") or []
        merged = [p for p in pulls if p.get("merged_at") and p.get("merge_commit_sha") == sha
                  and p.get("base", {}).get("ref") in ("main", "master")]
        if not merged:
            if msg.startswith(SCAFFOLD_PREFIX) and not (api(f"repos/{repo}/commits/{sha}") or {}).get("parents"):
                continue  # the initial scaffold of an empty repository is the single allowed direct commit
            violations.append(f"**BR-6 direct push** `{sha[:7]}` “{msg}” — no merged pull request")
            continue
        pr = merged[0]
        runs, page = [], 1
        while True:
            batch = (api(f"repos/{repo}/commits/{pr['head']['sha']}/check-runs?per_page=100&page={page}") or {}).get("check_runs", [])
            runs.extend(batch)
            if len(batch) < 100:
                break
            page += 1
        problems = check_state(runs, required)
        if problems:
            violations.append(f"**PR-7 merged without green required checks** #{pr['number']} “{pr['title']}” — {', '.join(problems)}")
    return violations


def record(repo, event, violations):
    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry = f"### {now} — push `{(event.get('after') or '')[:7]}`\n" + "\n".join(f"- [ ] {v}" for v in violations) + "\n"

    def gh(*a, check=True):
        return subprocess.run(["gh", *a], capture_output=True, text=True, encoding="utf-8", check=check)

    gh("label", "create", "kavosh:violation", "-R", repo, "--color", "B60205",
       "--description", "KavoshStart rule violation detected on main", "--force", check=False)
    existing = json.loads(gh("issue", "list", "-R", repo, "--label", "kavosh:violation", "--state", "open",
                             "--json", "number,body").stdout or "[]")
    if existing:
        gh("issue", "edit", str(existing[0]["number"]), "-R", repo, "--body", (existing[0]["body"] or "") + "\n" + entry)
    else:
        body = ("Violations of KavoshStart rules detected on `main`. Fix each with a PR (revert or correction), tick it, "
                "and close this issue when all are resolved.\n"
                "Rules: https://github.com/bagdeli/KavoshStart/blob/main/standard/RULES.md\n\n" + entry)
        gh("issue", "create", "-R", repo, "--title", "KavoshStart: rule violations on main", "--label", "kavosh:violation", "--body", body)
    return entry


def main():
    repo = os.environ["REPO"]
    required = [x.strip() for x in os.environ.get("REQUIRED", ",".join(DEFAULT_REQUIRED)).split(",") if x.strip()]
    event = json.load(open(os.environ["GITHUB_EVENT_PATH"], encoding="utf-8"))
    if os.environ.get("GITHUB_EVENT_NAME") == "workflow_dispatch":
        try:
            event = manual_dispatch_event(repo, os.environ.get("AUTHORIZED_SHA", ""),
                                          os.environ.get("GITHUB_ACTOR", "?"), gh_api)
        except RuntimeError as e:
            print(str(e))
            return 1
    try:
        violations = inspect(event, repo, required, gh_api)
    except RuntimeError as e:
        violations = [f"**main guard could not inspect this push** ({e}) — verify manually"]
    print("\n".join(violations) or "no violations")
    if not violations:
        return 0
    entry = record(repo, event, violations)
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write("## KavoshStart main guard\n\n" + entry)
    return 1  # a red main-guard check is itself visible and closes the REL-5 gate


if __name__ == "__main__":
    sys.exit(main())
