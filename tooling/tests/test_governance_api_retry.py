"""GitHub reads have bounded retry; failed reads cannot become green, writes never replay."""
import http.client
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import governance as g

def error(code):
    return urllib.error.HTTPError("https://api.github.com", code, "test", {}, io.BytesIO(b"failure"))

class Retry(unittest.TestCase):
    def test_get_retries_two_transient_failures_then_observes_true_response(self):
        class Response:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return json.dumps({"ok": True}).encode()
        with patch.dict("os.environ", {"GITHUB_TOKEN": "fake"}), \
             patch.object(g.urllib.request, "urlopen", side_effect=[error(502), error(503), Response()]) as url, \
             patch.object(g.time, "sleep") as sleep:
            self.assertEqual(g.github_api("repos/o/r/pulls"), {"ok": True})
            self.assertEqual(url.call_count, 3)
            self.assertEqual(sleep.call_count, 2)

    def test_exhaustion_stays_failure(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "fake"}), \
             patch.object(g.urllib.request, "urlopen", side_effect=[error(500) for _ in range(3)]) as url, \
             patch.object(g.time, "sleep"):
            with self.assertRaises(RuntimeError):
                g.github_api("repos/o/r/pulls")
            self.assertEqual(url.call_count, 3)

    def test_http_403_is_permission_not_network_retry(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "fake"}), \
             patch.object(g.urllib.request, "urlopen", side_effect=error(403)) as url, \
             patch.object(g.time, "sleep") as sleep:
            with self.assertRaises(RuntimeError):
                g.github_api("repos/o/r/pulls")
            self.assertEqual(url.call_count, 1)
            sleep.assert_not_called()

    def test_mutation_never_retries(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "fake"}), \
             patch.object(g.urllib.request, "urlopen", side_effect=error(503)) as url, \
             patch.object(g.time, "sleep") as sleep:
            with self.assertRaises(RuntimeError):
                g.github_api("repos/o/r/issues", method="POST", payload={"body":"x"})
            self.assertEqual(url.call_count, 1)
            sleep.assert_not_called()

    def test_dns_error_is_bounded(self):
        with patch.dict("os.environ", {"GITHUB_TOKEN": "fake"}), \
             patch.object(g.urllib.request, "urlopen", side_effect=urllib.error.URLError("dns")) as url, \
             patch.object(g.time, "sleep"):
            with self.assertRaises(RuntimeError):
                g.github_api("repos/o/r/pulls")
            self.assertEqual(url.call_count, 3)

    def test_truncated_response_is_retried_for_get_and_never_replayed_for_post(self):
        class Response:
            def __init__(self, incomplete=False):
                self.incomplete = incomplete
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self):
                if self.incomplete:
                    raise http.client.IncompleteRead(b'{"partial":', 42)
                return json.dumps({"ok": True}).encode()

        with patch.dict("os.environ", {"GITHUB_TOKEN": "example"}), \
             patch.object(g.urllib.request, "urlopen", side_effect=[
                 Response(True), Response(True), Response()]) as url, \
             patch.object(g.time, "sleep") as sleep:
            self.assertEqual(g.github_api("repos/example/project/pulls"), {"ok": True})
            self.assertEqual(url.call_count, 3)
            self.assertEqual(sleep.call_count, 2)
        with patch.dict("os.environ", {"GITHUB_TOKEN": "example"}), \
             patch.object(g.urllib.request, "urlopen",
                          side_effect=[Response(True) for _ in range(3)]) as url, \
             patch.object(g.time, "sleep"):
            with self.assertRaisesRegex(RuntimeError, "IncompleteRead"):
                g.github_api("repos/example/project/pulls")
            self.assertEqual(url.call_count, 3)
        with patch.dict("os.environ", {"GITHUB_TOKEN": "example"}), \
             patch.object(g.urllib.request, "urlopen", return_value=Response(True)) as url, \
             patch.object(g.time, "sleep") as sleep:
            with self.assertRaisesRegex(RuntimeError, "IncompleteRead"):
                g.github_api("repos/example/project/issues", method="POST", payload={"body": "example"})
            self.assertEqual(url.call_count, 1)
            sleep.assert_not_called()

    def test_truncated_json_without_content_length_retries_get_but_never_post(self):
        class Partial:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'{"items":['
        class Complete:
            def __enter__(self): return self
            def __exit__(self, *args): return False
            def read(self): return b'{"items":[]}'
        with patch.dict("os.environ", {"GITHUB_TOKEN": "example"}), \
             patch.object(g.urllib.request, "urlopen", side_effect=[Partial(), Complete()]) as url, \
             patch.object(g.time, "sleep") as sleep:
            self.assertEqual(g.github_api("repos/example/project/pulls"), {"items": []})
            self.assertEqual(url.call_count, 2)
            self.assertEqual(sleep.call_count, 1)
        with patch.dict("os.environ", {"GITHUB_TOKEN": "example"}), \
             patch.object(g.urllib.request, "urlopen", return_value=Partial()) as url:
            with self.assertRaisesRegex(RuntimeError, "JSONDecodeError"):
                g.github_api("repos/example/project/issues", method="POST", payload={"body":"example"})
            self.assertEqual(url.call_count, 1)

    def test_pr_file_pagination_is_complete_and_fails_closed_at_api_boundary(self):
        expected = [{"filename": f"src/file-{i}.py"} for i in range(81)]
        calls = []
        def fetch(command, path):
            self.assertEqual(command, "api")
            calls.append(path)
            return expected[(len(calls) - 1) * 20:len(calls) * 20]

        self.assertEqual(g.pull_request_files("example/project", 17, fetch), expected)
        self.assertEqual(len(calls), 5)
        self.assertEqual(calls[0], "repos/example/project/pulls/17/files?per_page=20&page=1")
        self.assertEqual(calls[-1], "repos/example/project/pulls/17/files?per_page=20&page=5")
        with self.assertRaisesRegex(RuntimeError, "malformed"):
            g.pull_request_files("example/project", 17, lambda *_: None)
        pages = []
        def full(command, path):
            pages.append(path)
            return [{"filename": "example.py"}] * 20
        with self.assertRaisesRegex(RuntimeError, "3000-file"):
            g.pull_request_files("example/project", 17, full)
        self.assertEqual(len(pages), 150)
