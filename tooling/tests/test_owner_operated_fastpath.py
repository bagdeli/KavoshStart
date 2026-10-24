"""Default owner-operated development must not inherit team paperwork gates."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling" / "src"))
sys.path.insert(0, str(ROOT / "scripts"))
import governance as g
import scaffold


def event(body="", title="tiny fix", branch="hotfix", base="main", private=True):
    return {"repository": {"default_branch": "main", "private": private},
            "pull_request": {"number": 77, "title": title, "body": body,
                             "head": {"ref": branch}, "base": {"ref": base},
                             "user": {"type": "User"}, "labels": [], "draft": False}}


def fake_gh(*args):
    path = args[1]
    if "/files" in path:
        return [{"filename": "docs/guide.md", "additions": 2, "deletions": 0}] if "page=1" in path else []
    return []


def findings(manifest, pr=None):
    g.results.clear()
    with patch.object(g, "gh", side_effect=fake_gh):
        g.check_pr(manifest, pr or event(), "example/example")
    return {rule: level for level, rule, _, _ in g.results}


class OwnerOperatedFastPath(unittest.TestCase):
    def test_default_is_not_inferred_from_visibility_tier_or_acceptance(self):
        for vis in ("private", "public"):
            for mode in ("none", "continuous"):
                m = {"visibility": vis, "tier": "T2", "acceptance": {"mode": mode}}
                self.assertFalse(g.team_process(m))
                m["review"] = {"teamProcess": True}
                self.assertTrue(g.team_process(m))

    def test_private_owner_no_paperwork_blocks_pr(self):
        out = findings({"visibility": "private", "acceptance": {"mode": "none"}, "ui": {"kind": "none"}})
        for rid in ("PR-1", "PR-2", "PR-4", "BR-2", "CR-1"):
            self.assertEqual(out[rid], "warn", (rid, out))
        self.assertFalse(any(v == "fail" for v in out.values()), out)

    def test_team_opt_in_keeps_formal_checks(self):
        m = {"visibility": "private", "review": {"teamProcess": True},
             "acceptance": {"mode": "none"}, "ui": {"kind": "none"}}
        out = findings(m)
        for rid in ("PR-1", "PR-2", "PR-4", "BR-2", "CR-1"):
            self.assertEqual(out[rid], "fail", (rid, out))

    def test_actual_identity_claim_is_not_silently_certified(self):
        body = "## AI involvement\n- Agent / model: fake\nCo-Authored-By: <Agent> <noreply@example.com>"
        out = findings({"visibility": "private", "ui": {"kind": "none"}}, event(body=body))
        self.assertEqual(out["AI-3"], "fail")

    def test_runner_native_labels_work_only_for_private_owner(self):
        m = {"visibility": "private", "repo": "example/example", "ci": {"runner": "self-hosted"}}
        expected = ["self-hosted", "linux", "x64"]
        self.assertEqual(g.runner_labels(m), expected)
        self.assertFalse(any(l == "fail" and r == "CI-2" for l,r,*_ in g.runner_manifest_problems(m)))
        self.assertEqual(json.loads(scaffold.values(dict(m, name="Example", summary="test", tier="T1",
                                                        runtime="server", kavoshStart="v8.1.0",
                                                        ui={"kind":"none"}, deploy={"method":"custom"}))['RUNS_ON_JSON']), expected)
        workflow = {".github/workflows/ci.yml": "jobs:\n  required:\n    runs-on: [self-hosted, linux, x64]\n"}
        self.assertFalse(any(l=="fail" for l,*_ in g.runner_workflow_problems(workflow,m)))
        m["review"]={"teamProcess": True}
        m["ci"]["runnerLabels"] = expected
        self.assertTrue(any(l == "fail" and r == "CI-2" for l,r,*_ in g.runner_manifest_problems(m)))
        m["visibility"]="public"
        m.pop("review")
        m["ci"]["runnerLabels"] = expected
        self.assertTrue(any(l == "fail" and r == "CI-2" for l,r,*_ in g.runner_manifest_problems(m)))

    def test_comments_in_pr_template_do_not_impose_fake_evidence(self):
        body = "## Change\nUpdated a typo.\n<!--\nRisk: high\nCo-Authored-By: <Agent> <noreply@example.com>\n## AI involvement\n-->"
        out = findings({"visibility": "private", "ui": {"kind": "none"}}, event(body=body))
        self.assertNotIn("AI-3", out)
        self.assertEqual(out["PR-4"], "warn")
        self.assertEqual(out["CR-1"], "warn")

    def test_agent_work_guide_has_no_unconditional_issue_or_upgrade_gate(self):
        protocol = (ROOT / "START.md").read_text(encoding="utf-8")
        work = protocol.split("## §4 WORK", 1)[1]
        self.assertIn("A newer standards tag alone does **not** route ordinary WORK to UPGRADE", work)
        self.assertIn("Issue/PR/Spec **if one exists**", work)
        self.assertIn("`review.teamProcess=true`", work)
        self.assertIn("continue unrelated authorized development", work)
        self.assertNotIn("`gh issue view <n>`", work)
        self.assertNotIn("Open a **draft PR early**", work)

    def test_schema_accepts_optional_team_choice(self):
        s = json.loads((ROOT/"intake/kavosh.project.schema.json").read_text())
        self.assertIn("teamProcess", s["properties"]["review"]["properties"])
        self.assertEqual(g.validate({"teamProcess": True}, s["properties"]["review"]), [])
        self.assertTrue(g.validate({"teamProcess": "true"}, s["properties"]["review"]))


if __name__ == "__main__":
    unittest.main()
