"""Generic Base-first delivery and release-unit preflight regression tests.

No consumer/private repository, host, customer, artifact or acceptance data.
"""
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
from feature_delivery import FeaturePlanError, plan_waves  # noqa: E402


def example():
    return {
        "schemaVersion": 1,
        "units": [
            {
                "id": "U-API", "featureIds": ["F-100"], "mode": "independent",
                "weight": 3, "acceptance": "A real API consumer succeeds", "dependsOn": [],
            },
            {
                "id": "U-HELP", "featureIds": ["F-300"], "mode": "independent",
                "weight": 2, "acceptance": "Offline guide opens", "dependsOn": [],
            },
            {
                "id": "U-PAIR", "featureIds": ["F-200", "F-201"], "mode": "atomic",
                "weight": 8, "acceptance": "A full protected transaction completes",
                "dependsOn": [{"unit": "U-API", "reason": "Consumes the stable API"}],
            },
        ],
    }


class FeatureDeliveryStructureTest(unittest.TestCase):
    def test_positive_independent_and_atomic_units_are_topologically_ordered(self):
        self.assertEqual(plan_waves(example()), [["U-API", "U-HELP"], ["U-PAIR"]])

    def test_positive_decisions_remain_structural_not_acceptance_proof(self):
        item = example()
        item["units"][0]["acceptance"] = "Expected but not actually tested"
        self.assertEqual(plan_waves(item)[0], ["U-API", "U-HELP"])

    def test_negative_cycle_requires_architecture_resolution(self):
        item = example()
        item["units"][0]["dependsOn"] = [{"unit": "U-PAIR", "reason": "cycle"}]
        with self.assertRaisesRegex(FeaturePlanError, "dependency cycle"):
            plan_waves(item)

    def test_negative_unknown_dependency_is_not_silently_ignored(self):
        item = example()
        item["units"][2]["dependsOn"][0]["unit"] = "U-NOT-DEFINED"
        with self.assertRaisesRegex(FeaturePlanError, "unknown prerequisite"):
            plan_waves(item)

    def test_negative_independent_multi_feature_requires_atomic_acceptance(self):
        item = example()
        item["units"][2]["mode"] = "independent"
        with self.assertRaisesRegex(FeaturePlanError, "atomic unit"):
            plan_waves(item)

    def test_negative_duplicate_feature_owner_rejected(self):
        item = example()
        item["units"][1]["featureIds"] = ["F-100"]
        with self.assertRaisesRegex(FeaturePlanError, "multiple units"):
            plan_waves(item)

    def test_negative_missing_dependency_reason_rejected(self):
        item = example()
        item["units"][2]["dependsOn"][0]["reason"] = " "
        with self.assertRaisesRegex(FeaturePlanError, "explanation required"):
            plan_waves(item)

    def test_negative_duplicate_edge_rejected(self):
        item = example()
        item["units"][2]["dependsOn"].append(
            {"unit": "U-API", "reason": "redundant dependency"}
        )
        with self.assertRaisesRegex(FeaturePlanError, "repeated prerequisite"):
            plan_waves(item)

    def test_negative_bad_version_or_weight_rejected(self):
        item = example()
        item["schemaVersion"] = 0
        with self.assertRaisesRegex(FeaturePlanError, "schemaVersion"):
            plan_waves(item)
        item = example()
        item["units"][0]["weight"] = 13
        with self.assertRaisesRegex(FeaturePlanError, "weight"):
            plan_waves(item)

    def test_standard_and_consumer_templates_share_the_human_decision_contract(self):
        rules = (ROOT / "standard/RULES.md").read_text(encoding="utf-8")
        guide = (ROOT / "standard/16-base-first-feature-delivery.md").read_text(encoding="utf-8")
        base = (ROOT / "templates/tier/T2/docs/architecture/base-contract.md").read_text(encoding="utf-8")
        feature = (ROOT / "templates/tier/T2/.github/ISSUE_TEMPLATE/feature.yml").read_text(encoding="utf-8")
        start = (ROOT / "START.md").read_text(encoding="utf-8")
        for rid in ["BASE-1", "BASE-2", "BASE-3", "TRN-1", "TRN-2", "TRN-3", "TRN-4", "TRN-5"]:
            self.assertIn(f"| {rid} |", rules)
            self.assertIn(rid, guide.split("\n", 4)[2])
        self.assertIn("B4 — Accepted Initial Base", guide)
        self.assertIn("B4 initial release", base)
        self.assertIn("Proposed release-unit treatment", feature)
        self.assertIn("Base-first", start)
        self.assertNotIn("Live CI status:", base)
        self.assertNotIn("github.com/", guide.split("## نمونهٔ مصنوعی")[0])


if __name__ == "__main__":
    unittest.main()
