"""v6 distinguishes independent SelfServer CI from GitHub-registered Actions runners.

An editable ADR does not prove owner consent or an external check publisher;
the tests verify only machine-checkable wiring and fail-closed boundaries.
"""
import json
import os
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
EXAMPLE = json.loads((ROOT / "intake" / "kavosh.project.example.json").read_text(encoding="utf-8"))
EXTERNAL = "docs/decisions/0001-external-ci.md"
RELEASE = "docs/decisions/0002-external-release.md"
TRUST = "docs/decisions/0003-runner-trust.md"
APPROVAL = "docs/decisions/0004-owner-exception.md"


def has_fail(results, rule):
    return any(level == "fail" and name == rule for level, name, *_ in results)


def setup_adrs(where):
    directory = Path(where) / "docs" / "decisions"
    directory.mkdir(parents=True, exist_ok=True)
    (directory / Path(EXTERNAL).name).write_text(
        "independent CI: exact SHA, trusted publisher, real required and "
        "kavosh / governance checks; release gate and credential boundary.\n",
        encoding="utf-8",
    )
    (directory / Path(RELEASE).name).write_text(
        "Release strategy: custom, semver vX.Y.Z immutable tag, exact source "
        "identity, provenance, required check and release gate.\n", encoding="utf-8",
    )
    script = Path(where) / "scripts" / "release.sh"
    script.parent.mkdir(parents=True, exist_ok=True)
    script.write_text("#!/bin/sh\nexit 1  # never pretend to publish a release\n",
                      encoding="utf-8")
    (directory / Path(TRUST).name).write_text(
        "Runner trust model with isolation: ephemeral virtual machine "
        "limits untrusted code; credential boundary excludes production.\n",
        encoding="utf-8",
    )
    (directory / Path(APPROVAL).name).write_text(
        "Scope: explicit owner approval for a narrow exception to the "
        "private registered runner policy. Untrusted code and credential boundary reviewed.\n",
        encoding="utf-8",
    )


def mode_manifest(runner):
    m = json.loads(json.dumps(EXAMPLE))
    m["kavoshStart"] = "v6.0.0"
    m["repo"] = "demo/Example"
    m["ci"] = {"runner": runner, "monthlyMinutesBudget": 0}
    if runner == "external":
        m["ci"]["externalCIADR"] = EXTERNAL
        m["release"] = {"strategy": "custom", "strategyADR": RELEASE, "externalCommand": "scripts/release.sh"}
    if runner == "self-hosted":
        m["ci"]["trustModelADR"] = TRUST
        m["ci"]["privateSelfHostedApprovalADR"] = APPROVAL
    return m


class RunnerAuthorityV6(unittest.TestCase):
    def test_schema_rejects_private_self_hosted_without_specific_exception(self):
        m = mode_manifest("self-hosted")
        m["ci"].pop("privateSelfHostedApprovalADR")
        self.assertTrue(g.validate(m, {"allOf": SCHEMA["allOf"]}))
        self.assertTrue(has_fail(g.runner_manifest_problems(m), "CI-1"))

    def test_external_requires_ci_adr_and_independent_release(self):
        m = mode_manifest("external")
        self.assertEqual(g.validate(m, {"allOf": SCHEMA["allOf"]}), [])
        with tempfile.TemporaryDirectory() as d:
            previous = os.getcwd()
            try:
                os.chdir(d)
                setup_adrs(d)
                self.assertFalse(has_fail(g.runner_manifest_problems(m), "CI-1"))
            finally:
                os.chdir(previous)
        m["release"]["strategy"] = "release-please"
        self.assertTrue(g.validate(m, {"allOf": SCHEMA["allOf"]}))
        m = mode_manifest("external")
        m["release"]["workflow"] = ".github/workflows/release.yml"
        self.assertTrue(g.validate(m, {"allOf": SCHEMA["allOf"]}))
        self.assertTrue(has_fail(g.runner_manifest_problems(m), "CI-1"))
        m = mode_manifest("external")
        m["ci"].pop("externalCIADR")
        self.assertTrue(g.validate(m, {"allOf": SCHEMA["allOf"]}))

    def test_external_refuses_all_github_actions_workflows(self):
        m = mode_manifest("external")
        self.assertFalse(has_fail(g.runner_workflow_problems({}, m), "CI-1"))
        self.assertTrue(has_fail(g.runner_workflow_problems({
            ".github/workflows/ci.yml": "jobs:\n  required:\n    runs-on: ubuntu-latest\n"
        }, m), "CI-1"))

    def test_external_cannot_masquerade_with_actions_metadata(self):
        m = mode_manifest("external")
        for field, value in (("runnerLabels", ["self-hosted"]), ("trustModelADR", TRUST),
                             ("requiredWorkflow", ".github/workflows/ci.yml"),
                             ("privateSelfHostedApprovalADR", APPROVAL)):
            with self.subTest(field=field):
                n = json.loads(json.dumps(m))
                n["ci"][field] = value
                self.assertTrue(g.validate(n, {"allOf": SCHEMA["allOf"]}))
                self.assertTrue(has_fail(g.runner_manifest_problems(n), "CI-1"))

    def test_gh_hosted_rejects_private_runner_and_external_fields(self):
        m = mode_manifest("github-hosted")
        self.assertEqual(g.validate(m, {"allOf": SCHEMA["allOf"]}), [])
        for field, value in (("runnerLabels", ["self-hosted"]), ("externalCIADR", EXTERNAL),
                             ("privateSelfHostedApprovalADR", APPROVAL)):
            with self.subTest(field=field):
                n = json.loads(json.dumps(m))
                n["ci"][field] = value
                self.assertTrue(g.validate(n, {"allOf": SCHEMA["allOf"]}))
                self.assertTrue(has_fail(g.runner_manifest_problems(n), "CI-1"))

    def test_private_github_actions_exception_requires_both_real_adrs(self):
        m = mode_manifest("self-hosted")
        self.assertEqual(g.validate(m, {"allOf": SCHEMA["allOf"]}), [])
        with tempfile.TemporaryDirectory() as d:
            previous = os.getcwd()
            try:
                os.chdir(d)
                self.assertTrue(has_fail(g.runner_manifest_problems(m), "CI-1"))
                setup_adrs(d)
                self.assertFalse(has_fail(g.runner_manifest_problems(m), "CI-1"))
                self.assertFalse(has_fail(g.runner_manifest_problems(m), "CI-2"))
                # A safe-looking ADR is never cryptographic human approval.
            finally:
                os.chdir(previous)

    def test_registered_self_hosted_workflows_must_use_exact_repo_labels(self):
        """An allowed runner must not accidentally select a shared GH host."""
        m = mode_manifest("self-hosted")
        good = {".github/workflows/ci.yml":
                "jobs:\n  required:\n"
                "    runs-on: [self-hosted, linux, x64, example]\n"}
        self.assertFalse(has_fail(g.runner_workflow_problems(good, m), "CI-1"))
        for labels in ("[self-hosted, linux]",
                       "[self-hosted, linux, x64, unrelated]",
                       "custom-label"):
            with self.subTest(labels=labels):
                bad = {".github/workflows/ci.yml":
                       "jobs:\n  required:\n    runs-on: " + labels + "\n"}
                self.assertTrue(has_fail(g.runner_workflow_problems(bad, m), "CI-1"))

    def test_scaffold_external_has_no_workflows_and_no_actions_release(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            m = mode_manifest("external")
            setup_adrs(d)
            (target / "kavosh.project.json").write_text(json.dumps(m), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCAFFOLD), str(target)],
                               capture_output=True, text=True, check=False)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            self.assertEqual(list((target / ".github" / "workflows").glob("*"))
                             if (target / ".github" / "workflows").exists() else [], [])
            self.assertFalse((target / "release-please-config.json").exists())
            self.assertFalse((target / ".release-please-manifest.json").exists())

    def test_scaffold_private_excepted_actions_only_on_manual_scope(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d)
            m = mode_manifest("self-hosted")
            setup_adrs(d)
            (target / "kavosh.project.json").write_text(json.dumps(m), encoding="utf-8")
            r = subprocess.run([sys.executable, str(SCAFFOLD), str(target)],
                               capture_output=True, text=True, check=False)
            self.assertEqual(r.returncode, 0, r.stderr + r.stdout)
            for name in ("ci.yml", "kavosh.yml", "release.yml"):
                content = (target / ".github" / "workflows" / name).read_text(encoding="utf-8")
                self.assertIn("PRIVATE_ACTIONS_DISPATCH_REQUIRED", content)
                self.assertIn("!true", content)
                self.assertIn("workflow_dispatch:", content)
            self.assertIn("[self-hosted, linux, x64, example]",
                          (target / ".github" / "workflows" / "ci.yml").read_text())

    def test_actual_owner_grant_and_check_publisher_are_human_boundaries(self):
        policy = (ROOT / "docs" / "decisions" /
                  "0018-runner-execution-authority.md").read_text(encoding="utf-8")
        self.assertIn("not proof", policy)
        self.assertIn("exact SHA", policy)
        self.assertIn("administrator", policy)
        self.assertIn("human", policy.lower())
        self.assertIn("not automatic", policy.lower())


if __name__ == "__main__":
    unittest.main()
