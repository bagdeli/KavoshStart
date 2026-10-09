"""Offline tests for layer P checks added in #6 (tooling/src/governance.py)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import governance as g  # noqa: E402

SHA = "11bd71901bbe5b1630ceea73d27597364c9af683"
M = {"repo": "bagdeli/KavoshSMS", "kavoshStart": "v1.1.0"}
KAVOSH_OK = """jobs:
  kavosh:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-governance.yml@v1.1.0
    with:
      enforce: true
  main-guard:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-main-guard.yml@v1.1.0
  health:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-health.yml@v1.1.0
"""
CI_OK = "jobs:\n  required:\n    runs-on: ubuntu-latest\n"
REL_OK = "jobs:\n  release:\n    uses: bagdeli/KavoshStart/.github/workflows/kavosh-release.yml@v1.1.0\n"


def wf(kavosh=KAVOSH_OK, ci=CI_OK, rel=REL_OK):
    out = {".github/workflows/ci.yml": ci, ".github/workflows/release.yml": rel}
    if kavosh is not None:
        out[".github/workflows/kavosh.yml"] = kavosh
    return out


def fails(results):
    return [r for r in results if r[0] == "fail"]


class Pinning(unittest.TestCase):
    def test_SEC2_positive_sha_pins_and_exact_kavosh_tag(self):
        """Covers: REL-6 (positive)"""
        text = f"steps:\n  - uses: actions/checkout@{SHA} # v4.2.2\n" + KAVOSH_OK
        self.assertEqual(g.unpinned_uses({"a.yml": text}, M), [])

    def test_SEC2_positive_local_action(self):
        self.assertEqual(g.unpinned_uses({"a.yml": "  - uses: ./.github/actions/x\n"}, M), [])

    def test_SEC2_negative_mutable_docker_action(self):
        self.assertEqual(len(g.unpinned_uses({"a.yml": "  - uses: docker://alpine:3\n"}, M)), 1)

    def test_SEC2_positive_docker_action_digest(self):
        self.assertEqual(g.unpinned_uses({"a.yml": f"  - uses: docker://alpine@sha256:{'a' * 64}\n"}, M), [])

    def test_SEC2_negative_tag_or_branch_pin(self):
        for ref in ("actions/checkout@v4", "actions/checkout@main", "actions/checkout"):
            self.assertEqual(len(g.unpinned_uses({"a.yml": f"      - uses: {ref}\n"}, M)), 1, ref)

    def test_REL6_negative_floating_or_mismatched_kavosh_ref(self):
        for ver in ("v1", "main", "v1.0.0"):
            text = f"    uses: bagdeli/KavoshStart/.github/workflows/kavosh-health.yml@{ver}\n"
            self.assertEqual(len(g.unpinned_uses({"k.yml": text}, M)), 1, ver)


class Wiring(unittest.TestCase):
    def test_AI4_positive_wired(self):
        """Covers: CI-7, REL-4, REL-5 (positive)"""
        self.assertEqual(fails(g.wiring_problems(wf(), M)), [])

    def test_AI4_negative_kavosh_yml_deleted(self):
        self.assertEqual(len(fails(g.wiring_problems(wf(kavosh=None), M))), 1)

    def test_AI4_negative_guard_job_removed(self):
        text = KAVOSH_OK.replace("kavosh-main-guard.yml", "something-else.yml")
        self.assertTrue(any("kavosh-main-guard" in r[2] for r in fails(g.wiring_problems(wf(kavosh=text), M))))

    def test_AI4_negative_enforce_false_outside_adoption(self):
        text = KAVOSH_OK.replace("enforce: true", "enforce: false")
        self.assertEqual(len(fails(g.wiring_problems(wf(kavosh=text), M))), 1)
        self.assertEqual(len(fails(g.wiring_problems(wf(kavosh=text), dict(M, adoptionPhase=True)))), 1)

    def test_AI4_negative_consumer_cannot_spoof_kavoshstart_identity(self):
        own_workflows = wf(
            kavosh=KAVOSH_OK.replace("bagdeli/KavoshStart/.github/workflows/", "./.github/workflows/").replace("@v1.1.0", ""),
            rel=REL_OK.replace("bagdeli/KavoshStart/.github/workflows/", "./.github/workflows/").replace("@v1.1.0", ""))
        findings = fails(g.wiring_problems(own_workflows, M, actual_repo="bagdeli/Demo"))
        self.assertTrue(any("expected uses: bagdeli/KavoshStart" in r[3] for r in findings))

    def test_CI7_negative_no_required_job(self):
        self.assertTrue(any(r[1] == "CI-7" for r in fails(g.wiring_problems(wf(ci="jobs:\n  test:\n"), M))))

    def test_REL5_negative_ungated_release(self):
        """Covers: REL-4 (negative)"""
        rel = "jobs:\n  r:\n    steps:\n      - uses: googleapis/release-please-action@x\n"
        self.assertTrue(any(r[1] == "REL-5" for r in fails(g.wiring_problems(wf(rel=rel), M))))

    def test_AI4_positive_kavoshstart_uses_local_refs(self):
        own = {"repo": "bagdeli/KavoshStart", "kavoshStart": "self"}
        text = KAVOSH_OK.replace("bagdeli/KavoshStart/.github/workflows/", "./.github/workflows/").replace("@v1.1.0", "")
        rel = REL_OK.replace("bagdeli/KavoshStart/.github/workflows/", "./.github/workflows/").replace("@v1.1.0", "")
        self.assertEqual(fails(g.wiring_problems(wf(kavosh=text, rel=rel), own)), [])


class WorkflowTimeoutChecks(unittest.TestCase):
    def test_CI3_positive_reusable_caller_without_timeout(self):
        text = """on:
  workflow_call:
    inputs:
      runs-on:
        type: string
jobs:
  governance:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-governance.yml@v1.2.0
    with:
      runs-on: ${{ inputs.runs-on }}
"""
        self.assertEqual(g.jobs_without_timeout(text), [])

    def test_CI3_positive_local_job_with_timeout(self):
        text = """jobs:
  required:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - run: true
"""
        self.assertEqual(g.jobs_without_timeout(text), [])

    def test_CI3_negative_local_job_without_timeout(self):
        text = """jobs:
  required:
    runs-on: ubuntu-latest
    steps:
      - run: true
"""
        self.assertEqual(g.jobs_without_timeout(text), ["required"])

    def test_CI3_negative_mixed_only_flags_unbounded_local_job(self):
        text = """jobs:
  reusable:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-health.yml@v1.2.0
    with:
      runs-on: '["self-hosted","linux","x64","demo"]'
  bounded:
    runs-on: ubuntu-latest
    timeout-minutes: 5
    steps:
      - run: true
  unbounded:
    runs-on: ubuntu-latest
    steps:
      - run: true
"""
        self.assertEqual(g.jobs_without_timeout(text), ["unbounded"])


TEMPLATE_BODY = """Closes #1

## AI involvement
<!-- Agent and model, or "none". -->
- Agent / model:
- Human reviewed the full diff: [ ]

Co-Authored-By: <Agent> <noreply@example.com>

## Checklist
"""


class AiSection(unittest.TestCase):
    def body(self, agent, trailer=None):
        b = TEMPLATE_BODY.replace("- Agent / model:", f"- Agent / model: {agent}")
        if trailer is not None:
            b = b.replace("Co-Authored-By: <Agent> <noreply@example.com>", trailer)
        return b

    def test_PR4_negative_untouched_template(self):
        self.assertTrue(fails(g.ai_section_problems(TEMPLATE_BODY)))

    def test_PR4_negative_missing_section(self):
        self.assertTrue(fails(g.ai_section_problems("Closes #1\n")))

    def test_AI3_positive_agent_with_real_trailer(self):
        b = self.body("Claude Code (Opus 5.5)", "Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>")
        self.assertEqual(fails(g.ai_section_problems(b)), [])

    def test_AI3_negative_agent_with_placeholder_trailer(self):
        self.assertTrue(fails(g.ai_section_problems(self.body("Codex"))))

    def test_AI3_negative_agent_without_trailer(self):
        self.assertTrue(fails(g.ai_section_problems(self.body("Codex", ""))))

    def test_PR4_positive_none_without_trailer(self):
        self.assertEqual(fails(g.ai_section_problems(self.body("none", ""))), [])

    def test_AI3_negative_none_but_placeholder_left(self):
        self.assertTrue(fails(g.ai_section_problems(self.body("none"))))


class StandardPinIdentity(unittest.TestCase):
    def test_STD1_positive_consumer_exact_release_pin(self):
        """Covers: STD-1 (positive)"""
        self.assertEqual(fails(g.standard_pin_problems(
            {"repo": "bagdeli/KavoshERP", "kavoshStart": "v1.7.0"}, "bagdeli/KavoshERP")), [])

    def test_STD1_positive_canonical_standard_uses_self(self):
        self.assertEqual(fails(g.standard_pin_problems(
            {"repo": "bagdeli/KavoshStart", "kavoshStart": "self"}, "bagdeli/KavoshStart")), [])

    def test_STD1_negative_consumer_cannot_use_self(self):
        """Covers: STD-1 (negative)"""
        out = fails(g.standard_pin_problems(
            {"repo": "bagdeli/KavoshERP", "kavoshStart": "self"}, "bagdeli/KavoshERP"))
        self.assertTrue(any(r[1] == "STD-1" for r in out))

    def test_STD1_negative_standard_cannot_pin_its_previous_release(self):
        out = fails(g.standard_pin_problems(
            {"repo": "bagdeli/KavoshStart", "kavoshStart": "v1.7.0"}, "bagdeli/KavoshStart"))
        self.assertTrue(any(r[1] == "STD-1" for r in out))


class StandardLifecycle(unittest.TestCase):
    def test_STD2_positive_normal_operation(self):
        """Covers: STD-2 (positive)"""
        out = g.standard_lifecycle_problems({"tier": "T1"})
        self.assertEqual(fails(out), [])

    def test_STD2_negative_legacy_adoption_true(self):
        """Covers: STD-2 (negative)"""
        out = g.standard_lifecycle_problems({"tier": "T1", "adoptionPhase": True})
        self.assertTrue(any(r[1] == "STD-2" for r in fails(out)))

    def test_ACC1_positive_T2_continuous_required_profile(self):
        out = g.standard_lifecycle_problems({"tier": "T2", "acceptance": {"mode": "continuous"}})
        self.assertEqual([r for r in fails(out) if r[1] == "ACC-1"], [])

    def test_ACC1_negative_T2_without_continuous_profile(self):
        out = g.standard_lifecycle_problems({"tier": "T2"})
        self.assertTrue(any(r[1] == "ACC-1" for r in fails(out)))


class ContinuousAcceptance(unittest.TestCase):
    def setUp(self):
        self.original = g.acceptance_scope
        g.acceptance_scope = lambda: {
            "schemaVersion": 1,
            "targetRelease": "v0.1.0",
            "items": [{"id": "AC-001", "issue": 12, "owner": "bagdeli", "risk": "high",
                       "evidence": ["ci", "test"]}],
        }
        self.manifest = {"acceptance": {"mode": "continuous"}}

    def tearDown(self):
        g.acceptance_scope = self.original

    def test_ACC1_positive_valid_scope_and_pr_mapping(self):
        self.assertEqual(fails(g.acceptance_scope_problems(self.manifest)), [])
        body = "## Acceptance mapping\n- AC-001\n"
        self.assertEqual(fails(g.acceptance_mapping_problems(self.manifest, body)), [])

    def test_ACC1_negative_unknown_missing_and_false_status_fields(self):
        self.assertTrue(fails(g.acceptance_mapping_problems(self.manifest, "## Acceptance mapping\n- AC-999\n")))
        self.assertTrue(fails(g.acceptance_mapping_problems(self.manifest, "## What and why\nx\n")))
        g.acceptance_scope = lambda: {
            "schemaVersion": 1, "targetRelease": "v0.1.0",
            "items": [{"id": "AC-001", "issue": 12, "owner": "bagdeli", "risk": "high",
                       "evidence": ["ci"], "status": "accepted"}],
        }
        out = fails(g.acceptance_scope_problems(self.manifest))
        self.assertTrue(out)
        self.assertIn("live status", out[0][3])
        self.assertIn("requires test evidence", out[0][3])


class Classification(unittest.TestCase):
    def test_SRC5_library_classifies_at_least_T1(self):
        m = {"runtime": "none", "projectKind": "library", "ui": {"kind": "none"},
             "data": {"sensitivity": "none", "regulatedIntegrations": [], "multiTenant": False},
             "size": {"domains": 1, "lifetime": "weeks", "parallelStreams": 1}, "users": {"audience": "internal", "scale": "1-10"}}
        self.assertEqual(g.expected_tier(m), "T1")
        self.assertEqual(g.expected_tier(dict(m, projectKind="tool")), "T0")


if __name__ == "__main__":
    unittest.main()
