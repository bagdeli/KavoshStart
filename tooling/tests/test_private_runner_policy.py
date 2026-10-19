"""Private self-hosted availability, consent-gated hosted Actions, and local-only checks."""
import json
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling" / "src"))
import governance as g  # noqa: E402

SCHEMA = json.loads((ROOT / "intake" / "kavosh.project.schema.json").read_text(encoding="utf-8"))
SCAFFOLD = ROOT / "scripts" / "scaffold.py"


def manifest(visibility="private", runner="github-hosted", tier="T1", runtime="server"):
    return {"visibility": visibility, "ci": {"runner": runner}, "tier": tier, "runtime": runtime}


class PrivateActionsPolicy(unittest.TestCase):
    def test_CI1_schema_visibility_help_respects_owner_runner_decision(self):
        """Covers: CI-1 documentation/schema must not reinstate the obsolete private ban."""
        visibility_help = SCHEMA["properties"]["visibility"]["description"].lower()
        self.assertIn("private repositories may use", visibility_help)
        self.assertIn("self-hosted runner", visibility_help)
        self.assertIn("explicitly approves each exact proposed run", visibility_help)
        self.assertNotIn("self-hosted is forbidden for private", visibility_help)

    def test_CI1_positive_private_hosted_manifest(self):
        """Covers: CI-1 (positive)"""
        m = manifest()
        self.assertEqual(g.validate(m, {"allOf": SCHEMA["allOf"]}), [])
        self.assertFalse(any(x[0] == "fail" for x in g.runner_manifest_problems(m)))
        self.assertFalse(any(x[0] == "fail" for x in g.runner_workflow_problems(
            {".github/workflows/ci.yml": "jobs:\n  required:\n    runs-on: ubuntu-latest\n"}, m)
            if x[1] == "CI-1"))

    def test_CI1_positive_private_self_hosted_manifest_and_isolated_labels(self):
        """Covers: CI-1 positive for a private runner hosted on an independent server."""
        m = manifest(runner="self-hosted")
        m["repo"] = "demo/Example"
        m["ci"].update(runnerLabels=["self-hosted", "linux", "x64", "example"],
                       trustModelADR="docs/decisions/0001-runner.md")
        self.assertEqual(g.validate(m, {"allOf": SCHEMA["allOf"]}), [])
        workflows = {".github/workflows/ci.yml":
                     "jobs:\n  required:\n    runs-on: [self-hosted, linux, x64, example]\n"}
        self.assertFalse(any(level == "fail" and rule == "CI-1"
                             for level, rule, _, _ in g.runner_workflow_problems(workflows, m)))
        self.assertFalse(any(level == "fail" and rule == "CI-1"
                             for level, rule, _, _ in g.runner_manifest_problems(m)))

    def test_CI2_negative_private_self_hosted_without_isolation_adr(self):
        m = manifest(runner="self-hosted")
        m["repo"] = "demo/Example"
        self.assertEqual(g.validate(m, {"allOf": SCHEMA["allOf"]}), [])
        self.assertTrue(any(level == "fail" and rule == "CI-2"
                            for level, rule, _, _ in g.runner_manifest_problems(m)))


    def test_CI2_positive_explicit_arm64_custom_repository_labels(self):
        """Covers: CI-2 (positive); custom physical profiles are not x64-only."""
        m = manifest(runner="self-hosted")
        m["repo"] = "demo/Example"
        labels = ["self-hosted", "linux", "ARM64", "example", "gpu"]
        m["ci"].update(runnerLabels=labels, trustModelADR="docs/decisions/0001-runner.md")
        findings = g.runner_manifest_problems(m)
        self.assertFalse(any(level == "fail" and "runner labels" in title.lower()
                             for level, _, title, _ in findings), findings)
        wf = {".github/workflows/ci.yml":
              "jobs:\n  required:\n    runs-on: " + json.dumps(labels) + "\n"}
        self.assertFalse(any(level == "fail" and rid == "CI-1"
                             for level, rid, _, _ in g.runner_workflow_problems(wf, m)))
        caller = ("jobs:\n  governance:\n"
                  "    uses: bagdeli/KavoshStart/.github/workflows/kavosh-governance.yml@v6.0.0\n"
                  "    with:\n      runs-on: '" + json.dumps(labels) + "'\n")
        self.assertFalse(any(level == "fail" and rid == "CI-1"
                             for level, rid, _, _ in g.runner_workflow_problems(
                                 {".github/workflows/kavosh.yml": caller}, m)))

    def test_CI2_positive_explicit_custom_scope_label_need_not_spell_repo_slug(self):
        """Covers: CI-2 (positive); the registered dedicated selector may differ from the repo slug."""
        m = manifest(runner="self-hosted")
        m["repo"] = "demo/Example"
        m["ci"].update(runnerLabels=["self-hosted", "Linux", "X64", "isolated-ci"],
                       trustModelADR="docs/decisions/0001-runner.md")
        findings = g.runner_manifest_problems(m)
        self.assertFalse(any(level == "fail" and "runner labels" in title.lower()
                             for level, _, title, _ in findings), findings)

    def test_CI2_negative_unapproved_trust_adr_cannot_certify_runner(self):
        """Covers: CI-2 (negative); a proposed ADR is not owner approval."""
        base = "runner trust model\nisolation\nuntrusted code\ncredential boundary\ndedicated container"
        with patch.object(g.Path, "is_file", return_value=True), \
             patch.object(g.Path, "read_text", return_value="- Status: proposed\n" + base):
            self.assertIn("awaits owner acceptance", g.runner_trust_adr_problem(
                "docs/decisions/0001-runner.md", "private"))
        with patch.object(g.Path, "is_file", return_value=True), \
             patch.object(g.Path, "read_text", return_value="- Status: accepted\n" + base):
            self.assertIsNone(g.runner_trust_adr_problem(
                "docs/decisions/0001-runner.md", "private"))

    def test_CI2_positive_bounded_non_vm_host_and_firewall_containment(self):
        """Covers: CI-2 (positive); accepted host controls need not create disposable VMs."""
        body = ("- Status: accepted with bounded residual risk by owner\n"
                "runner trust model: isolation by unprivileged service account and network firewall\n"
                "untrusted code: no forks, only reviewed same-repository changes\n"
                "credential boundary: no production/Test secrets or privileged sockets\n"
                "scope: limited CI jobs; workspace and cache cleanup on each run\n")
        with patch.object(g.Path, "is_file", return_value=True), patch.object(
                g.Path, "read_text", return_value=body):
            self.assertIsNone(g.runner_trust_adr_problem(
                "docs/decisions/0001-runner.md", "private"))

    def test_CI2_negative_firewall_alone_not_host_isolation(self):
        """Covers: CI-2 (negative); network isolation does not limit local host access."""
        body = ("- Status: accepted\n"
                "runner trust model\nisolation by network firewall only\n"
                "untrusted code blocked\ncredential boundary documented\n")
        with patch.object(g.Path, "is_file", return_value=True), patch.object(
                g.Path, "read_text", return_value=body):
            self.assertIn("host/process containment", g.runner_trust_adr_problem(
                "docs/decisions/0001-runner.md", "private"))

    def test_CI2_negative_unscoped_dynamic_duplicate_or_hosted_like_labels(self):
        """Covers: CI-2 (negative); labels must be scoped, bounded and unambiguous."""
        bad_profiles = (
            [],
            ["self-hosted", "linux", "wrong"],
            ["linux", "ARM64", "example"],
            ["self-hosted", "example"],
            ["self-hosted", "linux", "example", "EXAMPLE"],
            ["self-hosted", "linux", "x64", "shared"],
            ["self-hosted", "linux", "x64"],
            ["self-hosted", "linux", "example", "ubuntu-latest"],
            ["self-hosted", "linux", "example", "$" + "{{ matrix.os }}"],
            ["self-hosted", "linux", "example", "bad\nlabel"],
            ["self-hosted", "linux", "example", 3],
        )
        for labels in bad_profiles:
            with self.subTest(labels=labels):
                m = manifest(runner="self-hosted")
                m["repo"] = "demo/Example"
                m["ci"]["runnerLabels"] = labels
                findings = g.runner_manifest_problems(m)
                self.assertTrue(any(level == "fail" and rid == "CI-2"
                                    and "runner labels" in title.lower()
                                    for level, rid, title, _ in findings), findings)

    def test_CI1_negative_public_self_hosted_dynamic_selector(self):
        """Covers: CI-1 (negative); public self-hosted also requires literal routing."""
        m = manifest(visibility="public", runner="self-hosted")
        m["repo"] = "demo/Example"
        findings = g.runner_workflow_problems(
            {".github/workflows/ci.yml":
             "jobs:\n  required:\n    runs-on: $" + "{{ matrix.labels }}\n"}, m)
        self.assertTrue(any(level == "fail" and rid == "CI-1"
                            for level, rid, _, _ in findings), findings)

    def test_CI3_positive_owner_only_metered_approval_contract(self):
        """Covers: CI-3 (positive); owner-only prior permission is explicit."""
        visibility = SCHEMA["properties"]["visibility"]["description"].lower()
        runner = SCHEMA["properties"]["ci"]["properties"]["runner"]["description"].lower()
        self.assertIn("designated human billing owner", visibility)
        self.assertIn("designated human billing owner", runner)
        self.assertNotIn("owner/admin", visibility + runner)
        self.assertIn("ADR-0019", (ROOT / "standard" / "04-ci-runners-minutes.md").read_text(encoding="utf-8"))
        start = (ROOT / "START.md").read_text(encoding="utf-8")
        self.assertNotIn("owner/admin", start)
        self.assertIn("designated human billing owner", start)

    def test_CI1_positive_case_and_order_independent_self_hosted_match(self):
        """Covers: CI-1 (positive); GitHub self-hosted labels have case-insensitive set semantics."""
        m = manifest(runner="self-hosted")
        m["repo"] = "demo/Example"
        m["ci"]["runnerLabels"] = ["self-hosted", "Linux", "X64", "isolated-ci"]
        wf = {".github/workflows/ci.yml":
              "jobs:\n  required:\n    runs-on: [self-hosted, isolated-ci, x64, LINUX]\n"}
        problems = g.runner_workflow_problems(wf, m)
        self.assertFalse(any(level == "fail" and rid == "CI-1"
                             for level, rid, _, _ in problems), problems)
        caller = ("jobs:\n  governance:\n"
                  "    uses: bagdeli/KavoshStart/.github/workflows/kavosh-governance.yml@v6.0.0\n"
                  "    with:\n      runs-on: '[\"self-hosted\", \"isolated-ci\", \"x64\", \"linux\"]'\n")
        problems = g.runner_workflow_problems({".github/workflows/kavosh.yml": caller}, m)
        self.assertFalse(any(level == "fail" and rid == "CI-1"
                             for level, rid, _, _ in problems), problems)

    def test_CI1_negative_extra_or_duplicate_self_hosted_workflow_labels(self):
        """Covers: CI-1 (negative); relaxed order/case must not broaden runner selection."""
        m = manifest(runner="self-hosted")
        m["repo"] = "demo/Example"
        m["ci"]["runnerLabels"] = ["self-hosted", "linux", "x64", "isolated-ci"]
        for labels in ("[self-hosted, linux, x64]", 
                       "[self-hosted, linux, x64, isolated-ci, extra]",
                       "[self-hosted, linux, x64, isolated-ci, ISOLATED-CI]"):
            with self.subTest(labels=labels):
                wf = {".github/workflows/ci.yml":
                      "jobs:\n  required:\n    runs-on: " + labels + "\n"}
                problems = g.runner_workflow_problems(wf, m)
                self.assertTrue(any(level == "fail" and rid == "CI-1"
                                    for level, rid, _, _ in problems), problems)

    def test_CI1_negative_private_self_hosted_wrong_labels_or_unpinned_remote_runner(self):
        m = manifest(runner="self-hosted")
        m["repo"] = "demo/Example"
        for value in ("ubuntu-latest", "[self-hosted, linux]",
                      "[self-hosted, linux, x64, another-repo]", "custom-pool",
                      "${{ matrix.os }}"):
            with self.subTest(value=value):
                wf = {".github/workflows/ci.yml":
                      "jobs:\n  required:\n    runs-on: " + value + "\n"}
                self.assertTrue(any(level == "fail" and rule == "CI-1"
                                    for level, rule, _, _ in g.runner_workflow_problems(wf, m)))
        remote = {".github/workflows/kavosh.yml":
                  "jobs:\n  governance:\n"
                  "    uses: bagdeli/KavoshStart/.github/workflows/kavosh-governance.yml@v6.0.0\n"}
        self.assertTrue(any(level == "fail" and rule == "CI-1"
                            for level, rule, _, _ in g.runner_workflow_problems(remote, m)))


    def test_CI1_positive_private_self_hosted_standard_reusable_input(self):
        m = manifest(runner="self-hosted")
        m["repo"] = "demo/Example"
        source = ("jobs:\n  governance:\n"
                  "    uses: bagdeli/KavoshStart/.github/workflows/kavosh-governance.yml@v6.0.0\n"
                  "    with:\n"
                  "      runs-on: '[\"self-hosted\", \"linux\", \"x64\", \"example\"]'\n")
        problems = g.runner_workflow_problems({".github/workflows/kavosh.yml": source}, m)
        self.assertFalse(any(level == "fail" and rule == "CI-1"
                             for level, rule, _, _ in problems), problems)

    def test_CI1_negative_private_self_hosted_reusable_wrong_input(self):
        m = manifest(runner="self-hosted")
        m["repo"] = "demo/Example"
        base = ("jobs:\n  governance:\n"
                "    uses: bagdeli/KavoshStart/.github/workflows/kavosh-governance.yml@v6.0.0\n")
        cases = {
            "missing": base,
            "hosted": base + "    with:\n      runs-on: '[\"ubuntu-latest\"]'\n",
            "other-repo": base + "    with:\n      runs-on: '[\"self-hosted\", \"linux\", \"x64\", \"wrong\"]'\n",
            "dynamic": base + "    with:\n      runs-on: '${{ matrix.labels }}'\n",
            "spoofed-env": base + "    env:\n      runs-on: '[\"self-hosted\", \"linux\", \"x64\", \"example\"]'\n",
        }
        for name, source in cases.items():
            with self.subTest(name=name):
                problems = g.runner_workflow_problems({".github/workflows/kavosh.yml": source}, m)
                self.assertTrue(any(level == "fail" and rule == "CI-1"
                                    for level, rule, _, _ in problems), problems)

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
        self.assertEqual(g.validate(m, {"allOf": SCHEMA["allOf"]}), [])
        self.assertTrue(any(x[0] == "fail" and x[1] == "CI-2"
                            for x in g.runner_manifest_problems(m)))

    def test_CI1_positive_scaffolder_private_self_hosted_selects_local_labels(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp)
            data = manifest(runner="self-hosted")
            data.update(name="Example", repo="demo/Example", summary="A purely synthetic example",
                        kavoshStart="v6.0.0")
            data["ci"]["runnerLabels"] = ["self-hosted", "linux", "x64", "example"]
            (target / "kavosh.project.json").write_text(json.dumps(data), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(SCAFFOLD), str(target), "--dry-run"],
                                  capture_output=True, text=True)
            self.assertEqual(proc.returncode, 0, proc.stderr + proc.stdout)


if __name__ == "__main__":
    unittest.main()
