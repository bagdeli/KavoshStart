"""Offline tests for DEP rules in templates/runtime/server/deploy/kavosh-deploy.sh (needs bash + git)."""
import shutil
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "templates" / "runtime" / "server" / "deploy" / "kavosh-deploy.sh"
BASH = shutil.which("bash")


def latest(tags):
    with tempfile.TemporaryDirectory() as d:
        run = lambda *a: subprocess.run(["git", *a], cwd=d, check=True, capture_output=True)  # noqa: E731
        run("init", "-q")
        run("-c", "user.email=t@t", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "x")
        for t in tags:
            run("tag", t)
        out = subprocess.run([BASH, str(SCRIPT), "--print-target", d], capture_output=True, text=True, check=True)
        return out.stdout.strip()


@unittest.skipUnless(BASH, "bash not available")
class TagSelection(unittest.TestCase):
    def test_DEP2_positive_final_beats_its_rc(self):
        self.assertEqual(latest(["v1.0.1-rc.1", "v1.0.1", "v1.0.0"]), "v1.0.1")

    def test_DEP2_positive_numeric_minor(self):
        self.assertEqual(latest(["v1.9.0", "v1.10.0", "v1.2.0"]), "v1.10.0")

    def test_DEP2_positive_rc_of_newer_version_is_picked_on_test(self):
        self.assertEqual(latest(["v1.0.1", "v1.1.0-rc.2"]), "v1.1.0-rc.2")

    def test_DEP2_positive_rc_numbering(self):
        self.assertEqual(latest(["v2.0.0-rc.9", "v2.0.0-rc.10"]), "v2.0.0-rc.10")

    def test_DEP2_negative_non_semver_tags_ignored(self):
        self.assertEqual(latest(["develop", "v1", "v2.0.0-beta", "v1.2.3"]), "v1.2.3")

    def test_DEP2_negative_no_valid_tag(self):
        self.assertEqual(latest(["develop", "v1"]), "")


@unittest.skipUnless(BASH, "bash not available")
class ScriptContract(unittest.TestCase):
    def test_DEP6_continuous_recovery_checked_and_high_risk_snapshot_before_migration(self):
        text = SCRIPT.read_text(encoding="utf-8")
        recovery, snapshot, migrate, start = (text.index('eval "$BACKUP_HEALTHCHECK_CMD"'),
            text.index('eval "$BACKUP_CMD"'), text.index('eval "$MIGRATE_CMD"'), text.index('if start "$target"'))
        self.assertLess(recovery, snapshot)
        self.assertLess(snapshot, migrate)
        self.assertLess(migrate, start)
        self.assertIn("MIGRATE_CMD is set but BACKUP_HEALTHCHECK_CMD is empty", text)
        self.assertIn("high-risk migration requires BACKUP_CMD snapshot", text)

    def test_DEP3_dry_run_is_read_only_and_pin_is_production_only(self):
        with tempfile.TemporaryDirectory() as d:
            env = {"PROJECT": "sample", "REPO_URL": "https://example.invalid/repo.git",
                   "BASE": str(Path(d) / "base"), "CHANNEL": "production"}
            result = subprocess.run([BASH, str(SCRIPT), "--pin", "v1.2.3", "--dry-run"], env={**os.environ, **env},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((Path(d) / "base").exists())
            env["CHANNEL"] = "test"
            result = subprocess.run([BASH, str(SCRIPT), "--pin", "v1.2.3", "--dry-run"], env={**os.environ, **env},
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)

    def test_DEP4_env_outside_release_dirs_and_clean_export(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('ln -sfn "$BASE/shared/.env"', text)
        self.assertIn("git -C \"$BASE/repo.git\" archive", text)
        self.assertNotIn("checkout", text)

    def test_syntax(self):
        subprocess.run([BASH, "-n", str(SCRIPT)], check=True)


if __name__ == "__main__":
    unittest.main()
