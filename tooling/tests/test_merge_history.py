"""PR-7 regression: historical evidence must be valid at the merge boundary."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import main_guard as mg

CUT = "2026-01-10T10:00:00Z"
BEFORE = "2026-01-10T09:00:00Z"
AFTER = "2026-01-10T11:00:00Z"


def check(name="required", created=BEFORE, started=BEFORE, ended=BEFORE,
          status="completed", conclusion="success", ident=1):
    return {"id": ident, "name": name, "created_at": created, "started_at": started,
            "completed_at": ended, "status": status, "conclusion": conclusion}


class MergeHistory(unittest.TestCase):
    def problems(self, *runs):
        return mg.check_state_at_merge(runs, ["required"], CUT)

    def test_PR7_positive_green_before_merge(self):
        self.assertEqual(self.problems(check()), [])

    def test_PR7_negative_green_only_after_merge(self):
        self.assertIn("pending at merge", self.problems(check(ended=AFTER))[0])

    def test_PR7_positive_post_merge_rerun_does_not_rewrite_history(self):
        for status, conclusion in [("queued", None), ("completed", "failure")]:
            later = check(created=AFTER, started=AFTER, ended=AFTER,
                          status=status, conclusion=conclusion, ident=2)
            self.assertEqual(self.problems(check(), later), [])

    def test_PR7_negative_no_old_evidence_then_later_green(self):
        self.assertIn("missing at merge", self.problems(
            check(created=AFTER, started=AFTER, ended=AFTER))[0])

    def test_PR7_negative_pre_merge_queued_rerun_cannot_inherit_green(self):
        later = check(created="2026-01-10T09:59:50Z", started=AFTER,
                      ended=AFTER, ident=2)
        self.assertIn("pending at merge", self.problems(check(), later)[0])

    def test_PR7_negative_unknown_completion_is_not_green(self):
        self.assertIn("completion time unavailable", self.problems(check(ended=None))[0])

    def test_PR7_negative_unknown_origin_after_merge_is_unverifiable(self):
        self.assertIn("origin unavailable", self.problems(check(), check(
            created=None, started=AFTER, ended=AFTER, ident=2))[0])

    def test_PR7_negative_naive_or_invalid_merge_time(self):
        for timestamp in (None, "bad", "2026-01-10T10:00:00"):
            self.assertIn("merge timestamp unavailable", mg.check_state_at_merge(
                [check()], ["required"], timestamp)[0])

    def test_PR7_positive_timezone_offsets_compare_as_instants(self):
        run = check(created="2026-01-10T12:30:00+03:30",
                    started="2026-01-10T12:30:00+03:30",
                    ended="2026-01-10T12:45:00+03:30")
        self.assertEqual(self.problems(run), [])

    def test_PR7_negative_newer_failure_wins_not_slow_old_completion(self):
        old = check(ended="2026-01-10T09:59:00Z")
        newer = check(created="2026-01-10T09:30:00Z", started="2026-01-10T09:30:00Z",
                      ended="2026-01-10T09:31:00Z", conclusion="failure", ident=2)
        self.assertIn("failure at merge", self.problems(old, newer)[0])
        self.assertEqual(self.problems(old, newer), self.problems(newer, old))

    def test_PR7_negative_inconsistent_timestamps(self):
        self.assertIn("inconsistent", self.problems(check(created=CUT))[0])

    def test_PR7_positive_all_check_pages_are_requested(self):
        calls = []
        def api(path):
            calls.append(path)
            if path.endswith("&page=1"):
                return {"check_runs": [check(name="unrelated")] * 100}
            return {"check_runs": [check()]}
        runs = mg.historical_check_runs("o/r", "h1", ["required"], api)
        self.assertEqual(len(runs), 1)
        self.assertEqual(len(calls), 2)
        self.assertTrue(all("filter=all" in path for path in calls))

    def test_PR7_negative_actions_run_queued_before_job_creation(self):
        run = check(created=None, started=AFTER, ended=AFTER)
        run.update(app={"slug": "github-actions"},
                   html_url="https://github.com/o/r/actions/runs/10/job/20")
        def api(path):
            if "/check-runs?" in path:
                return {"check_runs": [run]}
            if path.endswith("/actions/jobs/20"):
                return {"id": 20, "run_id": 10, "run_attempt": 1, "head_sha": "h1",
                        "name": "required", "created_at": AFTER}
            return {"id": 10, "head_sha": "h1", "run_attempt": 1, "created_at": BEFORE}
        rows = mg.historical_check_runs("o/r", "h1", ["required"], api)
        self.assertIn("pending at merge", self.problems(*rows)[0])

    def test_PR7_negative_actions_head_mismatch_fails_closed(self):
        run = check()
        run.update(app={"slug": "github-actions"},
                   html_url="https://github.com/o/r/actions/runs/10/job/20")
        def api(path):
            return {"check_runs": [run]} if "/check-runs?" in path else {}
        with self.assertRaisesRegex(RuntimeError, "identity mismatch"):
            mg.historical_check_runs("o/r", "h1", ["required"], api)


if __name__ == "__main__":
    unittest.main()
