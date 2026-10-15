"""Read-only documentation-contract checks for risk-sized QA and network escalation."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ProportionateQuality(unittest.TestCase):
    def test_two_evidence_routes_are_explicit(self):
        s = read("standard/11-risk-evidence-merge.md")
        self.assertIn("A — deterministic", s)
        self.assertIn("B — evaluative", s)
        self.assertIn("human review", s)
        self.assertIn("machine comparison", s)
        self.assertIn("cannot be replaced", s)

    def test_penetration_is_stage_and_risk_scoped(self):
        s = read("standard/08-security.md")
        self.assertIn("تست نفوذ دستی جامع", s)
        self.assertIn("پیش از مواجههٔ عمومی", s)
        self.assertIn("آزمون منفی", s)
        self.assertIn("SSDF", s)

    def test_existing_receipt_safety_remains_unwaived(self):
        s = read("standard/11-risk-evidence-merge.md")
        self.assertIn("ACC-3", s)
        self.assertIn("do not turn a missing source-bound receipt into PASS", s)

    def test_network_failure_does_not_demand_mirror_or_fabricate_ip(self):
        for p in ("intake/QUESTIONNAIRE.md", "standard/04-ci-runners-minutes.md"):
            self.assertNotIn("KavoshRepo", read(p))
        s = read("START.md")
        for word in ("DNS", "IP unknown", "HTTP 401/403/404", "report", "without userinfo"):
            self.assertIn(word, s)

    def test_agent_cannot_turn_proposals_into_new_gates(self):
        s = read("standard/11-risk-evidence-merge.md")
        self.assertIn("An agent cannot create a mandatory", s)
        self.assertIn("lifecycle timing", s)


if __name__ == "__main__":
    unittest.main()
