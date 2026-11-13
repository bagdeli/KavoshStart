"""Documentation-contract regressions; NOT agent behavior or product acceptance tests."""
import base64
import json
import os
import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def rows(text, prefix="G"):
    """Read the bounded questionnaire/project table, not arbitrary owner decisions."""
    result = []
    for line in text.splitlines():
        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if cells and re.match(rf"^{prefix}[0-9]+(?:\s|$)", cells[0]):
            result.append(cells)
    return result


class IntakeArchitectureContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.questionnaire = (ROOT / "intake/QUESTIONNAIRE.md").read_text(encoding="utf-8")
        cls.protocol = (ROOT / "START.md").read_text(encoding="utf-8")
        cls.project = (ROOT / "templates/common/PROJECT.md").read_text(encoding="utf-8")
        cls.spec = (ROOT / "templates/tier/T1/specs/_template/spec.md").read_text(encoding="utf-8")

    def test_all_architecture_subjects_have_unique_required_prompts(self):
        table = rows(self.questionnaire)
        self.assertEqual([r[0] for r in table], [f"G{i}" for i in range(1, 11)])
        for r in table:
            self.assertEqual(len(r), 5)
            self.assertEqual(r[1], "R")
            self.assertIn("PROJECT.md#architecture-decisions", r[3])
            self.assertTrue(r[2] and r[4])

    def test_project_template_reuses_same_subjects_and_existing_anchor(self):
        ids = [r[0].split()[0] for r in rows(self.project)]
        self.assertEqual(ids, [r[0] for r in rows(self.questionnaire)])
        self.assertIn('id="architecture-decisions"', self.project)
        self.assertIn("Do not add unsupported manifest keys", self.protocol)

    def test_licensing_is_explicit_and_not_inferred_from_internal_use(self):
        licence = rows(self.questionnaire)[0]
        self.assertIn("لایسنس", licence[2])
        self.assertIn("regardless of internal/public audience", licence[4])
        self.assertIn("Product licensing is distinct", licence[4])
        self.assertIn("including product licensing", self.protocol)

    def test_identity_data_network_and_delivery_are_not_omitted(self):
        table = {r[0]: r for r in rows(self.questionnaire)}
        for key, expected in {"G2": "authorization", "G3": "authoritative", "G4": "offline",
                              "G5": "recovery", "G6": "engineering", "G7": "recorded custom UI contract",
                              "G8": "observability", "G9": "assertion", "G10": "Explicit owner choice G10"}.items():
            # G9 asks for evidence planning; exact assertion detail belongs to the Spec.
            value = table[key][4] + (self.spec if key == "G9" else "")
            self.assertIn(expected, value, key)
        self.assertIn("selected design system package", table["G7"][4])

    def test_optional_main_branch_protection_choice(self):
        item = next(r for r in rows(self.questionnaire) if r[0] == "G10")
        self.assertEqual(item[1], "R")
        self.assertIn("بله یا خیر", item[2])
        self.assertIn("BR-6/BR-7/PR-7", item[4])
        self.assertIn("G10 — محافظت سروری", self.project)
        self.assertIn("G10=NO or unresolved never creates/changes rulesets", self.protocol)
        self.assertIn("--main-ruleset --apply", self.protocol)
        bootstrap = (ROOT / "scripts/bootstrap-repo.sh").read_text(encoding="utf-8")
        self.assertIn("--main-ruleset)", bootstrap)
        self.assertIn("RULES_MODE=both", bootstrap)
        self.assertIn('if [ "$RULES_MODE" != main ]; then', bootstrap)
        self.assertIn("--main-ruleset cannot be combined with --milestone", bootstrap)
        self.assertIn('if [ "$RULES_MODE" = main ] && [ "$f" = tags ]', bootstrap)

    def _run_bootstrap_with_mock_github(self, *options, existing="[]", readback=None, runner="none", protected="false"):
        """Exercise the real bootstrap shell with a non-networking gh stub."""
        with tempfile.TemporaryDirectory() as tmp:
            work = Path(tmp)
            calls_file = work / "gh-requests"
            gh = work / "gh"
            payload = base64.b64encode(json.dumps({"ci": {"runner": runner}}).encode("utf-8")).decode("ascii")
            baseline = json.loads((ROOT / "templates/rulesets" / ("main-local-only.json" if runner == "none" else "main.json")).read_text(encoding="utf-8"))
            baseline["id"] = 471
            gh.write_text("""#!/bin/sh
printf '%s\\n' "$*" >> "$GH_CALLS"
case "$*" in
  *contents/kavosh.project.json*) printf '%s\\n' '__MANIFEST__' ;;
  *" -X POST "*) printf '%s\\n' '{"id":471}' ;;
  *rulesets/471*) printf '%s\\n' "$GH_RULESET_DETAIL" ;;
  *rules/branches/main*) printf '%s\\n' "$GH_EXISTING_MAIN_RULES" ;;
  *branches/main*) printf '%s\\n' "$GH_MAIN_PROTECTED" ;;
esac
""".replace("__MANIFEST__", payload), encoding="utf-8")
            gh.chmod(0o755)
            environment = os.environ.copy()
            environment.update({
                "PATH": str(work) + os.pathsep + environment.get("PATH", ""),
                "GH_CALLS": str(calls_file),
                "GH_EXISTING_MAIN_RULES": existing,
                "GH_MAIN_PROTECTED": protected,
                "GH_RULESET_DETAIL": readback if readback is not None else json.dumps(baseline),
            })
            run = subprocess.run(
                ["bash", str(ROOT / "scripts/bootstrap-repo.sh"), "example/demo", *options],
                capture_output=True, text=True, env=environment, timeout=15, check=False,
            )
            calls = calls_file.read_text(encoding="utf-8").splitlines() if calls_file.exists() else []
            return run, calls

    def test_main_only_dry_run_does_not_call_mutating_api(self):
        run, calls = self._run_bootstrap_with_mock_github("--main-ruleset")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("main-local-only.json", run.stdout)
        self.assertNotIn("tags.json", run.stdout)
        self.assertFalse(any("-X POST" in call or "-X PATCH" in call for call in calls), calls)

    def test_main_only_apply_changes_only_main_ruleset_and_reads_back(self):
        run, calls = self._run_bootstrap_with_mock_github("--main-ruleset", "--apply")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("created and read back", run.stdout)
        self.assertTrue(any("-X POST repos/example/demo/rulesets" in call for call in calls), calls)
        self.assertTrue(any("rulesets/471" in call for call in calls), calls)
        self.assertFalse(any("tags.json" in call or "milestones" in call or
                             "permissions/workflow" in call or " -X PATCH " in call
                             for call in calls), calls)

    def test_main_only_ci_ruleset_verifies_required_status_contexts(self):
        run, calls = self._run_bootstrap_with_mock_github("--main-ruleset", "--apply", runner="self-hosted")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertIn("created and read back", run.stdout)
        self.assertTrue(any("main.json" in call for call in calls), calls)

    def test_main_only_ci_ruleset_rejects_missing_status_context(self):
        detail = json.loads((ROOT / "templates/rulesets/main.json").read_text(encoding="utf-8"))
        detail["id"] = 471
        detail["rules"] = [r for r in detail["rules"] if r["type"] != "required_status_checks"]
        run, calls = self._run_bootstrap_with_mock_github(
            "--main-ruleset", "--apply", runner="self-hosted", readback=json.dumps(detail)
        )
        self.assertNotEqual(run.returncode, 0)
        self.assertNotIn("created and read back", run.stdout)
        self.assertTrue(any("rulesets/471" in call for call in calls), calls)

    def test_main_only_apply_refuses_existing_branch_ruleset(self):
        existing = '[{"ruleset_id":11,"type":"pull_request"}]'
        run, calls = self._run_bootstrap_with_mock_github("--main-ruleset", "--apply", existing=existing)
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("no duplicate", run.stderr)
        self.assertTrue(any("rules/branches/main" in call for call in calls), calls)
        self.assertFalse(any("-X POST" in call for call in calls), calls)

    def test_main_only_ignores_unrelated_branch_rules(self):
        # Only effective rules for main are queried. A rule targeting an unrelated
        # branch is absent from that endpoint and must not block main protection.
        run, calls = self._run_bootstrap_with_mock_github("--main-ruleset", "--apply", existing="[]")
        self.assertEqual(run.returncode, 0, run.stderr)
        self.assertFalse(any("repos/example/demo/rulesets " in call and "-X POST" not in call for call in calls))
        self.assertTrue(any("rules/branches/main" in call for call in calls))

    def test_main_only_refuses_existing_classic_protection(self):
        run, calls = self._run_bootstrap_with_mock_github("--main-ruleset", "--apply", protected="true")
        self.assertNotEqual(run.returncode, 0)
        self.assertIn("no duplicate", run.stderr)
        self.assertFalse(any("-X POST" in call for call in calls), calls)

    def test_main_only_rejects_incorrect_github_readback(self):
        readback = '{"id":471,"target":"tag","enforcement":"active","conditions":{"ref_name":{"include":["~DEFAULT_BRANCH"]}},"rules":[]}'
        run, calls = self._run_bootstrap_with_mock_github("--main-ruleset", "--apply", readback=readback)
        self.assertNotEqual(run.returncode, 0)
        self.assertNotIn("created and read back", run.stdout)
        self.assertTrue(any("rulesets/471" in call for call in calls), calls)

    def test_main_only_rejects_broader_flags_without_mutation(self):
        for flags in (
            ("--main-ruleset", "--rulesets", "--apply"),
            ("--main-ruleset", "--milestone", "Example", "--apply"),
            ("--main-ruleset", "--team-process", "--apply"),
        ):
            with self.subTest(flags=flags):
                run, calls = self._run_bootstrap_with_mock_github(*flags)
                self.assertNotEqual(run.returncode, 0)
                self.assertEqual(calls, [])

    def test_no_ui_is_a_real_not_needed_path(self):
        ui = next(r for r in rows(self.questionnaire) if r[0] == "G7")[4]
        self.assertIn("ui.kind=none", ui)
        self.assertIn("do not create UI tasks", ui)

    def test_not_needed_does_not_multiply_work_or_receipts(self):
        self.assertIn("creates no implementation, test, evidence receipt or separate Issue", self.questionnaire)
        self.assertIn("not one PR per source requirement or intake answer", self.protocol)

    def test_inheritance_and_repeated_sessions_reuse_answers(self):
        self.assertIn("inherited` with an explicit approved profile/version/reference", self.questionnaire)
        self.assertIn("ask again only for a missing or materially changed decision", self.protocol)
        self.assertIn("Reopen only decisions affected by this scope", self.protocol)

    def test_unresolved_choices_block_only_dependent_implementation(self):
        self.assertIn("Block only dependent implementation", self.questionnaire)
        self.assertIn("unrelated authorized work may continue", self.protocol)
        self.assertIn("dependent work:", self.spec)
        self.assertIn("needed before:", self.spec)
        self.assertIn("Required identity/scaffold inputs must be known", self.protocol)

    def test_vague_answer_is_never_silent_approval(self):
        self.assertNotIn('If the owner answers vaguely ("معمولی", "بعداً"), use the default', self.questionnaire)
        self.assertIn("Suggestions are not accepted defaults", self.protocol)
        self.assertIn("Never convert vague answers", self.questionnaire)

    def test_receipt_rollout_is_planned_without_fabricating_a_producer(self):
        self.assertIn("real availability of separate evidence/decision Apps", self.protocol)
        self.assertIn("Missing elected producers block only the elected protocol", self.protocol)
        self.assertIn("کار/Workflow/credential/receipt/Issue جدید ایجاد نمی‌کند", self.questionnaire)
        self.assertNotIn("unless the owner explicitly chooses a documented phased adoption", self.protocol)

    def test_runner_instruction_distinguishes_self_hosted_from_hosted_private_quota(self):
        self.assertIn("self-hosted runner on an existing accepted, least-privileged host", self.protocol)
        self.assertIn("without a second machine or mandatory trust ADR", self.protocol)
        self.assertIn("explicit authorization", self.protocol)
        self.assertNotIn("Self-hosted is not an option for private repositories", self.protocol)

    def test_spec_links_evidence_without_manufacturing_acceptance(self):
        self.assertIn("## Evidence plan", self.spec)
        self.assertIn("Given … when … then …", self.spec)
        self.assertIn("not a pass, a receipt or human approval", self.spec)
        self.assertIn("Reuse shared evidence with traceability", self.spec)

    def test_planning_is_not_permission_or_a_new_product_audit(self):
        self.assertIn("not execution/credential/Production authorization", self.questionnaire)
        self.assertIn("do not authorize work on that product", self.protocol)
        self.assertIn("Never use `--admin`", self.protocol)
        self.assertIn("Production data changes and credentials require direct human authorization", self.protocol)


if __name__ == "__main__":
    unittest.main()
