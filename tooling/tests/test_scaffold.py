import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import scaffold  # noqa: E402


class StandardPin(unittest.TestCase):
    def test_consumer_exact_release_pin_is_valid(self):
        scaffold.validate_standard_pin({"repo": "bagdeli/KavoshERP", "kavoshStart": "v1.7.0"})

    def test_canonical_standard_self_identity_is_valid(self):
        scaffold.validate_standard_pin({"repo": "bagdeli/KavoshStart", "kavoshStart": "self"})

    def test_consumer_self_identity_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "reserved"):
            scaffold.validate_standard_pin({"repo": "bagdeli/KavoshERP", "kavoshStart": "self"})

    def test_unresolved_or_floating_consumer_pin_is_rejected(self):
        for pin in ("vX.Y.Z", "v1", "main", "1.7.0", None):
            with self.subTest(pin=pin):
                with self.assertRaisesRegex(SystemExit, "exact release tag"):
                    scaffold.validate_standard_pin({"repo": "bagdeli/KavoshERP", "kavoshStart": pin})

    def test_package_job_follows_release_artifact_deploy_outcome(self):
        base = {
            "name": "Example",
            "repo": "bagdeli/Example",
            "summary": "Example project for scaffold adapter tests",
            "tier": "T1",
            "runtime": "server",
            "kavoshStart": "v2.0.5",
            "ui": {"kind": "none"},
            "deploy": {"method": "release-artifact"},
            "ci": {"runner": "github-hosted", "monthlyMinutesBudget": 0},
        }
        self.assertEqual(scaffold.values(base)["PACKAGE"], "true")
        base["deploy"]["method"] = "pull-build"
        base["runtime"] = "desktop"
        self.assertEqual(scaffold.values(base)["PACKAGE"], "false")

    def test_standard_version_pin_is_rejected(self):
        with self.assertRaisesRegex(SystemExit, "must use kavoshStart 'self'"):
            scaffold.validate_standard_pin({"repo": "bagdeli/KavoshStart", "kavoshStart": "v1.7.0"})


if __name__ == "__main__":
    unittest.main()
