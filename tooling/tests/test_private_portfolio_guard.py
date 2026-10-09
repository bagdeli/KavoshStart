"""Offline contract for the private portfolio supervisor reference implementation (#75)."""
import base64
import json
import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import private_portfolio_guard as ppg  # noqa: E402
import portfolio_guard as pg  # noqa: E402

REPO = "bagdeli/PrivateDemo"
LATEST = "v2.1.0"
RECENT = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")


def b64(text):
    return {"content": base64.b64encode(text.encode()).decode()}


class FakeApi:
    def __init__(self, pin=LATEST, tier="T1", acceptance=None, private=True):
        self.private = private
        self.files = {
            "kavosh.project.json": json.dumps({
                "repo": REPO, "kavoshStart": pin, "tier": tier, "visibility": "private",
                "acceptance": acceptance or {"mode": "none"},
                "ci": {"runner": "self-hosted", "monthlyMinutesBudget": 0},
            }),
            ".github/workflows/kavosh.yml": f"""jobs:
  kavosh:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-governance.yml@{pin}
    with:
      enforce: true
  main-guard:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-main-guard.yml@{pin}
  health:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-health.yml@{pin}
""",
            ".github/workflows/ci.yml": "jobs:\n  required:\n    runs-on: ubuntu-latest\n",
            ".github/workflows/release.yml": f"jobs:\n  release:\n    uses: bagdeli/KavoshStart/.github/workflows/kavosh-release.yml@{pin}\n",
            "acceptance/scope.json": json.dumps({"items": [{"id": "AC-1"}]}),
        }
        self.tree = list(pg.REQUIRED_FILES)
        self.health = [{"number": 1, "updated_at": RECENT}]
        self.head_checks = ["main-guard / main-guard", "required"]

    def get(self, path):
        if path == f"repos/{REPO}":
            return {
                "private": self.private, "archived": False, "default_branch": "main",
                "allow_squash_merge": True, "allow_merge_commit": False,
                "allow_rebase_merge": False, "delete_branch_on_merge": True,
            }
        if "/contents/" in path:
            name = path.split("/contents/")[1].split("?")[0]
            value = self.files.get(name)
            return b64(value) if value is not None else None
        if "/git/trees/" in path:
            return {"tree": [{"path": path} for path in self.tree]}
        if "/branches/" in path:
            return {"commit": {"sha": "a" * 40}}
        if "/check-runs" in path:
            return {"check_runs": [{"name": name} for name in self.head_checks]}
        if "labels=kavosh:health" in path:
            return self.health
        if "labels=kavosh:violation" in path:
            return []
        raise AssertionError(path)


class PrivatePortfolio(unittest.TestCase):
    def test_positive_clean_private_repo(self):
        text, failures, warnings = ppg.run(FakeApi(), [REPO], latest=LATEST)
        self.assertEqual((failures, warnings), (0, 0), text)
        self.assertIn(REPO, text)

    def test_freshness_lag_is_visible_but_not_silent_upgrade_failure(self):
        text, failures, warnings = ppg.run(FakeApi(pin="v2.0.6"), [REPO], latest=LATEST)
        self.assertEqual(failures, 0, text)
        self.assertEqual(warnings, 1)
        self.assertIn("consumer preflight", text)

    def test_invalid_pin_fails(self):
        _, failures, _ = ppg.run(FakeApi(pin="main"), [REPO], latest=LATEST)
        self.assertGreater(failures, 0)

    def test_t2_requires_continuous_nonempty_scope(self):
        api = FakeApi(tier="T2", acceptance={"mode": "none"})
        _, failures, _ = ppg.run(api, [REPO], latest=LATEST)
        self.assertGreater(failures, 0)
        api = FakeApi(tier="T2", acceptance={"mode": "continuous"})
        api.files["acceptance/scope.json"] = json.dumps({"items": []})
        _, failures, _ = ppg.run(api, [REPO], latest=LATEST)
        self.assertGreater(failures, 0)

    def test_non_private_target_is_rejected(self):
        _, failures, _ = ppg.run(FakeApi(private=False), [REPO], latest=LATEST)
        self.assertGreater(failures, 0)

    def test_inventory_is_private_configuration_not_repo_catalog(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "inventory.json"
            path.write_text(json.dumps({"schemaVersion": 1, "repositories": [REPO]}), encoding="utf-8")
            self.assertEqual(ppg.load_inventory(str(path)), [REPO])

    def test_cli_refuses_without_private_control_surface_guard(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "inventory.json"
            path.write_text(json.dumps({"schemaVersion": 1, "repositories": [REPO]}), encoding="utf-8")
            with mock.patch.dict(os.environ, {}, clear=True):
                self.assertEqual(ppg.main(["--inventory", str(path)]), 2)

    def test_cli_refuses_public_kavoshstart_surface(self):
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "inventory.json"
            path.write_text(json.dumps({"schemaVersion": 1, "repositories": [REPO]}), encoding="utf-8")
            env = {"KAVOSH_PRIVATE_CONTROL_SURFACE": "1", "GITHUB_REPOSITORY": ppg.HOME}
            with mock.patch.dict(os.environ, env, clear=True):
                self.assertEqual(ppg.main(["--inventory", str(path)]), 2)


if __name__ == "__main__":
    unittest.main()
