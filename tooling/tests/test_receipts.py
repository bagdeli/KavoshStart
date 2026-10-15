"""ACC-2/3: executable receipt contracts with positive controls and hostile fixtures.

App identities/data here are synthetic. Passing fixtures are not live approval,
UAT, producer installation or product acceptance.
"""
import base64
import copy
import json
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import receipts as rv
import release_gate as rg
import health

SOURCE, CANDIDATE, TREE, NEW_TREE = "b" * 40, "a" * 40, "c" * 40, "d" * 40


class Fixture:
    def __init__(self):
        self.now = datetime.now(timezone.utc).replace(microsecond=0)
        self.candidate = SOURCE
        self.manifest = {"acceptance": {"mode": "continuous"},
                         "ci": {"requiredWorkflow": ".github/workflows/ci.yml"}}
        self.item = {"id": "AC-001", "issue": 12, "owner": "owner", "risk": "critical",
                     "evidence": list(rv.RECEIPT_KINDS),
                     "assertions": {k: [f"{k}:reject-invalid-input"] for k in rv.RECEIPT_KINDS}}
        self.scope = {"schemaVersion": 1, "targetRelease": "v1.0.0", "items": [self.item]}
        self.policy = {"schemaVersion": 1, "maxAgeDays": 14, "producers": {}}
        for kind in (*rv.RECEIPT_KINDS, "approval", "defer"):
            decision = kind in ("approval", "defer")
            self.policy["producers"][kind] = {"appId": 200002 if decision else 200001,
                "checkName": f"acceptance/{kind}", "mode": "decision" if decision else "actions"}
            if not decision:
                self.policy["producers"][kind].update(workflow=".github/workflows/ci.yml", job="required")
        self.objects = {}
        self.receipts = {}
        self.calls = []
        self.fail_paths = set()
        self.objects[f"git/commits/{SOURCE}"] = {"sha": SOURCE, "tree": {"sha": TREE}}
        self.objects[f"git/commits/{CANDIDATE}"] = {"sha": CANDIDATE, "tree": {"sha": NEW_TREE}}
        self.objects[f"compare/{SOURCE}...{SOURCE}"] = {"status": "identical"}
        self.objects[f"compare/{SOURCE}...{CANDIDATE}"] = {"status": "ahead"}
        run = {"id": 99, "run_attempt": 1, "head_sha": SOURCE, "path": ".github/workflows/ci.yml",
               "status": "completed", "conclusion": "success", "repository": {"full_name": "o/r"},
               "head_repository": {"full_name": "o/r"}, "run_started_at": self.time(-60)}
        self.objects["actions/runs/99"] = copy.deepcopy(run)
        self.objects["actions/runs/99/attempts/1"] = run
        self.objects["actions/jobs/100"] = {"id": 100, "run_id": 99, "run_attempt": 1,
            "head_sha": SOURCE, "name": "required", "status": "completed", "conclusion": "success",
            "completed_at": self.time(-30)}
        for index, kind in enumerate((*rv.RECEIPT_KINDS, "approval", "defer")):
            receipt = {"schemaVersion": 1, "repository": "o/r", "acceptanceId": "AC-001", "kind": kind,
                "targetRelease": "v1.0.0", "sourceSha": SOURCE, "sourceTree": TREE,
                "issuedAt": self.time(-20), "expiresAt": self.time(3600), "outcome": "pass"}
            if kind in rv.RECEIPT_KINDS:
                receipt.update(assertions=[{"id": self.item["assertions"][kind][0], "outcome": "pass"}],
                               runId=99, runAttempt=1, jobId=100, artifactId=1000+index,
                               artifactDigest="sha256:" + "e"*64)
                self.objects[f"actions/artifacts/{1000+index}"] = {"id": 1000+index,
                    "name": f"kavosh-evidence-99-1-{kind}", "size_in_bytes": 42, "expired": False,
                    "digest": receipt["artifactDigest"], "created_at": self.time(-40),
                    "expires_at": self.time(7200), "workflow_run": {"id": 99, "head_sha": SOURCE}}
            else:
                receipt.update(subject="owner", decision="accept" if kind == "approval" else "defer", issuedAt=self.time(-5))
            self.receipts[kind] = receipt
            self.objects[f"check-runs/{500+index}"] = {"id": 500+index, "head_sha": SOURCE,
                "app": {"id": self.policy["producers"][kind]["appId"]}, "name": f"acceptance/{kind}",
                "status": "completed", "conclusion": "success", "completed_at": self.time(-1 if kind in ("approval", "defer") else -10), "output": {}}
        self.seal()

    def time(self, seconds):
        return (self.now + timedelta(seconds=seconds)).isoformat()

    def seal(self):
        links = {}
        for index, (kind, receipt) in enumerate(self.receipts.items()):
            receipt.update(scopeDigest=rv.receipt_digest(self.item), policyDigest=rv.receipt_digest(self.policy))
            if kind == "approval":
                receipt["bindingsDigest"] = rv.receipt_digest({"mergedSha": SOURCE,
                    "ciRun": "https://github.com/o/r/actions/runs/99", "evidence": links.copy()})
            elif kind == "defer":
                receipt["bindingsDigest"] = rv.receipt_digest({"deferredTo": self.item.get("deferredTo"),
                                                                "deferIssue": self.item.get("deferIssue")})
            check = self.objects[f"check-runs/{500+index}"]
            check["output"]["text"] = json.dumps(receipt)
            links[kind] = f"https://api.github.com/repos/o/r/check-runs/{500+index}#{rv.receipt_digest(receipt)}"
        self.links = links
        self.body = f"Accepted-By: @owner\nAcceptance-Merged-SHA: {SOURCE}\nAcceptance-Evidence-Run: https://github.com/o/r/actions/runs/99\n"
        self.body += "\n".join(f"{rv.RECEIPT_MARKERS[k]}: {links[k]}" for k in self.item["evidence"])
        self.body += f"\nAcceptance-Decision-Evidence: {links['approval']}\n"
        self.defer_body = f"Defer-Approved-By: @owner\nDefer-Decision-Evidence: {links['defer']}\n"

    def api(self, path):
        self.calls.append(path)
        if not path.startswith("repos/o/r/"):
            raise AssertionError("external request: " + path)
        path = path.removeprefix("repos/o/r/")
        if path in self.fail_paths:
            raise RuntimeError("unavailable")
        if path.startswith("contents/"):
            file = path.split("?", 1)[0][9:]
            value = {"kavosh.project.json": self.manifest, "acceptance/scope.json": self.scope,
                     rv.RECEIPT_POLICY: self.policy}[file]
            return {"content": base64.b64encode(json.dumps(value).encode()).decode()}
        if path == "issues/12":
            return {"state": "closed", "body": self.body}
        if path == "issues/13":
            return {"state": "closed", "body": self.defer_body}
        if path not in self.objects:
            raise RuntimeError("missing test resource: " + path)
        return copy.deepcopy(self.objects[path])

    def report(self):
        return rv.receipt_scope_report("o/r", self.candidate, self.manifest, self.scope, self.api, self.now)


class Receipts(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()

    def assertRejected(self, text=None):
        errors = self.f.report()["problems"]
        self.assertTrue(errors)
        if text:
            self.assertIn(text, "; ".join(errors))

    def test_ACC3_positive_all_evidence_and_independent_decision(self):
        self.assertEqual(self.f.report(), {"verified": ["AC-001"], "deferred": [], "problems": []})
        self.assertEqual(rg.acceptance_reasons("o/r", SOURCE, self.f.api), [])

    def test_ACC2_positive_Health_and_Release_share_verifier(self):
        self.assertIs(health.receipt_scope_report, rg.receipt_scope_report)
        args = ("o/r", SOURCE, self.f.manifest, self.f.scope, self.f.api, self.f.now)
        self.assertEqual(health.receipt_scope_report(*args), rg.receipt_scope_report(*args))

    def test_ACC2_negative_Health_cannot_accept_a_failed_receipt(self):
        self.f.objects["check-runs/502"]["conclusion"] = "failure"
        self.assertRejected("publisher/result")
        self.assertTrue(rg.acceptance_reasons("o/r", SOURCE, self.f.api))

    def test_ACC3_negative_owner_marker_and_green_CI_are_insufficient(self):
        self.f.body = self.f.body.split("Acceptance-CI-Receipt:")[0]
        self.assertEqual(rg.acceptance_source_reasons("o/r", SOURCE, self.f.api)[0], "AC-001: missing Acceptance-Test-Evidence")
        self.assertRejected("exact sha256 receipt")

    def test_ACC3_negative_arbitrary_URLs_never_fetched(self):
        self.f.body = self.f.body.replace(self.f.links["test"], "https://127.0.0.1/private")
        self.assertRejected("exact sha256 receipt")
        self.assertFalse(any("127.0.0.1" in path for path in self.f.calls))

    def test_ACC3_negative_mutated_receipt_breaks_digest(self):
        self.f.objects["check-runs/501"]["output"]["text"] += " "
        self.assertEqual(self.f.report()["problems"], [])  # harmless formatting is canonicalized
        self.f.objects["check-runs/501"]["output"]["text"] = json.dumps({"outcome": "pass"})
        self.assertRejected("digest changed")

    def test_ACC3_negative_missing_deleted_expired_or_wrong_artifact(self):
        original = copy.deepcopy(self.f.objects["actions/artifacts/1001"])
        for field, value in (("expired", True), ("digest", "sha256:"+"f"*64), ("id", 0),
                             ("size_in_bytes", 0), ("name", "unrelated"), ("expires_at", self.f.time(-1))):
            with self.subTest(field=field):
                self.f.objects["actions/artifacts/1001"] = {**original, field: value}
                self.assertRejected()
        self.f.objects["actions/artifacts/1001"] = original
        self.f.fail_paths.add("actions/artifacts/1001")
        self.assertRejected("RuntimeError")

    def test_ACC3_negative_untrusted_or_shared_App(self):
        for app in (15368, 1144995, 300003):
            self.f.objects["check-runs/505"]["app"]["id"] = app
            self.assertRejected("publisher/result")
        self.f.policy["producers"]["approval"]["appId"] = 15368
        self.f.seal()
        self.assertRejected("independently controlled")

    def test_ACC3_negative_evidence_App_cannot_approve_itself(self):
        self.f.policy["producers"]["approval"]["appId"] = 200001
        self.f.seal()
        self.assertRejected("independent of evidence")

    def test_ACC3_negative_wrong_scope_kind_subject_or_result(self):
        for field, value in (("kind", "ci"), ("targetRelease", "v2.0.0"), ("acceptanceId", "AC-999"),
                             ("repository", "o/other"), ("outcome", "failure")):
            with self.subTest(field=field):
                f = self.f = Fixture()
                f.receipts["test"][field] = value
                f.seal()
                self.assertRejected("scope/kind/policy")
        self.f = Fixture()
        self.f.receipts["approval"]["subject"] = "someone-else"
        self.f.seal()
        self.assertRejected("this owner/scope/evidence")

    def test_ACC3_negative_edited_bindings_invalidate_approval(self):
        self.f.objects["actions/runs/98"] = {**self.f.objects["actions/runs/99"], "id": 98}
        self.f.body = self.f.body.replace("actions/runs/99", "actions/runs/98")
        self.assertRejected("this owner/scope/evidence")

    def test_ACC3_negative_expired_future_or_unbounded_receipts(self):
        for field, value in (("expiresAt", self.f.time(-1)), ("issuedAt", self.f.time(60)),
                             ("expiresAt", self.f.time(366*86400)), ("issuedAt", "2026-10-15T01:00:00")):
            with self.subTest(field=field):
                self.f = Fixture()
                self.f.receipts["test"][field] = value
                self.f.seal()
                self.assertRejected()

    def test_ACC3_negative_generic_green_job_lacks_required_assertions(self):
        self.f.receipts["ui"]["assertions"] = [{"id": "lint:passed", "outcome": "pass"}]
        self.f.seal()
        self.assertRejected("declared assertions")

    def test_ACC3_negative_failed_or_duplicate_assertions(self):
        self.f.receipts["test"]["assertions"][0]["outcome"] = "skipped"
        self.f.seal()
        self.assertRejected("actual passing")
        self.f = Fixture()
        self.f.receipts["test"]["assertions"] *= 2
        self.f.seal()
        self.assertRejected("declared assertions")

    def test_ACC3_negative_bad_workflow_job_attempt_or_source(self):
        for path, field, value in (("actions/runs/99/attempts/1", "path", ".github/workflows/tidy.yml"),
                                  ("actions/runs/99/attempts/1", "head_sha", CANDIDATE),
                                  ("actions/jobs/100", "run_attempt", 2),
                                  ("actions/jobs/100", "name", "cleanup"),
                                  ("actions/jobs/100", "conclusion", "skipped")):
            with self.subTest(field=field, path=path):
                self.f = Fixture()
                self.f.objects[path][field] = value
                self.assertRejected("mismatch")

    def test_ACC3_positive_manual_UAT_uses_independent_attestor(self):
        self.f.policy["producers"]["ui"] = {"appId": 200001, "checkName": "acceptance/ui", "mode": "manual"}
        self.f.receipts["ui"]["externalEvidenceDigest"] = "sha256:"+"f"*64
        self.f.seal()
        self.assertEqual(self.f.report()["problems"], [])
        self.assertFalse(any("actions/artifacts/1002" in path for path in self.f.calls))

    def test_ACC3_negative_manual_digest_missing(self):
        self.f.policy["producers"]["ui"]["mode"] = "manual"
        self.f.seal()
        self.assertRejected("immutable external evidence")

    def test_ACC3_positive_independent_scoped_defer(self):
        self.f.item.update(deferredTo="v1.1.0", deferIssue=13)
        self.f.seal()
        self.assertEqual(self.f.report(), {"verified": [], "deferred": ["AC-001"], "problems": []})
        self.assertEqual(rg.acceptance_reasons("o/r", SOURCE, self.f.api), [])

    def test_ACC3_negative_defer_marker_without_receipt(self):
        self.f.item.update(deferredTo="v1.1.0", deferIssue=13)
        self.f.seal()
        self.f.defer_body = "Defer-Approved-By: @owner\n"
        self.assertRejected("exact sha256 receipt")

    def test_ACC3_negative_invalid_paths_and_missing_assertion_contract(self):
        for path in ("../src", "/src", "src/*", "src//file", "src\\file", "src/./file"):
            self.f.item["evidencePaths"] = [path]
            self.assertRejected("literal repository paths")
        self.f.item.pop("evidencePaths")
        self.f.item.pop("assertions")
        self.assertRejected("assertion IDs")

    def set_paths(self):
        f = self.f
        f.candidate = CANDIDATE
        f.item["evidencePaths"] = ["src"]
        node = {"path": "src", "type": "tree", "mode": "040000", "sha": "1"*40}
        for tree in (TREE, NEW_TREE):
            f.objects[f"git/trees/{tree}"] = {"sha": tree, "truncated": False, "tree": [copy.deepcopy(node)]}
        f.seal()

    def test_ACC3_positive_reviewed_unchanged_dependency_paths_allow_reuse(self):
        self.set_paths()
        self.assertEqual(self.f.report()["problems"], [])

    def test_ACC3_negative_changed_dependency_or_control_invalidates_reuse(self):
        self.set_paths()
        self.f.objects[f"git/trees/{NEW_TREE}"]["tree"][0]["sha"] = "2"*40
        self.assertRejected("source change: src")
        self.set_paths()
        self.f.objects[f"git/trees/{NEW_TREE}"]["tree"].append(
            {"path": ".github", "type": "tree", "mode": "040000", "sha": "2"*40})
        self.assertRejected("source change: .github")

    def test_ACC3_negative_whole_tree_is_conservative_default(self):
        self.f.candidate = CANDIDATE
        self.assertRejected("candidate tree changed")

    def test_ACC3_negative_truncated_trees_and_missing_paths(self):
        self.set_paths()
        self.f.objects[f"git/trees/{NEW_TREE}"]["truncated"] = True
        self.assertRejected("tree incomplete")
        self.set_paths()
        self.f.item["evidencePaths"] = ["nonexistent"]
        self.f.seal()
        self.assertRejected("source change: nonexistent")

    def test_ACC3_negative_source_must_be_an_ancestor(self):
        self.set_paths()
        self.f.objects[f"compare/{SOURCE}...{CANDIDATE}"]["status"] = "diverged"
        self.assertRejected("not an ancestor")

    def test_ACC3_negative_duplicate_marker_or_JSON_keys(self):
        self.f.body += f"Acceptance-CI-Receipt: {self.f.links['ci']}\n"
        self.assertRejected("exact sha256 receipt")
        self.f = Fixture()
        self.f.objects["check-runs/500"]["output"]["text"] = '{"schemaVersion":1,"schemaVersion":1}'
        self.assertRejected("duplicate receipt JSON")

    def test_ACC3_negative_approval_cannot_predate_evidence(self):
        self.f.receipts["approval"]["issuedAt"] = self.f.time(-20)
        self.f.seal()
        self.assertRejected("approval predates")

    def test_ACC3_negative_malformed_remote_objects_are_visible(self):
        for value in (None, [], {"app": []}):
            self.f = Fixture()
            self.f.objects["check-runs/500"] = value
            self.assertRejected()

    def test_ACC3_negative_boolean_schema_version(self):
        self.f.receipts["test"]["schemaVersion"] = True
        self.f.seal()
        self.assertRejected("scope/kind/policy")

    def test_CR2_negative_receipt_policy_cannot_claim_low_risk(self):
        import governance
        out, _ = governance.change_risk_problems("Risk: low\nCapabilities: control-plane\n",
                                                ["acceptance/security/receipt-policy.json"])
        self.assertTrue(any(level == "fail" and rule == "CR-2" for level, rule, *_ in out))

    def test_CR2_positive_receipt_policy_declares_high_risk(self):
        import governance
        out, _ = governance.change_risk_problems("Risk: high\nCapabilities: control-plane\n",
                                                ["acceptance/security/receipt-policy.json"])
        self.assertFalse(any(level == "fail" for level, *_ in out))

    def test_generated_workflows_embed_the_exact_shared_source(self):
        import importlib.util
        root = Path(__file__).resolve().parents[2]
        spec = importlib.util.spec_from_file_location("build_receipt_workflows", root / "tooling/build_workflows.py")
        builder = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(builder)
        import textwrap
        shared = (root / "tooling/src/receipts.py").read_text().rstrip()
        expected = textwrap.indent(shared, " " * 10, lambda line: bool(line.strip()))
        for workflow, source in (("kavosh-release.yml", "release_gate.py"), ("kavosh-health.yml", "health.py")):
            generated = builder.build(workflow, source)
            self.assertEqual(generated.count("# BEGIN shared receipt verifier"), 1)
            self.assertIn(expected, generated)
            self.assertNotIn("from receipts import", generated)
            self.assertNotIn("__PYTHON__", generated)
        template = (root / "tooling/templates/kavosh-release.yml").read_text()
        self.assertEqual(template.count("__PYTHON__"), 1)
        self.assertIn('python3 "$KAVOSH_RELEASE_GATE_SCRIPT" --verify-release-pr', template)

    def test_ACC2_negative_moving_scope_snapshot_is_not_verified(self):
        stale = copy.deepcopy(self.f.scope)
        stale["targetRelease"] = "v0.9.0"
        report = rv.receipt_scope_report("o/r", SOURCE, self.f.manifest, stale, self.f.api, self.f.now)
        self.assertEqual(report["verified"], [])
        self.assertIn("contract changed during snapshot", ";".join(report["problems"]))

    def test_REL5_negative_new_pending_rerun_during_receipts_keeps_gate_closed(self):
        from unittest.mock import patch
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "output"
            with patch.dict("os.environ", {"GITHUB_OUTPUT": str(output)}), \
                 patch.object(rg, "gate", side_effect=[(True, []), (False, ["required is pending"])]), \
                 patch.object(rg, "acceptance_reasons", return_value=[]):
                self.assertEqual(rg.main(["--repo", "o/r", "--sha", SOURCE]), 1)
            self.assertNotIn("open=true", output.read_text())

    def test_receipt_documentation_uses_the_implemented_digest_separator(self):
        root = Path(__file__).resolve().parents[2]
        for path in ("standard/11-continuous-acceptance.md", "templates/tier/T2/acceptance/README.md"):
            text = (root / path).read_text()
            self.assertIn("#sha256:", text)
            self.assertNotIn("#sha256=", text)

    def test_ACC3_positive_noncontinuous_profile_needs_no_receipt_API(self):
        self.f.manifest["acceptance"]["mode"] = "none"
        self.assertEqual(self.f.report()["problems"], [])
        self.assertEqual(self.f.calls, [])


if __name__ == "__main__":
    unittest.main()
