"""Read-only operator network diagnostics: no network traffic in the tests."""
import importlib.util
import socket
import unittest
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("network_failure_report", ROOT / "scripts/network_failure_report.py")
network = importlib.util.module_from_spec(spec)
spec.loader.exec_module(network)
FIXED_TIME = datetime(2026, 10, 15, 18, 0, tzinfo=timezone.utc)


def fake_dns(host, port, type):
    assert (host, port, type) == ("packages.example.org", 443, socket.SOCK_STREAM)
    return [(socket.AF_INET, socket.SOCK_STREAM, 0, "", ("203.0.113.11", port)),
            (socket.AF_INET6, socket.SOCK_STREAM, 0, "", ("2001:db8::11", port, 0, 0)),
            (socket.AF_INET, socket.SOCK_STREAM, 0, "", ("203.0.113.11", port))]


class NetworkFailureReport(unittest.TestCase):
    def test_resolved_ipv4_ipv6_are_reported_without_download(self):
        r = network.report("https://user:password@packages.example.org/archive.tgz?token=SECRET#fragment",
                           "download", 3, "timeout", resolver=fake_dns, now=FIXED_TIME)
        self.assertEqual(r["url_sanitized"], "https://packages.example.org/archive.tgz")
        self.assertEqual(r["dns_name"], "packages.example.org")
        self.assertEqual(r["ip_addresses_from_current_environment"], ["2001:db8::11", "203.0.113.11"])
        self.assertEqual(r["attempts_failed"], 3)
        self.assertEqual(r["observed_at_utc"], "2026-10-15T18:00:00+00:00")
        self.assertNotIn("SECRET", str(r))
        self.assertNotIn("user:password", str(r))

    def test_dns_failure_does_not_fabricate_ip(self):
        def broken(*args, **kwargs):
            raise socket.gaierror(-2, "unknown host")
        r = network.report("https://packages.example.org/x", "upload", 2, "dns", resolver=broken, now=FIXED_TIME)
        self.assertEqual(r["ip_addresses_from_current_environment"], [])
        self.assertIn("not resolved here", r["ip_resolution"])

    def test_token_paths_are_suppressed(self):
        s = network.sanitize("https://user:secret@packages.example.org/asset/token-abcdef/" + "a" * 80 + "/file.tgz?sig=1")
        self.assertIn("[redacted]", s["url"])
        self.assertTrue(s["url"].endswith("/file.tgz"))
        self.assertNotIn("token-abcdef", s["url"])

    def test_invalid_urls_and_single_attempt_rejected(self):
        for url in ("file:///etc/passwd", "ftp://packages.example.org", "no-url", "https://packages.example.org:bad/"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                network.sanitize(url)
        with self.assertRaises(ValueError):
            network.report("https://packages.example.org/", "download", 1, "dns", resolver=fake_dns)

    def test_auth_denials_are_not_mislabeled_firewall(self):
        for code in ("http-401", "http-403", "http-404"):
            with self.subTest(code=code):
                r = network.report("https://packages.example.org/", "download", 2, code, resolver=fake_dns, now=FIXED_TIME)
                self.assertIn("not proof of a network block", r["operator_hint"])

    def test_no_implicit_relay_or_tls_bypass(self):
        r = network.report("https://packages.example.org/", "download", 2, "http-429", resolver=fake_dns, now=FIXED_TIME)
        self.assertIn("no implicit proxy", r["action"])
        self.assertNotIn("mirror", r["url_sanitized"])


if __name__ == "__main__":
    unittest.main()
