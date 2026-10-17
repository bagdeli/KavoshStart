"""Documentation-contract tests for explicitly conditional AGPL acceptance.

These checks detect missing policy language only; they cannot establish legal
compatibility for any concrete component or approve a commercial release.
"""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ConditionalAGPLPolicy(unittest.TestCase):
    def test_explicit_allow_after_case_by_case_no_conflict_review(self):
        policy = (ROOT / "standard/15-third-party-components.md").read_text(encoding="utf-8")
        for term in ("AGPL-3.0-only", "AGPL-3.0-or-later", "ممنوعیت مطلق ندارند",
                     "approved", "blocked", "needs-legal-review", "تناقض حل‌نشده",
                     "Corresponding Source", "§13", "بررسی حقوقی معتبر"):
            with self.subTest(term=term):
                self.assertIn(term, policy)
        self.assertNotIn("AGPL مطلقاً ممنوع", policy)

    def test_consumer_template_requires_a_real_decision_not_scanner_approval(self):
        template = (ROOT / "templates/common/docs/THIRD_PARTY.md").read_text(encoding="utf-8")
        for term in ("AGPL-specific decision", "network source offer",
                     "approved", "blocked", "needs-legal-review",
                     "qualified legal review", "never treat a scanner result as approval"):
            with self.subTest(term=term):
                self.assertIn(term, template)

    def test_legal_gate_is_explicitly_human_not_a_machine_compliance_claim(self):
        adr = (ROOT / "docs/decisions/0016-third-party-component-governance.md").read_text(encoding="utf-8")
        self.assertIn("no automated licence-compatibility certification", adr)
        self.assertIn("expressly permits", adr)


if __name__ == "__main__":
    unittest.main()
