"""Lean T2 owner-managed profile: no mandatory AC or independent attestation plumbing."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling" / "src"))
import governance as g  # noqa: E402
import release_gate as release  # noqa: E402


class OwnerManagedProfile(unittest.TestCase):
    def test_example_is_lean_and_schema_supports_both_profiles(self):
        m = json.loads((ROOT / "intake/kavosh.project.example.json").read_text(encoding="utf-8"))
        schema = json.loads((ROOT / "intake/kavosh.project.schema.json").read_text(encoding="utf-8"))
        self.assertEqual(m["acceptance"], {"mode": "owner-managed"})
        modes = schema["properties"]["acceptance"]["properties"]["mode"]["enum"]
        self.assertEqual(set(modes), {"none", "owner-managed", "continuous"})

    def test_T2_owner_mode_needs_no_scope_mapping_or_attestor(self):
        m = {"tier": "T2", "acceptance": {"mode": "owner-managed"}}
        self.assertFalse(any(x[0] == "fail" for x in g.standard_lifecycle_problems(m)))
        self.assertEqual(g.acceptance_scope_problems(m), [])
        self.assertEqual(g.acceptance_mapping_problems(m, "No AC issue referenced"), [])
        with patch.object(release, "_json_file", return_value={"acceptance": {"mode": "owner-managed"}}):
            self.assertEqual(release.acceptance_reasons("demo/example", "a" * 40,
                api=lambda path: self.fail("owner-managed mode must not invoke evidence APIs")), [])

    def test_old_continuous_profile_remains_explicit_and_strict(self):
        m = {"tier": "T2", "acceptance": {"mode": "continuous"}}
        self.assertFalse(any(x[0] == "fail" for x in g.standard_lifecycle_problems(m)))
        with patch.object(g, "acceptance_scope", return_value=None):
            self.assertTrue(any(x[0] == "fail" for x in g.acceptance_scope_problems(m)))

    def test_simple_pr_without_issue_risk_label_or_ai_section(self):
        m = {"visibility": "private", "acceptance": {"mode": "owner-managed"},
             "ui": {"kind": "none"}, "limits": {}}
        event = {"repository": {"default_branch": "main", "private": True},
                 "pull_request": {"number": 1, "title": "Improve behavior", "body": "Verified locally",
                                  "head": {"ref": "work"}, "base": {"ref": "main"},
                                  "user": {"type": "User"}, "labels": [], "draft": False}}
        original = g.gh
        try:
            g.results.clear()
            g.gh = lambda *_: []
            g.check_pr(m, event, "demo/example")
        finally:
            g.gh = original
        verdict = {rule: state for state, rule, *_ in g.results}
        for rule in ("PR-1", "PR-2", "BR-2", "CR-1", "PR-4", "UI-2"):
            self.assertEqual(verdict.get(rule), "ok", rule)
        self.assertFalse(any(state == "fail" and rule.startswith("ACC-")
                             for state, rule, *_ in g.results))

    def scaffold(self, mode):
        m = json.loads((ROOT / "intake/kavosh.project.example.json").read_text(encoding="utf-8"))
        m["kavoshStart"] = "v7.1.4"
        m["acceptance"] = {"mode": mode}
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            (d / "kavosh.project.json").write_text(json.dumps(m), encoding="utf-8")
            done = subprocess.run([sys.executable, str(ROOT / "scripts/scaffold.py"), str(d)],
                                  capture_output=True, text=True)
            self.assertEqual(done.returncode, 0, done.stderr)
            return {p.relative_to(d).as_posix() for p in d.rglob("*") if p.is_file()}

    def test_default_t2_does_not_scaffold_attestation_infrastructure(self):
        files = self.scaffold("owner-managed")
        for path in ("acceptance/scope.json", "acceptance/security/receipt-policy.json",
                     "acceptance/README.md", ".github/workflows/ai-review.yml"):
            self.assertNotIn(path, files)
        self.assertIn(".github/workflows/ci.yml", files)
        self.assertIn(".github/workflows/release.yml", files)

    def test_optional_continuous_can_still_scaffold_legacy_receipts(self):
        files = self.scaffold("continuous")
        self.assertIn("acceptance/scope.json", files)
        self.assertIn("acceptance/security/receipt-policy.json", files)


if __name__ == "__main__":
    unittest.main()
