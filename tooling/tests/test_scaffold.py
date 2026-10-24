import sys
import json
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import scaffold  # noqa: E402


class StandardPin(unittest.TestCase):
    def test_ACC1_positive_T2_default_excludes_optional_services(self):
        owner = {"tier": "T2", "acceptance": {"mode": "none"}}
        self.assertFalse(scaffold.include_template("tier/T2", "acceptance/scope.json", owner))
        self.assertFalse(scaffold.include_template("tier/T2", "acceptance/security/receipt-policy.json", owner))
        self.assertFalse(scaffold.include_template("tier/T2", ".github/workflows/ai-review.yml", owner))
        self.assertFalse(scaffold.include_template("common", "docs/THIRD_PARTY.md", owner))

    def test_ACC1_positive_explicit_team_acceptance_installs_only_selected_contract(self):
        m = {"tier": "T2", "acceptance": {"mode": "continuous", "assurance": "attested"}}
        self.assertTrue(scaffold.include_template("tier/T2", "acceptance/scope.json", m))
        self.assertFalse(scaffold.include_template("tier/T2", ".github/workflows/ai-review.yml", m))
        self.assertTrue(scaffold.include_template("common", "PROJECT.md", m))


    def test_consumer_exact_release_pin_is_valid(self):
        scaffold.validate_standard_pin({"repo": "bagdeli/ExampleConsumer", "kavoshStart": "v1.7.0"})

    def test_canonical_standard_self_identity_is_valid(self):
        scaffold.validate_standard_pin({"repo": "bagdeli/KavoshStart", "kavoshStart": "self"})

    def test_consumer_self_identity_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "reserved"):
            scaffold.validate_standard_pin({"repo": "bagdeli/ExampleConsumer", "kavoshStart": "self"})

    def test_unresolved_or_floating_consumer_pin_is_rejected(self):
        for pin in ("vX.Y.Z", "v1", "main", "1.7.0", None):
            with self.subTest(pin=pin):
                with self.assertRaisesRegex(SystemExit, "exact release tag"):
                    scaffold.validate_standard_pin({"repo": "bagdeli/ExampleConsumer", "kavoshStart": pin})

    def test_package_job_follows_release_artifact_deploy_outcome(self):
        base = {
            "name": "Example",
            "repo": "bagdeli/Example",
            "summary": "Example project for scaffold adapter tests",
            "tier": "T1",
            "runtime": "server",
            "kavoshStart": "v2.0.5",
            "ui": {"kind": "none"},
            "deploy": {"method": "release-artifact"},
            "ci": {"runner": "github-hosted", "monthlyMinutesBudget": 0},
        }
        self.assertEqual(scaffold.values(base)["PACKAGE"], "true")
        base["deploy"]["method"] = "pull-build"
        base["runtime"] = "desktop"
        self.assertEqual(scaffold.values(base)["PACKAGE"], "false")

    def test_standard_version_pin_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "must use kavoshStart 'self'"):
            scaffold.validate_standard_pin({"repo": "bagdeli/KavoshStart", "kavoshStart": "v1.7.0"})


class SelectedScaffolding(unittest.TestCase):
    def manifest(self, team=False, method="custom"):
        m = json.loads((ROOT / "intake/kavosh.project.example.json").read_text())
        m["kavoshStart"] = "v8.1.0"
        m["review"] = {"teamProcess": team}
        m["acceptance"] = {"mode": "none"}
        m["deploy"]["method"] = method
        return m

    def test_owner_core_retained_and_unselected_team_files_omitted(self):
        for team in (False, True):
            with tempfile.TemporaryDirectory() as temp:
                root = Path(temp)
                (root / "kavosh.project.json").write_text(json.dumps(self.manifest(team)))
                run = subprocess.run([sys.executable, str(ROOT / "scripts/scaffold.py"), temp], capture_output=True)
                self.assertEqual(run.returncode, 0, run.stderr)
                for name in ("PROJECT.md", "AGENTS.md", "Makefile", ".githooks/pre-push",
                             ".github/workflows/ci.yml", ".github/workflows/kavosh.yml",
                             ".github/workflows/release.yml"):
                    self.assertTrue((root / name).is_file(), name)
                self.assertEqual((root / "specs/_template/spec.md").exists(), team)
                self.assertEqual((root / ".github/ISSUE_TEMPLATE/task.yml").exists(), team)
                self.assertFalse((root / "compose.yaml").exists())
                self.assertFalse((root / "deploy").exists())
                self.assertFalse((root / "docs/runbooks/deploy.md").exists())
                self.assertFalse((root / "acceptance").exists())
                self.assertNotIn("package-ecosystem: pip", (root / ".github/dependabot.yml").read_text())
                self.assertNotIn("package-ecosystem: npm", (root / ".github/dependabot.yml").read_text())
                self.assertIn("check-full: check", (root / "Makefile").read_text())
                self.assertNotEqual(subprocess.run(["make", "test"], cwd=root, capture_output=True).returncode, 0)

    def test_per_job_selection_is_rendered_without_changing_default_runner(self):
        import yaml
        m = self.manifest()
        m["visibility"] = "private"
        m["ci"].update(runner="self-hosted", runnerLabels=["self-hosted", "linux", "x64", "example-ci"],
                       runnerJobLabels={".github/workflows/release.yml#release": ["self-hosted", "linux", "x64", "example-release"]})
        vals = scaffold.values(m)
        rel = ".github/workflows/release.yml"
        text = scaffold.render((ROOT / "templates/common" / rel).read_text(), vals, rel)
        text = scaffold.render_job_runners(text, rel, m)
        actual = json.loads(yaml.safe_load(text)["jobs"]["release"]["with"]["runs-on"])
        self.assertEqual(actual, m["ci"]["runnerJobLabels"][rel + "#release"])
        rel = ".github/workflows/ci.yml"
        text = scaffold.render((ROOT / "templates/common" / rel).read_text(), vals, rel)
        text = scaffold.render_job_runners(text, rel, m)
        self.assertEqual(yaml.safe_load(text)["jobs"]["required"]["runs-on"], m["ci"]["runnerLabels"])

    def test_adopt_never_overwrites_a_pending_review_file(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / "kavosh.project.json").write_text(json.dumps(self.manifest()))
            (root / "README.md").write_text("existing product documentation")
            (root / "README.md.kavosh-new").write_text("owner review in progress")
            run = subprocess.run([sys.executable, str(ROOT / "scripts/scaffold.py"), temp, "--adopt"], capture_output=True)
            self.assertNotEqual(run.returncode, 0)
            self.assertEqual((root / "README.md").read_text(), "existing product documentation")
            self.assertEqual((root / "README.md.kavosh-new").read_text(), "owner review in progress")

    def test_bootstrap_default_is_dry_run_without_team_taxonomy_or_milestone(self):
        cmd = ["bash", str(ROOT / "scripts/bootstrap-repo.sh"), "example/example"]
        run = subprocess.run(cmd, capture_output=True, text=True)
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("DRY-RUN", run.stdout)
        self.assertNotIn("type:epic", run.stdout)
        self.assertNotIn("/milestones", run.stdout)
        team = subprocess.run(cmd + ["--team-process", "--milestone", "v0.2.0"], capture_output=True, text=True)
        self.assertEqual(team.returncode, 0, team.stderr)
        self.assertIn("type:epic", team.stdout)
        self.assertIn("/milestones", team.stdout)
        self.assertIn("v0.2.0", team.stdout)

    def test_scaffold_rejects_invalid_manifest_before_writing_any_templates(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            m = self.manifest()
            m["capabilities"] = ["server", "server"]  # schema.uniqueItems
            (root / "kavosh.project.json").write_text(json.dumps(m), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(ROOT / "scripts/scaffold.py"), temp],
                                  capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("SRC-5", proc.stderr)
            self.assertIn("duplicate", proc.stderr)
            self.assertEqual({p.name for p in root.iterdir()}, {"kavosh.project.json"})
            m["capabilities"] = ["server"]
            m["ci"]["monthlyMinutesBudget"] = "none"  # schema integer
            (root / "kavosh.project.json").write_text(json.dumps(m), encoding="utf-8")
            proc = subprocess.run([sys.executable, str(ROOT / "scripts/scaffold.py"), temp],
                                  capture_output=True, text=True)
            self.assertNotEqual(proc.returncode, 0)
            self.assertIn("SRC-5", proc.stderr)
            self.assertEqual({p.name for p in root.iterdir()}, {"kavosh.project.json"})

    def test_runner_label_yaml_is_lossless_even_with_quoting_characters(self):
        import yaml
        m = self.manifest()
        m["visibility"] = "private"
        m["ci"].update(runner="self-hosted", runnerLabels=["self-hosted", "linux", "x64", "rack's-01"],
                       runnerJobLabels={".github/workflows/release.yml#release":
                                        ["self-hosted", "linux", "x64", "rack's-02"]})
        vals = scaffold.values(m)
        ci = scaffold.render((ROOT / "templates/common/.github/workflows/ci.yml").read_text(),
                             vals, ".github/workflows/ci.yml")
        release = scaffold.render((ROOT / "templates/common/.github/workflows/release.yml").read_text(),
                                  vals, ".github/workflows/release.yml")
        release = scaffold.render_job_runners(release, ".github/workflows/release.yml", m)
        caller = scaffold.render((ROOT / "templates/common/.github/workflows/kavosh.yml").read_text(),
                                 vals, ".github/workflows/kavosh.yml")
        self.assertEqual(yaml.safe_load(ci)["jobs"]["required"]["runs-on"], m["ci"]["runnerLabels"])
        self.assertEqual(json.loads(yaml.safe_load(release)["jobs"]["release"]["with"]["runs-on"]),
                         m["ci"]["runnerJobLabels"][".github/workflows/release.yml#release"])
        self.assertEqual(json.loads(yaml.safe_load(caller)["jobs"]["kavosh"]["with"]["runs-on"]),
                         m["ci"]["runnerLabels"])

    def test_pull_adapter_is_not_removed_by_owner_mode(self):
        m = self.manifest(method="pull-build")
        self.assertTrue(scaffold.include_template("runtime/server", "compose.yaml", m))
        self.assertTrue(scaffold.include_template("runtime/server", "deploy/kavosh-deploy.sh", m))
        self.assertFalse(scaffold.include_template("tier/T1", "docs/runbooks/local-validation.md", m))
        m["ci"]["runner"] = "none"
        self.assertTrue(scaffold.include_template("tier/T1", "docs/runbooks/local-validation.md", m))


if __name__ == "__main__":
    unittest.main()
