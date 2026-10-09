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
        self.head_checks = ["main-guard / main-guard", "required"]
        self.health = [{"number": 9, "updated_at": RECENT, "state": "closed"}]
        self.violations = []
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
        if "/branches/" in path:
            return {"commit": {"sha": "h" * 40}}
        if "/check-runs" in path:
            return {"check_runs": [{"name": n} for n in self.head_checks]}
        if "labels=kavosh:health" in path:
            return self.health
        if "labels=kavosh:violation" in path:
            return self.violations
        if path == f"repos/{REPO}":
            return dict(self.settings, private=self.private, archived=False, default_branch="main")
        raise AssertionError(path)


def rules(api):
    _, findings, _ = pg.inspect_repo(api, REPO, "main", api.private)
    return {r for r, _ in findings}


def portfolio(api):
    return pg.run(api, "bagdeli", inventory=[REPO])


class MutationApi:
    def __init__(self, found=None):
        self.found = found or []
        self.calls = []

    def get(self, path):
        self.calls.append(("GET", path, None))
        if "/issues?" in path:
            return list(self.found)
        return None

    def request(self, path, method="GET", payload=None, allow_status=()):
        self.calls.append((method, path, payload))
        return None


class LayerO(unittest.TestCase):
    def test_O_positive_clean_repo(self):
        """Covers: BR-5, PR-5, BR-9, AI-4, REL-6 (positive)"""
        self.assertEqual(rules(FakeApi()), set())
        text, n = portfolio(FakeApi())
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

    def test_O_positive_inspection_needs_no_administration_permission(self):
        self.assertEqual(rules(FakeApi()), set())

    def test_O_negative_main_guard_not_running(self):
        """Covers: BR-9 (negative)"""
        self.assertIn("M", rules(FakeApi(head_checks=["required"])))

    def test_O_negative_health_stopped_or_missing(self):
        """Covers: BR-9 (negative)"""
        self.assertIn("H", rules(FakeApi(health=[{"number": 9, "updated_at": OLD}])))
        self.assertIn("H", rules(FakeApi(health=[])))

    def test_O_negative_open_violations(self):
        self.assertIn("PR-7", rules(FakeApi(violations=[{"number": 4}])))

    def test_O_negative_registered_adoption_manifest_removed(self):
        api = FakeApi()
        api.files["kavosh.project.json"] = None
        text, n = portfolio(api)
        self.assertEqual(n, 1)
        self.assertIn("manifest missing", text)
        self.assertIn("no kavosh.project.json", text)

    def test_CI1_negative_O_visibility_changed(self):
        self.assertIn("CI-1", rules(FakeApi(private=True)))

    def test_CI2_positive_portfolio_does_not_require_runner_admin_endpoint(self):
        api = FakeApi()
        text, n = portfolio(api)
        self.assertEqual(n, 0, text)

    def test_SEC5_positive_public_repo_is_reported(self):
        """Covers: SEC-5 (positive)"""
        text, n = portfolio(FakeApi(private=False))
        self.assertEqual(n, 0, text)
        self.assertIn(REPO, text)

    def test_SEC5_negative_private_repo_is_omitted_even_if_visible_to_token(self):
        """Covers: SEC-5 (negative)"""
        api = FakeApi(private=True)
        text, n = portfolio(api)
        self.assertEqual(n, 0, text)
        self.assertNotIn(REPO, text)
        self.assertNotIn("not adopted", text)

    def test_SEC5_negative_stale_public_enumeration_never_inspects_now_private_repo(self):
        api = FakeApi()
        original_get = api.get
        file_reads = []

        def visibility_changes(path):
            if "/contents/" in path:
                file_reads.append(path)
            if path == f"repos/{REPO}":
                return dict(original_get(path), private=True)
            return original_get(path)

        api.get = visibility_changes
        text, n = portfolio(api)
        self.assertEqual(n, 0, text)
        self.assertNotIn(REPO, text)
        self.assertEqual(file_reads, [])

    def test_SEC5_negative_repo_becomes_private_before_publication(self):
        api = FakeApi()
        original_get = api.get
        metadata_reads = {"count": 0}

        def becomes_private(path):
            data = original_get(path)
            if path == f"repos/{REPO}":
                metadata_reads["count"] += 1
                if metadata_reads["count"] >= 3:
                    return dict(data, private=True)
            return data

        api.get = becomes_private
        text, n = portfolio(api)
        self.assertEqual(n, 0, text)
        self.assertNotIn(REPO, text)

    def test_O_positive_green_report_closes_existing_portfolio_issue(self):
        api = MutationApi(found=[{"number": 7, "body": "old"}])
        pg.update_issue("green", 0, api)
        self.assertTrue(any(method == "PATCH" and path.endswith("/issues/7") and payload.get("state") == "closed"
                            for method, path, payload in api.calls if payload))
        self.assertTrue(any(method == "POST" and path.endswith("/issues/7/comments")
                            for method, path, _ in api.calls))

    def test_O_negative_findings_create_portfolio_issue_when_missing(self):
        api = MutationApi()
        pg.update_issue("report body", 2, api)
        created = [(method, path, payload) for method, path, payload in api.calls
                   if method == "POST" and path.endswith("/issues") and payload and payload.get("title")]
        self.assertEqual(len(created), 1)
        self.assertEqual(created[0][2]["labels"], ["kavosh:portfolio"])

    def test_O_runtime_has_no_direct_github_cli_dependency(self):
        script = (ROOT / "scripts" / "portfolio_guard.py").read_text(encoding="utf-8")
        template = (ROOT / "tooling" / "templates" / "kavosh-portfolio.yml").read_text(encoding="utf-8")
        self.assertNotIn('subprocess.run(["gh"', script)
        self.assertNotIn("gh issue ", template)
        self.assertNotIn("gh label ", template)

    def test_O_reports_frozen_v1_consumers(self):
        api = FakeApi()
        api.files[".github/workflows/release.yml"] = RELEASE.replace(f"@{PIN}", "@v1")
        text, _ = portfolio(api)
        self.assertIn(f"Consumers of frozen tag `v1`: {REPO}", text)


if __name__ == "__main__":
    unittest.main()
