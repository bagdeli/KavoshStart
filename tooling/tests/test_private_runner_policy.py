"""Private local-only conformance: never Actions, regardless of tier/runtime."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling/src"))
import governance as g

SCHEMA = json.loads((ROOT / "intake/kavosh.project.schema.json").read_text(encoding="utf-8"))
EXAMPLE = json.loads((ROOT / "intake/kavosh.project.example.json").read_text(encoding="utf-8"))


def manifest(visibility="private", runner="none", tier="T2", runtime="server"):
    return {"visibility": visibility, "tier": tier, "runtime": runtime,
            "ci": {"runner": runner, "monthlyMinutesBudget": 0}, "repo": "demo/example"}


class PrivateActionsPolicy(unittest.TestCase):
    def test_CI1_positive_private_all_tiers_runtimes_are_local_only(self):
        """Covers: CI-1 (positive)"""
        for tier in ("T0", "T1", "T2"):
            for runtime in ("none", "server", "static", "desktop"):
                m = manifest(tier=tier, runtime=runtime)
                with self.subTest(tier=tier, runtime=runtime):
                    self.assertEqual(g.validate(m, {"allOf": SCHEMA["allOf"]}), [])
                    self.assertFalse(any(z[0] == "fail" for z in g.runner_manifest_problems(m)))
                    self.assertFalse(any(z[0] == "fail" for z in g.runner_workflow_problems({}, m)))

    def test_CI1_negative_private_any_runner_even_manual_dispatch(self):
        """Covers: CI-1 (negative)"""
        for runner in ("github-hosted", "self-hosted"):
            with self.subTest(runner=runner):
                m = manifest(runner=runner)
                self.assertTrue(g.validate(m, {"allOf": SCHEMA["allOf"]}))
                self.assertTrue(any(z[0] == "fail" and z[1] == "CI-1"
                                    for z in g.runner_manifest_problems(m)))

    def test_CI1_negative_private_any_workflow_even_conditional_or_reusable(self):
        m = manifest()
        for name, text in (
            ("hosted.yml", "name: hosted\non: workflow_dispatch\njobs:\n  a:\n    if: false\n    runs-on: ubuntu-latest\n"),
            ("self.yml", "jobs:\n  a:\n    runs-on: [self-hosted, linux, x64]\n"),
            ("remote.yml", "jobs:\n  a:\n    uses: external/foo/.github/workflows/build.yml@abc\n"),
            ("empty.yml", "# a disabled workflow file is still forbidden\n"),
        ):
            with self.subTest(name=name):
                got = g.runner_workflow_problems({".github/workflows/"+name: text}, m)
                self.assertTrue(any(z[0] == "fail" and z[1] == "CI-1" for z in got))

    def test_CI1_negative_private_metadata_budget_and_workflow(self):
        for key, value in (
            ("runnerLabels", ["self-hosted", "linux"]), ("runners", 1),
            ("trustModelADR", "docs/decisions/0001-trust.md"),
            ("requiredWorkflow", ".github/workflows/ci.yml"),
            ("monthlyMinutesBudget", 1),
        ):
            m = manifest()
            m["ci"][key] = value
            with self.subTest(key=key):
                self.assertTrue(g.validate(m, {"allOf": SCHEMA["allOf"]}))
                self.assertTrue(any(z[0] == "fail" and z[1] == "CI-1"
                                    for z in g.runner_manifest_problems(m)))

    def test_CI1_positive_public_standard_hosted(self):
        m = manifest(visibility="public", runner="github-hosted")
        self.assertFalse(any(z[0] == "fail" for z in g.runner_manifest_problems(m)))
        got = g.runner_workflow_problems({
            ".github/workflows/ci.yml": "jobs:\n  build:\n    runs-on: ubuntu-latest\n",
        }, m)
        self.assertFalse(any(z[0] == "fail" and z[1] == "CI-1" for z in got))

    def test_CI1_negative_public_none_outside_T1_static(self):
        m = manifest(visibility="public",runner="none",tier="T2",runtime="server")
        self.assertTrue(g.validate(m, {"allOf": SCHEMA["allOf"]}))
        self.assertTrue(any(z[0] == "fail" for z in g.runner_manifest_problems(m)))

    def test_CI1_positive_public_T1_static_none(self):
        m = manifest(visibility="public",runner="none",tier="T1",runtime="static")
        self.assertEqual(g.validate(m, {"allOf": SCHEMA["allOf"]}), [])
        self.assertFalse(any(z[0] == "fail" for z in g.runner_manifest_problems(m)))

    def test_CI1_positive_private_example_intake_defaults_to_none(self):
        self.assertEqual(EXAMPLE["visibility"], "private")
        self.assertEqual(EXAMPLE["ci"], {"runner":"none","monthlyMinutesBudget":0})

    def test_CI1_negative_scaffolder_rejects_both_runner_kinds_for_private(self):
        for runner in ("self-hosted", "github-hosted"):
            with self.subTest(runner=runner), tempfile.TemporaryDirectory() as tmp:
                path=Path(tmp)
                m=json.loads(json.dumps(EXAMPLE))
                m["repo"]="demo/Example"
                m["kavoshStart"]="v5.0.0"
                m["ci"]={"runner":runner,"monthlyMinutesBudget":0}
                (path/"kavosh.project.json").write_text(json.dumps(m),encoding="utf-8")
                x=subprocess.run([sys.executable,str(ROOT/"scripts/scaffold.py"),str(path),"--dry-run"],
                                 capture_output=True,text=True)
                self.assertNotEqual(x.returncode,0)
                self.assertIn("CI-1",x.stderr+x.stdout)

    def test_CI1_positive_private_T2_scaffolds_without_any_workflows(self):
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)
            m=json.loads(json.dumps(EXAMPLE))
            m["repo"]="demo/Example"
            m["kavoshStart"]="v5.0.0"
            (path/"kavosh.project.json").write_text(json.dumps(m),encoding="utf-8")
            x=subprocess.run([sys.executable,str(ROOT/"scripts/scaffold.py"),str(path)],
                             capture_output=True,text=True)
            self.assertEqual(x.returncode,0,x.stderr+x.stdout)
            self.assertEqual(list((path/".github/workflows").rglob("*")) if (path/".github/workflows").exists() else [],[])
