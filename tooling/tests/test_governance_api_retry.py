"""GitHub reads have bounded retry; failed reads cannot become green, writes never replay."""
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
