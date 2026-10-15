"""Real ZIP/JUnit/SQLite -> evidence adapter -> shared verifier integration.

Only GitHub identities and API transport are synthetic. No live App is installed
or impersonated; no result here is product acceptance or a human decision.
"""
import copy
from datetime import timedelta
import hashlib
import io
import json
from pathlib import Path
import sqlite3
import stat
import sys
import unittest
import warnings
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import artifact_receipt as ar
from test_receipts import Fixture, SOURCE
import receipts as rv


def archive_of(report, entries=None):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.writestr("reports/results.xml", report)
        for name, raw in entries or []:
            z.writestr(name, raw)
    return stream.getvalue()


def digest(raw):
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def schema_report(broken=False):
    db = sqlite3.connect(":memory:")
    try:
        db.execute("CREATE TABLE document(storage_key TEXT NOT NULL)")
        db.execute("INSERT INTO document VALUES('file-1')")
        try:
            value = db.execute("SELECT file_data FROM document" if broken else
                               "SELECT storage_key FROM document").fetchone()[0]
            if value != "file-1":
                raise AssertionError("wrong stored key")
            detail = ""
        except (sqlite3.OperationalError, AssertionError):
            detail = "<failure>actual schema read failed</failure>"
        return (f'<testsuite tests="1" failures="{int(bool(detail))}">'
                f'<testcase name="test:reject-invalid-input">{detail}</testcase></testsuite>').encode()
    finally:
        db.close()


class ArtifactReceipt(unittest.TestCase):
    def setUp(self):
        self.f = Fixture()
        self.now = self.f.now - timedelta(seconds=8)
        self.zip = archive_of(schema_report())
        self.f.policy["producers"]["test"]["reportPath"] = "reports/results.xml"
        self.f.objects["actions/artifacts/1001"]["digest"] = digest(self.zip)
        self.f.objects["branches/main"] = {"commit": {"sha": SOURCE}}
        self.f.seal()
        self.writes, self.downloads = [], []
        self.publisher = 200001

    def api(self, path, method="GET", payload=None):
        if method != "GET":
            self.assertEqual((path, method), ("repos/o/r/check-runs", "POST"))
            self.writes.append(copy.deepcopy(payload))
            self.f.objects["check-runs/901"] = {**copy.deepcopy(payload), "id": 901,
                                               "app": {"id": self.publisher}}
            return {"id": 901}
        return self.f.api(path)

    def download(self, repo, artifact, maximum):
        self.downloads.append((repo, artifact, maximum))
        return self.zip

    def args(self):
        return ("o/r", SOURCE, "AC-001", "test", 99, 1, 100, 1001,
                rv.receipt_digest(self.f.policy), self.api, self.download)

    def prepare(self):
        return ar.prepare_evidence(*self.args(), now=self.now)

    def test_ACC3_positive_actual_SQLite_artifact_to_shared_acceptance_verifier(self):
        link = ar.publish_evidence(*self.args(), now=self.now)
        self.assertEqual(len(self.writes), 1)
        self.assertEqual(self.downloads, [("o/r", 1001, ar.MAX_ARCHIVE)])
        request = self.writes[0]
        parsed = rv.receipt_json(request["output"]["text"])
        self.assertEqual(parsed["artifactDigest"], digest(self.zip))
        self.assertEqual(parsed["assertions"], [{"id": "test:reject-invalid-input", "outcome": "pass"}])
        # Feed the actual adapter output into the SAME Health/Release evaluator.
        # Reseal the synthetic decision explicitly; production needs a real human.
        self.f.body = self.f.body.replace(self.f.links["test"], link)
        links = {k: link if k == "test" else self.f.links[k] for k in self.f.item["evidence"]}
        approval = self.f.receipts["approval"]
        old = self.f.links["approval"]
        approval["bindingsDigest"] = rv.receipt_digest({"mergedSha": SOURCE,
            "ciRun": "https://github.com/o/r/actions/runs/99", "evidence": links})
        self.f.objects["check-runs/505"]["output"]["text"] = json.dumps(approval)
        self.f.body = self.f.body.replace(old, f'https://api.github.com/repos/o/r/check-runs/505#{rv.receipt_digest(approval)}')
        self.assertEqual(self.f.report(), {"verified": ["AC-001"], "deferred": [], "problems": []})

    def test_ACC3_negative_real_schema_failure_never_published(self):
        self.zip = archive_of(schema_report(broken=True))
        self.f.objects["actions/artifacts/1001"]["digest"] = digest(self.zip)
        with self.assertRaisesRegex(ValueError, "failed or skipped"):
            ar.publish_evidence(*self.args(), now=self.now)
        self.assertEqual(self.writes, [])

    def test_ACC3_negative_tampered_bytes_never_published(self):
        self.zip += b"tamper"
        with self.assertRaisesRegex(ValueError, "digest mismatch"):
            ar.publish_evidence(*self.args(), now=self.now)
        self.assertEqual(self.writes, [])

    def test_ACC3_negative_product_cannot_self_admit_policy(self):
        args = list(self.args())
        args[8] = "sha256:" + "0" * 64
        with self.assertRaisesRegex(ValueError, "externally admitted"):
            ar.publish_evidence(*args, now=self.now)
        self.assertEqual(self.writes, [])
        self.assertEqual(self.downloads, [])

    def test_ACC3_negative_foreign_source_job_and_expired_metadata_precede_download(self):
        original = copy.deepcopy(self.f.objects)
        for path, field, value in (("actions/runs/99/attempts/1", "head_sha", "a" * 40),
                                  ("actions/jobs/100", "name", "cleanup"),
                                  ("actions/artifacts/1001", "expired", True)):
            with self.subTest(path=path, field=field):
                self.f.objects = copy.deepcopy(original)
                self.f.objects[path][field] = value
                with self.assertRaises(ValueError):
                    self.prepare()
                self.assertEqual(self.downloads, [])

    def test_ACC3_negative_unintegrated_source_is_not_post_merge_evidence(self):
        self.f.objects[f"compare/{SOURCE}...{SOURCE}"]["status"] = "diverged"
        with self.assertRaisesRegex(ValueError, "not integrated"):
            self.prepare()
        self.assertEqual(self.downloads, [])

    def test_ACC3_negative_green_unrelated_assertions_cannot_be_published(self):
        self.zip = archive_of(b'<testsuite><testcase name="tidy-only"/></testsuite>')
        self.f.objects["actions/artifacts/1001"]["digest"] = digest(self.zip)
        with self.assertRaisesRegex(ValueError, "declared assertions"):
            ar.publish_evidence(*self.args(), now=self.now)
        self.assertEqual(self.writes, [])

    def test_ACC3_negative_wrong_real_publisher_rejected_on_readback(self):
        self.publisher = 15368
        with self.assertRaisesRegex(ValueError, "publisher/result"):
            ar.publish_evidence(*self.args(), now=self.now)
        self.assertEqual(len(self.writes), 1)  # no retry, no Issue/approval mutation

    def test_ACC3_positive_prepare_is_read_only_and_not_acceptance(self):
        request = self.prepare()
        self.assertEqual(self.writes, [])
        self.assertIn("not human acceptance", request["output"]["summary"])
        self.assertEqual(rv.receipt_json(request["output"]["text"])["kind"], "test")

    def test_ACC3_negative_invalid_IDs_or_decision_attempt(self):
        for index, value in ((1, "bad"), (3, "approval"), (4, True), (5, 0), (7, -1)):
            with self.subTest(index=index):
                args = list(self.args())
                args[index] = value
                with self.assertRaises(ValueError):
                    ar.prepare_evidence(*args, now=self.now)
        self.assertEqual(self.writes, [])
        self.assertEqual(self.downloads, [])

    def test_ACC3_negative_missing_or_unreviewed_report_path(self):
        self.f.policy["producers"]["test"].pop("reportPath")
        with self.assertRaisesRegex(ValueError, "reportPath"):
            self.prepare()

    def test_ACC3_positive_clock_matches_GitHub_second_precision(self):
        request = ar.prepare_evidence(*self.args(), now=self.now.replace(microsecond=500000))
        receipt = rv.receipt_json(request["output"]["text"])
        self.assertEqual(receipt["issuedAt"], self.now.isoformat())
        self.assertEqual(request["completed_at"], self.now.isoformat())

    def test_ACC3_negative_naive_publisher_clock(self):
        with self.assertRaisesRegex(ValueError, "timezone"):
            ar.prepare_evidence(*self.args(), now=self.now.replace(tzinfo=None))

    def test_ACC3_negative_ZIP_traversal_duplicate_symlink_and_truncated(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            duplicate = archive_of(schema_report(), [("reports/results.xml", schema_report())])
        symlink = zipfile.ZipInfo("linked")
        symlink.external_attr = (stat.S_IFLNK | 0o777) << 16
        unsafe = [archive_of(schema_report(), [("../outside", "bad")]), duplicate,
                  archive_of(schema_report(), [(symlink, "elsewhere")]), self.zip[:100]]
        for archive in unsafe:
            with self.subTest(size=len(archive)), self.assertRaises(ValueError):
                ar.artifact_assertions(archive, digest(archive), "reports/results.xml")

    def test_ACC3_negative_ZIP_or_JUnit_limits(self):
        archive = self.zip
        with self.assertRaisesRegex(ValueError, "missing or exceeds"):
            ar.artifact_assertions(b"", digest(b""), "reports/results.xml")
        with self.assertRaisesRegex(ValueError, "missing, ambiguous"):
            ar.artifact_assertions(archive, digest(archive), "missing.xml")
        huge = archive_of(b"x" * (ar.MAX_BYTES + 1))
        with self.assertRaisesRegex(ValueError, "oversized"):
            ar.artifact_assertions(huge, digest(huge), "reports/results.xml")

    def test_ACC3_negative_download_failure_writes_nothing(self):
        def unavailable(*_):
            raise OSError("unavailable")
        args = list(self.args()); args[-1] = unavailable
        with self.assertRaises(OSError):
            ar.publish_evidence(*args, now=self.now)
        self.assertEqual(self.writes, [])

    def test_ACC3_negative_unknown_publication_result_is_not_retried(self):
        writes = []
        def uncertain(path, method="GET", payload=None):
            if method == "POST":
                writes.append(path)
                raise OSError("connection lost after send")
            return self.api(path)
        args = list(self.args()); args[-2] = uncertain
        with self.assertRaises(OSError):
            ar.publish_evidence(*args, now=self.now)
        self.assertEqual(writes, ["repos/o/r/check-runs"])


if __name__ == "__main__":
    unittest.main()
