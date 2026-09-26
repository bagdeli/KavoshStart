"""Offline tests for REL-5 (tooling/src/release_gate.py). Rule ids in test names feed the contract test (#7)."""
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


class ReleaseGate(unittest.TestCase):
    def gate(self, runs_seq, head=SHA, wait=0):
        return rg.gate("o/r", SHA, REQ, api=fake_api(runs_seq, head), wait=wait, interval=0, sleep=lambda s: None)

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
