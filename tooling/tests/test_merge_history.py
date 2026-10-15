"""PR-7 regression: historical evidence must be valid at the merge boundary."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import main_guard as mg
import release_gate as rg

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


class SupersededMalformedHistory(unittest.TestCase):
    """Do not waive skipped results; require provable supersession and source."""

    def row(self, created="2026-01-10T09:30:00Z", **overrides):
        row = check(created=created, started=created, ended=created)
        row.update(app={"id": 15368, "slug": "github-actions"}, head_sha="a" * 40,
                   html_url="https://github.com/o/r/actions/runs/10/job/20",
                   _history_workflow_id=1234)
        row.update(overrides)
        return row

    def old_bad(self, **overrides):
        return self.row(created=BEFORE, completed_at="2026-01-10T08:59:59Z",
                        conclusion="skipped", **overrides)

    def problems(self, *rows):
        return mg.check_state_at_merge(rows, ["required"], CUT)

    def test_older_malformed_is_superseded_independent_of_input_order_or_conclusion(self):
        # It is chronological/source supersession, never a blanket skipped waiver.
        for conclusion in ("skipped", "success", "failure", "cancelled"):
            bad = self.old_bad()
            bad["conclusion"] = conclusion
            for rows in ((bad, self.row()), (self.row(), bad)):
                with self.subTest(conclusion=conclusion, order=rows[0]["created_at"]):
                    self.assertEqual(self.problems(*rows), [])

    def test_newer_valid_failure_remains_red(self):
        self.assertIn("failure at merge", self.problems(
            self.old_bad(), self.row(conclusion="failure"))[0])

    def test_effective_malformed_tied_origin_and_older_success_remain_red(self):
        for bad_origin in ("2026-01-10T09:30:00Z", "2026-01-10T09:45:00Z"):
            bad = self.row(created=bad_origin, completed_at=BEFORE, conclusion="skipped")
            self.assertIn("inconsistent", self.problems(self.row(), bad)[0])
        self.assertIn("inconsistent", self.problems(self.old_bad())[0])

    def test_unknown_origin_never_inherits_later_green_even_with_premerge_start(self):
        for created in (None, "bad", "2026-01-10T09:00:00"):
            bad = self.old_bad(created_at=created)
            self.assertIn("inconsistent", self.problems(bad, self.row())[0])

    def test_valid_start_fallback_preserves_release_mirror_history(self):
        # Generic release-publisher check shape: valid start/end, no creation
        # time or Actions-job URL. This original fallback is not supersession.
        mirror = self.row(created_at=None,
                          html_url="https://github.com/o/r/runs/100",
                          _history_workflow_id=None)
        self.assertEqual(self.problems(mirror), [])
        ordinary = self.row(created=BEFORE)
        for rows in ((ordinary, mirror), (mirror, ordinary)):
            self.assertEqual(self.problems(*rows), [])

    def test_start_fallback_cannot_supersede_malformed_history(self):
        later = self.row(created_at=None)
        for rows in ((self.old_bad(), later), (later, self.old_bad())):
            self.assertIn("inconsistent", self.problems(*rows)[0])

    def test_start_fallback_does_not_waive_bad_or_postmerge_results(self):
        for fields, problem in (
            ({"conclusion": "failure"}, "failure at merge"),
            ({"status": "queued", "completed_at": None}, "pending at merge"),
            ({"completed_at": AFTER}, "pending at merge"),
            ({"started_at": AFTER, "completed_at": AFTER}, "origin unavailable"),
            ({"started_at": None, "completed_at": None}, "origin unavailable"),
        ):
            with self.subTest(fields=fields):
                self.assertIn(problem, self.problems(self.row(created_at=None, **fields))[0])

    def test_release_publisher_result_is_readable_by_historical_consumer(self):
        # Exercise the maintained publisher, then the reader against the minimal
        # REST shape: server start/end and /runs URL, with no created_at field.
        for conclusion in ("success", "failure"):
            with self.subTest(conclusion=conclusion):
                checks = []

                def api(path, method="GET", payload=None):
                    if path == "repos/o/r/check-runs" and method == "POST":
                        response = dict(payload)
                        response.update(id=100, started_at=BEFORE, completed_at=BEFORE,
                                        html_url="https://github.com/o/r/runs/100",
                                        app={"id": 15368, "slug": "github-actions"})
                        checks.append(response)
                        return response
                    if path == "repos/o/r/statuses/" + "a" * 40 and method == "POST":
                        return payload
                    if "/check-runs?" in path and method == "GET":
                        return {"check_runs": checks}
                    raise AssertionError("unexpected API call: " + path)

                workflow_run = {"id": 10, "status": "completed", "conclusion": conclusion,
                                "html_url": "https://github.com/o/r/actions/runs/10"}
                self.assertEqual(rg._publish_check("o/r", "a" * 40, "required", workflow_run, api),
                                 conclusion == "success")
                rows = mg.historical_check_runs("o/r", "a" * 40, ["required"], api)
                self.assertNotIn("created_at", rows[0])
                problems = self.problems(*rows)
                if conclusion == "success":
                    self.assertEqual(problems, [])
                else:
                    self.assertIn("failure at merge", problems[0])

    def test_unproven_or_different_source_cannot_supersede(self):
        for fields in (
            {"app": {}}, {"app": {"id": 999, "slug": "github-actions"}},
            {"app": {"id": True, "slug": "github-actions"}},
            {"app": {"id": 15368, "slug": "other"}},
            {"head_sha": "b" * 40}, {"head_sha": None},
            {"html_url": "https://github.com/foreign/r/actions/runs/10/job/20"},
            {"html_url": None}, {"_history_workflow_id": None},
            {"_history_workflow_id": 999}, {"_history_workflow_id": True},
        ):
            with self.subTest(fields=fields):
                self.assertIn("inconsistent", self.problems(
                    self.old_bad(**fields), self.row())[0])

    def test_newer_pending_or_postmerge_success_cannot_authorize_merge(self):
        for fields in (
            {"status": "queued", "conclusion": None, "completed_at": None},
            {"status": "in_progress", "conclusion": None, "completed_at": None},
            {"completed_at": AFTER},
        ):
            with self.subTest(fields=fields):
                self.assertTrue(self.problems(self.old_bad(), self.row(**fields)))
                self.assertIn("pending at merge", self.problems(
                    self.row(created=BEFORE), self.row(**fields))[0])

    def test_missing_completion_requires_same_strict_supersession(self):
        old = self.row(created=BEFORE, completed_at=None)
        self.assertEqual(self.problems(old, self.row()), [])
        self.assertIn("completion time unavailable", self.problems(
            self.row(), self.row(created="2026-01-10T09:45:00Z", completed_at=None))[0])

    def test_postmerge_attempt_cannot_supersede_older_malformed_evidence(self):
        after = self.row(created=AFTER)
        self.assertIn("inconsistent", self.problems(self.old_bad(), after)[0])

    def test_other_check_name_never_supersedes(self):
        self.assertIn("inconsistent", self.problems(
            self.old_bad(), self.row(name="unrelated"))[0])



if __name__ == "__main__":
    unittest.main()
