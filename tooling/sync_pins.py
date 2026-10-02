#!/usr/bin/env python3
"""Synchronize Dependabot's workflow action pins to workflow templates.

Source of truth: the repository workflows in .github/workflows/*.yml.
Updates matching owner/action references in tooling/templates and product templates.
"""
import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTION_RE = re.compile(
    r"^(?P<prefix>[ \t]*-[ \t]+uses:[ \t]*)"
    r"(?P<action>[^@ \t]+)@(?P<ref>[^ \t#]+)"
    r"(?P<suffix>[ \t]+#.*)?$",
    re.MULTILINE,
)
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


def extract_pins(text, source="<workflow>"):
    pins = {}
    for match in ACTION_RE.finditer(text):
        action, ref = match.group("action"), match.group("ref")
        if not SHA_RE.fullmatch(ref):
            continue
        pin = (ref, match.group("suffix") or "")
        if action in pins and pins[action] != pin:
            raise ValueError(f"{source}: conflicting pins for {action}")
        pins[action] = pin
    return pins


def synchronize_text(text, pins):
    def replace(match):
        pin = pins.get(match.group("action"))
        if pin is None:
            return match.group(0)
        sha, suffix = pin
        return f"{match.group('prefix')}{match.group('action')}@{sha}{suffix}"
    return ACTION_RE.sub(replace, text)


def source_pins(workflow_dir):
    pins = {}
    for path in sorted([*workflow_dir.glob("*.yml"), *workflow_dir.glob("*.yaml")]):
        for action, pin in extract_pins(path.read_text(encoding="utf-8"), str(path)).items():
            if action in pins and pins[action] != pin:
                raise ValueError(f"conflicting source pins for {action}")
            pins[action] = pin
    if not pins:
        raise ValueError(f"no SHA-pinned actions found in {workflow_dir}")
    return pins


def targets(root):
    yield from sorted((root / "tooling" / "templates").glob("*.yml"))
    yield from sorted((root / "tooling" / "templates").glob("*.yaml"))
    yield from sorted((root / "templates").rglob("*.yml"))
    yield from sorted((root / "templates").rglob("*.yaml"))


def sync(root=ROOT, check=False):
    pins = source_pins(root / ".github" / "workflows")
    drift = []
    for path in targets(root):
        original = path.read_text(encoding="utf-8")
        updated = synchronize_text(original, pins)
        if updated != original:
            drift.append(path.relative_to(root).as_posix())
            if not check:
                path.write_text(updated, encoding="utf-8", newline="\n")
    return drift


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="fail if workflow templates have stale pins")
    parser.add_argument("--root", type=Path, default=ROOT, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        drift = sync(args.root.resolve(), args.check)
    except ValueError as error:
        print(f"workflow pin error: {error}", file=sys.stderr)
        return 1
    if drift and args.check:
        print("stale workflow action pins: " + ", ".join(drift))
        print("run python3 tooling/sync_pins.py, then python3 tooling/build_workflows.py")
        return 1
    print("workflow action pins up to date" if not drift else "updated: " + ", ".join(drift))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
