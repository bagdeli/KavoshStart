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


class MinuteBudget(unittest.TestCase):
    def test_CI3_positive_below_budget(self):
        self.assertEqual(h.minute_budget_level(50, 100), (True, 50))

    def test_CI3_negative_over_budget(self):
        self.assertEqual(h.minute_budget_level(101, 100), (False, 101))


class TemplateHardening(unittest.TestCase):
    def test_CI2_runner_installer_rejects_rootful_docker_and_is_ephemeral(self):
        """Covers: CI-2 (negative rootful access, positive ephemeral rootless runner)"""
        text = (ROOT / "scripts/install-runner.sh").read_text(encoding="utf-8")
        self.assertIn("rootful Docker is root-equivalent", text)
        self.assertIn("only accepts rootless Docker runners", text)
        self.assertNotIn("usermod -aG docker", text)
        self.assertIn("--ephemeral", text)

    def test_SEC1_gitleaks_download_is_checksum_verified(self):
        for tier in ("T1", "T2"):
            text = (ROOT / f"templates/tier/{tier}/.github/workflows/ci.yml").read_text(encoding="utf-8")
            self.assertIn("sha256sum -c", text, tier)
            self.assertNotIn("| tar -xz", text, tier)

    def test_SEC1_pre_commit_uses_current_gitleaks_interface(self):
        text = (ROOT / "templates/common/.githooks/pre-commit").read_text(encoding="utf-8")
        self.assertIn("gitleaks git --pre-commit --staged", text)
        self.assertNotIn("gitleaks protect", text)

    def test_CI8_node_setup_has_fallback_without_node_version_file(self):
        for f in ("templates/common/.github/workflows/ci.yml", "templates/tier/T1/.github/workflows/ci.yml",
                  "templates/tier/T2/.github/workflows/ci.yml"):
            text = (ROOT / f).read_text(encoding="utf-8")
            self.assertIn("hashFiles('.node-version') == ''", text, f)

    def test_ai_review_manual_dispatch_takes_pr_number(self):
        text = (ROOT / "templates/tier/T2/.github/workflows/ai-review.yml").read_text(encoding="utf-8")
        self.assertIn("pr_number:", text)
        self.assertIn("inputs.pr_number", text)


if __name__ == "__main__":
    unittest.main()
