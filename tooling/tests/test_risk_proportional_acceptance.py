"""Risk-based native acceptance proves only required CI; legacy attested remains strict."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from test_receipts import Fixture, SOURCE, CANDIDATE
import receipts as rv


def native():
    f = Fixture()
    f.manifest["acceptance"]["assurance"] = "risk-based"
    f.item.update(risk="medium", evidence=["ci"], assertions={"ci": ["repository::required"]})
    f.seal()
    return f


class RiskBasedAcceptance(unittest.TestCase):
    def test_ACC3_positive_native_required_ci_no_attestor(self):
        f = native()
        f.fail_paths.add("contents/" + rv.RECEIPT_POLICY)
        result = f.report()
        self.assertEqual(result["problems"], [])
        self.assertEqual(result["verified"], ["AC-001"])
        self.assertFalse(any(rv.RECEIPT_POLICY in p for p in f.calls))

    def test_ACC3_negative_failed_unrelated_or_wrong_source_ci(self):
        for edit in (
            lambda f: f.objects["actions/runs/99"].update(conclusion="failure"),
            lambda f: f.objects["actions/runs/99"].update(head_sha="f" * 40),
            lambda f: f.objects["actions/runs/99"].update(path=".github/workflows/not-ci.yml"),
            lambda f: setattr(f, "body", f.body.replace(SOURCE, "f" * 40)),
        ):
            with self.subTest(edit=edit):
                f = native()
                edit(f)
                self.assertTrue(f.report()["problems"])

    def test_ACC3_negative_source_tree_changed_without_reviewed_paths(self):
        f = native()
        f.candidate = CANDIDATE
        result = f.report()
        self.assertTrue(result["problems"])
        self.assertTrue(any("native source invalid" in p for p in result["problems"]))

    def test_ACC3_negative_specialist_or_arbitrary_assertion_requires_attestor(self):
        for ev, assertions in (
            (["ci", "test"], {"ci": ["repository::required"], "test": ["domain::deny"]}),
            (["ci"], {"ci": ["business::assertion"]}),
            (["ci", "ui"], {"ci": ["repository::required"], "ui": ["render::reviewed"]}),
        ):
            with self.subTest(evidence=ev):
                f = native()
                f.item.update(evidence=ev, assertions=assertions)
                f.policy["producers"] = {}
                f.seal()
                self.assertTrue(f.report()["problems"])

    def test_ACC3_negative_high_risk_and_deferred_remain_independent(self):
        for high, deferred in ((True, False), (False, True)):
            f = native()
            if high:
                f.item["risk"] = "critical"
            if deferred:
                f.item.update(deferredTo="v1.1.0", deferIssue=13)
            f.policy["producers"] = {}
            f.seal()
            self.assertTrue(f.report()["problems"])

    def test_ACC3_negative_default_legacy_attested_remains_strict(self):
        f = native()
        f.manifest["acceptance"].pop("assurance")
        f.policy["producers"] = {}
        f.seal()
        self.assertTrue(f.report()["problems"])

    def test_ACC3_negative_owner_marker_is_not_an_authenticated_decision(self):
        f = native()
        f.body = f.body.replace("Accepted-By: @owner", "Accepted-By: @other")
        self.assertTrue(f.report()["problems"])
