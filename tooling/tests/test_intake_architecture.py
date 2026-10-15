"""Documentation-contract regressions; NOT agent behavior or product acceptance tests."""
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def rows(text, prefix="G"):
    """Read the bounded questionnaire/project table, not arbitrary owner decisions."""
    result = []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if cells and re.match(rf"^{prefix}[0-9]+(?:\s|$)", cells[0]):
            result.append(cells)
    return result


class IntakeArchitectureContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questionnaire = (ROOT / "intake/QUESTIONNAIRE.md").read_text(encoding="utf-8")
        cls.protocol = (ROOT / "START.md").read_text(encoding="utf-8")
        cls.project = (ROOT / "templates/common/PROJECT.md").read_text(encoding="utf-8")
        cls.spec = (ROOT / "templates/tier/T1/specs/_template/spec.md").read_text(encoding="utf-8")

    def test_all_architecture_subjects_have_unique_required_prompts(self):
        table = rows(self.questionnaire)
        self.assertEqual([r[0] for r in table], [f"G{i}" for i in range(1, 10)])
        for r in table:
            self.assertEqual(len(r), 5)
            self.assertEqual(r[1], "R")
            self.assertIn("PROJECT.md#architecture-decisions", r[3])
            self.assertTrue(r[2] and r[4])

    def test_project_template_reuses_same_subjects_and_existing_anchor(self):
        ids = [r[0].split()[0] for r in rows(self.project)]
        self.assertEqual(ids, [r[0] for r in rows(self.questionnaire)])
        self.assertIn('id="architecture-decisions"', self.project)
        self.assertIn("Do not add unsupported manifest keys", self.protocol)

    def test_licensing_is_explicit_and_not_inferred_from_internal_use(self):
        licence = rows(self.questionnaire)[0]
        self.assertIn("لایسنس", licence[2])
        self.assertIn("regardless of internal/public audience", licence[4])
        self.assertIn("Product licensing is distinct", licence[4])
        self.assertIn("including product licensing", self.protocol)

    def test_identity_data_network_and_delivery_are_not_omitted(self):
        table = {r[0]: r for r in rows(self.questionnaire)}
        for key, expected in {"G2": "authorization", "G3": "authoritative", "G4": "offline",
                              "G5": "recovery", "G6": "engineering", "G7": "KavoshUI",
                              "G8": "observability", "G9": "assertion"}.items():
            # G9 asks for evidence planning; exact assertion detail belongs to the Spec.
            value = table[key][4] + (self.spec if key == "G9" else "")
            self.assertIn(expected, value, key)

    def test_no_ui_is_a_real_not_needed_path(self):
        ui = next(r for r in rows(self.questionnaire) if r[0] == "G7")[4]
        self.assertIn("ui.kind=none", ui)
        self.assertIn("do not create UI tasks", ui)

    def test_not_needed_does_not_multiply_work_or_receipts(self):
        self.assertIn("creates no implementation, test, evidence receipt or separate Issue", self.questionnaire)
        self.assertIn("not one PR per source requirement or intake answer", self.protocol)

    def test_inheritance_and_repeated_sessions_reuse_answers(self):
        self.assertIn("inherited` with an explicit approved profile/version/reference", self.questionnaire)
        self.assertIn("ask again only for a missing or materially changed decision", self.protocol)
        self.assertIn("Reopen only decisions affected by this scope", self.protocol)

    def test_unresolved_choices_block_only_dependent_implementation(self):
        self.assertIn("Block only dependent implementation", self.questionnaire)
        self.assertIn("unrelated authorized work may continue", self.protocol)
        self.assertIn("dependent work:", self.spec)
        self.assertIn("needed before:", self.spec)
        self.assertIn("Required identity/scaffold inputs must be known", self.protocol)

    def test_vague_answer_is_never_silent_approval(self):
        self.assertNotIn('If the owner answers vaguely ("معمولی", "بعداً"), use the default', self.questionnaire)
        self.assertIn("Suggestions are not accepted defaults", self.protocol)
        self.assertIn("Never convert vague answers", self.questionnaire)

    def test_receipt_rollout_is_planned_without_fabricating_a_producer(self):
        self.assertIn("real admitted evidence/decision producers", self.protocol)
        self.assertIn("before promising delivery", self.protocol)
        self.assertIn("not permission to invent receipts or build a new App by default", self.questionnaire)
        self.assertNotIn("unless the owner explicitly chooses a documented phased adoption", self.protocol)

    def test_runner_instruction_matches_mechanism_neutral_CI2(self):
        self.assertNotIn("so use rootless Docker or a disposable VM", self.protocol)
        self.assertIn("options, not universal requirements", self.protocol)
        self.assertIn("explicitly reviewed containment/trust strategy", self.protocol)

    def test_spec_links_evidence_without_manufacturing_acceptance(self):
        self.assertIn("## Evidence plan", self.spec)
        self.assertIn("Given … when … then …", self.spec)
        self.assertIn("not a pass, a receipt or human approval", self.spec)
        self.assertIn("Reuse shared evidence with traceability", self.spec)

    def test_planning_is_not_permission_or_a_new_product_audit(self):
        self.assertIn("not execution/credential/Production authorization", self.questionnaire)
        self.assertIn("do not authorize work on that product", self.protocol)
        self.assertIn("Never use `--admin`", self.protocol)
        self.assertIn("Production data changes and credentials require direct human authorization", self.protocol)


if __name__ == "__main__":
    unittest.main()
