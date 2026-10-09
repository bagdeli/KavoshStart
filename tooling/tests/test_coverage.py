"""Positive/negative tests for machine-enforced MUSTs not covered elsewhere (#7).
Governance file/manifest checks run against a real scaffolded repository in a temp dir; PR checks use a fake gh;
agent-guard hooks run in a temp git repo with a bare remote."""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling" / "src"))
import governance as g  # noqa: E402
import health as h  # noqa: E402

EXAMPLE = json.loads((ROOT / "intake" / "kavosh.project.example.json").read_text(encoding="utf-8"))
# The checked-in example deliberately carries unresolved vX.Y.Z. Test fixtures resolve it before scaffold/governance.
EXAMPLE["kavoshStart"] = "v1.7.0"
BASH = shutil.which("bash")
GIT_ID = ["-c", "user.email=t@t", "-c", "user.name=t"]


def git(cwd, *a, check=True):
    return subprocess.run(["git", *a], cwd=cwd, capture_output=True, text=True, check=check)


@contextmanager
def scaffolded(mutate=None, manifest=None):
    """A freshly scaffolded T2/server repo (passes governance), optionally mutated, as the cwd."""
    d = Path(tempfile.mkdtemp())
    prev = os.getcwd()
    try:
        git(d, "init", "-q", "-b", "main")
        (d / "kavosh.project.json").write_text(json.dumps(manifest or EXAMPLE), encoding="utf-8")
        subprocess.run([sys.executable, str(ROOT / "scripts" / "scaffold.py"), str(d)], capture_output=True, check=True)
        if mutate:
            mutate(d)
        git(d, "add", "-A")
        os.chdir(d)
        g.results.clear()
        yield d
    finally:
        os.chdir(prev)
        shutil.rmtree(d, ignore_errors=True)


def failed(rule):
    return [r for r in g.results if r[0] == "fail" and r[1] == rule]


def run_files(mutate=None, manifest=None):
    with scaffolded(mutate, manifest):
        m = g.check_manifest()
        g.check_files(m)
        return list(g.results)


def fails_for(rule, mutate=None, manifest=None):
    return [r for r in run_files(mutate, manifest) if r[0] == "fail" and r[1] == rule]


class GovernanceFiles(unittest.TestCase):
    def test_baseline_scaffold_is_clean(self):
        """Covers: AI-1, SRC-2, SRC-3, DOC-1, CI-1, SEC-3, SEC-4, SRC-7, SRC-5, UI-1 (positive)"""
        self.assertEqual([r for r in run_files() if r[0] == "fail"], [])

    def test_AI1_negative_agents_md_too_long(self):
        self.assertTrue(fails_for("AI-1", lambda d: (d / "AGENTS.md").write_text("x\n" * 200, encoding="utf-8")))

    def test_SRC2_negative_sha_in_docs(self):
        self.assertTrue(fails_for("SRC-2", lambda d: (d / "docs" / "notes.md").write_text("head " + "a" * 40, encoding="utf-8")))

    def test_SRC2_positive_exact_sha_in_docs_audits(self):
        def setup(d):
            path = d / "docs" / "audits" / "evidence.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Exact source: " + "a" * 40, encoding="utf-8")
        self.assertEqual(fails_for("SRC-2", setup), [])

    def test_SRC2_positive_exact_sha_in_versioned_release_notes(self):
        def setup(d):
            path = d / "docs" / "release" / "RELEASE_NOTES_0.1.0.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("Reviewed source commit: " + "a" * 40, encoding="utf-8")
        self.assertEqual(fails_for("SRC-2", setup), [])

    def test_SRC4_positive_standards_citation_is_not_live_issue_state(self):
        def setup(d):
            (d / "AGENTS.md").write_text("# Agent rules\nUse UTS #39 confusable detection.\n", encoding="utf-8")
        warnings = [r for r in run_files(setup) if r[0] == "warn" and r[1] == "SRC-4"]
        self.assertEqual(warnings, [])

    def test_SRC4_negative_explicit_issue_reference_is_live_state(self):
        def setup(d):
            (d / "AGENTS.md").write_text("# Agent rules\nCurrent blocker: Issue #39.\n", encoding="utf-8")
        warnings = [r for r in run_files(setup) if r[0] == "warn" and r[1] == "SRC-4"]
        self.assertTrue(warnings)

    def test_SRC3_negative_status_file(self):
        self.assertTrue(fails_for("SRC-3", lambda d: (d / "STATUS.md").write_text("status", encoding="utf-8")))

    def test_DOC1_negative_oversized_markdown(self):
        self.assertTrue(fails_for("DOC-1", lambda d: (d / "big.md").write_text("a" * 70000, encoding="utf-8")))

    def test_CI3_negative_private_hosted_without_scoped_dispatch_guard(self):
        def mutate(d):
            f = d / ".github/workflows/ci.yml"
            f.write_text(f.read_text(encoding="utf-8").replace("PRIVATE_HOSTED_DISPATCH_REQUIRED", ""), encoding="utf-8")
        self.assertTrue(fails_for("CI-3", mutate))

    def test_CI3_negative_private_hosted_with_automatic_job_gate_enabled(self):
        def mutate(d):
            for name in ("ci.yml", "kavosh.yml", "release.yml"):
                f = d / ".github/workflows" / name
                f.write_text(f.read_text(encoding="utf-8").replace("!true", "!false"), encoding="utf-8")
        self.assertTrue(fails_for("CI-3", mutate))

    def test_CI3_negative_private_hosted_without_dispatch(self):
        def mutate(d):
            for name in ("ci.yml", "kavosh.yml", "release.yml"):
                f = d / ".github/workflows" / name
                f.write_text(f.read_text(encoding="utf-8").replace("workflow_dispatch:", "manual_run_disabled:"), encoding="utf-8")
        self.assertTrue(fails_for("CI-3", mutate))

    def test_CI1_positive_public_repo_on_github_hosted(self):
        m = dict(EXAMPLE, visibility="public", tier="T2", ci={"runner": "github-hosted", "monthlyMinutesBudget": 0})
        self.assertEqual(fails_for("CI-1", manifest=m), [])

    def test_CI1_negative_public_repo_on_self_hosted(self):
        m = dict(EXAMPLE, visibility="public", ci={"runner": "github-hosted", "monthlyMinutesBudget": 0})
        def mutate(d):
            f = d / ".github/workflows/ci.yml"
            f.write_text(f.read_text(encoding="utf-8").replace("runs-on: ubuntu-latest", "runs-on: [self-hosted, linux]"), encoding="utf-8")
        self.assertTrue(fails_for("CI-1", mutate, manifest=m))

    def test_CI1_positive_input_definition_and_comments_are_not_runners(self):
        """Regression: `runs-on:` as an input key followed by a description, and comments, are not runner values."""
        text = ("      runs-on:\n"
                "        description: private repos pass self-hosted labels\n"
                "    runs-on: ubuntu-latest  # not self-hosted\n")
        self.assertEqual(g.runs_on_values(text), ["", "ubuntu-latest"])

    def test_CI1_positive_standard_reusable_runner_expression(self):
        self.assertEqual(g.runner_workflow_problems(
            {"workflow.yml": "jobs:\n  test:\n    runs-on: ${{ fromJSON(inputs.runs-on) }}\n"},
            dict(EXAMPLE, visibility="public"))[0][0], "ok")

    def test_CI1_positive_self_hosted_yaml_label_list(self):
        m = dict(EXAMPLE, ci={"runner": "self-hosted", "monthlyMinutesBudget": 0,
                             "runnerLabels": ["self-hosted", "linux", "x64", "kavoshsms"]})
        workflows = {"ci.yml": "jobs:\n  test:\n    runs-on: [self-hosted, linux, x64, kavoshsms]\n"}
        self.assertEqual(g.runner_workflow_problems(workflows, m)[0][0], "ok")

    def test_CI1_positive_private_hosted_is_allowed_with_per_run_scope(self):
        m = json.loads(json.dumps(EXAMPLE))
        m["ci"] = {"runner": "github-hosted", "monthlyMinutesBudget": 0}
        self.assertEqual(g.runner_manifest_problems(m)[0][0], "ok")
        self.assertEqual(fails_for("CI-1", manifest=m), [])

    def test_CI2_negative_public_self_hosted_without_trust_ADR(self):
        m = json.loads(json.dumps(EXAMPLE))
        m["visibility"] = "public"
        m["ci"] = {"runner": "self-hosted", "runnerLabels": ["self-hosted", "linux", "x64", "example"], "monthlyMinutesBudget": 0}
        self.assertEqual(g.runner_manifest_problems(m)[1][0], "fail")

    def test_CI1_positive_local_only_T1_static(self):
        self.assertEqual(fails_for("CI-1", manifest=local_only_static_manifest()), [])

    def test_CI1_negative_local_only_runner_outside_T1_static(self):
        m = local_only_static_manifest()
        m["runtime"] = "server"
        self.assertTrue(fails_for("CI-1", manifest=m))

    def test_CI3_positive_budget_hint_does_not_invalidate_local_only_profile(self):
        m = local_only_static_manifest()
        m["ci"]["monthlyMinutesBudget"] = 1
        self.assertEqual(fails_for("CI-1", manifest=m), [])

    def test_SEC3_negative_no_permissions(self):
        def mutate(d):
            f = d / ".github/workflows/ci.yml"
            f.write_text(f.read_text(encoding="utf-8").replace("permissions:\n  contents: read\n", ""), encoding="utf-8")
        self.assertTrue(fails_for("SEC-3", mutate))

    def test_SEC4_negative_no_dependabot(self):
        self.assertTrue(fails_for("SEC-4", lambda d: (d / ".github/dependabot.yml").unlink()))

    def test_SRC7_negative_no_project_md(self):
        self.assertTrue(fails_for("SRC-7", lambda d: (d / "PROJECT.md").unlink()))


class ReleaseTags(unittest.TestCase):
    def test_REL3_negative_component_in_tag(self):
        def mutate(d):
            f = d / "release-please-config.json"
            f.write_text(f.read_text(encoding="utf-8").replace('"include-component-in-tag": false,', ""), encoding="utf-8")
        self.assertTrue(fails_for("REL-3", mutate))

    def test_REL3_positive_plain_version_tags(self):
        self.assertEqual(g.release_tag_config('{"include-v-in-tag": true, "include-component-in-tag": false}')[0], "ok")


def local_only_static_manifest():
    m = json.loads(json.dumps(EXAMPLE))
    m.update(tier="T1", runtime="static", visibility="private")
    m["data"] = {"sensitivity": "internal", "regulatedIntegrations": [], "multiTenant": False}
    m["size"] = {"domains": 2, "lifetime": "months", "parallelStreams": 1}
    m["ui"] = {"kind": "admin", "kavoshui": "1.0.0", "locales": ["fa-IR"]}
    m["deploy"] = {"method": "pull-build", "environments": []}
    m["ci"] = {"runner": "none", "monthlyMinutesBudget": 0}
    return m


class Manifest(unittest.TestCase):
    def test_SRC5_negative_manifest_identity_must_match_trusted_repository(self):
        with scaffolded() as _:
            g.results.clear()
            g.check_manifest(actual_repo="another-owner/another-repo")
            self.assertTrue(failed("SRC-5"))

    def test_SRC5_negative_schema_violation(self):
        self.assertTrue(fails_for("SRC-5", manifest=dict(EXAMPLE, tier="T9")))

    def test_SRC5_negative_release_artifact_parent_traversal(self):
        m = json.loads(json.dumps(EXAMPLE))
        m.setdefault("release", {"strategy": "release-please"})
        m["release"]["artifact"] = {"command": "make package", "paths": ["../secret.zip"]}
        self.assertTrue(fails_for("SRC-5", manifest=m))

    def test_SRC5_negative_tier_below_classification(self):
        self.assertTrue(fails_for("SRC-5", manifest=dict(EXAMPLE, tier="T0")))

    def test_UI1_negative_ui_without_kavoshui_pin(self):
        self.assertTrue(fails_for("UI-1", manifest=dict(EXAMPLE, ui={"kind": "admin", "kavoshui": None})))

    def test_UI1_positive_ui_exception_with_safety_ADR(self):
        m = json.loads(json.dumps(EXAMPLE))
        m["ui"] = {"kind": "admin", "kavoshui": None, "locales": ["fa-IR"],
                   "exceptionADR": "docs/decisions/0002-ui-exception.md"}
        def setup(d):
            path=d / m["ui"]["exceptionADR"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# UI exception\nscope RTL accessibility tests", encoding="utf-8")
        self.assertEqual(fails_for("UI-1", setup, manifest=m), [])

    def test_UI1_negative_ui_exception_missing_evidence(self):
        m = json.loads(json.dumps(EXAMPLE))
        m["ui"] = {"kind": "admin", "kavoshui": None, "locales": ["fa-IR"],
                   "exceptionADR": "docs/decisions/0002-ui-exception.md"}
        self.assertTrue(fails_for("UI-1", manifest=m))

    def test_DEP1_positive_custom_deploy_with_equivalent_gates_ADR(self):
        m = json.loads(json.dumps(EXAMPLE))
        m["deploy"]["method"] = "custom"
        m["deploy"]["authorizationADR"] = "docs/decisions/0003-custom-deploy.md"
        def setup(d):
            path=d / m["deploy"]["authorizationADR"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Safety and release gates\nREL-5 least privilege tag rollback database", encoding="utf-8")
        self.assertEqual(fails_for("DEP-1", setup, manifest=m), [])

    def test_DEP1_negative_custom_deploy_without_ADR(self):
        m = json.loads(json.dumps(EXAMPLE))
        m["deploy"]["method"] = "custom"
        self.assertTrue(fails_for("DEP-1", manifest=m))

    def test_DEP5_positive_T1_maintenance_window_with_ADR(self):
        m = json.loads(json.dumps(EXAMPLE)); m["tier"] = "T1"
        m["data"] = {"sensitivity": "internal", "regulatedIntegrations": [], "multiTenant": False}
        m["size"] = {"domains": 2, "lifetime": "months", "parallelStreams": 1}
        m["deploy"]["migrationMode"] = "maintenance-window"
        m["deploy"]["migrationADR"] = "docs/decisions/0004-maintenance.md"
        def setup(d):
            path=d / m["deploy"]["migrationADR"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Migration and recovery\nmaintenance window backup restore test rollback", encoding="utf-8")
        self.assertEqual(fails_for("DEP-5", setup, manifest=m), [])

    def test_DEP5_negative_T2_maintenance_window(self):
        m = json.loads(json.dumps(EXAMPLE))
        m["deploy"]["migrationMode"] = "maintenance-window"
        m["deploy"]["migrationADR"] = "docs/decisions/0004-maintenance.md"
        def setup(d):
            path=d / m["deploy"]["migrationADR"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Migration and recovery\nmaintenance window backup restore test rollback", encoding="utf-8")
        self.assertTrue(fails_for("DEP-5", setup, manifest=m))

    def test_CI2_positive_runner_capacity_is_not_fixed_by_tier(self):
        self.assertEqual(fails_for("CI-2"), [])

    def test_CI2_negative_private_runner_labels_are_repo_scoped(self):
        m = dict(EXAMPLE, ci={"runner": "self-hosted", "monthlyMinutesBudget": 0,
                             "runnerLabels": ["self-hosted", "linux", "x64", "another-repo"],
                             "trustModelADR": "docs/decisions/0002-runner.md"})
        def setup(d):
            path=d / m["ci"]["trustModelADR"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Runner trust model\nIsolation uses rootless container execution. Untrusted code is excluded from this runner. Credential boundary excludes production credentials.", encoding="utf-8")
        self.assertTrue(fails_for("CI-2", setup, manifest=m))

    def test_CI2_positive_private_rootless_runner_with_exact_repo_labels(self):
        m = json.loads(json.dumps(EXAMPLE))
        m["ci"] = {"runner": "self-hosted", "monthlyMinutesBudget": 0,
                   "runnerLabels": ["self-hosted", "linux", "x64", "kavoshsms"],
                   "trustModelADR": "docs/decisions/0002-runner.md"}
        def setup(d):
            path=d / m["ci"]["trustModelADR"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Runner trust model\nIsolation uses rootless container execution. Untrusted code is excluded from this runner. Credential boundary excludes production credentials.", encoding="utf-8")
        self.assertEqual(fails_for("CI-2", setup, manifest=m), [])

    def test_CI2_positive_private_dedicated_runner_with_bounded_trust(self):
        m = json.loads(json.dumps(EXAMPLE))
        m["ci"] = {"runner": "self-hosted", "monthlyMinutesBudget": 0,
                   "runnerLabels": ["self-hosted", "linux", "x64", "kavoshsms"],
                   "trustModelADR": "docs/decisions/0002-runner.md"}
        def setup(d):
            path=d / m["ci"]["trustModelADR"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                "# Runner trust model\nIsolation uses a dedicated repository runner. "
                "Untrusted code is blocked by the same-repository PR boundary. "
                "Credential boundary excludes production and unrelated product credentials.",
                encoding="utf-8")
        self.assertEqual(fails_for("CI-2", setup, manifest=m), [])

    def test_CI2_negative_dedicated_runner_without_trust_boundaries(self):
        m = json.loads(json.dumps(EXAMPLE))
        m["ci"] = {"runner": "self-hosted", "monthlyMinutesBudget": 0,
                   "runnerLabels": ["self-hosted", "linux", "x64", "kavoshsms"],
                   "trustModelADR": "docs/decisions/0002-runner.md"}
        def setup(d):
            path=d / m["ci"]["trustModelADR"]
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text("# Runner trust model\nIsolation uses a dedicated runner.", encoding="utf-8")
        self.assertTrue(fails_for("CI-2", setup, manifest=m))


def pr_event(title="feat(api): add x", head="feat/12-add-x", base="main",
             body="Closes #12\n\n## Change risk\nRisk: medium\nCapabilities: api\nRationale: bounded behavior\n",
             labels=(), private=True):
    return {"repository": {"default_branch": "main", "private": private},
            "pull_request": {"number": 7, "title": title, "body": body, "head": {"ref": head}, "base": {"ref": base},
                             "user": {"type": "User"}, "labels": [{"name": l} for l in labels]}}


def fake_gh(lines=100, parent_base=None, filename="src/a.py"):
    def gh(*args):
        path = args[1]
        if "/files" in path:
            return [{"filename": filename, "additions": lines, "deletions": 0}] if "page=1" in path else []
        if "head=" in path:
            return [{"base": {"ref": parent_base}}] if parent_base else []
        return []
    return gh


def run_pr(visibility="private", **kw):
    gh_kw = {k: kw.pop(k) for k in ("lines", "parent_base", "filename") if k in kw}
    g.results.clear()
    original, g.gh = g.gh, fake_gh(**gh_kw)
    try:
        g.check_pr({"limits": {"prMaxLines": 400}, "visibility": visibility,
                    "ui": {"kind": "admin", "kavoshui": "1.0.0"}}, pr_event(**kw), "o/r")
    finally:
        g.gh = original
    return {r[1]: r[0] for r in g.results}


class PullRequest(unittest.TestCase):
    def test_PR1_PR2_PR3_BR2_BR4_positive_good_pr(self):
        """Covers: PR-1, PR-2, PR-3, BR-2, BR-4 (positive)"""
        r = run_pr()
        for rule in ("PR-1", "PR-2", "PR-3", "BR-2", "BR-4"):
            self.assertEqual(r[rule], "ok", rule)

    def test_PR1_negative_no_linked_issue(self):
        self.assertEqual(run_pr(body="no link")["PR-1"], "fail")

    def test_PR2_negative_title(self):
        self.assertEqual(run_pr(title="Post-v1.1 canonical continuation")["PR-2"], "fail")

    def test_PR3_positive_large_diff_is_telemetry_not_gate(self):
        self.assertEqual(run_pr(lines=1500)["PR-3"], "ok")

    def test_UI2_positive_no_visual_change_needs_no_evidence(self):
        self.assertEqual(run_pr().get("UI-2"), "ok")

    def test_UI2_negative_visual_change_needs_render_evidence(self):
        self.assertEqual(run_pr(filename="src/components/button.tsx").get("UI-2"), "fail")

    def test_UI2_positive_visual_change_with_evidence(self):
        body = "Closes #12\n\n## Change risk\nRisk: medium\nCapabilities: ui\nRationale: rendered component change\n\nUI evidence: https://example.test/rendered.png"
        self.assertEqual(run_pr(filename="src/components/button.tsx", body=body).get("UI-2"), "ok")

    def test_BR2_negative_branch_name(self):
        self.assertEqual(run_pr(head="agent/lccg-reconcile-20260925")["BR-2"], "fail")

    def test_CI1_negative_repository_made_public_but_manifest_private(self):
        self.assertEqual(run_pr(private=False).get("CI-1"), "fail")

    def test_BR4_negative_long_lived_base(self):
        self.assertEqual(run_pr(base="vnext/integration-20260918")["BR-4"], "fail")


def cmp(days_ago, ahead):
    date = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%SZ")
    return {"ahead_by": ahead, "commits": [{"commit": {"committer": {"date": date}}}]}


class HealthPure(unittest.TestCase):
    def test_BR8_positive_short_branches(self):
        self.assertEqual(h.branch_problems({"feat/1-x": cmp(1, 3)}, 3)[2], [])

    def test_BR8_negative_hidden_truth_branch(self):
        self.assertEqual(h.branch_problems({"vnext/integration": cmp(1, 537)}, 3)[2], ["vnext/integration (+537)"])

    def test_REL3_positive_version_tags(self):
        self.assertEqual(h.non_version_tags(["v1.0.0", "v1.1.0-rc.2", "v1",
                                             "KavoshStart-v1.1.0"]), [])

    def test_REL3_negative_other_tags(self):
        self.assertEqual(h.non_version_tags(["develop", "v1.0.0", "release-1",
                                             "KavoshStart-v1.2.0"]),
                         ["develop", "release-1", "KavoshStart-v1.2.0"])


@unittest.skipUnless(BASH, "bash not available")
class AgentGuardHooks(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        git(self.tmp, "init", "-q", "--bare", "remote.git")
        self.work = self.tmp / "work"
        git(self.tmp, "init", "-q", "-b", "main", "work")
        shutil.copytree(ROOT / "templates/common/.githooks", self.work / ".githooks")
        git(self.work, "config", "core.hooksPath", ".githooks")
        git(self.work, "remote", "add", "origin", "../remote.git")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def commit(self, name, text, msg="feat: x"):
        (self.work / name).write_text(text, encoding="utf-8")
        git(self.work, "add", "-f", name)
        return git(self.work, *GIT_ID, "commit", "-q", "-m", msg, check=False)

    def test_SEC1_positive_normal_commit(self):
        self.assertEqual(self.commit("a.py", "print('ok')\n").returncode, 0)

    def test_SEC1_negative_env_file(self):
        self.assertNotEqual(self.commit(".env", "X=1\n").returncode, 0)

    def test_SEC1_negative_secret_in_code(self):
        fake = "api" + "_key = " + '"' + "abcdefghijklmnop" + "qrstuvwxyz0123" + '"\n'  # assembled so this file itself passes SEC-1
        self.assertNotEqual(self.commit("c.py", fake).returncode, 0)

    def test_BR6_negative_hook_blocks_push_to_main(self):
        """Covers: BR-7 (negative)"""
        self.commit("a.txt", "a", "chore: scaffold from KavoshStart v1.1.0")
        self.assertEqual(git(self.work, "push", "-q", "origin", "main", check=False).returncode, 0)  # initial scaffold
        self.commit("b.txt", "b")
        self.assertNotEqual(git(self.work, "push", "-q", "origin", "main", check=False).returncode, 0)

    def test_BR6_positive_feature_branch_push(self):
        self.commit("a.txt", "a")
        git(self.work, "switch", "-q", "-c", "feat/1-x")
        self.assertEqual(git(self.work, "push", "-q", "origin", "feat/1-x", check=False).returncode, 0)


if __name__ == "__main__":
    unittest.main()
