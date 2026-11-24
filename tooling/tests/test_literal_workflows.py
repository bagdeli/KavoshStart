"""Executable generator regression: large embedded scripts must remain literals."""
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import build_workflows as builder


class LiteralEmbeddedWorkflows(unittest.TestCase):
    def test_positive_all_current_embedded_templates_build(self):
        for template, source in builder.PAIRS.items():
            with self.subTest(template=template):
                builder.build(template, source)


    def test_governance_checkout_budget_and_enforcement(self):
        source = builder.build("kavosh-governance.yml", "governance.py")
        self.assertEqual(source, (ROOT / ".github/workflows/kavosh-governance.yml").read_text())
        self.assertIn("    timeout-minutes: ${{ contains(fromJSON(inputs.runs-on), 'self-hosted') && 25 || 5 }}", source)
        self.assertIn("        timeout-minutes: ${{ contains(fromJSON(inputs.runs-on), 'self-hosted') && 15 || 5 }}", source)
        self.assertIn('GIT_TERMINAL_PROMPT: "0"', source)
        self.assertIn('GIT_HTTP_LOW_SPEED_LIMIT: "1"', source)
        self.assertIn('GIT_HTTP_LOW_SPEED_TIME: "60"', source)
        self.assertIn("fetch-depth: 1", source)
        self.assertIn("persist-credentials: false", source)
        self.assertNotIn("continue-on-error:", source)
        self.assertLess(source.index("Checkout exact source"), source.index("Verify exact checked-out commit"))
        self.assertLess(source.index("Verify exact checked-out commit"), source.index("Check KavoshStart rules"))

    def test_governance_exact_source_verification_rejects_wrong_head(self):
        template = (ROOT / "tooling/templates/kavosh-governance.yml").read_text()
        step = template.split("      - name: Verify exact checked-out commit\n", 1)[1]
        script = step.split("        run: |\n", 1)[1].split("      - name:", 1)[0]
        script = "\n".join(line[10:] for line in script.splitlines())
        with tempfile.TemporaryDirectory() as work:
            subprocess.run(["git", "init", "-q", work], check=True)
            subprocess.run(["git", "-C", work, "-c", "user.name=Example",
                            "-c", "user.email=example@example.invalid",
                            "commit", "--allow-empty", "-qm", "fixture"], check=True)
            head = subprocess.check_output(["git", "-C", work, "rev-parse", "HEAD"], text=True).strip()
            for expected, allowed in ((head, True), ("0" * 40, False), ("not-a-sha", False), ("", False)):
                with self.subTest(expected=expected):
                    result = subprocess.run(["bash", "-c", script], cwd=work,
                                            env=dict(os.environ, EXPECTED_SOURCE=expected),
                                            capture_output=True, text=True)
                    self.assertEqual(result.returncode == 0, allowed, result.stderr)

    def test_rc_wrappers_keep_legacy_permissions_and_isolate_staging_permissions(self):
        legacy = builder.build("kavosh-rc.yml", "rc_gate.py")
        staging = builder.build("kavosh-test-staging.yml", "rc_gate.py")
        self.assertIn("name: kavosh-rc", legacy)
        self.assertIn("  checks: read", legacy)
        self.assertNotIn("  actions: read", legacy)
        self.assertNotIn("  issues: read", legacy)
        self.assertIn("name: kavosh-test-staging", staging)
        self.assertIn("  actions: read", staging)
        self.assertIn("  issues: read", staging)
        self.assertIn('KAVOSH_RC_REQUIRE_TEST_STAGING: "1"', staging)
        self.assertNotIn('KAVOSH_RC_REQUIRE_TEST_STAGING: "1"', legacy)

    def test_positive_context_in_env_not_in_script(self):
        template = '''      - env:
          BRANCH: ${{ github.event.repository.default_branch }}
        run: |
          python3 - <<'PYTHON'
__PYTHON__
          PYTHON
          echo "$BRANCH"
'''
        builder.validate_embedded_blocks(template, "print('ok')\n" * 3000)

    def test_negative_inline_context_in_large_release_script(self):
        template = (ROOT / "tooling/templates/kavosh-release.yml").read_text()
        old = template.replace('--branch "$DEFAULT_BRANCH"',
                               '--branch "${{ github.event.repository.default_branch }}"')
        self.assertNotEqual(old, template)
        with self.assertRaisesRegex(ValueError, "move context to step env"):
            builder.validate_embedded_blocks(old, "print('ok')\n" * 3000)

    def test_negative_interpolation_introduced_in_python_source(self):
        with self.assertRaisesRegex(ValueError, "embedded source"):
            builder.validate_embedded_blocks("", 'print("${{ github.token }}")')

    def test_positive_separate_short_run_can_use_context(self):
        template = '''      - run: |
          python3 - <<'PYTHON'
__PYTHON__
          PYTHON
      - run: echo '${{ github.sha }}'
'''
        builder.validate_embedded_blocks(template, "pass")

    def test_positive_release_branch_preserved_in_environment(self):
        template = (ROOT / "tooling/templates/kavosh-release.yml").read_text()
        self.assertIn('DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}', template)
        self.assertIn('--branch "$DEFAULT_BRANCH"', template)
        self.assertNotIn('--branch "${{', template)


if __name__ == "__main__":
    unittest.main()
