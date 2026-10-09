"""Offline tests for layer H (tooling/src/health.py) and template hardening from #6."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling" / "src"))
import health as h  # noqa: E402


def issue(num, *labels):
    return {"number": num, "labels": [{"name": l} for l in labels]}


def commit(sha, msg, parents=({"sha": "p"},)):
    return {"sha": sha, "commit": {"message": msg}, "parents": list(parents)}


class TypeLabels(unittest.TestCase):
    def test_WK1_positive_exactly_one(self):
        self.assertEqual(h.type_label_problems([issue(1, "type:task", "priority:P1")]), [])

    def test_WK1_negative_none_or_two(self):
        out = h.type_label_problems([issue(1, "priority:P1"), issue(2, "type:task", "type:bug")])
        self.assertEqual(out, ["#1 (0 type labels)", "#2 (2 type labels)"])

    def test_WK1_positive_automation_issues_exempt(self):
        self.assertEqual(h.type_label_problems([issue(3, "kavosh:health"), issue(4, "kavosh:violation")]), [])


class DirectPushes(unittest.TestCase):
    def test_BR6_positive_all_from_merged_prs(self):
        pulls = {"a" * 40: [{"merged_at": "x", "merge_commit_sha": "a" * 40,
                              "base": {"ref": "main"}}]}
        self.assertEqual(h.direct_pushes([commit("a" * 40, "feat: x")], lambda s: pulls.get(s, [])), [])

    def test_BR6_negative_commit_without_pr(self):
        self.assertEqual(h.direct_pushes([commit("b" * 40, "fix: hot")], lambda s: []), ["bbbbbbb"])

    def test_BR6_positive_initial_scaffold_root(self):
        self.assertEqual(h.direct_pushes([commit("c" * 40, "chore: scaffold from KavoshStart v1.1.0", ())], lambda s: []), [])

    def test_AI3_trailer_ratio(self):
        cs = [commit("a", "feat: x\n\nCo-Authored-By: Claude <noreply@anthropic.com>"), commit("b", "fix: y")]
        self.assertEqual(h.trailer_ratio(cs), (1, 2))


class ReportLifecycle(unittest.TestCase):
    def test_healthy_report_can_close(self):
        self.assertTrue(h.report_is_green([("✅", "CI-1", "runner", "ok", "ok")]))

    def test_warning_or_failure_keeps_report_open(self):
        self.assertFalse(h.report_is_green([("⚠️", "REL-1", "release", "old", "fresh")]))
        self.assertFalse(h.report_is_green([("❌", "SRC-5", "manifest", "missing", "present")]))


class DraftStacks(unittest.TestCase):
    def test_BR4_draft_stacks_are_reported_as_warnings_until_ready(self):
        prs = [{"number": 12, "draft": True, "base": {"ref": "feat/11-parent"}},
               {"number": 13, "draft": False, "base": {"ref": "main"}}]
        self.assertEqual(h.draft_stack_warnings(prs), ["#12→feat/11-parent"])

    def test_BR4_draft_on_main_has_no_stack_warning(self):
        self.assertEqual(h.draft_stack_warnings([{"number": 12, "draft": True, "base": {"ref": "main"}}]), [])


class MinuteBudget(unittest.TestCase):
    def test_CI3_positive_below_budget(self):
        self.assertEqual(h.minute_budget_level(50, 100), (True, 50))

    def test_CI3_negative_over_budget(self):
        self.assertEqual(h.minute_budget_level(101, 100), (False, 101))

    def test_CI3_public_standard_hosted_minutes_are_not_billable(self):
        self.assertFalse(h.hosted_minutes_are_billable("public", "github-hosted"))

    def test_CI3_private_hosted_minutes_remain_budgeted(self):
        self.assertTrue(h.hosted_minutes_are_billable("private", "github-hosted"))

    def test_CI3_self_hosted_is_not_treated_as_public_hosted(self):
        self.assertTrue(h.hosted_minutes_are_billable("public", "self-hosted"))


class AcceptanceDebt(unittest.TestCase):
    def test_ACC2_positive_closed_evidenced_and_approved_defer(self):
        scope = {"schemaVersion": 1, "items": [
            {"id": "AC-001", "issue": 12, "owner": "bagdeli"},
            {"id": "AC-002", "issue": 13, "owner": "bagdeli", "deferredTo": "v0.2.0", "deferIssue": 14},
        ]}
        issues = {
            12: {"state": "closed", "body": "Acceptance-Merged-SHA: " + "a" * 40 +
                 "\nAcceptance-Evidence-Run: https://github.com/o/r/actions/runs/1\nAccepted-By: @bagdeli\n"},
            14: {"state": "closed", "body": "Defer-Approved-By: @bagdeli\n"},
        }
        out = h.acceptance_health(scope, issues.get)
        self.assertEqual(out["open"], [])
        self.assertEqual(out["missing_evidence"], [])
        self.assertEqual(out["defer_problems"], [])

    def test_ACC2_negative_surfaces_open_missing_evidence_and_bad_defer(self):
        scope = {"schemaVersion": 1, "items": [
            {"id": "AC-001", "issue": 12, "owner": "bagdeli"},
            {"id": "AC-002", "issue": 13, "owner": "bagdeli"},
            {"id": "AC-003", "owner": "bagdeli", "deferredTo": "v0.2.0", "deferIssue": 14},
        ]}
        issues = {
            12: {"state": "open", "body": "", "created_at": "2026-09-01T00:00:00Z"},
            13: {"state": "closed", "body": "Accepted-By: @bagdeli\n"},
            14: {"state": "closed", "body": ""},
        }
        out = h.acceptance_health(scope, issues.get)
        self.assertEqual(out["open"], ["AC-001"])
        self.assertEqual(out["missing_evidence"], ["AC-002"])
        self.assertEqual(out["defer_problems"], ["AC-003"])


class TemplateHardening(unittest.TestCase):
    def test_CI2_runner_installer_rejects_rootful_docker_and_is_ephemeral(self):
        """Covers: CI-2 (negative rootful access, positive ephemeral rootless runner)"""
        text = (ROOT / "scripts/install-runner.sh").read_text(encoding="utf-8")
        self.assertIn("rootful Docker is root-equivalent", text)
        self.assertIn("only accepts rootless Docker runners", text)
        self.assertNotIn("usermod -aG docker", text)
        self.assertIn("--ephemeral", text)

    def test_SEC1_gitleaks_download_is_checksum_verified(self):
        text = (ROOT / "templates/common/.github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("sha256sum -c", text)
        self.assertIn("'{{TIER}}' != 'T0'", text)
        self.assertNotIn("| tar -xz", text)

    def test_SEC1_pre_commit_uses_current_gitleaks_interface(self):
        text = (ROOT / "templates/common/.githooks/pre-commit").read_text(encoding="utf-8")
        self.assertIn("gitleaks git --pre-commit --staged", text)
        self.assertNotIn("gitleaks protect", text)

    def test_CI8_node_setup_has_fallback_without_node_version_file(self):
        text = (ROOT / "templates/common/.github/workflows/ci.yml").read_text(encoding="utf-8")
        self.assertIn("hashFiles('.node-version') == ''", text)

    def test_ai_review_manual_dispatch_takes_pr_number(self):
        text = (ROOT / "templates/tier/T2/.github/workflows/ai-review.yml").read_text(encoding="utf-8")
        self.assertIn("pr_number:", text)
        self.assertIn("inputs.pr_number", text)


if __name__ == "__main__":
    unittest.main()
