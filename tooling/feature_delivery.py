#!/usr/bin/env python3
"""Offline structural preflight for synthetic or owner-authored feature release units.

This tool does NOT certify a Base, a Feature, a release, a dependency decision,
a risk classification, a signed artifact or a GitHub acceptance receipt.
It reads one declared dependency plan from a file or stdin and prints
topological candidate waves for human review. No network or mutation.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

IDENTIFIER = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\Z")
WEIGHTS = {1, 2, 3, 5, 8}
MODES = {"independent", "atomic"}


class FeaturePlanError(ValueError):
    """A malformed or structurally impossible proposed delivery graph."""


def _object(value: object, keys: set[str], name: str) -> dict:
    if not isinstance(value, dict) or set(value) != keys:
        raise FeaturePlanError(f"{name}: expected fields {sorted(keys)}")
    return value


def _identifier(value: object, name: str) -> str:
    if not isinstance(value, str) or not IDENTIFIER.fullmatch(value):
        raise FeaturePlanError(f"{name}: invalid ID")
    return value


def _nonempty(value: object, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FeaturePlanError(f"{name}: explanation required")
    return value.strip()


def plan_waves(document: object) -> list[list[str]]:
    """Validate uniqueness, exact atomic boundaries, known dependencies and DAG."""
    root = _object(document, {"schemaVersion", "units"}, "plan")
    if type(root["schemaVersion"]) is not int or root["schemaVersion"] != 1:
        raise FeaturePlanError("unsupported schemaVersion (expected 1)")
    units = root["units"]
    if not isinstance(units, list) or not units:
        raise FeaturePlanError("units must be a nonempty list")

    by_id: dict[str, dict] = {}
    assigned_features: set[str] = set()
    for index, item in enumerate(units):
        unit = _object(
            item, {"id", "featureIds", "mode", "weight", "acceptance", "dependsOn"},
            f"units[{index}]",
        )
        uid = _identifier(unit["id"], "unit.id")
        if uid in by_id:
            raise FeaturePlanError(f"duplicate release unit: {uid}")
        by_id[uid] = unit
        features = unit["featureIds"]
        if not isinstance(features, list) or not features:
            raise FeaturePlanError(f"{uid}: featureIds must be nonempty")
        for f in features:
            fid = _identifier(f, f"{uid}.featureIds")
            if fid in assigned_features:
                raise FeaturePlanError(f"feature appears in multiple units: {fid}")
            assigned_features.add(fid)
        mode = unit["mode"]
        if not isinstance(mode, str) or mode not in MODES:
            raise FeaturePlanError(f"{uid}: mode must be independent or atomic")
        if mode == "independent" and len(features) != 1:
            raise FeaturePlanError(f"{uid}: multiple features require one atomic unit")
        if mode == "atomic" and len(features) < 2:
            raise FeaturePlanError(f"{uid}: atomic unit must contain at least two features")
        weight = unit["weight"]
        if type(weight) is not int or weight not in WEIGHTS:
            raise FeaturePlanError(f"{uid}: unknown relative weight")
        _nonempty(unit["acceptance"], f"{uid}.acceptance")
        if not isinstance(unit["dependsOn"], list):
            raise FeaturePlanError(f"{uid}: dependsOn must be a list")

    incoming: dict[str, set[str]] = {uid: set() for uid in by_id}
    reverse: dict[str, set[str]] = defaultdict(set)
    for uid, unit in by_id.items():
        for item in unit["dependsOn"]:
            edge = _object(item, {"unit", "reason"}, f"{uid}.dependsOn")
            parent = _identifier(edge["unit"], f"{uid}.dependsOn.unit")
            _nonempty(edge["reason"], f"{uid}.dependsOn.reason")
            if parent == uid:
                raise FeaturePlanError(f"{uid}: self-dependency")
            if parent not in by_id:
                raise FeaturePlanError(f"{uid}: unknown prerequisite {parent}")
            if parent in incoming[uid]:
                raise FeaturePlanError(f"{uid}: repeated prerequisite {parent}")
            incoming[uid].add(parent)
            reverse[parent].add(uid)

    remaining = set(by_id)
    waves = []
    while remaining:
        ready = sorted(uid for uid in remaining if not incoming[uid])
        if not ready:
            raise FeaturePlanError("dependency cycle: architecture decision required")
        waves.append(ready)
        remaining.difference_update(ready)
        for parent in ready:
            for child in reverse[parent]:
                incoming[child].remove(parent)
    return waves


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", help="Read JSON from a file, or - for standard input")
    args = parser.parse_args(argv)
    try:
        if args.file == "-":
            document = json.load(sys.stdin)
        else:
            document = json.loads(Path(args.file).read_text(encoding="utf-8"))
        waves = plan_waves(document)
    except (OSError, UnicodeError, json.JSONDecodeError, FeaturePlanError) as exc:
        print(f"feature-plan: INVALID: {exc}", file=sys.stderr)
        return 2
    for index, wave in enumerate(waves, 1):
        print(f"wave {index}: {', '.join(wave)}")
    print("structure only; human dependency/acceptance decision still required")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
