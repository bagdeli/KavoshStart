"""UI-2 visual receipt lookups need read-only Actions access in reusable governance."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / "tooling" / "templates" / "kavosh-governance.yml"
GENERATED = ROOT / ".github" / "workflows" / "kavosh-governance.yml"
EXPECTED = {"contents": "read", "pull-requests": "write", "actions": "read"}


def effective_workflow_permissions(source: str) -> dict[str, str]:
    """Parse the reusable workflow's explicit root token scope, not step text."""
    if source.count("\npermissions:\n") != 1 or source.count("\njobs:\n") != 1:
        raise ValueError("missing or ambiguous reusable workflow permissions/jobs")
    segment = source.split("\npermissions:\n", 1)[1].split("\njobs:\n", 1)[0]
    result = {}
    for line in segment.splitlines():
        if not line.strip():
            continue
        if not line.startswith("  ") or line.startswith("    ") or ": " not in line:
            raise ValueError("unexpected token scope structure")
        key, value = line.strip().split(": ", 1)
        if key in result:
            raise ValueError("duplicate permission")
        result[key] = value
    return result


class ReusableGovernanceActionsPermissionTests(unittest.TestCase):
    def test_UI2_workflow_template_and_generated_have_minimum_scopes(self):
        for path in (TEMPLATE, GENERATED):
            with self.subTest(path=path):
                source = path.read_text(encoding="utf-8")
                self.assertIn("\n  workflow_call:\n", source)
                self.assertEqual(effective_workflow_permissions(source), EXPECTED)
                self.assertNotIn("\n    permissions:\n", source.split("\njobs:\n", 1)[1])

    def test_UI2_regression_detects_removed_or_escalated_actions_permission(self):
        source = TEMPLATE.read_text(encoding="utf-8")
        self.assertEqual(source.count("\n  actions: read\n"), 1)
        for replacement in ("\n", "\n  actions: write\n", "\n  checks: read\n"):
            with self.subTest(replacement=replacement):
                mutated = source.replace("\n  actions: read\n", replacement, 1)
                self.assertNotEqual(effective_workflow_permissions(mutated), EXPECTED)

    def test_UI2_real_receipt_endpoints_remain_required(self):
        source = (ROOT / "tooling" / "src" / "governance.py").read_text(encoding="utf-8")
        self.assertIn('f"repos/{repo}/actions/runs/{rid}"', source)
        self.assertIn('f"repos/{repo}/actions/runs/{rid}/attempts/{attempt}/jobs?per_page=100"', source)
        self.assertIn('run.get("head_sha") != sha', source)
        self.assertIn('step.get("conclusion") == "success"', source)


if __name__ == "__main__":
    unittest.main()
