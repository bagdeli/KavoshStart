"""ACC-3 regressions: a green but unrelated run is not acceptance evidence."""
import base64
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import release_gate as rg

MERGED, SOURCE, TREE = "b" * 40, "c" * 40, "d" * 40
WORKFLOW = ".github/workflows/ci.yml"
BODY = (f"Acceptance-Merged-SHA: {MERGED}\n"
        "Acceptance-Evidence-Run: https://github.com/o/r/actions/runs/99\n"
        "Accepted-By: @owner\n")


class AcceptanceProvenance(unittest.TestCase):
    def setUp(self):
        self.run = {"id": 99, "status": "completed", "conclusion": "success",
                    "head_sha": MERGED, "path": WORKFLOW,
                    "repository": {"full_name": "o/r"},
                    "head_repository": {"full_name": "o/r"}}
        self.pr = {"merged_at": "2026-01-10T10:00:00Z", "merge_commit_sha": MERGED,
                   "head": {"sha": SOURCE, "repo": {"full_name": "o/r"}},
                   "base": {"ref": "main", "repo": {"full_name": "o/r"}}}
        self.trees = {MERGED: TREE, SOURCE: TREE}
        self.calls = []

    def api(self, path):
        self.calls.append(path)
        if path.endswith("/actions/runs/99"):
            return copy.deepcopy(self.run)
        if path.endswith("/pulls/7"):
            return copy.deepcopy(self.pr)
        if "/git/commits/" in path:
            sha = path.rsplit("/", 1)[1]
            return {"sha": sha, "tree": {"sha": self.trees.get(sha)}}
        raise AssertionError(path)

    def problems(self, body=BODY, workflow=WORKFLOW):
        return rg.acceptance_run_problems("o/r", MERGED, body, workflow, self.api)

    def test_ACC3_positive_exact_accepted_source_and_workflow(self):
        self.assertEqual(self.problems(), [])

    def test_ACC3_negative_unrelated_green_source(self):
        self.run["head_sha"] = SOURCE
        self.assertIn("source SHA differs", " ".join(self.problems()))

    def test_ACC3_negative_housekeeping_workflow_is_not_CI_evidence(self):
        self.run["path"] = ".github/workflows/housekeeping.yml"
        self.assertIn("declared required CI", " ".join(self.problems()))

    def test_ACC3_negative_missing_metadata_and_failed_runs(self):
        good = copy.deepcopy(self.run)
        for field in ("id", "path", "head_sha", "repository", "head_repository"):
            self.run = copy.deepcopy(good)
            del self.run[field]
            self.assertTrue(self.problems(), field)
        self.run = good
        for state in ("failure", "skipped", "cancelled", None):
            self.run["conclusion"] = state
            self.assertTrue(self.problems(), state)

    def test_ACC3_negative_wrong_source_repository(self):
        self.run["head_repository"] = {"full_name": "outsider/fork"}
        self.assertIn("source repository", " ".join(self.problems()))

    def test_ACC3_positive_verified_identical_tree_squash(self):
        self.run["head_sha"] = SOURCE
        self.assertEqual(self.problems(BODY + "Acceptance-Evidence-PR: 7\n"), [])

    def test_ACC3_negative_squash_with_changed_tree(self):
        self.run["head_sha"] = SOURCE
        self.trees[MERGED] = "e" * 40
        self.assertIn("tree differs", " ".join(self.problems(BODY + "Acceptance-Evidence-PR: 7\n")))

    def test_ACC3_negative_unmerged_or_unrelated_PR(self):
        self.run["head_sha"] = SOURCE
        for change in ({"merged_at": None}, {"merge_commit_sha": "e" * 40}):
            original = copy.deepcopy(self.pr)
            self.pr.update(change)
            self.assertTrue(self.problems(BODY + "Acceptance-Evidence-PR: 7\n"))
            self.pr = original

    def test_ACC3_negative_external_link_never_triggers_external_request(self):
        body = BODY.replace("https://github.com/o/r/actions/runs/99", "https://other.invalid/run")
        self.assertTrue(self.problems(body))
        self.assertEqual(self.calls, [])

    def test_ACC3_positive_versioned_custom_workflow_adapter(self):
        self.run["path"] = ".github/workflows/product-check.yml@refs/heads/main"
        self.assertEqual(self.problems(workflow=".github/workflows/product-check.yml"), [])

    def test_ACC3_negative_duplicate_or_empty_markers(self):
        self.assertIsNone(rg._marker("Accepted-By:\nOther: @owner\n", "Accepted-By"))
        self.assertIsNone(rg._marker("Accepted-By: @owner\nAccepted-By: @other\n", "Accepted-By"))

    def test_ACC3_positive_CRLF_receipts(self):
        self.assertEqual(self.problems(BODY.replace("\n", "\r\n")), [])

    def test_ACC3_negative_duplicate_blank_marker(self):
        self.assertIsNone(rg._marker("Accepted-By: @owner\nAccepted-By:\n", "Accepted-By"))

    def test_ACC3_negative_source_stage_rejects_wrong_source(self):
        def api(path):
            if "/contents/" in path:
                value = ({"acceptance": {"mode": "continuous"}, "ci": {"requiredWorkflow": WORKFLOW}}
                         if "kavosh.project.json" in path else
                         {"schemaVersion": 1, "targetRelease": "v1.0.0", "items": [
                             {"id": "AC-001", "issue": 12, "owner": "owner",
                              "risk": "low", "evidence": ["ci"]}]})
                return {"content": base64.b64encode(json.dumps(value).encode()).decode()}
            if path.endswith("/issues/12"):
                return {"state": "closed", "body": BODY}
            if "/compare/" in path:
                return {"status": "ahead"}
            return self.api(path)
        self.assertEqual(rg.acceptance_source_reasons("o/r", "a" * 40, api), [])
        self.run["head_sha"] = SOURCE
        self.assertTrue(rg.acceptance_source_reasons("o/r", "a" * 40, api))


if __name__ == "__main__":
    unittest.main()
