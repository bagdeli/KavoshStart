#!/usr/bin/env python3
"""Extract exact assertion outcomes from JUnit XML for a trusted receipt publisher.

This offline adapter neither authenticates a producer nor grants acceptance. A
trusted App must read the actual run artifact, verify provenance, and publish the
receipt; never publish an owner-supplied JSON claim without inspecting evidence.
"""
import argparse
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

MAX_BYTES = 16 * 1024 * 1024


def assertion_outcomes(raw):
    if not isinstance(raw, bytes) or not raw or len(raw) > MAX_BYTES:
        raise ValueError("JUnit input missing or exceeds 16 MiB")
    text = raw.decode("utf-8-sig")
    if "\x00" in text or "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
        raise ValueError("JUnit DTD/entity declarations are forbidden")
    root = ET.fromstring(text)
    if root.tag not in ("testsuites", "testsuite"):
        raise ValueError("JUnit root must be testsuites or testsuite")
    results, seen = [], set()
    for case in root.iter("testcase"):
        name = case.get("name")
        if not name or not name.strip():
            raise ValueError("JUnit testcase has no name")
        identifier = f"{case.get('classname', '')}::{name}" if case.get("classname") else name
        if identifier in seen:
            raise ValueError(f"ambiguous duplicate JUnit assertion: {identifier}")
        seen.add(identifier)
        bad = [tag for tag in ("failure", "error", "skipped") if case.find(tag) is not None]
        status = case.get("status", "run")
        if status not in ("run", "passed", "notrun", "disabled", "skipped"):
            raise ValueError("unrecognized JUnit testcase status")
        outcome = "fail" if any(t in bad for t in ("failure", "error")) else "skipped" if bad or status in ("notrun", "disabled", "skipped") else "pass"
        results.append({"id": identifier, "outcome": outcome})
    if not results:
        raise ValueError("empty JUnit report is not passing evidence")
    # Aggregate counters must not hide missing/omitted testcase results.
    for suite in root.iter():
        if suite.tag not in ("testsuite", "testsuites"):
            continue
        cases = list(suite.iter("testcase"))
        actual = {"tests": len(cases), "failures": sum(c.find("failure") is not None for c in cases),
                  "errors": sum(c.find("error") is not None for c in cases),
                  "skipped": sum(c.find("skipped") is not None or c.get("status") in ("notrun", "disabled", "skipped") for c in cases)}
        for key, count in actual.items():
            if suite.get(key) is not None and int(suite.get(key)) != count:
                raise ValueError(f"JUnit {key} summary disagrees with testcase evidence")
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    args = parser.parse_args(argv)
    try:
        with args.report.open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        print(json.dumps({"schemaVersion": 1, "assertions": assertion_outcomes(raw)}, indent=2))
    except (OSError, ValueError, ET.ParseError) as exc:
        print(f"JUnit evidence rejected: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
