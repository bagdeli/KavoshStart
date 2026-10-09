#!/usr/bin/env python3
"""Private portfolio supervisor reference implementation.

This script is intentionally NOT wired into public KavoshStart Actions. Run it only
from a private control surface that owns its inventory and token.

Example:
  KAVOSH_PRIVATE_CONTROL_SURFACE=1 GH_TOKEN=... \
    python3 scripts/private_portfolio_guard.py --inventory /secure/kavosh-private.json

Inventory shape:
  {"schemaVersion": 1, "repositories": ["owner/private-repo", ...]}

The report may contain private repository names and therefore must remain inside the
private control surface. KavoshStart public files/issues/releases never receive it.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import portfolio_guard as pg  # noqa: E402

HOME = "bagdeli/KavoshStart"
PIN_RE = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def load_inventory(path: str) -> list[str]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schemaVersion") != 1:
        raise ValueError("private inventory schemaVersion must be 1")
    repos = data.get("repositories")
    if not isinstance(repos, list) or not repos:
        raise ValueError("private inventory repositories must be a non-empty array")
    if any(not isinstance(repo, str) or not REPO_RE.fullmatch(repo) for repo in repos):
        raise ValueError("private inventory contains an invalid owner/repository name")
    if len(repos) != len(set(repos)):
        raise ValueError("private inventory repositories must be unique")
    return repos


def latest_stable(api) -> str | None:
    releases = api.get(f"repos/{HOME}/releases?per_page=100") or []
    candidates = []
    for item in releases:
        tag = item.get("tag_name")
        match = PIN_RE.fullmatch(tag or "")
        if not match or item.get("draft") or item.get("prerelease"):
            continue
        candidates.append((tuple(map(int, match.groups())), tag))
    return max(candidates)[1] if candidates else None


def acceptance_findings(api, repo: str, branch: str, manifest: dict) -> list[tuple[str, str]]:
    if manifest.get("tier") != "T2":
        return []
    findings = []
    if (manifest.get("acceptance") or {}).get("mode") != "continuous":
        findings.append(("ACC-1", "T2 requires acceptance.mode=continuous"))
        return findings
    raw = pg.content(api, repo, "acceptance/scope.json", branch)
    if raw is None:
        return [("ACC-1", "continuous T2 is missing acceptance/scope.json")]
    try:
        scope = json.loads(raw)
    except ValueError:
        return [("ACC-1", "acceptance/scope.json is not valid JSON")]
    items = scope.get("items") if isinstance(scope, dict) else None
    if not isinstance(items, list) or not items:
        findings.append(("ACC-1", "continuous T2 acceptance scope must be non-empty"))
    return findings


def inspect_private(api, repo: str, latest: str | None):
    meta = api.get(f"repos/{repo}")
    if not meta:
        return None, [("O", "repository is not visible to the private supervisor token")], []
    if meta.get("private") is not True:
        return None, [("SEC-5", "private supervisor inventory contains a non-private repository")], []
    if meta.get("archived"):
        return None, [], [("O", "repository is archived")]

    branch = meta.get("default_branch") or "main"
    manifest, findings, info = pg.inspect_repo(api, repo, branch, True)
    warnings = []
    if not info.get("adopted"):
        return None, [("SRC-5", "kavosh.project.json is missing")], warnings

    pin = info.get("pin")
    if not isinstance(pin, str) or not PIN_RE.fullmatch(pin):
        findings.append(("STD-1", f"KavoshStart pin is not an exact stable tag: {pin!r}"))
    elif latest and pin != latest:
        warnings.append(("STD-1", f"KavoshStart pin {pin} is behind latest stable {latest}; run consumer preflight and classify the delta"))

    findings.extend(acceptance_findings(api, repo, branch, manifest))
    return info, findings, warnings


def run(api, inventory: list[str], latest: str | None = None):
    latest = latest if latest is not None else latest_stable(api)
    rows, failures, warnings = [], 0, 0
    for repo in inventory:
        info, bad, warn = inspect_private(api, repo, latest)
        failures += len(bad)
        warnings += len(warn)
        rows.append((repo, (info or {}).get("tier", "?"), (info or {}).get("pin", "?"), bad, warn))

    lines = [
        "# Private portfolio supervisor",
        "",
        f"Failures: **{failures}** · Freshness warnings: **{warnings}** · Latest KavoshStart: `{latest or 'unknown'}`",
        "",
        "| Repository | Tier | KavoshStart | Result |",
        "|---|---|---|---|",
    ]
    for repo, tier, pin, bad, warn in rows:
        cells = [f"❌ {rule}: {text}" for rule, text in bad]
        cells += [f"⚠️ {rule}: {text}" for rule, text in warn]
        lines.append(f"| {repo} | {tier} | {pin} | {'<br>'.join(cells) or '✅'} |")
    lines += [
        "",
        "_PRIVATE OUTPUT: target names/findings must stay inside the private control surface._",
    ]
    return "\n".join(lines) + "\n", failures, warnings


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--inventory", required=True, help="private JSON inventory path")
    parser.add_argument("--report", help="optional private report output path")
    args = parser.parse_args(argv)

    if os.environ.get("KAVOSH_PRIVATE_CONTROL_SURFACE") != "1":
        print("refusing to emit private portfolio metadata: set KAVOSH_PRIVATE_CONTROL_SURFACE=1 in the private control surface", file=sys.stderr)
        return 2
    if os.environ.get("GITHUB_REPOSITORY") == HOME:
        print("refusing to run private supervisor from public KavoshStart", file=sys.stderr)
        return 2

    try:
        inventory = load_inventory(args.inventory)
        report, failures, _warnings = run(pg.Api(), inventory)
    except (OSError, ValueError, PermissionError, RuntimeError) as exc:
        print(f"private supervisor failed: {exc}", file=sys.stderr)
        return 2

    print(report, end="")
    if args.report:
        Path(args.report).write_text(report, encoding="utf-8")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
