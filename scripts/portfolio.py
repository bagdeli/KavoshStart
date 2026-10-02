#!/usr/bin/env python3
"""Portfolio view of all KavoshStart projects of an owner (standard/09, CI-3). Read-only; runs locally with gh.

    python3 scripts/portfolio.py bagdeli            # all repos with kavosh.project.json
    python3 scripts/portfolio.py bagdeli --minutes  # + estimated billable minutes this month (slower)
"""
import base64
import json
import math
import subprocess
import sys
from datetime import datetime, timezone

ACCOUNT_LIMIT, RESERVE_LIMIT = 2000, 1600
NOW = datetime.now(timezone.utc)


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def minutes(repo):
    total, page = 0, 1
    start = NOW.strftime("%Y-%m-01")
    while page <= 4:
        data = gh(f"repos/{repo}/actions/runs?created=%3E%3D{start}&per_page=100&page={page}") or {}
        runs = data.get("workflow_runs", [])
        for run in runs:
            for job in (gh(f"repos/{repo}/actions/runs/{run['id']}/jobs?per_page=100") or {}).get("jobs", []):
                if "self-hosted" in (job.get("labels") or []) or not job.get("completed_at") or not job.get("started_at"):
                    continue
                total += math.ceil(max((ts(job["completed_at"]) - ts(job["started_at"])).total_seconds(), 1) / 60)
        if len(runs) < 100:
            break
        page += 1
    return total


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return 2
    owner, with_minutes = sys.argv[1], "--minutes" in sys.argv
    repos = json.loads(subprocess.run(["gh", "repo", "list", owner, "--limit", "200", "--no-archived", "--json",
                                       "nameWithOwner,isPrivate"], capture_output=True, text=True, encoding="utf-8",
                                      check=True).stdout)
    rows, budget_sum, used_sum = [], 0, 0
    for r in repos:
        name = r["nameWithOwner"]
        raw = gh(f"repos/{name}/contents/kavosh.project.json")
        if not raw:
            rows.append((name, "—", "—", "not adopted", "", "", ""))
            continue
        m = json.loads(base64.b64decode(raw["content"]).decode("utf-8"))
        budget = m.get("ci", {}).get("monthlyMinutesBudget", 0) if r["isPrivate"] else 0
        budget_sum += budget
        used = minutes(name) if with_minutes and r["isPrivate"] else None
        used_sum += used or 0
        rel = gh(f"repos/{name}/releases?per_page=1") or []
        viol = gh(f"repos/{name}/issues?labels=kavosh:violation&state=open") or []
        rows.append((name, m.get("tier"), m.get("runtime"), m.get("kavoshStart"),
                     f"{used if used is not None else '?'} / {budget}" if r["isPrivate"] else "public standard hosted (no Actions-minute charge; storage is separate)",
                     rel[0]["tag_name"] if rel else "none", str(len(viol))))
    print(f"| Repository | Tier | Runtime | KavoshStart | Minutes (month) | Latest release | Violations |")
    print("|---|---|---|---|---|---|---|")
    for row in rows:
        print("| " + " | ".join(str(c) for c in row) + " |")
    print()
    ok = budget_sum <= RESERVE_LIMIT
    print(f"Sum of budgets: {budget_sum} / {RESERVE_LIMIT} allowed ({ACCOUNT_LIMIT} account limit) — {'OK' if ok else 'OVER — CI-3 violated'}")
    if with_minutes:
        print(f"Estimated billable minutes used this month (private repos, hosted runners): {used_sum} / {ACCOUNT_LIMIT}")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
