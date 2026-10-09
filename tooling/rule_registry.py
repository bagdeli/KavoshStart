#!/usr/bin/env python3
"""Generate/check the machine-readable KavoshStart rule registry.

RULES.md remains the canonical prose. This file makes its structure and
lifecycle/enforcement metadata deterministic for tooling and consumers.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RULES = ROOT / "standard" / "RULES.md"
REGISTRY = ROOT / "standard" / "rules.registry.json"
ROW = re.compile(
    r"^\|\s*([A-Z]+-\d+)\s*\|(.*)\|\s*(MUST|SHOULD|MAY)\s*\|([^|]*)\|([^|]*)\|\s*$"
)
RULE_ID = re.compile(r"[A-Z]+-\d+")
MACHINE_LAYERS = {"A", "P", "M", "G", "H", "S", "O", "E"}
COVERAGE_LAYERS = {"P", "M", "G", "H", "O", "E"}


def parse_layers(raw: str) -> tuple[list[str], list[str]]:
    delegated = RULE_ID.findall(raw) if "via" in raw else []
    layers = sorted(
        {
            token
            for token in re.findall(r"(?<![A-Za-z-])([A-Z])(?![A-Za-z-])", raw)
            if token in MACHINE_LAYERS | {"R"}
        }
    )
    return layers, delegated


def parse_rules(text: str | None = None) -> list[dict]:
    text = RULES.read_text(encoding="utf-8") if text is None else text
    out = []
    seen = set()
    for line in text.splitlines():
        match = ROW.match(line)
        if not match:
            continue
        rule_id, statement, level, tier, raw_layers = match.groups()
        if rule_id in seen:
            raise ValueError(f"duplicate rule id: {rule_id}")
        seen.add(rule_id)
        layers, delegated = parse_layers(raw_layers.strip())
        direct_machine = sorted(set(layers) & MACHINE_LAYERS)
        coverage_required = (
            level == "MUST"
            and not delegated
            and bool(set(layers) & COVERAGE_LAYERS)
        )
        out.append(
            {
                "id": rule_id,
                "statement": statement.strip(),
                "level": level,
                "tier": tier.strip(),
                "enforcement": {
                    "raw": raw_layers.strip(),
                    "layers": layers,
                    "delegatedVia": delegated,
                    "machineEnforced": bool(direct_machine),
                    "humanReview": "R" in layers,
                },
                "lifecycle": {
                    "owner": "KavoshStart",
                    "status": "active",
                    "source": "standard/RULES.md",
                    "introducedAtOrBefore": "v2.0.6",
                    "deprecatedIn": None,
                    "replacement": None,
                },
                "coverage": {
                    "positiveNegativeRequired": coverage_required,
                    "contract": (
                        "tooling/tests/test_rules.py"
                        if coverage_required
                        else None
                    ),
                },
            }
        )
    if not out:
        raise ValueError("no rules parsed from standard/RULES.md")
    return out


def build_registry(text: str | None = None) -> dict:
    return {
        "schemaVersion": 1,
        "source": "standard/RULES.md",
        "generatedBy": "tooling/rule_registry.py",
        "coverageContract": "tooling/tests/test_rules.py",
        "historicalMetadataPolicy": {
            "existingRules": "introducedAtOrBefore v2.0.6; do not invent older exact versions",
            "futureRules": "record exact introduction/deprecation/replacement metadata when lifecycle changes",
        },
        "rules": parse_rules(text),
    }


def render_registry(text: str | None = None) -> str:
    return json.dumps(build_registry(text), ensure_ascii=False, indent=2) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--check", action="store_true")
    group.add_argument("--write", action="store_true")
    args = parser.parse_args(argv)

    rendered = render_registry()
    if args.write:
        REGISTRY.write_text(rendered, encoding="utf-8")
        print(f"wrote {REGISTRY.relative_to(ROOT)}")
        return 0

    current = REGISTRY.read_text(encoding="utf-8") if REGISTRY.exists() else ""
    if current != rendered:
        print(
            "rules.registry.json is stale; run: python3 tooling/rule_registry.py --write",
            file=sys.stderr,
        )
        return 1
    print(f"rule registry is current: {len(build_registry()['rules'])} rules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
