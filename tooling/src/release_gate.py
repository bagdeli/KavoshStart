#!/usr/bin/env python3
"""Release gate (REL-5): a release may be created only from a `main` commit whose required checks
exist AND succeeded. Missing, pending (after the wait), failed, cancelled or skipped = no release.
CI being unavailable (e.g. billing) is never permission to release.

    python3 tooling/src/release_gate.py --repo owner/name --sha <commit>
        [--required "required,main-guard / main-guard"] [--wait 300] [--branch main]

Exit 0 = gate open, or the commit was superseded by a newer main head (nothing to do, not an error).
Exit 1 = gate closed (reason printed). Writes open=true|false to $GITHUB_OUTPUT when available.
Needs gh (GH_TOKEN) and python3 stdlib only. Embedded into kavosh-release.yml by build_workflows.py.
"""
import argparse
import json
import os
import subprocess
import sys
import time

DEFAULT_REQUIRED = ["required", "main-guard / main-guard"]
PENDING = {"queued", "in_progress", "waiting", "requested", "pending"}


def gh_api(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True, encoding="utf-8")
    if r.returncode != 0:
        raise RuntimeError(f"gh api {path}: {r.stderr.strip()}")
    return json.loads(r.stdout) if r.stdout.strip() else {}


def check_runs(repo, sha, api=None):
    api = api or gh_api
    runs, page = [], 1
    while True:
        data = api(f"repos/{repo}/commits/{sha}/check-runs?per_page=100&page={page}")
        batch = data.get("check_runs", [])
        runs += batch
        if len(batch) < 100:
            return runs
        page += 1


def evaluate(runs, required):
    """Return (open, pending, reasons). The newest run per name wins (re-runs replace older results)."""
    latest = {}
    for r in runs:
        name = r.get("name", "")
        if name not in latest or (r.get("started_at") or "") > (latest[name].get("started_at") or ""):
            latest[name] = r
    reasons, pending = [], False
    for name in required:
        r = latest.get(name)
        if r is None:
            reasons.append(f"missing required check '{name}'")
        elif r.get("status") in PENDING:
            pending = True
            reasons.append(f"'{name}' is still {r.get('status')}")
        elif r.get("conclusion") != "success":
            reasons.append(f"'{name}' concluded {r.get('conclusion')}")
    return (not reasons), pending, reasons


def gate(repo, sha, required, branch="main", wait=300, interval=15, api=None, sleep=time.sleep):
    api = api or gh_api
    head = api(f"repos/{repo}/branches/{branch}").get("commit", {}).get("sha")
    if head != sha:
        return None, [f"{sha[:7]} is not the current head of {branch} ({(head or '?')[:7]}); the next run will handle the newer commit"]
    deadline = time.monotonic() + wait
    while True:
        ok, pending, reasons = evaluate(check_runs(repo, sha, api), required)
        if ok or not pending or time.monotonic() >= deadline:
            return ok, reasons
        sleep(interval)


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--repo", required=True)
    p.add_argument("--sha", required=True)
    p.add_argument("--branch", default="main")
    p.add_argument("--required", default=",".join(DEFAULT_REQUIRED))
    p.add_argument("--wait", type=int, default=300, help="seconds to wait for pending required checks")
    a = p.parse_args(argv)
    required = [x.strip() for x in a.required.split(",") if x.strip()]
    if not required:
        print("REL-5: no required checks configured — refusing to open the gate")
        return 1
    try:
        ok, reasons = gate(a.repo, a.sha, required, a.branch, a.wait)
    except RuntimeError as e:
        print(f"REL-5 gate CLOSED: cannot read checks ({e}) — unavailable CI is not permission to release")
        return 1
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"open={'true' if ok else 'false'}\n")
    if ok is None:
        print(f"REL-5: {reasons[0]} — skipping")
        return 0
    if ok:
        print(f"REL-5 gate OPEN for {a.sha[:7]}: {', '.join(required)} succeeded")
        return 0
    print(f"REL-5 gate CLOSED for {a.sha[:7]}:")
    for r in reasons:
        print(f"  - {r}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
