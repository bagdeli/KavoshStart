"""Offline tests for layer M (tooling/src/main_guard.py): BR-6, BR-7, PR-7."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import main_guard as mg  # noqa: E402

REPO = "o/r"
REQ = ["kavosh / governance", "required"]


def check(name, conclusion="success", status="completed", started="2026-09-26T10:00:00Z"):
    return {"name": name, "status": status, "conclusion": conclusion, "started_at": started}


def api_for(pulls_by_sha=None, runs_by_head=None, parents_by_sha=None):
    pulls_by_sha, runs_by_head, parents_by_sha = pulls_by_sha or {}, runs_by_head or {}, parents_by_sha or {}

    def api(path):
        parts = path.split("/")
        sha = parts[4]
        if path.endswith("/pulls"):
            return pulls_by_sha.get(sha, [])
        if "/check-runs" in path:
            return {"check_runs": runs_by_head.get(sha, [])}
        return {"parents": parents_by_sha.get(sha, [{"sha": "p"}])}
    return api


def pr(num, sha, head):
    return {"number": num, "title": f"feat: pr {num}", "merged_at": "2026-09-26T10:00:00Z", "merge_commit_sha": sha,
            "head": {"sha": head}, "base": {"ref": "main"}}


def push(*commits, forced=False):
    return {"ref": "refs/heads/main", "forced": forced, "before": "b" * 40, "after": "c" * 40,
            "pusher": {"name": "bagdeli"}, "commits": [{"id": s, "message": m} for s, m in commits]}


class MainGuard(unittest.TestCase):
    def test_PR7_positive_owner_dispatch_binds_exact_current_main_sha(self):
        sha = "m1"
        def api(path):
            if path.endswith("/branches/main"):
                return {"commit": {"sha": sha}}
            return {"commit": {"message": "feat: verified"}, "parents": [{"sha": "p1"}]}
        event = mg.manual_dispatch_event(REPO, sha, "bagdeli", api)
        self.assertEqual(event["after"], sha)
        self.assertEqual(event["commits"][0]["id"], sha)
        self.assertEqual(event["pusher"]["name"], "bagdeli")

    def test_PR7_negative_owner_dispatch_rejects_stale_head(self):
        def api(path):
            return {"commit": {"sha": "current"}}
        with self.assertRaisesRegex(RuntimeError, "authorization expired"):
            mg.manual_dispatch_event(REPO, "old", "bagdeli", api)

    def test_PR7_positive_squash_merge_all_green(self):
        """Covers: BR-7, BR-6 (positive)"""
        api = api_for({"m1": [pr(5, "m1", "h1")]}, {"h1": [check("kavosh / governance"), check("required")]})
        self.assertEqual(mg.inspect(push(("m1", "feat: x")), REPO, REQ, api), [])

    def test_BR6_positive_squash_merge_uses_exact_pr_fallback_during_association_lag(self):
        """Regression: commit→pull association may lag seconds behind a completed squash merge."""
        merge = pr(79, "m1", "h1")
        calls = []
        def api(path):
            calls.append(path)
            if path.endswith("/commits/m1/pulls"):
                return []
            if path.endswith("/pulls/79"):
                return merge
            if "/commits/h1/check-runs" in path:
                return {"check_runs": [check("kavosh / governance"), check("required")]}
            return {"parents": [{"sha": "p"}]}
        event = push(("m1", "fix(governance): exact squash (#79)"))
        self.assertEqual(mg.inspect(event, REPO, REQ, api), [])
        self.assertTrue(any(path.endswith("/pulls/79") for path in calls))

    def test_BR6_negative_pr_suffix_cannot_fake_merge_provenance(self):
        fake = pr(79, "different-merge", "h1")
        def api(path):
            if path.endswith("/commits/m1/pulls"):
                return []
            if path.endswith("/pulls/79"):
                return fake
            return {"parents": [{"sha": "p"}]}
        event = push(("m1", "fix: forged-looking title (#79)"))
        self.assertIn("BR-6 direct push", mg.inspect(event, REPO, REQ, api)[0])

    def test_PR7_negative_required_check_missing(self):
        api = api_for({"m1": [pr(5, "m1", "h1")]}, {"h1": [check("kavosh / governance")]})
        v = mg.inspect(push(("m1", "feat: x")), REPO, REQ, api)
        self.assertEqual(len(v), 1)
        self.assertIn("'required' missing", v[0])

    def test_PR7_negative_no_checks_at_all(self):
        api = api_for({"m1": [pr(5, "m1", "h1")]}, {"h1": []})
        v = mg.inspect(push(("m1", "feat: x")), REPO, REQ, api)
        self.assertIn("'kavosh / governance' missing", v[0])
        self.assertIn("'required' missing", v[0])

    def test_PR7_negative_failed_pending_skipped(self):
        for runs in ([check("kavosh / governance", "failure"), check("required")],
                     [check("kavosh / governance"), check("required", None, "in_progress")],
                     [check("kavosh / governance", "skipped"), check("required")],
                     [check("kavosh / governance", "cancelled"), check("required")]):
            api = api_for({"m1": [pr(5, "m1", "h1")]}, {"h1": runs})
            self.assertEqual(len(mg.inspect(push(("m1", "feat: x")), REPO, REQ, api)), 1, runs)

    def test_PR7_positive_rerun_newest_wins(self):
        runs = [check("required", "failure", started="2026-09-26T09:00:00Z"), check("required"),
                check("kavosh / governance")]
        api = api_for({"m1": [pr(5, "m1", "h1")]}, {"h1": runs})
        self.assertEqual(mg.inspect(push(("m1", "feat: x")), REPO, REQ, api), [])

    def test_PR7_negative_queued_rerun_supersedes_old_success(self):
        runs = [check("required"), {"name": "required", "status": "queued", "conclusion": None,
                                    "started_at": None, "created_at": None}, check("kavosh / governance")]
        api = api_for({"m1": [pr(5, "m1", "h1")]}, {"h1": runs})
        self.assertIn("'required' queued", mg.inspect(push(("m1", "feat: x")), REPO, REQ, api)[0])

    def test_PR7_negative_unrelated_merged_pull_does_not_prove_provenance(self):
        unrelated = pr(5, "a-different-squash", "old-head")
        api = api_for({"m1": [unrelated]}, {"old-head": [check("kavosh / governance"), check("required")]})
        self.assertIn("BR-6 direct push", mg.inspect(push(("m1", "feat: copied")), REPO, REQ, api)[0])

    def test_PR7_negative_required_configuration_cannot_be_empty_or_weakened(self):
        violation = mg.inspect(push(("m1", "feat: x")), REPO, [], api_for())
        self.assertTrue(any("configuration error" in v for v in violation))

    def test_BR6_negative_direct_push(self):
        v = mg.inspect(push(("d1", "fix: hot")), REPO, REQ, api_for())
        self.assertIn("BR-6 direct push", v[0])

    def test_BR6_positive_initial_scaffold_root_commit(self):
        api = api_for(parents_by_sha={"s1": []})
        self.assertEqual(mg.inspect(push(("s1", "chore: scaffold from KavoshStart v1.1.0")), REPO, REQ, api), [])

    def test_BR6_negative_scaffold_message_not_root(self):
        v = mg.inspect(push(("s2", "chore: scaffold from KavoshStart v1.1.0")), REPO, REQ, api_for())
        self.assertIn("BR-6 direct push", v[0])

    def test_BR6_negative_multiple_commits_in_one_push(self):
        api = api_for({"m1": [pr(5, "m1", "h1")], "m2": [pr(6, "m2", "h2")]},
                      {"h1": [check("kavosh / governance"), check("required")], "h2": [check("kavosh / governance"), check("required")]})
        v = mg.inspect(push(("m1", "feat: a"), ("m2", "feat: b")), REPO, REQ, api)
        self.assertTrue(any("one push added 2 commits" in x for x in v))

    def test_record_uses_api_seam_without_github_cli(self):
        calls = []
        def api(path, method="GET", payload=None, allow_status=()):
            calls.append((path, method, payload))
            if "/issues?" in path:
                return []
            return {}
        event = push(("m1", "fix: hot"))
        entry = mg.record(REPO, event, ["**BR-6 direct push** test"], api=api)
        self.assertIn("BR-6 direct push", entry)
        self.assertTrue(any(path.endswith("/labels") and method == "POST" for path, method, _ in calls))
        self.assertTrue(any(path.endswith("/issues") and method == "POST" for path, method, _ in calls))

    def test_BR7_negative_force_push(self):
        v = mg.inspect(push(forced=True), REPO, REQ, api_for())
        self.assertIn("BR-7 force-push", v[0])


if __name__ == "__main__":
    unittest.main()
