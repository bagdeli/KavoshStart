"""Regression contract for ruleset-eligible release-please PR verification (#83)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]

TRUST_TERMS = (
    "pull_request_target:",
    "github.event.pull_request.head.repo.full_name == github.repository",
    "github.event.pull_request.user.login == 'github-actions[bot]'",
    "startsWith(github.event.pull_request.head.ref, 'release-please--branches--')",
)


class ReleasePrTargetContract(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def assert_trusted_target(self, relative):
        text = self.read(relative)
        for term in TRUST_TERMS:
            self.assertIn(term, text, f"{relative}: missing trusted release target term {term}")

    def test_REL5_self_check_target_is_narrow_and_read_only_checkout(self):
        relative = ".github/workflows/self-check.yml"
        self.assert_trusted_target(relative)
        text = self.read(relative)
        self.assertIn("'release-pr-target-ignored' || 'required'", text)
        self.assertIn("github.event.pull_request.head.sha || github.sha", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("permissions:\n  contents: read", text)

    def test_REL5_common_ci_target_preserves_required_context_only_for_trusted_release_pr(self):
        relative = "templates/common/.github/workflows/ci.yml"
        self.assert_trusted_target(relative)
        text = self.read(relative)
        self.assertIn("'release-pr-target-ignored' || 'required'", text)
        self.assertIn("persist-credentials: false", text)

    def test_REL5_kavosh_target_preserves_context_and_disables_comment_write_path(self):
        for relative in (
            ".github/workflows/kavosh.yml",
            "templates/common/.github/workflows/kavosh.yml",
        ):
            with self.subTest(relative=relative):
                self.assert_trusted_target(relative)
                text = self.read(relative)
                self.assertIn("'release-pr-target-ignored' || 'kavosh'", text)
                self.assertIn("authorization-head:", text)
                self.assertIn("github.event.pull_request.head.sha", text)
                self.assertIn("comment:", text)
                self.assertIn("github.event_name != 'pull_request_target'", text)

    def test_REL5_release_workflow_no_longer_uses_dispatch_proxy(self):
        for relative in (
            "tooling/templates/kavosh-release.yml",
            ".github/workflows/release.yml",
            "templates/common/.github/workflows/release.yml",
        ):
            with self.subTest(relative=relative):
                text = self.read(relative)
                self.assertNotIn("Dispatch exact-head verification for the release PR", text)
                self.assertNotIn("required-workflow:", text)
                self.assertNotIn("kavosh-workflow:", text)


if __name__ == "__main__":
    unittest.main()
