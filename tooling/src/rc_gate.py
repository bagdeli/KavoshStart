#!/usr/bin/env python3
"""REL-7: create an immutable release-candidate only from exact current main with required checks green."""
import argparse
import json
import os
import re
import subprocess
import sys

RC_RE = re.compile(r"^v([0-9]+)[.]([0-9]+)[.]([0-9]+)-rc[.]([0-9]+)$")
FINAL_RE = re.compile(r"^v([0-9]+)[.]([0-9]+)[.]([0-9]+)$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DEFAULT_REQUIRED = ("required", "main-guard / main-guard")


def parse_rc(tag):
    m = RC_RE.fullmatch(tag or "")
    return tuple(map(int, m.groups())) if m else None


def parse_final(tag):
    m = FINAL_RE.fullmatch(tag or "")
    return tuple(map(int, m.groups())) if m else None


def evaluate_checks(runs, required):
    latest = {}
    pending = {}
    for run in runs:
        name = run.get("name", "")
        if run.get("status") != "completed":
            pending[name] = run
        stamp = run.get("started_at") or run.get("created_at") or ""
        old = latest.get(name)
        old_stamp = (old or {}).get("started_at") or (old or {}).get("created_at") or ""
        pending_now = run.get("status") != "completed"
        pending_old = (old or {}).get("status") != "completed"
        if (old is None or stamp > old_stamp or
                (pending_now and not pending_old and (not stamp or stamp == old_stamp))):
            latest[name] = run
    latest.update(pending)
    reasons = []
    for name in required:
        run = latest.get(name)
        if run is None:
            reasons.append(f"missing required check '{name}'")
        elif run.get("status") != "completed":
            reasons.append(f"'{name}' is {run.get('status')}")
        elif run.get("conclusion") != "success":
            reasons.append(f"'{name}' concluded {run.get('conclusion')}")
    return reasons


def candidate_reasons(tag, sha, required, current_head, runs, tag_names):
    rc = parse_rc(tag)
    reasons = []
    if not rc:
        reasons.append("tag must match vX.Y.Z-rc.N")
        return reasons
    if not SHA_RE.fullmatch(sha or ""):
        reasons.append("expected SHA must be 40 lowercase hex")
    if current_head != sha:
        reasons.append("expected SHA is not the current main head")
    required = list(dict.fromkeys(required))
    if not set(DEFAULT_REQUIRED).issubset(required):
        reasons.append("required checks must include required and main-guard / main-guard")
    reasons += evaluate_checks(runs, required)

    base = rc[:3]
    rc_number = rc[3]
    names = set(tag_names)
    if tag in names:
        reasons.append("RC tag already exists")
    final_name = "v" + ".".join(map(str, base))
    if final_name in names:
        reasons.append("final tag for this version already exists")

    finals = [v for name in names if (v := parse_final(name))]
    if finals and max(finals) >= base:
        reasons.append("RC base version must be newer than the latest final version")

    same_base = [r[3] for name in names if (r := parse_rc(name)) and r[:3] == base]
    if same_base and rc_number <= max(same_base):
        reasons.append("RC number must be greater than every existing RC for this version")
    return reasons


def gh_api(path, method="GET", payload=None, allow_missing=False):
    cmd = ["gh", "api"]
    if method != "GET":
        cmd += ["-X", method]
    cmd.append(path)
    if payload is not None:
        cmd += ["--input", "-"]
    result = subprocess.run(cmd, input=json.dumps(payload) if payload is not None else None,
                            capture_output=True, text=True, encoding="utf-8")
    if result.returncode != 0:
        if allow_missing and ("404" in result.stderr or "Not Found" in result.stderr):
            return None
        raise RuntimeError(f"gh api {path}: {result.stderr.strip()}")
    return json.loads(result.stdout) if result.stdout.strip() else {}


def paged(repo, suffix, key=None):
    out = []
    for page in range(1, 11):
        sep = "&" if "?" in suffix else "?"
        data = gh_api(f"repos/{repo}/{suffix}{sep}per_page=100&page={page}")
        batch = data.get(key, []) if key else data
        out += batch
        if len(batch) < 100:
            break
    return out


def run_gate(repo, tag, sha, required):
    head = gh_api(f"repos/{repo}/branches/main").get("commit", {}).get("sha")
    runs = paged(repo, f"commits/{sha}/check-runs", key="check_runs")
    tags = [item.get("name", "") for item in paged(repo, "tags")]
    reasons = candidate_reasons(tag, sha, required, head, runs, tags)
    if gh_api(f"repos/{repo}/releases/tags/{tag}", allow_missing=True) is not None:
        reasons.append("GitHub Release for this RC already exists")
    return list(dict.fromkeys(reasons))


def create_prerelease(repo, tag, sha):
    release = gh_api(f"repos/{repo}/releases", method="POST", payload={
        "tag_name": tag,
        "target_commitish": sha,
        "name": tag,
        "prerelease": True,
        "draft": False,
        "generate_release_notes": True,
    })
    ref = gh_api(f"repos/{repo}/git/ref/tags/{tag}")
    actual = ref.get("object", {}).get("sha")
    if actual != sha or release.get("tag_name") != tag or release.get("prerelease") is not True:
        raise RuntimeError(f"post-create RC verification failed: tag points to {actual or '?'}")
    return release


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--sha", required=True)
    p.add_argument("--required", default=",".join(DEFAULT_REQUIRED))
    args = p.parse_args(argv)
    required = [x.strip() for x in args.required.split(",") if x.strip()]
    try:
        reasons = run_gate(args.repo, args.tag, args.sha, required)
    except RuntimeError as exc:
        print(f"REL-7 gate CLOSED: {exc}")
        return 1
    if reasons:
        print("REL-7 gate CLOSED:")
        for reason in reasons:
            print(f"  - {reason}")
        return 1
    # Re-read the exact main/check/tag state immediately before mutation. The owner authorization
    # is capability-scoped to this tag + SHA and expires if main/check state moved.
    try:
        reasons = run_gate(args.repo, args.tag, args.sha, required)
    except RuntimeError as exc:
        print(f"REL-7 pre-create gate CLOSED: {exc}")
        return 1
    if reasons:
        print("REL-7 pre-create gate CLOSED:")
        for reason in reasons:
            print(f"  - {reason}")
        return 1
    try:
        release = create_prerelease(args.repo, args.tag, args.sha)
    except RuntimeError as exc:
        print(f"REL-7 creation FAILED: {exc}")
        return 1
    print(f"REL-7 RC CREATED {release.get('html_url', args.tag)}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"tag={args.tag}\n")
            fh.write(f"release-url={release.get('html_url', '')}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
