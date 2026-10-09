"""Regression contract for bot release-PR verification without owner-click mechanics (#83)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class ReleasePrBridgeContract(unittest.TestCase):
    def read(self, relative):
        return (ROOT / relative).read_text(encoding="utf-8")

    def test_REL5_no_pull_request_target_proxy_remains(self):
        for relative in (
            ".github/workflows/self-check.yml",
            ".github/workflows/kavosh.yml",
            "templates/common/.github/workflows/ci.yml",
            "templates/common/.github/workflows/kavosh.yml",
        ):
            with self.subTest(relative=relative):
                self.assertNotIn("pull_request_target:", self.read(relative))

    def test_REL5_release_bridge_has_exact_workflow_inputs_and_check_write(self):
        text = self.read("tooling/templates/kavosh-release.yml")
        self.assertIn("required-workflow:", text)
        self.assertIn("kavosh-workflow:", text)
        self.assertIn("checks: write", text)
        self.assertIn("statuses: write", text)
        self.assertIn("actions: write", text)
        self.assertIn("--verify-release-pr", text)
        self.assertIn("required", text)
        self.assertIn("kavosh / governance", self.read("tooling/src/release_gate.py"))

    def test_REL5_dispatch_contract_remains_bounded_and_exact_head(self):
        for relative in (
            ".github/workflows/self-check.yml",
            "templates/common/.github/workflows/ci.yml",
        ):
            text = self.read(relative)
            self.assertIn("pr-number:", text)
            self.assertIn("expected-head:", text)
            self.assertIn("persist-credentials: false", text)
        for relative in (
            ".github/workflows/kavosh.yml",
            "templates/common/.github/workflows/kavosh.yml",
        ):
            text = self.read(relative)
            self.assertIn("mode:", text)
            self.assertIn("pr-number:", text)
            self.assertIn("expected-head:", text)

    def test_REL5_common_ci_private_dispatch_does_not_require_github_cli(self):
        text = self.read("templates/common/.github/workflows/ci.yml")
        self.assertNotIn('gh api "repos/$REPO/pulls/$PR_NUMBER"', text)
        self.assertIn("urllib.request", text)


if __name__ == "__main__":
    unittest.main()
