import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import sync_pins


class SyncPins(unittest.TestCase):
    def test_updates_matching_sha_and_version_comment(self):
        source = "- uses: actions/checkout@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # v7.0.1\n"
        pins = sync_pins.extract_pins(source)
        target = "- uses: actions/checkout@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb # v4.2.2\n"
        self.assertEqual(
            sync_pins.synchronize_text(target, pins),
            "- uses: actions/checkout@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # v7.0.1\n",
        )

    def test_leaves_unrelated_and_local_references_unchanged(self):
        source = "- uses: actions/checkout@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # v7.0.1\n"
        pins = sync_pins.extract_pins(source)
        target = (
            "- uses: actions/checkout@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb # v4.2.2\n"
            "- uses: actions/setup-python@v5\n"
            "- uses: ./local-action\n"
        )
        updated = sync_pins.synchronize_text(target, pins)
        self.assertIn("actions/setup-python@v5", updated)
        self.assertIn("./local-action", updated)
        self.assertIn("actions/checkout@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # v7.0.1", updated)

    def test_rejects_conflicting_source_pins(self):
        source = (
            "- uses: actions/checkout@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # v4\n"
            "- uses: actions/checkout@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb # v5\n"
        )
        with self.assertRaisesRegex(ValueError, "conflicting pins"):
            sync_pins.extract_pins(source, "workflow.yml")

    def test_check_reports_drift_and_write_mode_repairs_it(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root / ".github" / "workflows").mkdir(parents=True)
            (root / "tooling" / "templates").mkdir(parents=True)
            (root / "templates").mkdir()
            (root / ".github" / "workflows" / "ci.yml").write_text(
                "- uses: actions/checkout@aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa # v7\n",
                encoding="utf-8",
            )
            target = root / "templates" / "ci.yml"
            target.write_text(
                "- uses: actions/checkout@bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb # v4\n",
                encoding="utf-8",
            )
            self.assertEqual(sync_pins.sync(root, check=True), ["templates/ci.yml"])
            self.assertEqual(sync_pins.sync(root), ["templates/ci.yml"])
            self.assertEqual(sync_pins.sync(root, check=True), [])


if __name__ == "__main__":
    unittest.main()
