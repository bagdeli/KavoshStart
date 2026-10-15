"""Source-bound UI evidence; mocked API, no human approval fabricated."""
import sys
import unittest
from copy import deepcopy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import governance as g

SHA = "a" * 40
REPO = "owner/product"
RUN = "https://github.com/owner/product/actions/runs/42"

def pr():
    return {"number": 1, "head": {"sha": SHA}, "user": {"login": "author", "type": "User"}}

def approved():
    return {"id": 99, "state": "APPROVED", "commit_id": SHA,
            "submitted_at": "2026-10-15T12:30:00Z", "user": {"login": "reviewer", "type": "User"}}

def api(reviews=None, run=None, jobs=None):
    responses = {
        f"repos/{REPO}/pulls/1/reviews?per_page=100": [] if reviews is None else reviews,
        f"repos/{REPO}/actions/runs/42": run if run is not None else {
            "id": 42, "head_sha": SHA, "status": "completed", "conclusion": "success",
            "head_repository": {"full_name": REPO}, "event": "pull_request", "run_attempt": 1},
        f"repos/{REPO}/actions/runs/42/attempts/1/jobs?per_page=100": jobs if jobs is not None else
          {"jobs": [{"conclusion": "success", "steps": [
              {"name": "Visual regression", "status": "completed", "conclusion": "success",
               "started_at": "2026-10-15T12:28:00Z", "completed_at": "2026-10-15T12:29:00Z"}]}]},
    }
    def get(op, key):
        assert op == "api", op
        return deepcopy(responses[key])
    return get

class VerifiedVisual(unittest.TestCase):
    def decide(self, evidence=None, **kw):
        return g.verified_visual_review(REPO, pr(), evidence if evidence is not None else f"UI evidence: {RUN}", api(**kw))[0]

    def test_real_visual_step_succeeds(self):
        self.assertEqual(self.decide(), "ok")

    def test_human_review_on_exact_head_succeeds_without_run(self):
        self.assertEqual(self.decide("no link", reviews=[approved()]), "ok")

    def test_url_or_marker_alone_does_not_pass(self):
        for evidence in ("UI evidence: image.png", "UI evidence: https://example.com/x.png",
                         "UI evidence: https://github.com/other/repo/actions/runs/42", "no link"):
            with self.subTest(evidence=evidence):
                self.assertEqual(self.decide(evidence), "fail")

    def test_stale_failed_or_wrong_run_rejected(self):
        for patch in ({"head_sha": "b" * 40}, {"conclusion": "failure"},
                      {"status": "in_progress"}, {"run_attempt": 0},
                      {"head_repository": {"full_name": "other/repo"}},
                      {"event": "other"}, {"id": 100}):
            run = {"id": 42, "head_sha": SHA, "status": "completed", "conclusion": "success",
                   "head_repository": {"full_name": REPO}, "event": "pull_request", "run_attempt": 1}
            run.update(patch)
            with self.subTest(patch=patch):
                self.assertEqual(self.decide(run=run), "fail")

    def test_skipped_impact_or_no_real_visual_step_rejected(self):
        for step in (
            {"name": "Resolve browser test impact", "status": "completed", "conclusion": "success",
             "started_at": "a", "completed_at": "b"},
            {"name": "Visual regression", "status": "completed", "conclusion": "skipped",
             "started_at": "a", "completed_at": "b"},
            {"name": "Visual regression", "status": "completed", "conclusion": "success"},
        ):
            self.assertEqual(self.decide(jobs={"jobs": [{"conclusion": "success", "steps": [step]}]}), "fail")

    def test_stale_bot_self_or_changed_review_rejected(self):
        for patch in ({"commit_id": "b" * 40}, {"state": "COMMENTED"}, {"submitted_at": None},
                      {"user": {"login": "agent[bot]", "type": "Bot"}},
                      {"user": {"login": "author", "type": "User"}}):
            review = approved()
            review.update(patch)
            self.assertEqual(self.decide("no link", reviews=[review]), "fail")
        old = approved()
        new = dict(old, id=101, state="CHANGES_REQUESTED", submitted_at="2026-10-15T13:00:00Z")
        self.assertEqual(self.decide("no link", reviews=[old, new]), "fail")

    def test_missing_exact_sha_is_not_proof(self):
        p = pr()
        p["head"]["sha"] = None
        self.assertEqual(g.verified_visual_review(REPO, p, f"UI evidence: {RUN}", api())[0], "fail")
