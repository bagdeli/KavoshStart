"""Executable generator regression: large embedded scripts must remain literals."""
import sys
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
