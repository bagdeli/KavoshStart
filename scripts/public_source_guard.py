#!/usr/bin/env python3
"""Generic, conservative prepublication screening for this PUBLIC standards repo.

The scanner knows only the public upstream identity and deliberately fictional
names; real private consumer inventories, URLs and examples NEVER belong here.
It must not echo suspect text or private file paths to an Actions log.
It is a supplement to human review before a GitHub Issue/PR/comment exists.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
PUBLIC_NAME = "KavoshStart"
# Reserved synthetic fixture identities, not a catalog of real consumers.
FICTIONAL_NAMES = frozenset({"Example", "Demo", "ExampleConsumer", "PrivateDemo"})
REPO_REF = re.compile(r"(?i)\bbagdeli/(?:[a-z0-9_.-]+)")
BRANDED_NAME = re.compile(r"\bKavosh(?!Start\b)[A-Z][A-Za-z0-9]*\b")
INTERNAL_HOST = re.compile(r"(?i)\b[a-z0-9-]+(?:\.[a-z0-9-]+)*\.(?:internal|lan|corp|local)\b")


def categories(text: str, private_literals: tuple[str, ...] = ()) -> set[str]:
    """Find obvious references only; never return or print matched content."""
    found = set()
    for match in REPO_REF.finditer(text):
        name = match.group(0).split("/", 1)[1]
        if name.casefold() not in {x.casefold() for x in FICTIONAL_NAMES | {PUBLIC_NAME}}:
            found.add("unknown-owner-repository")
    if BRANDED_NAME.search(text):
        found.add("specific-project-identifier")
    if INTERNAL_HOST.search(text):
        found.add("internal-host")
    # An optional owner-held, untracked literal inventory may add matches.
    for literal in private_literals:
        if literal and literal.casefold() in text.casefold():
            found.add("external-private-identifier")
            break
    return found


def tracked_bytes(staged: bool) -> list[bytes]:
    if staged:
        names = subprocess.check_output(
            ["git", "-C", str(ROOT), "diff", "--cached", "--name-only",
             "--diff-filter=ACMR", "-z"], stderr=subprocess.DEVNULL
        ).split(b"\0")
    else:
        names = subprocess.check_output(
            ["git", "-C", str(ROOT), "ls-files", "-z"],
            stderr=subprocess.DEVNULL
        ).split(b"\0")
    contents = []
    for raw in names:
        if not raw:
            continue
        name = os.fsdecode(raw)
        # Inspect path names too, but do not echo them in error messages.
        contents.append(raw)
        if staged:
            try:
                data = subprocess.check_output(
                    ["git", "-C", str(ROOT), "show", f":{name}"],
                    stderr=subprocess.DEVNULL
                )
            except subprocess.CalledProcessError:
                continue
        else:
            try:
                data = (ROOT / name).read_bytes()
            except (FileNotFoundError, IsADirectoryError, PermissionError):
                continue
        if b"\0" not in data:  # binary assets cannot be safely decoded into source facts
            contents.append(data)
    return contents


def local_literals(path_value: str | None) -> tuple[str, ...]:
    if not path_value:
        return ()
    path = Path(path_value).resolve()
    if path == ROOT or ROOT in path.parents:
        raise ValueError("external private-pattern file must stay outside public repository")
    # The file path and literals are deliberately absent from all logs.
    content = path.read_text(encoding="utf-8")
    return tuple(line.strip() for line in content.splitlines()
                 if line.strip() and not line.lstrip().startswith("#"))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Screen public source without leaking the findings")
    modes = ap.add_mutually_exclusive_group()
    modes.add_argument("--staged", action="store_true")
    modes.add_argument("--stdin", action="store_true",
                       help="preflight a proposed public issue/PR/comment before posting it")
    ap.add_argument("--private-literals-file", default=None,
                    help="optional operator-only inventory outside this public checkout")
    args = ap.parse_args(argv)
    try:
        sensitive = local_literals(args.private_literals_file)
        if args.stdin:
            candidates = [sys.stdin.buffer.read()]
        else:
            candidates = tracked_bytes(args.staged)
        counts: dict[str, int] = {}
        for blob in candidates:
            if b"\0" in blob:
                continue
            for category in categories(blob.decode("utf-8", errors="replace"), sensitive):
                counts[category] = counts.get(category, 0) + 1
    except (OSError, UnicodeError, ValueError, subprocess.CalledProcessError) as exc:
        # Never serialize a private pathname or private literal in output.
        print(f"SEC-5: privacy preflight unavailable ({type(exc).__name__}); no PASS", file=sys.stderr)
        return 2
    if counts:
        print("SEC-5: blocked potential confidential reference(s): " +
              ", ".join(f"{key}={value}" for key, value in sorted(counts.items())) +
              ". Inspect locally; do not post the candidate text or identifiers.", file=sys.stderr)
        return 1
    print("SEC-5: generic pattern preflight passed (human semantic review still required)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
