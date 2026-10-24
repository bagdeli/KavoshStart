"""Offline tests for REL-7 release-candidate gating."""
import sys
import unittest
from unittest import mock
import base64
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import rc_gate as rc  # noqa: E402

SHA = "a" * 40
REQ = ["required", "main-guard / main-guard"]


def check(name, status="completed", conclusion="success", stamp="2026-10-09T00:00:00Z"):
    return {"name": name, "status": status, "conclusion": conclusion, "started_at": stamp}


class ReleaseCandidateGate(unittest.TestCase):
    def test_REL7_legacy_absent_contract_and_malformed_release_fail_closed(self):
        checks = [check("required"), check("main-guard / main-guard")]
        def gate_for(manifest):
            def api(path, method="GET", payload=None, allow_missing=False):
                if path == "repos/example/repo/branches/main":
                    return {"commit": {"sha": SHA}}
                if path.startswith("repos/example/repo/contents/"):
                    return {"content": base64.b64encode(json.dumps(manifest).encode()).decode()}
                if allow_missing:
                    return None
                raise AssertionError(path)
            with mock.patch.object(rc, "gh_api", side_effect=api), mock.patch.object(
                    rc, "paged", side_effect=lambda repo, suffix, key=None:
                    checks if key == "check_runs" else [{"name": "v1.5.0"}]):
                return rc.run_gate("example/repo", "v1.6.0-rc.1", SHA, REQ)
        self.assertEqual(gate_for({}), [])
        self.assertEqual(gate_for({"release": {}}), [])
        for invalid in (None, [], "bad"):
            with self.subTest(release=invalid):
                reasons = gate_for({"release": invalid})
                self.assertTrue(any("manifest staging check unavailable: ValueError" in reason for reason in reasons))

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

    def test_REL7_negative_pending_rerun_supersedes_old_success(self):
        runs = [
            check("required", conclusion="success", stamp="2026-10-09T00:00:00Z"),
            {"name": "required", "status": "queued", "conclusion": None,
             "started_at": None, "created_at": None},
            check("main-guard / main-guard"),
        ]
        reasons = rc.candidate_reasons("v1.6.0-rc.1", SHA, REQ, SHA, runs, ["v1.5.0"])
        self.assertTrue(any("required" in reason and "queued" in reason for reason in reasons))

    def test_required_check_floor_cannot_be_removed(self):
        reasons = rc.candidate_reasons(
            "v1.6.0-rc.1", SHA, ["required"], SHA,
            [check("required")], ["v1.5.0"],
        )
        self.assertTrue(any("required checks must include" in r for r in reasons))

    def test_staging_requires_exact_owner_dispatch_and_maps_prerequisites(self):
        manifest = {"owner": "example-owner", "runtime": "server", "acceptance": {"mode": "continuous"},
                    "deploy": {"method": "pull-build", "environments": ["test"]},
                    "ci": {"requiredWorkflow": ".github/workflows/ci.yml"},
                    "release": {"strategy": "release-please", "testStaging": {"schemaVersion": 1, "target": "test",
                      "callerWorkflow": ".github/workflows/rc.yml", "prerequisites": {
                        key: {"acceptanceId": "AC-001", "assertion": "backup::roundtrip"}
                        for key in ("full", "originals", "recovery", "capacity")}}}}
        scope = {"schemaVersion": 1, "targetRelease": "v1.2.3", "items": [{
            "id": "AC-001", "issue": 42, "owner": "example-owner", "risk": "high", "evidence": ["ci", "test"],
            "assertions": {"ci": ["repo::required"], "test": ["backup::roundtrip"]}}]}
        run = {"id": 7, "run_attempt": 1, "event": "workflow_dispatch", "status": "in_progress", "head_branch": "main",
               "head_sha": SHA, "repository": {"full_name": "example/repo"},
               "head_repository": {"full_name": "example/repo"},
               "path": ".github/workflows/rc.yml@refs/heads/main",
               "actor": {"login": "example-owner", "type": "User"},
               "triggering_actor": {"login": "example-owner", "type": "User"}}
        def api(path):
            if path.startswith("repos/example/repo/contents/"):
                payload = manifest if "kavosh.project.json" in path else scope if "scope.json" in path else {
                    "schemaVersion": 1, "maxAgeDays": 14, "producers": {"test": {"appId": 7654321, "checkName": "Test Evidence"}}}
                return {"content": base64.b64encode(json.dumps(payload).encode()).decode()}
            if path.endswith("/actions/runs/7/attempts/1"):
                return run
            if path == "repos/example/repo/actions/runs/8":
                return {"id": 8, "run_attempt": 1, "event": "push", "status": "completed", "conclusion": "success", "head_sha": SHA,
                        "head_branch": "main", "repository": {"full_name": "example/repo"},
                        "head_repository": {"full_name": "example/repo"},
                        "path": ".github/workflows/ci.yml"}
            if path == "repos/example/repo/actions/runs/8/attempts/1/jobs?per_page=100&page=1":
                return {"jobs": [{"id": 80, "run_id": 8, "run_attempt": 1, "head_sha": SHA, "name": "required",
                                  "status": "completed", "conclusion": "success"}]}
            if path == "repos/example/repo/issues/42":
                return {"state": "open", "body": f"Staging-Merged-SHA: {SHA}\nStaging-CI-Run: https://github.com/example/repo/actions/runs/8\nStaging-Test-Evidence: synthetic"}
            raise AssertionError(path)
        env = {"TAG": "v1.2.3-rc.1", "GITHUB_REF": "refs/heads/main",
               "GITHUB_RUN_ID": "7", "GITHUB_RUN_ATTEMPT": "1", "KAVOSH_RC_REQUIRE_TEST_STAGING": "1"}
        with mock.patch.object(rc.ReceiptVerifier, "verify"):
            self.assertEqual(rc.staging_reasons("example/repo", SHA, api, 7, 1, "v1.2.3-rc.1", env), [])
        run["triggering_actor"] = {"login": "other-user"}
        with mock.patch.object(rc.ReceiptVerifier, "verify"):
            self.assertTrue(any("manifest owner" in reason for reason in
                                rc.staging_reasons("example/repo", SHA, api, 7, 1, "v1.2.3-rc.1", env)))
        run["triggering_actor"] = {"login": "example-owner"}
        manifest["release"]["testStaging"]["prerequisites"]["capacity"]["assertion"] = "undeclared"
        with mock.patch.object(rc.ReceiptVerifier, "verify"):
            self.assertTrue(any("prerequisite capacity" in reason for reason in
                                rc.staging_reasons("example/repo", SHA, api, 7, 1, "v1.2.3-rc.1", env)))
        self.assertTrue(any("actual RC candidate" in reason for reason in
                            rc.staging_reasons("example/repo", SHA, api, 7, 1, "v1.3.0-rc.1", env)))


if __name__ == "__main__":
    unittest.main()
