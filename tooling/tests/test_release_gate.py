"""Offline tests for REL-5 (tooling/src/release_gate.py). Rule ids in test names feed the contract test (#7)."""
import base64
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import release_gate as rg  # noqa: E402

REQ = ["required", "main-guard / main-guard"]
SHA = "a" * 40


def run(name, status="completed", conclusion="success", started="2026-09-26T10:00:00Z"):
    return {"name": name, "status": status, "conclusion": conclusion, "started_at": started}


def fake_api(runs_seq, head=SHA):
    """runs_seq: list of check-run lists returned on successive polls."""
    state = {"i": 0}

    def api(path):
        if "/branches/" in path:
            return {"commit": {"sha": head}}
        runs = runs_seq[min(state["i"], len(runs_seq) - 1)]
        state["i"] += 1
        return {"check_runs": runs}
    return api


def acceptance_api(issue_body=None, issue_state="closed", run_conclusion="success", compare_status="ahead",
                   defer=False, defer_approved=True):
    manifest = {"acceptance": {"mode": "continuous"}}
    item = {"id": "AC-001", "issue": 12, "owner": "bagdeli", "risk": "high", "evidence": ["ci", "test"]}
    if defer:
        item.update({"deferredTo": "v0.2.0", "deferIssue": 13})
    scope = {"schemaVersion": 1, "targetRelease": "v0.1.0", "items": [item]}
    good = (
        f"Acceptance-Merged-SHA: {'b' * 40}\n"
        "Acceptance-Evidence-Run: https://github.com/o/r/actions/runs/99\n"
        "Acceptance-Test-Evidence: https://test.example/evidence/1\n"
        "Accepted-By: @bagdeli\n"
    )
    body = good if issue_body is None else issue_body

    def enc(obj):
        return {"content": base64.b64encode(json.dumps(obj).encode()).decode()}

    def api(path):
        if "contents/kavosh.project.json" in path:
            return enc(manifest)
        if "contents/acceptance/scope.json" in path:
            return enc(scope)
        if "/issues/13" in path:
            return {"state": "closed", "body": "Defer-Approved-By: @bagdeli\n" if defer_approved else ""}
        if "/issues/12" in path:
            return {"state": issue_state, "body": body}
        if "/compare/" in path:
            return {"status": compare_status}
        if "/actions/runs/99" in path:
            return {"status": "completed", "conclusion": run_conclusion}
        raise AssertionError(path)
    return api


class AcceptanceReleaseGate(unittest.TestCase):
    def test_ACC3_positive_closed_item_with_exact_provenance(self):
        self.assertEqual(rg.acceptance_reasons("o/r", SHA, api=acceptance_api()), [])

    def test_ACC3_positive_owner_approved_future_defer(self):
        self.assertEqual(rg.acceptance_reasons("o/r", SHA, api=acceptance_api(defer=True)), [])

    def test_ACC3_positive_legacy_profile_is_backward_compatible(self):
        def api(path):
            if "contents/kavosh.project.json" in path:
                payload = base64.b64encode(json.dumps({"tier": "T2"}).encode()).decode()
                return {"content": payload}
            raise AssertionError(path)
        self.assertEqual(rg.acceptance_reasons("o/r", SHA, api=api), [])

    def test_ACC3_negative_issue_only_stale_failed_or_unapproved_evidence(self):
        issue_only = "Accepted-By: @bagdeli\nAcceptance-Merged-SHA: " + "b" * 40 + "\n"
        cases = [
            acceptance_api(issue_body=issue_only),
            acceptance_api(compare_status="diverged"),
            acceptance_api(run_conclusion="failure"),
            acceptance_api(issue_state="open"),
            acceptance_api(defer=True, defer_approved=False),
        ]
        for api in cases:
            with self.subTest(api=api):
                self.assertTrue(rg.acceptance_reasons("o/r", SHA, api=api))


class ReleasePrBridge(unittest.TestCase):
    def trusted_pr(self):
        return {
            "number": 111,
            "base": {"ref": "main"},
            "head": {
                "ref": "release-please--branches--main--components--KavoshStart",
                "sha": "b" * 40,
                "repo": {"full_name": "o/r"},
            },
            "user": {"login": "github-actions[bot]"},
        }

    def test_REL5_positive_dispatches_and_publishes_ruleset_checks(self):
        pr = self.trusted_pr()
        calls = []
        run_state = {
            ".github/workflows/ci.yml": [
                {"id": 10, "head_sha": pr["head"]["sha"], "status": "completed",
                 "conclusion": "success", "html_url": "https://example/ci", "created_at": "2026-10-10T00:00:00Z"}
            ],
            ".github/workflows/kavosh.yml": [
                {"id": 20, "head_sha": pr["head"]["sha"], "status": "completed",
                 "conclusion": "success", "html_url": "https://example/kavosh", "created_at": "2026-10-10T00:00:01Z"}
            ],
        }
        dispatch_count = {".github/workflows/ci.yml": 0, ".github/workflows/kavosh.yml": 0}

        def api(path, method="GET", payload=None):
            calls.append((path, method, payload))
            if "/pulls?" in path:
                return [pr]
            if "/actions/workflows/" in path and path.endswith("/dispatches"):
                workflow = (
                    ".github/workflows/ci.yml"
                    if "%2Fci.yml" in path
                    else ".github/workflows/kavosh.yml"
                )
                dispatch_count[workflow] += 1
                return {}
            if "/actions/workflows/" in path and "/runs?" in path:
                workflow = (
                    ".github/workflows/ci.yml"
                    if "%2Fci.yml" in path
                    else ".github/workflows/kavosh.yml"
                )
                if dispatch_count[workflow] == 0:
                    return {"workflow_runs": []}
                return {"workflow_runs": run_state[workflow]}
            if path.endswith("/check-runs") and method == "POST":
                return {"id": 100}
            raise AssertionError((path, method, payload))

        result = rg.verify_release_pr(
            "o/r", "main", ".github/workflows/ci.yml", ".github/workflows/kavosh.yml",
            wait=1, interval=0, api=api, sleep=lambda _: None,
        )
        self.assertTrue(result["ok"])
        published = [payload for path, method, payload in calls
                     if path.endswith("/check-runs") and method == "POST"]
        self.assertEqual([p["name"] for p in published], ["required", "kavosh / governance"])
        self.assertTrue(all(p["head_sha"] == pr["head"]["sha"] for p in published))
        self.assertTrue(all(p["conclusion"] == "success" for p in published))

    def test_REL5_negative_untrusted_release_like_pr_is_ignored(self):
        pr = self.trusted_pr()
        pr["user"] = {"login": "someone"}
        def api(path, method="GET", payload=None):
            if "/pulls?" in path:
                return [pr]
            raise AssertionError(path)
        self.assertIsNone(rg.verify_release_pr(
            "o/r", "main", ".github/workflows/ci.yml", ".github/workflows/kavosh.yml",
            api=api,
        ))

    def test_REL5_negative_failed_dispatched_check_publishes_failure(self):
        pr = self.trusted_pr()
        calls = []
        dispatched = {"ci": False, "k": False}
        def api(path, method="GET", payload=None):
            calls.append((path, method, payload))
            if "/pulls?" in path:
                return [pr]
            if path.endswith("/dispatches"):
                if "%2Fci.yml" in path:
                    dispatched["ci"] = True
                else:
                    dispatched["k"] = True
                return {}
            if "/runs?" in path:
                is_ci = "%2Fci.yml" in path
                ready = dispatched["ci"] if is_ci else dispatched["k"]
                if not ready:
                    return {"workflow_runs": []}
                return {"workflow_runs": [{
                    "id": 10 if is_ci else 20,
                    "head_sha": pr["head"]["sha"],
                    "status": "completed",
                    "conclusion": "failure" if is_ci else "success",
                    "html_url": "https://example/run",
                    "created_at": "2026-10-10T00:00:00Z",
                }]}
            if path.endswith("/check-runs") and method == "POST":
                return {}
            raise AssertionError(path)
        result = rg.verify_release_pr(
            "o/r", "main", ".github/workflows/ci.yml", ".github/workflows/kavosh.yml",
            wait=1, interval=0, api=api, sleep=lambda _: None,
        )
        self.assertFalse(result["ok"])
        published = [payload for path, method, payload in calls
                     if path.endswith("/check-runs") and method == "POST"]
        self.assertEqual(published[0]["conclusion"], "failure")
        self.assertEqual(published[1]["conclusion"], "success")


class ReleaseGate(unittest.TestCase):
    def gate(self, runs_seq, head=SHA, wait=0, api=None):
        return rg.gate("o/r", SHA, REQ, api=api or fake_api(runs_seq, head), wait=wait, interval=0, sleep=lambda s: None)

    def test_REL5_positive_all_required_green(self):
        ok, _ = self.gate([[run("required"), run("main-guard / main-guard"), run("other", conclusion="failure")]])
        self.assertTrue(ok)

    def test_REL5_negative_missing_check(self):
        ok, reasons = self.gate([[run("required")]])
        self.assertFalse(ok)
        self.assertIn("missing required check 'main-guard / main-guard'", reasons)

    def test_REL5_negative_no_checks_at_all(self):
        ok, reasons = self.gate([[]])
        self.assertFalse(ok)
        self.assertEqual(len(reasons), 2)

    def test_REL5_negative_failed_cancelled_skipped(self):
        for conclusion in ("failure", "cancelled", "skipped", "startup_failure", "timed_out", None):
            ok, _ = self.gate([[run("required", conclusion=conclusion), run("main-guard / main-guard")]])
            self.assertFalse(ok, conclusion)

    def test_REL5_negative_pending_after_wait(self):
        ok, reasons = self.gate([[run("required", status="in_progress", conclusion=None), run("main-guard / main-guard")]])
        self.assertFalse(ok)
        self.assertTrue(any("still in_progress" in r for r in reasons))

    def test_REL5_positive_pending_then_green(self):
        seq = [[run("required", status="queued", conclusion=None), run("main-guard / main-guard")],
               [run("required"), run("main-guard / main-guard")]]
        ok, _ = self.gate(seq, wait=60)
        self.assertTrue(ok)

    def test_REL5_positive_rerun_newest_wins(self):
        runs = [run("required", conclusion="failure", started="2026-09-26T09:00:00Z"),
                run("required", conclusion="success", started="2026-09-26T10:00:00Z"),
                run("main-guard / main-guard")]
        ok, _ = self.gate([runs])
        self.assertTrue(ok)

    def test_REL5_negative_queued_rerun_supersedes_old_success(self):
        runs = [run("required"), {"name": "required", "status": "queued", "conclusion": None,
                                  "started_at": None, "created_at": None}, run("main-guard / main-guard")]
        ok, reasons = self.gate([runs])
        self.assertFalse(ok)
        self.assertIn("still queued", " ".join(reasons))

    def test_REL5_negative_main_changes_during_check_wait(self):
        state = {"head_reads": 0, "run_reads": 0}

        def moving_api(path):
            if "/branches/" in path:
                state["head_reads"] += 1
                return {"commit": {"sha": SHA if state["head_reads"] == 1 else "b" * 40}}
            state["run_reads"] += 1
            return {"check_runs": [run("required", status="in_progress", conclusion=None), run("main-guard / main-guard")]
                    if state["run_reads"] == 1 else [run("required"), run("main-guard / main-guard")]}

        ok, reasons = self.gate([], wait=60, api=moving_api)
        self.assertIsNone(ok)
        self.assertIn("stopped being the current head", reasons[0])

    def test_REL5_negative_not_head_of_main(self):
        ok, reasons = self.gate([[run("required"), run("main-guard / main-guard")]], head="b" * 40)
        self.assertIsNone(ok)  # superseded by a newer main head: no release from this commit, no red job
        self.assertIn("not the current head", reasons[0])

    def test_REL5_negative_api_unavailable(self):
        def broken(path):
            raise RuntimeError("HTTP 403")
        rg.gh_api, original = broken, rg.gh_api
        try:
            self.assertEqual(rg.main(["--repo", "o/r", "--sha", SHA, "--wait", "0"]), 1)
        finally:
            rg.gh_api = original


if __name__ == "__main__":
    unittest.main()
