"""Rule registry lifecycle/parity regressions (#110)."""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import rule_registry as rr  # noqa: E402


class RuleRegistryContract(unittest.TestCase):
    def test_registry_matches_canonical_rules_exactly(self):
        actual = json.loads((ROOT / "standard" / "rules.registry.json").read_text(encoding="utf-8"))
        self.assertEqual(actual, rr.build_registry())

    def test_registry_has_every_rule_once(self):
        registry = rr.build_registry()
        ids = [rule["id"] for rule in registry["rules"]]
        self.assertEqual(len(ids), 87)
        self.assertEqual(len(ids), len(set(ids)))

    def test_machine_musts_declare_positive_negative_coverage_contract(self):
        gaps = [
            rule["id"]
            for rule in rr.build_registry()["rules"]
            if (
                rule["level"] == "MUST"
                and not rule["enforcement"]["delegatedVia"]
                and set(rule["enforcement"]["layers"]) & rr.COVERAGE_LAYERS
                and not rule["coverage"]["positiveNegativeRequired"]
            )
        ]
        self.assertEqual(gaps, [])

    def test_delegated_rule_does_not_claim_direct_coverage_requirement(self):
        sample = "| ZZ-1 | delegated example | MUST | All | via SRC-2 |\n"
        rule = rr.build_registry(sample)["rules"][0]
        self.assertEqual(rule["enforcement"]["delegatedVia"], ["SRC-2"])
        self.assertFalse(rule["coverage"]["positiveNegativeRequired"])

    def test_registry_drift_is_detectable(self):
        changed = rr.render_registry(
            "| ZZ-1 | new machine rule | MUST | All | P |\n"
        )
        self.assertNotEqual(
            changed,
            (ROOT / "standard" / "rules.registry.json").read_text(encoding="utf-8"),
        )


if __name__ == "__main__":
    unittest.main()
