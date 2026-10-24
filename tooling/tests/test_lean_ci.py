"""Keep default source CI small; heavy conformance is explicitly requested."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class LeanCIPolicy(unittest.TestCase):
    def test_source_contract_runs_for_every_required_job(self):
        ci = (ROOT / ".github/workflows/self-check.yml").read_text(encoding="utf-8")
        self.assertIn("      - run: pip install --quiet pyyaml && make check", ci)
        self.assertIn("github.event_name == 'pull_request' && !github.event.pull_request.draft", ci)
        self.assertIn("    name: required", ci)

    def test_heavy_steps_only_run_when_owner_requests_full_mode(self):
        ci = (ROOT / ".github/workflows/self-check.yml").read_text(encoding="utf-8")
        for name in ("Exercise the pinned Node setup action",
                     "Prepare isolated cross-domain fixture dependencies",
                     "Exercise real capability boundaries and seeded regressions",
                     "Verify live artifact transport and tamper rejection"):
            with self.subTest(step=name):
                self.assertIn("      - name: " + name + "\n"
                              "        if: ${{ github.event_name == 'workflow_dispatch' && inputs.ci-full }}\n", ci)

    def test_artifact_outputs_are_not_created_for_default_pr(self):
        ci = (ROOT / ".github/workflows/self-check.yml").read_text(encoding="utf-8")
        self.assertIn("always() && github.event_name == 'workflow_dispatch' && inputs.ci-full", ci)
        self.assertEqual(ci.count("github.event_name == 'workflow_dispatch' && inputs.ci-full"
                                  " && github.repository == 'bagdeli/KavoshStart'"), 2)


if __name__ == "__main__":
    unittest.main()
