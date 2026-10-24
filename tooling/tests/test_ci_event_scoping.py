"""Bounded regression for label-trigger cost and required-check/permission integrity."""
import re
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import yaml

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import ci_scope


def expression(source, context):
    """Evaluate this workflow's boolean/string subset with synthetic GitHub context."""
    source = source.strip()
    if source.startswith('${{'):
        source = source[3:-2].strip()
    source = source.replace('&&', ' and ').replace('||', ' or ')
    source = re.sub(r'!(?!=)', 'not ', source)
    source = re.sub(r'\btrue\b', 'True', source)
    source = re.sub(r'\bfalse\b', 'False', source)
    return eval(source, {'__builtins__': {}}, {'github': context})


def context(event='pull_request', action='synchronize', label='', draft=False, fork=False):
    return NS(event_name=event, repository='demo/Example', ref='refs/heads/main',
              event=NS(action=action, label=NS(name=label), pull_request=NS(
                  number=42, draft=draft, head=NS(repo=NS(
                      full_name='other/Example' if fork else 'demo/Example')))))


def workflow(private=False, self_hosted=False):
    text = (ROOT / 'templates/common/.github/workflows/ci.yml').read_text()
    values = {'PRIVATE_HOSTED': str(private).lower(), 'SELF_HOSTED': str(self_hosted).lower(),
              'RUNS_ON_YAML': '[ubuntu-latest]', 'CI_TIMEOUT': '10', 'TIER': 'T2'}
    for name, value in values.items():
        text = text.replace('{{' + name + '}}', value)
    return yaml.safe_load(text)


def group(source, ctx):
    return re.sub(r'\$\{\{(.*?)\}\}', lambda match: str(expression(match.group(1), ctx)), source)


class CIEventScopingTests(unittest.TestCase):
    def test_labels_cannot_start_jobs_or_replace_required_or_cancel_real_ci(self):
        for private, self_hosted in [(False, False), (False, True), (True, False)]:
            data = workflow(private, self_hosted)
            job = data['jobs']['required']
            concurrent = data['concurrency']
            for draft in (False, True):
                for fork in (False, True):
                    for label in ('unrelated', 'ci:full'):
                        ctx = context(action='labeled', label=label, draft=draft, fork=fork)
                        with self.subTest(private=private, self_hosted=self_hosted,
                                          draft=draft, fork=fork, label=label):
                            expected = label == 'ci:full' and not private and (not self_hosted or not fork)
                            self.assertEqual(bool(expression(job['if'], ctx)), expected)
                            if label != 'ci:full':
                                self.assertEqual(expression(job['name'], ctx), 'ci-label-noop')
                                self.assertFalse(expression(concurrent['cancel-in-progress'], ctx))
                                self.assertNotEqual(group(concurrent['group'], ctx),
                                                    group(concurrent['group'], context()))
                            else:
                                self.assertEqual(expression(job['name'], ctx), 'required')

    def test_real_events_keep_required_identity_and_existing_consent_fork_guards(self):
        for private, self_hosted in [(False, False), (False, True), (True, False)]:
            data = workflow(private, self_hosted)
            job = data['jobs']['required']
            for event in ('push', 'workflow_dispatch', 'pull_request'):
                for draft in (False, True):
                    for fork in (False, True):
                        ctx = context(event=event, draft=draft, fork=fork)
                        expected = (event == 'workflow_dispatch' or (not private and (
                            event == 'push' or (not draft and (not self_hosted or not fork)))))
                        with self.subTest(event=event, private=private, self_hosted=self_hosted,
                                          draft=draft, fork=fork):
                            self.assertEqual(bool(expression(job['if'], ctx)), expected)
                            self.assertEqual(expression(job['name'], ctx), 'required')
        source = (ROOT / 'templates/common/.github/workflows/ci.yml').read_text()
        self.assertIn('NOT proof of prior human consent', source)
        self.assertNotIn('one-run authorization:', source)

    def test_both_governance_callers_keep_only_job_owned_writes_and_required_reads(self):
        for path in ('.github/workflows/kavosh.yml', 'templates/common/.github/workflows/kavosh.yml'):
            data = yaml.safe_load((ROOT / path).read_text())
            events = data.get('on', data.get(True))
            self.assertNotIn('labeled', events['pull_request']['types'])
            self.assertIn('edited', events['pull_request']['types'])
            self.assertTrue(all(value == 'read' for value in data['permissions'].values()))
            for job_id, workflow_name, write in (
                ('kavosh', 'governance', 'pull-requests'),
                ('main-guard', 'main-guard', 'issues'), ('health', 'health', 'issues')
            ):
                grants = data['jobs'][job_id]['permissions']
                self.assertEqual({name for name, mode in grants.items() if mode == 'write'}, {write})
                callee = yaml.safe_load((ROOT / f'.github/workflows/kavosh-{workflow_name}.yml').read_text())
                for name, mode in callee['permissions'].items():
                    self.assertIn(grants.get(name), ('read', 'write') if mode == 'read' else ('write',))
                self.assertEqual(grants['actions'], 'read')


class StandardVerificationScope(unittest.TestCase):
    def test_docs_only_keeps_core_but_not_external_fixtures(self):
        full, _ = ci_scope.choose_full("pull_request", ["README.md", "standard/05-ai-agents.md"])
        self.assertFalse(full)
        for paths in (None, [], ["docs/note.md", "tooling/src/governance.py"],
                      [".github/workflows/self-check.yml"], ["tooling/conformance-requirements.txt"],
                      ["templates/common/AGENTS.md"], ["docs/../secret.md"], ["unknown.md"]):
            self.assertTrue(ci_scope.choose_full("pull_request", paths)[0], paths)

    def test_release_main_and_unknown_context_keep_full_verification(self):
        for event in ("push", "unrecognized"):
            self.assertTrue(ci_scope.choose_full(event, ["README.md"])[0])
        self.assertTrue(ci_scope.choose_full("workflow_dispatch", requested=True)[0])
        self.assertTrue(ci_scope.choose_full("workflow_dispatch", release_pr=True)[0])
        self.assertFalse(ci_scope.choose_full("workflow_dispatch")[0])

    def test_workflow_core_is_unconditional_and_full_failure_not_masked(self):
        data = yaml.safe_load((ROOT / ".github/workflows/self-check.yml").read_text())
        job = data["jobs"]["required"]
        self.assertEqual(job["name"], "required")
        steps = job["steps"]
        core = next(x for x in steps if "make check" in x.get("run", ""))
        self.assertNotIn("if", core)
        for step in steps:
            self.assertNotIn("continue-on-error", step)
        for name in ("Exercise the pinned Node setup action", "Prepare isolated cross-domain fixture dependencies",
                     "Exercise real capability boundaries and seeded regressions",
                     "Verify live artifact transport and tamper rejection"):
            step = next(x for x in steps if x.get("name") == name)
            self.assertEqual(step["if"], "steps.scope.outputs.full == 'true'")
        upload = next(x for x in steps if x.get("id") == "conformance-artifact")
        self.assertIn("always()", upload["if"])
        self.assertIn("steps.conformance.outcome != 'skipped'", upload["if"])

    def test_exact_diff_and_unavailable_diff_are_distinguished(self):
        with tempfile.TemporaryDirectory() as temp:
            def git(*args):
                return subprocess.check_output(["git", *args], cwd=temp, stderr=subprocess.DEVNULL).decode().strip()
            git("init", "-q")
            git("config", "user.name", "Example")
            git("config", "user.email", "example@invalid.test")
            Path(temp, "README.md").write_text("before")
            git("add", "."); git("commit", "-qm", "base")
            base = git("rev-parse", "HEAD")
            Path(temp, "README.md").write_text("after")
            git("add", "."); git("commit", "-qm", "doc")
            self.assertEqual(ci_scope.changed_paths(base, temp), ["README.md"])
            self.assertIsNone(ci_scope.changed_paths("x" * 40, temp))
            self.assertIsNone(ci_scope.changed_paths("0" * 40, temp))

    def test_release_dispatch_rejects_wrong_head_and_reports_core_not_run_truthfully(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            event = root / "event.json"
            env = dict(os.environ, GITHUB_EVENT_NAME="workflow_dispatch", GITHUB_EVENT_PATH=str(event),
                       GITHUB_OUTPUT=str(root / "out"), GITHUB_STEP_SUMMARY=str(root / "summary"),
                       GITHUB_SHA="a" * 40)
            event.write_text(json.dumps({"inputs": {"pr-number": "1", "expected-head": "b" * 40}}))
            cmd = [sys.executable, str(ROOT / "tooling/ci_scope.py")]
            self.assertNotEqual(subprocess.run(cmd, env=env, capture_output=True).returncode, 0)
            event.write_text(json.dumps({"inputs": {"ci-full": "false"}}))
            run = subprocess.run(cmd, env=env, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("full=false", (root / "out").read_text())
            self.assertIn("NOT_RUN", (root / "summary").read_text())
            event.write_text(json.dumps({"inputs": {"pr-number": "1", "expected-head": "a" * 40}}))
            run = subprocess.run(cmd, env=env, capture_output=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertIn("full=true", (root / "out").read_text())


    def test_unreadable_dispatch_event_cannot_silently_select_core_only(self):
        with tempfile.TemporaryDirectory() as temp:
            event = Path(temp, "event.json")
            output = Path(temp, "output")
            env = dict(os.environ, GITHUB_EVENT_NAME="workflow_dispatch", GITHUB_EVENT_PATH=str(event),
                       GITHUB_OUTPUT=str(output))
            for payload in (None, "{broken", "[]"):
                if payload is not None:
                    event.write_text(payload)
                run = subprocess.run([sys.executable, str(ROOT / "tooling/ci_scope.py")],
                                     env=env, capture_output=True)
                self.assertNotEqual(run.returncode, 0)
                self.assertFalse(output.exists(), "unknown input must not emit full=false")


if __name__ == '__main__':
    unittest.main()
