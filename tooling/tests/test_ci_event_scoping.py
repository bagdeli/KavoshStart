"""Bounded regression for label-trigger cost and required-check/permission integrity."""
import re
import unittest
from pathlib import Path
from types import SimpleNamespace as NS

import yaml

ROOT = Path(__file__).resolve().parents[2]


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


if __name__ == '__main__':
    unittest.main()
