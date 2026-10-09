"""Offline tests for REL-7 release-candidate gating."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import rc_gate as rc  # noqa: E402

SHA = "a" * 40
REQ = ["required", "main-guard / main-guard"]


def check(name, status="completed", conclusion="success", stamp="2026-10-09T00:00:00Z"):
    return {"name": name, "status": status, "conclusion": conclusion, "started_at": stamp}


class ReleaseCandidateGate(unittest.TestCase):
    def test_REL7_positive_next_rc_from_exact_green_main(self):
        reasons = rc.candidate_reasons(
            "v1.6.0-rc.2", SHA, REQ, SHA,
            [check("required"), check("main-guard / main-guard")],
            ["v1.5.0", "v1.6.0-rc.1"],
        )
        self.assertEqual(reasons, [])

    def test_REL7_negative_rejects_invalid_stale_red_or_colliding_candidates(self):
        scenarios = [
            ("v1.6.0", SHA, SHA, [check("required"), check("main-guard / main-guard")], ["v1.5.0"]),
            ("v1.6.0-rc.1", SHA, "b" * 40, [check("required"), check("main-guard / main-guard")], ["v1.5.0"]),
            ("v1.6.0-rc.1", SHA, SHA, [check("required", conclusion="failure"), check("main-guard / main-guard")], ["v1.5.0"]),
            ("v1.5.0-rc.2", SHA, SHA, [check("required"), check("main-guard / main-guard")], ["v1.5.0"]),
            ("v1.6.0-rc.1", SHA, SHA, [check("required"), check("main-guard / main-guard")], ["v1.5.0", "v1.6.0-rc.1"]),
        ]
        for tag, sha, head, runs, tags in scenarios:
            with self.subTest(tag=tag, head=head, tags=tags):
                self.assertTrue(rc.candidate_reasons(tag, sha, REQ, head, runs, tags))

    def test_rc_sequence_must_increase(self):
        reasons = rc.candidate_reasons(
            "v2.0.0-rc.2", SHA, REQ, SHA,
            [check("required"), check("main-guard / main-guard")],
            ["v1.9.0", "v2.0.0-rc.3"],
        )
        self.assertIn("RC number must be greater than every existing RC for this version", reasons)

    def test_required_check_floor_cannot_be_removed(self):
        reasons = rc.candidate_reasons(
            "v1.6.0-rc.1", SHA, ["required"], SHA,
            [check("required")], ["v1.5.0"],
        )
        self.assertTrue(any("required checks must include" in r for r in reasons))


if __name__ == "__main__":
    unittest.main()
