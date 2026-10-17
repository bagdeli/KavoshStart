"""Private GitHub-hosted-only Actions and risk-sized local-only regression checks."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling" / "src"))
import governance as g  # noqa: E402

SCHEMA = json.loads((ROOT / "intake" / "kavosh.project.schema.json").read_text(encoding="utf-8"))
SCAFFOLD = ROOT / "scripts" / "scaffold.py"


def manifest(visibility="private", runner="github-hosted", tier="T1", runtime="server"):
    return {"visibility": visibility, "ci": {"runner": runner}, "tier": tier, "runtime": runtime}


class PrivateActionsPolicy(unittest.TestCase):
    def test_CI1_positive_private_hosted_manifest(self):
        """Covers: CI-1 (positive)"""
        m = manifest()
        self.assertEqual(g.validate(m, {"allOf": SCHEMA["allOf"]}), [])
        self.assertFalse(any(x[0] == "fail" for x in g.runner_manifest_problems(m)))
        self.assertFalse(any(x[0] == "fail" for x in g.runner_workflow_problems(
            {".github/workflows/ci.yml": "jobs:\n  required:\n    runs-on: ubuntu-latest\n"}, m)
            if x[1] == "CI-1"))

    def test_CI1_negative_private_self_hosted_without_owner_exception(self):
        """Covers: CI-1 (negative)"""
        m = manifest(runner="self-hosted")
        m["ci"]["trustModelADR"] = "docs/decisions/0001-isolation.md"
        self.assertTrue(g.validate(m, {"allOf": SCHEMA["allOf"]}))
        self.assertTrue(any(level == "fail" and rule == "CI-1"
                            for level, rule, _, _ in g.runner_manifest_problems(m)))
        self.assertTrue(any(level == "fail" and rule == "CI-2"
                            for level, rule, _, _ in g.runner_manifest_problems(m)))

    def test_CI1_positive_new_standard_hosted_labels(self):
        """Current official GitHub standard runner labels are accepted."""
        m = manifest()
        for label in ("ubuntu-26.04", "ubuntu-26.04-arm",
                      "windows-11-vs2026-arm", "macos-26-intel", "xcode-27"):
            with self.subTest(label=label):
                wf = {".github/workflows/ci.yml":
                      "jobs:\n  required:\n    runs-on: " + label + "\n"}
                findings = g.runner_workflow_problems(wf, m)
                self.assertFalse(any(x[0] == "fail" and x[1] == "CI-1"
                                     for x in findings), label)

    def test_CI1_negative_private_dynamic_and_group_runners(self):
        m = manifest()
        for value in ("\u0024{{ matrix.os }}", "{group: trusted-pool, labels: ubuntu-latest}",
                      "[self-hosted, linux]", "custom-label", ""):
            with self.subTest(value=value):
                wf = {".github/workflows/ci.yml": f"jobs:\n  required:\n    runs-on: {value}\n"}
                findings = g.runner_workflow_problems(wf, m)
                self.assertTrue(any(x[0] == "fail" and x[1] == "CI-1" for x in findings), value)

    def test_CI1_negative_private_hosted_with_stale_self_hosted_metadata(self):
        for key, value in (("runnerLabels", ["self-hosted", "linux"]),
                           ("runners", 1),
                           ("trustModelADR", "docs/decisions/0001-trust.md")):
            with self.subTest(field=key):
                m = manifest()
                m["ci"][key] = value
                self.assertTrue(g.validate(m, {"allOf": SCHEMA["allOf"]}))
                self.assertTrue(any(x[0] == "fail" and x[1] == "CI-1"
                                    for x in g.runner_manifest_problems(m)))

    def test_CI1_negative_unverified_external_reusable_workflow(self):
        m = manifest()
        workflows = {".github/workflows/custom.yml": (
            "jobs:\n  external:\n"
            "    uses: external/example/.github/workflows/build.yml@" + "a" * 40 + "\n"
        )}
        findings = g.runner_workflow_problems(workflows, m)
        self.assertTrue(any(x[0] == "fail" and x[1] == "CI-1"
                            for x in findings))

    def test_CI1_positive_local_reusable_workflow_with_hosted_job(self):
        m = manifest()
        workflows = {
            ".github/workflows/call.yml":
                "jobs:\n  local:\n    uses: ./.github/workflows/safe.yml\n",
            ".github/workflows/safe.yml":
                "jobs:\n  hosted:\n    runs-on: ubuntu-latest\n",
        }
        result = g.runner_workflow_problems(workflows, m)
        self.assertFalse(any(x[0] == "fail" and x[1] == "CI-1" for x in result))

    def test_CI1_negative_missing_local_reusable_workflow(self):
        result = g.runner_workflow_problems({
            ".github/workflows/custom.yml":
                "jobs:\n  local:\n    uses: ./.github/workflows/missing.yml\n"
        }, manifest())
        self.assertTrue(any(x[0] == "fail" and x[1] == "CI-1" for x in result))

    def test_CI1_positive_standard_reusable_workflow_uses_hosted_input(self):
        workflows = {".github/workflows/kavosh.yml": (
            "jobs:\n  governance:\n"
            "    uses: bagdeli/KavoshStart/.github/workflows/kavosh-governance.yml@v5.0.0\n"
            "    with:\n      runs-on: '[\"ubuntu-latest\"]'\n"
        )}
        result = g.runner_workflow_problems(workflows, manifest())
        self.assertFalse(any(x[0] == "fail" and x[1] == "CI-1" for x in result))

    def test_CI1_positive_local_only_t1_static(self):
        m = manifest(runner="none", tier="T1", runtime="static")
        self.assertEqual(g.validate(m, {"allOf": SCHEMA["allOf"]}), [])
        self.assertFalse(any(x[0] == "fail" for x in g.runner_manifest_problems(m)))
        self.assertFalse(any(x[0] == "fail" for x in g.runner_workflow_problems({}, m)))

    def test_CI1_negative_local_only_not_static_or_with_workflows(self):
        m = manifest(runner="none", tier="T1", runtime="server")
        self.assertTrue(g.validate(m, {"allOf": SCHEMA["allOf"]}))
        self.assertTrue(any(x[0] == "fail" for x in g.runner_manifest_problems(m)))
        m["runtime"] = "static"
        findings = g.runner_workflow_problems({".github/workflows/ci.yml": "jobs:\n"}, m)
        self.assertTrue(any(x[0] == "fail" for x in findings))

    def test_CI1_positive_public_exception_requires_real_adr_not_private_exception(self):
        m = manifest(visibility="public", runner="self-hosted")
        self.assertTrue(g.validate(m, {"allOf": SCHEMA["allOf"]}))
        self.assertTrue(any(x[0] == "fail" and x[1] == "CI-2"
                            for x in g.runner_manifest_problems(m)))

    def test_CI1_negative_scaffolder_rejects_private_self_hosted(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            data = manifest(runner="self-hosted")
            data.update(name="Example", repo="demo/Example", summary="A purely synthetic example",
                        kavoshStart="v4.0.0")
            (target / "kavosh.project.json").write_text(json.dumps(data), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(SCAFFOLD), str(target), "--dry-run"],
                                  capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("CI-1", proc.stderr + proc.stdout)


if __name__ == "__main__":
    unittest.main()
