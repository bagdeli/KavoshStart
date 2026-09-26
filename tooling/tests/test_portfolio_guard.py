"""Offline tests for Layer O (scripts/portfolio_guard.py): detects enforcement removed or weakened from outside."""
import base64
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import portfolio_guard as pg  # noqa: E402

REPO = "bagdeli/Demo"
PIN = "v1.1.0"
MANIFEST = {"repo": REPO, "kavoshStart": PIN, "tier": "T1", "visibility": "public",
            "ci": {"runner": "github-hosted", "monthlyMinutesBudget": 0}}
KAVOSH = f"""jobs:
  kavosh:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-governance.yml@{PIN}
    with:
      enforce: true
  main-guard:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-main-guard.yml@{PIN}
  health:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-health.yml@{PIN}
"""
CI = "jobs:\n  required:\n    runs-on: ubuntu-latest\n"
RELEASE = f"jobs:\n  release:\n    uses: bagdeli/KavoshStart/.github/workflows/kavosh-release.yml@{PIN}\n"
RECENT = (datetime.now(timezone.utc) - timedelta(days=2)).strftime("%Y-%m-%dT%H:%M:%SZ")
OLD = (datetime.now(timezone.utc) - timedelta(days=20)).strftime("%Y-%m-%dT%H:%M:%SZ")


def b64(text):
    return {"content": base64.b64encode(text.encode()).decode()}


class FakeApi:
    def __init__(self, **over):
        self.files = {"kavosh.project.json": json.dumps(MANIFEST), ".github/workflows/kavosh.yml": KAVOSH,
                      ".github/workflows/ci.yml": CI, ".github/workflows/release.yml": RELEASE}
        self.tree = list(pg.REQUIRED_FILES)
        self.settings = {"allow_squash_merge": True, "allow_merge_commit": False, "allow_rebase_merge": False,
                         "delete_branch_on_merge": True}
        self.token_perm = "read"
        self.head_checks = ["main-guard / main-guard", "required"]
        self.health = [{"number": 9, "updated_at": RECENT}]
        self.violations = []
        self.runners = [{"status": "online"}]
        self.private = False
        self.__dict__.update(over)

    def repos(self, owner):
        return [{"nameWithOwner": REPO, "isPrivate": self.private, "isArchived": False, "defaultBranchRef": {"name": "main"}}]

    def get(self, path):
        if "/contents/" in path:
            f = path.split("/contents/")[1].split("?")[0]
            return b64(self.files[f]) if self.files.get(f) is not None else None
        if "/git/trees/" in path:
            return {"tree": [{"path": p} for p in self.tree]}
        if path.endswith("/actions/permissions/workflow"):
            if self.token_perm is PermissionError:
                raise PermissionError("403")
            return {"default_workflow_permissions": self.token_perm}
        if path.endswith("/actions/runners"):
            return {"runners": self.runners}
        if "/branches/" in path:
            return {"commit": {"sha": "h" * 40}}
        if "/check-runs" in path:
            return {"check_runs": [{"name": n} for n in self.head_checks]}
        if "labels=kavosh:health" in path:
            return self.health
        if "labels=kavosh:violation" in path:
            return self.violations
        if path == f"repos/{REPO}":
            return self.settings
        raise AssertionError(path)


def rules(api):
    _, findings, _ = pg.inspect_repo(api, REPO, "main", api.private)
    return {r for r, _ in findings}


class LayerO(unittest.TestCase):
    def test_O_positive_clean_repo(self):
        """Covers: BR-5, PR-5, BR-9, AI-4, REL-6 (positive)"""
        self.assertEqual(rules(FakeApi()), set())
        text, n = pg.run(FakeApi(), "bagdeli")
        self.assertEqual(n, 0, text)

    def test_O_negative_kavosh_yml_deleted(self):
        """Covers: AI-4 (negative)"""
        api = FakeApi()
        api.files[".github/workflows/kavosh.yml"] = None
        self.assertIn("AI-4", rules(api))

    def test_O_negative_guard_ref_changed(self):
        """Covers: REL-6 (negative)"""
        for ref in ("v1", "v1.0.0", "main"):
            api = FakeApi()
            api.files[".github/workflows/kavosh.yml"] = KAVOSH.replace(f"kavosh-health.yml@{PIN}", f"kavosh-health.yml@{ref}")
            self.assertIn("REL-6", rules(api), ref)

    def test_O_negative_enforce_false(self):
        api = FakeApi()
        api.files[".github/workflows/kavosh.yml"] = KAVOSH.replace("enforce: true", "enforce: false")
        self.assertIn("AI-4", rules(api))

    def test_O_negative_hook_removed(self):
        api = FakeApi(tree=[p for p in pg.REQUIRED_FILES if p != ".githooks/pre-push"])
        self.assertIn("AI-4", rules(api))

    def test_O_negative_settings_drift(self):
        """Covers: PR-5, BR-5 (negative)"""
        api = FakeApi()
        api.settings["allow_merge_commit"] = True
        self.assertIn("PR-5/BR-5", rules(api))

    def test_O_negative_token_write(self):
        self.assertIn("SEC-3", rules(FakeApi(token_perm="write")))

    def test_O_negative_cannot_read_settings_is_a_finding(self):
        self.assertIn("O", rules(FakeApi(token_perm=PermissionError)))

    def test_O_negative_main_guard_not_running(self):
        """Covers: BR-9 (negative)"""
        self.assertIn("M", rules(FakeApi(head_checks=["required"])))

    def test_O_negative_health_stopped_or_missing(self):
        """Covers: BR-9 (negative)"""
        self.assertIn("H", rules(FakeApi(health=[{"number": 9, "updated_at": OLD}])))
        self.assertIn("H", rules(FakeApi(health=[])))

    def test_O_negative_open_violations(self):
        self.assertIn("PR-7", rules(FakeApi(violations=[{"number": 4}])))

    def test_O_positive_not_adopted_repo_is_listed_not_failed(self):
        api = FakeApi()
        api.files["kavosh.project.json"] = None
        text, n = pg.run(api, "bagdeli")
        self.assertEqual(n, 0)
        self.assertIn("not adopted", text)

    def test_CI1_negative_O_visibility_changed(self):
        self.assertIn("CI-1", rules(FakeApi(private=True)))

    def test_CI2_negative_O_no_online_runner(self):
        self.assertIn("CI-2", rules(FakeApi(private=True, runners=[{"status": "offline"}])))

    def test_SEC5_positive_public_repo_is_reported(self):
        """Covers: SEC-5 (positive)"""
        text, n = pg.run(FakeApi(private=False), "bagdeli")
        self.assertEqual(n, 0, text)
        self.assertIn(REPO, text)

    def test_SEC5_negative_private_repo_is_omitted_even_if_visible_to_token(self):
        """Covers: SEC-5 (negative)"""
        api = FakeApi(private=True)
        text, n = pg.run(api, "bagdeli")
        self.assertEqual(n, 0, text)
        self.assertNotIn(REPO, text)
        self.assertNotIn("not adopted", text)

    def test_O_reports_frozen_v1_consumers(self):
        api = FakeApi()
        api.files[".github/workflows/release.yml"] = RELEASE.replace(f"@{PIN}", "@v1")
        text, _ = pg.run(api, "bagdeli")
        self.assertIn(f"Consumers of frozen tag `v1`: {REPO}", text)


if __name__ == "__main__":
    unittest.main()
