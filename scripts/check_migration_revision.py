#!/usr/bin/env python3
"""Optional read-only revision check for ONE-head migration profiles.

Read authoritative source head(s) from the checked-out migration tool and
optionally compare an observed applied current revision; never run upgrade.
Only operator-reviewed native commands are meaningful evidence. No shell is used.
Never print command stdout/stderr (may contain private infrastructure details).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

REV = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
SUFFIX = re.compile(r"^\s*([A-Za-z0-9][A-Za-z0-9._-]{0,127})(?:\s+\(head\))?\s*$")
RESERVED = {"head", "heads", "base", "current", "latest", "none", "unknown"}


def parse_single_revision(output: str) -> str:
    """Read exactly one immutable revision, or reject the source as ambiguous."""
    if not isinstance(output, str) or len(output.encode("utf-8")) > 4096:
        raise ValueError("invalid revision output size")
    rows = output.strip().splitlines()
    if len(rows) != 1:
        raise ValueError("expected exactly one revision line")
    match = SUFFIX.fullmatch(rows[0])
    if not match or not REV.fullmatch(match[1]) or match[1].lower() in RESERVED:
        raise ValueError("invalid or ambiguous revision format")
    return match[1]


def argv(raw: str) -> list[str]:
    try:
        value = json.loads(raw)
    except (TypeError, ValueError) as exc:
        raise ValueError("command must be a JSON argument list") from exc
    if (not isinstance(value, list) or not 1 <= len(value) <= 32
            or any(not isinstance(x, str) or not x or len(x) > 256 or "\0" in x
                   for x in value)):
        raise ValueError("invalid command argument list")
    # No subprocess shell is used; operator still must choose a trustworthy
    # native command instead of e.g. echo of a preselected expected revision.
    return value


def observed_revision(command: list[str], seconds: int = 20) -> str:
    try:
        result = subprocess.run(
            command, capture_output=True, timeout=seconds, check=False,
            text=True, encoding="utf-8", errors="replace"
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ValueError(f"revision command unavailable ({type(exc).__name__})") from exc
    if result.returncode != 0:
        raise ValueError("revision command exited nonzero")
    return parse_single_revision(result.stdout)


def main(args: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only one-head migration source/current check")
    parser.add_argument("--source-command", required=True, help="JSON argv for native source heads command")
    parser.add_argument("--applied-command", help="JSON argv for read-only applied revision command")
    opts = parser.parse_args(args)
    try:
        expected = observed_revision(argv(opts.source_command))
        if opts.applied_command:
            observed = observed_revision(argv(opts.applied_command))
            if expected != observed:
                raise ValueError("source head and applied revision differ")
    except ValueError as exc:
        # No command, stdout, revision, path or DB hostname is echoed.
        print(f"MIGRATION_HEAD=FAIL ({type(exc).__name__}; source/current proof invalid)", file=sys.stderr)
        return 1
    status = "source-and-applied" if opts.applied_command else "source-only"
    print(f"MIGRATION_HEAD=PASS scope={status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
