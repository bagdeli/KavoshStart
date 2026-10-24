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


def event(body="Fix the documented example; checked its rendered output.", title="tiny fix", branch="hotfix", base="main", private=True):
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

    def test_empty_ready_pr_is_not_a_fastpath(self):
        for body in ("", "<!-- placeholder -->", "## Change\n## Verification"):
            out = findings({"visibility": "private", "ui": {"kind": "none"}}, event(body=body))
            self.assertEqual(out["PR-1"], "fail")
        draft = event(body="")
        draft["pull_request"]["draft"] = True
        self.assertEqual(findings({"visibility": "private"}, draft)["PR-1"], "warn")

    def test_risk_floor_survives_missing_forms_and_bot_metadata(self):
        for path in ("src/auth/roles.py", "migrations/002.sql", "tooling/src/governance.py",
                     "tooling/src/rc_gate.py", "tooling/src/receipts.py",
                     "tooling/templates/kavosh-release.yml", "intake/kavosh.project.schema.json"):
            for body, bot in (("Owner requested this scoped change.", False), ("Dependency update", True)):
                rows, risk = g.change_risk_problems(body, [{"filename": path}], bot=bot, structured=False)
                self.assertEqual(risk, "high", (path, rows))
                self.assertTrue(any(rule == "CR-2" and level == "warn" for level,rule,*_ in rows))
            for body in ("Risk: low", "Risk: medium\nCapabilities: control-plane"):
                rows, risk = g.change_risk_problems(body, [{"filename": path}], structured=False)
                self.assertEqual(risk, "high")
                self.assertTrue(any(rule == "CR-2" and level == "fail" for level,rule,*_ in rows))
        rows, risk = g.change_risk_problems("Risk: low\nCapabilities: docs", ["docs/example.md"], structured=False)
        self.assertEqual(risk, "low")
        self.assertFalse(any(level == "fail" for level,*_ in rows))

    def test_owner_document_shape_is_advisory_but_core_files_are_not(self):
        with tempfile.TemporaryDirectory() as temp:
            docs = {"AGENTS.md": "x\n" * 180 + "a" * 40,
                    "STATUS.md": "historical note", "large.md": "x" * 70000}
            for name, content in docs.items():
                Path(temp, name).write_text(content)
            import os
            previous = os.getcwd()
            try:
                os.chdir(temp)
                for team in (False, True):
                    g.results.clear()
                    with patch.object(g, "git_files", return_value=list(docs)), patch.object(g, "read", side_effect=lambda f: docs.get(f, "")):
                        g.check_files({"review": {"teamProcess": team}, "ci": {"runner": "none"}, "release": {"strategy": "custom"}})
                    expected = "fail" if team else "warn"
                    for rule in ("AI-1", "SRC-2", "SRC-3", "DOC-1"):
                        self.assertTrue(any(level == expected and rid == rule for level,rid,*_ in g.results), (team,rule,g.results))
                    self.assertTrue(any(level == "fail" and rid == "AI-4" for level,rid,*_ in g.results))
                    self.assertTrue(any(level == "fail" and rid == "SRC-7" for level,rid,*_ in g.results))
            finally:
                os.chdir(previous)

    def test_schema_accepts_optional_team_choice(self):
        s = json.loads((ROOT/"intake/kavosh.project.schema.json").read_text())
        self.assertIn("teamProcess", s["properties"]["review"]["properties"])
        self.assertEqual(g.validate({"teamProcess": True}, s["properties"]["review"]), [])
        self.assertTrue(g.validate({"teamProcess": "true"}, s["properties"]["review"]))


if __name__ == "__main__":
    unittest.main()
