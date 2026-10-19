"""Focused, fully synthetic SEC-5 public source privacy screening regressions."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import public_source_guard as pg  # noqa: E402


class PublicSourcePrivacy(unittest.TestCase):
    def test_SEC5_positive_public_identity_and_fictional_examples(self):
        """Covers: SEC-5 (positive); common upstream links and fake fixture names stay valid."""
        safe = "bagdeli/KavoshStart bagdeli/Example bagdeli/Demo"
        self.assertEqual(pg.categories(safe), set())
        self.assertEqual(pg.categories("a reusable CI template with no consumer details"), set())

    def test_SEC5_negative_private_like_repository_and_brand_name(self):
        """Covers: SEC-5 (negative); no hardcoded actual private project names here."""
        unexpected = "bagdeli/" + "FictionalUnlistedService"
        self.assertIn("unknown-owner-repository", pg.categories(unexpected))
        brand = "Kavosh" + "FictionalService"
        self.assertIn("specific-project-identifier", pg.categories(brand))

    def test_SEC5_negative_nonpublic_host_or_owner_held_literal(self):
        domain = "candidate." + "internal"
        self.assertIn("internal-host", pg.categories(domain))
        literal = "unique-" + "fixture-hidden"
        self.assertIn("external-private-identifier",
                      pg.categories("message " + literal, (literal,)))

    def test_SEC5_negative_rejected_text_not_echoed_to_public_log(self):
        example = "bagdeli/" + "FictionalNeverShare"
        with mock.patch.object(sys, "stdin", io.TextIOWrapper(io.BytesIO(example.encode()))):
            stderr, stdout = io.StringIO(), io.StringIO()
            with contextlib.redirect_stderr(stderr), contextlib.redirect_stdout(stdout):
                result = pg.main(["--stdin"])
        self.assertEqual(result, 1)
        self.assertNotIn(example, stderr.getvalue() + stdout.getvalue())

    def test_SEC5_negative_private_inventory_inside_public_checkout_not_accepted(self):
        self.assertRaises(ValueError, pg.local_literals, str(ROOT / "private-patterns.txt"))


if __name__ == "__main__":
    unittest.main()
