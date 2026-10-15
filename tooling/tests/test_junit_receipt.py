"""Actual assertion-outcome adapter tests; not string-presence conformance."""
from pathlib import Path
import sqlite3
import sys
import unittest
import xml.etree.ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from junit_receipt import assertion_outcomes


class JunitReceipt(unittest.TestCase):
    def test_ACC3_positive_report_preserves_actual_pass_fail_and_skip(self):
        raw = b'<testsuite tests="3" failures="1" skipped="1"><testcase classname="db" name="migrate"/><testcase name="read"><failure>missing column</failure></testcase><testcase name="ui"><skipped/></testcase></testsuite>'
        self.assertEqual([x["outcome"] for x in assertion_outcomes(raw)], ["pass", "fail", "skipped"])

    def test_ACC3_negative_empty_duplicate_hidden_failure_and_entity(self):
        for raw in (b'<testsuite/>', b'<testsuite><testcase name="x"/><testcase name="x"/></testsuite>',
                    b'<testsuite failures="1"><testcase name="x"/></testsuite>',
                    b'<!DOCTYPE testsuite [<!ENTITY x "fake">]><testsuite/>',
                    b'<testsuite><testcase/></testsuite>',
                    b'<testsuite><testcase name="x" status="invented"/></testsuite>'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                assertion_outcomes(raw)

    def test_ACC3_negative_disabled_test_is_not_passed(self):
        raw = b'<testsuite tests="1" skipped="1"><testcase name="x" status="notrun"/></testsuite>'
        self.assertEqual(assertion_outcomes(raw)[0]["outcome"], "skipped")

    def test_database_fixture_observes_actual_schema(self):
        """A real SQLite migration/read and a seeded obsolete-column defect, not a fake DB."""
        db = sqlite3.connect(":memory:")
        try:
            db.executescript("CREATE TABLE document(id INTEGER PRIMARY KEY, storage_key TEXT); INSERT INTO document VALUES(1, 'blob-1');")
            self.assertEqual(db.execute("SELECT storage_key FROM document WHERE id=1").fetchone()[0], "blob-1")
            with self.assertRaises(sqlite3.OperationalError):
                db.execute("SELECT file_data FROM document")
        finally:
            db.close()

    def test_database_fixture_failure_cannot_be_serialized_as_pass(self):
        """Exercise unittest -> JUnit -> assertion parser using an actual schema failure."""
        class SchemaCase(unittest.TestCase):
            def runTest(self):
                db = sqlite3.connect(":memory:")
                try:
                    db.execute("CREATE TABLE document(storage_key TEXT)")
                    db.execute("SELECT file_data FROM document")
                finally:
                    db.close()
        result = unittest.TestResult()
        SchemaCase().run(result)
        self.assertFalse(result.wasSuccessful())
        suite = ET.Element("testsuite", tests="1", errors=str(len(result.errors)))
        case = ET.SubElement(suite, "testcase", classname="db", name="read")
        for _, error in result.errors:
            ET.SubElement(case, "error").text = error
        self.assertEqual(assertion_outcomes(ET.tostring(suite))[0]["outcome"], "fail")


if __name__ == "__main__":
    unittest.main()
