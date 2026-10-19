"""Minimal positive/negative proof for an optional source-owned one-head preflight."""
import contextlib
import io
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
import check_migration_revision as m  # noqa: E402


class MigrationRevisionCheck(unittest.TestCase):
    def test_positive_single_source_and_applied_revision(self):
        self.assertEqual(m.parse_single_revision("abc123 (head)\n"), "abc123")
        self.assertEqual(m.parse_single_revision("abc123\n"), "abc123")
        with mock.patch.object(m, "observed_revision", side_effect=["abc123", "abc123"]):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(m.main(["--source-command", '["alembic","heads"]',
                                         "--applied-command", '["alembic","current"]']), 0)
            self.assertIn("scope=source-and-applied", output.getvalue())

    def test_negative_multiple_heads_missing_invalid_or_stale_revision(self):
        for bad in ("abc123 (head)\ndef456 (head)", "", "head",
                    "debug line\nabc123", "abc123 other", "broken revision"):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    m.parse_single_revision(bad)
        with mock.patch.object(m, "observed_revision", side_effect=["abc123", "def456"]):
            with contextlib.redirect_stderr(io.StringIO()) as error:
                self.assertEqual(m.main(["--source-command", '["alembic","heads"]',
                                         "--applied-command", '["alembic","current"]']), 1)
                self.assertNotIn("abc123", error.getvalue())

    def test_negative_commands_are_arg_arrays_not_untrusted_shell_text(self):
        for raw in ("", "alembic heads", '["alembic",null]', "[]", '[""]',
                    '["bash","-c","echo abc123"]', '["alembic","upgrade","head"]',
                    '["alembic","stamp","head"]', '["alembic","-c","../secret.ini","heads"]'):
            with self.subTest(raw=raw):
                with self.assertRaises(ValueError):
                    m.argv(raw)
        self.assertEqual(m.argv('["alembic","heads"]', "heads"), ["alembic", "heads"])
        self.assertEqual(m.argv('["alembic","current"]', "current"), ["alembic", "current"])

    def test_negative_nonexecuted_or_bad_command_is_not_pass(self):
        with mock.patch.object(m.subprocess, "run", side_effect=FileNotFoundError):
            with self.assertRaises(ValueError):
                m.observed_revision(["not-installed-migration-tool"])
        with mock.patch.object(m, "observed_revision", side_effect=ValueError):
            with contextlib.redirect_stderr(io.StringIO()):
                self.assertEqual(m.main(["--source-command", '["alembic","heads"]']), 1)


if __name__ == "__main__":
    unittest.main()
