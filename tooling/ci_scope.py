#!/usr/bin/env python3
"""Select existing conformance steps; core checks always run in the same required job.

Only an exact, non-empty, documentation-only PR diff can omit cross-domain tools.
Unknown event/diff/source means full verification, never a successful empty check.
"""
import json
import os
import re
import subprocess
from pathlib import Path

SAFE_DOC_ROOTS = ("docs/", "standard/", "adoption/", "intake/")
SAFE_DOC_FILES = {"README.md", "CHANGELOG.md", "PROJECT.md"}
SHA = re.compile(r"^[0-9a-f]{40}$")


def doc_only(path):
    return (isinstance(path, str) and ".." not in path.split("/")
            and not path.startswith("/") and path.endswith(".md")
            and (path in SAFE_DOC_FILES or path.startswith(SAFE_DOC_ROOTS)))


def choose_full(event_name, paths=None, requested=False, release_pr=False):
    if requested or release_pr or event_name == "push":
        return True, "explicit full request, release verification or main integration"
    if event_name == "workflow_dispatch":
        return False, "manual core verification; conformance was not requested"
    if event_name != "pull_request" or not paths:
        return True, "unknown event or unavailable/empty exact diff"
    if all(doc_only(path) for path in paths):
        return False, "documentation-only PR; core unit/schema/scaffold checks still run"
    return True, "source, templates, tests, dependencies or workflow boundary changed"


def changed_paths(base, cwd=None):
    if not SHA.fullmatch(base or ""):
        return None
    try:
        data = subprocess.check_output(
            ["git", "diff", "--name-only", "--no-renames", "-z", base, "HEAD", "--"],
            cwd=cwd, stderr=subprocess.DEVNULL, timeout=30)
        return [name.decode("utf-8", errors="strict") for name in data.split(b"\0") if name]
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError):
        return None


def main():
    event_name = os.environ.get("GITHUB_EVENT_NAME", "")
    try:
        event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    except (KeyError, OSError, ValueError) as error:
        raise SystemExit("workflow event unavailable; verification scope is unknown") from error
    inputs = event.get("inputs") or {}
    pr = str(inputs.get("pr-number") or "")
    expected = str(inputs.get("expected-head") or "")
    if event_name == "workflow_dispatch" and (pr or expected):
        if not (pr.isdigit() and int(pr) > 0 and SHA.fullmatch(expected)
                and expected == os.environ.get("GITHUB_SHA")):
            raise SystemExit("release verification requires the exact dispatch head and PR number")
    base = ((event.get("pull_request") or {}).get("base") or {}).get("sha")
    paths = changed_paths(base) if event_name == "pull_request" else None
    full, reason = choose_full(event_name, paths,
                              requested=inputs.get("ci-full") in (True, "true"), release_pr=bool(pr))
    output = f"full={str(full).lower()}\n"
    with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as handle:
        handle.write(output)
    summary = ("## Verification scope\nCore checks: required on every executing job.\n"
               f"Conformance: {'selected' if full else 'NOT_RUN (not selected)'}. {reason}.\n")
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as handle:
            handle.write(summary)
    print(output.strip(), reason)


if __name__ == "__main__":
    main()
