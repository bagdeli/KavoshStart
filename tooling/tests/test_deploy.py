"""Offline tests for deployment/environment rules in templates/runtime/server/deploy/kavosh-deploy.sh."""
import os
import shutil
import stat
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
        for tag in tags:
            run("tag", tag)
        out = subprocess.run([BASH, str(SCRIPT), "--print-target", d], capture_output=True, text=True, check=True)
        return out.stdout.strip()


def make_executable(path, text):
    path.write_text(text, encoding="utf-8")
    path.chmod(path.stat().st_mode | stat.S_IXUSR)


def admitted_environment(root, wrong_sha=False, health_fails=False):
    """Create a filesystem-only standard Test host plus fake curl/systemctl for --verify-environment."""
    tag = "v1.2.3"
    base = root / "base"
    repo = base / "repo.git"
    repo.mkdir(parents=True)
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "-c", "user.email=t@t", "-c", "user.name=t",
                    "commit", "-q", "--allow-empty", "-m", "x"], cwd=repo, check=True)
    subprocess.run(["git", "tag", tag], cwd=repo, check=True)
    sha = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo, check=True,
                         capture_output=True, text=True).stdout.strip()

    (base / "releases" / tag).mkdir(parents=True)
    (base / "shared").mkdir()
    (base / "shared" / ".env").write_text("SYNTHETIC=1\n", encoding="utf-8")
    (base / "current").symlink_to(Path("releases") / tag)

    state = root / "state"
    state.mkdir()
    (state / "deploy.env").write_text("PROJECT=sample\n", encoding="utf-8")

    deploy_bin = root / "kavosh-deploy-sample"
    make_executable(deploy_bin, "#!/usr/bin/env bash\nexit 0\n")
    unit_dir = root / "units"
    unit_dir.mkdir()
    (unit_dir / "kavosh-deploy-sample.service").write_text("[Service]\n", encoding="utf-8")
    (unit_dir / "kavosh-deploy-sample.timer").write_text("[Timer]\n", encoding="utf-8")

    fake_systemctl = root / "systemctl"
    make_executable(fake_systemctl, "#!/usr/bin/env bash\nexit 0\n")

    fake_curl = root / "curl"
    make_executable(fake_curl, """#!/usr/bin/env bash
set -euo pipefail
url="${!#}"
case "$url" in
  */version)
    sha="$FAKE_SHA"
    if [ "${FAKE_WRONG_SHA:-0}" = 1 ]; then sha="bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb"; fi
    printf '{"version":"%s","sha":"%s"}' "$FAKE_VERSION" "$sha"
    ;;
  */health)
    [ "${FAKE_HEALTH_FAIL:-0}" != 1 ] || exit 22
    printf '{"status":"ok"}'
    ;;
  *) exit 22 ;;
esac
""")

    env = {
        **os.environ,
        "PROJECT": "sample",
        "BASE": str(base),
        "CHANNEL": "test",
        "DEPLOY_METHOD": "pull-build",
        "REPO_URL": "https://example.invalid/repo.git",
        "VERSION_URL": "http://127.0.0.1:18080/version",
        "HEALTH_URL": "http://127.0.0.1:18080/health",
        "PUBLIC_BASE_URL": "https://test.example.invalid",
        "STATE_DIR": str(state),
        "DEPLOY_BIN": str(deploy_bin),
        "UNIT_DIR": str(unit_dir),
        "SYSTEMCTL": str(fake_systemctl),
        "CURL": str(fake_curl),
        "FAKE_VERSION": tag,
        "FAKE_SHA": sha,
        "FAKE_WRONG_SHA": "1" if wrong_sha else "0",
        "FAKE_HEALTH_FAIL": "1" if health_fails else "0",
    }
    return env, unit_dir


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
    def test_DEP3_positive_identity_is_separate_and_exact(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('VERSION_URL="${VERSION_URL:-http://127.0.0.1:8080/version}"', text)
        self.assertIn('HEALTH_URL="${HEALTH_URL:-http://127.0.0.1:8080/health}"', text)
        self.assertIn('d.get("version")==os.environ["EXPECTED_VERSION"]', text)
        self.assertIn('d.get("sha")==os.environ["EXPECTED_SHA"]', text)

    def test_DEP3_negative_wrong_runtime_sha_fails_environment(self):
        """Covers: DEP-3, DEP-8 (negative)"""
        with tempfile.TemporaryDirectory() as d:
            env, _ = admitted_environment(Path(d), wrong_sha=True)
            result = subprocess.run([BASH, str(SCRIPT), "--verify-environment"], env=env,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("runtime-drift", result.stderr)

    def test_DEP4_positive_clean_release_env_boundary_and_independent_health(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('ln -sfn "$BASE/shared/.env"', text)
        self.assertIn('git -C "$BASE/repo.git" archive', text)
        self.assertNotIn("git checkout", text)
        self.assertIn('health_ok "$HEALTH_URL"', text)
        self.assertIn('health_ok "$PUBLIC_BASE_URL/health"', text)

    def test_DEP4_negative_health_failure_is_not_hidden_by_valid_version(self):
        with tempfile.TemporaryDirectory() as d:
            env, _ = admitted_environment(Path(d), health_fails=True)
            result = subprocess.run([BASH, str(SCRIPT), "--verify-environment"], env=env,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("runtime-drift", result.stderr)

    def test_DEP5_positive_maintenance_window_is_T1_direct_per_tag_authorized(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("--authorize-maintenance-window", text)
        self.assertIn('[ "$manifest_tier" = T1 ]', text)
        self.assertIn('[ "${MAINTENANCE_AUTH_TAG:-}" = "$target" ]', text)
        self.assertIn('eval "$MAINTENANCE_STOP_CMD"', text)

    def test_DEP5_negative_maintenance_failure_does_not_assume_rollback_compatibility(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("maintenance-window migration is not assumed backward-compatible", text)
        self.assertIn("service remains stopped for manual recovery", text)

    def test_DEP6_positive_recovery_checked_before_migration(self):
        text = SCRIPT.read_text(encoding="utf-8")
        recovery = text.index('eval "$BACKUP_HEALTHCHECK_CMD"')
        restore_test = text.index('eval "$RESTORE_TEST_CHECK_CMD"')
        snapshot = text.index('eval "$BACKUP_CMD"')
        migrate = text.index('eval "$MIGRATE_CMD"')
        self.assertLess(recovery, restore_test)
        self.assertLess(restore_test, snapshot)
        self.assertLess(snapshot, migrate)

    def test_DEP6_negative_missing_recovery_inputs_fail_closed(self):
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn("MIGRATE_CMD is set but BACKUP_HEALTHCHECK_CMD is empty", text)
        self.assertIn("MIGRATE_CMD is set but RESTORE_TEST_CHECK_CMD is empty", text)
        self.assertIn("high-risk migration requires BACKUP_CMD snapshot", text)
        self.assertIn("database is never automatically restored", text)

    def test_DEP7_positive_standard_environment_is_admitted(self):
        """Covers: DEP-3, DEP-4, DEP-7, DEP-8 (positive)"""
        with tempfile.TemporaryDirectory() as d:
            env, _ = admitted_environment(Path(d))
            result = subprocess.run([BASH, str(SCRIPT), "--verify-environment"], env=env,
                                    capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("ENVIRONMENT_CONFORMANCE=PASS", result.stdout)

    def test_DEP7_negative_missing_project_scoped_timer_rejects_admission(self):
        with tempfile.TemporaryDirectory() as d:
            env, units = admitted_environment(Path(d))
            (units / "kavosh-deploy-sample.timer").unlink()
            result = subprocess.run([BASH, str(SCRIPT), "--verify-environment"], env=env,
                                    capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("ENVIRONMENT_CONFORMANCE=FAIL", result.stderr)

    def test_DEP8_positive_noop_path_rechecks_runtime_instead_of_exiting_blindly(self):
        text = SCRIPT.read_text(encoding="utf-8")
        block = text[text.index('if [ "$target" = "$current" ]'):text.index('log "deploying $target')]
        self.assertIn('runtime_ok_once "$target" "$target_sha"', block)
        self.assertIn("no deployment drift", block)

    def test_DEP8_negative_noop_drift_returns_failure(self):
        text = SCRIPT.read_text(encoding="utf-8")
        block = text[text.index('if [ "$target" = "$current" ]'):text.index('log "deploying $target')]
        self.assertIn('log "DRIFT $target', block)
        self.assertIn("exit 1", block)

    def test_DEP9_positive_pull_image_requires_and_runs_artifact_verifier(self):
        env = {
            **os.environ,
            "PROJECT": "sample",
            "REPO_URL": "https://example.invalid/repo.git",
            "PUBLIC_BASE_URL": "https://test.example.invalid",
            "DEPLOY_METHOD": "pull-image",
            "ARTIFACT_VERIFY_CMD": "true",
        }
        result = subprocess.run([BASH, str(SCRIPT), "--dry-run"], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        text = SCRIPT.read_text(encoding="utf-8")
        self.assertIn('docker compose -p "$PROJECT" pull', text)
        self.assertIn('eval "$ARTIFACT_VERIFY_CMD"', text)
        self.assertIn("--no-build --pull never", text)

    def test_DEP9_negative_pull_image_without_provenance_verifier_fails(self):
        env = {
            **os.environ,
            "PROJECT": "sample",
            "REPO_URL": "https://example.invalid/repo.git",
            "PUBLIC_BASE_URL": "https://test.example.invalid",
            "DEPLOY_METHOD": "pull-image",
        }
        result = subprocess.run([BASH, str(SCRIPT), "--dry-run"], env=env, capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn("ARTIFACT_VERIFY_CMD", result.stderr)

    def test_DEP3_dry_run_is_read_only_and_pin_is_production_only(self):
        with tempfile.TemporaryDirectory() as d:
            env = {
                **os.environ,
                "PROJECT": "sample",
                "REPO_URL": "https://example.invalid/repo.git",
                "PUBLIC_BASE_URL": "https://test.example.invalid",
                "BASE": str(Path(d) / "base"),
                "CHANNEL": "production",
            }
            result = subprocess.run([BASH, str(SCRIPT), "--pin", "v1.2.3", "--dry-run"],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertFalse((Path(d) / "base").exists())
            env["CHANNEL"] = "test"
            result = subprocess.run([BASH, str(SCRIPT), "--pin", "v1.2.3", "--dry-run"],
                                    env=env, capture_output=True, text=True)
            self.assertEqual(result.returncode, 2)

    def test_syntax(self):
        subprocess.run([BASH, "-n", str(SCRIPT)], check=True)


if __name__ == "__main__":
    unittest.main()
