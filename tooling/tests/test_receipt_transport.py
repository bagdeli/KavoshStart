"""Transport boundaries. Fake I/O here; self-check also reads a real run artifact."""
import hashlib
import io
import json
from pathlib import Path
import sys
import unittest
import urllib.error
from unittest.mock import Mock, patch
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import receipt_transport as rt
import receipt_transport_smoke as smoke

REPO, TOKEN, SOURCE = "o/r", "secret-do-not-print", "a" * 40
STORAGE = "https://example.blob.core.windows.net/container/artifact.zip?sig=secret-signed-url"


class Response(io.BytesIO):
    def __init__(self, raw=b"{}", headers=None, status=200):
        super().__init__(raw)
        self.headers, self.status = headers or {}, status


def redirect(location=STORAGE, code=302):
    return urllib.error.HTTPError("https://api.github.com/test", code, "redirect",
                                  {"Location": location}, io.BytesIO(b"private-body"))


def payload(kind="test"):
    return {"head_sha": SOURCE, "status": "completed", "conclusion": "success",
            "output": {"text": json.dumps({"repository": REPO, "kind": kind, "sourceSha": SOURCE})}}


class ReceiptTransport(unittest.TestCase):
    def setUp(self):
        self.t = rt.GitHubReceiptTransport(REPO, TOKEN)
        self.t._opener = Mock()

    def test_exact_json_read_authenticates_only_api(self):
        self.t._opener.open.return_value = Response(b'{"id":10}')
        self.assertEqual(self.t("repos/o/r/actions/artifacts/10"), {"id": 10})
        request = self.t._opener.open.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.github.com/repos/o/r/actions/artifacts/10")
        self.assertEqual(request.get_header("Authorization"), "Bearer " + TOKEN)

    def test_repository_and_endpoint_confinement(self):
        paths = ["repos/other/r/issues/1", "repos/o/r/../x/issues/1", "repos/o/r/secrets",
                 "repos/o/r/actions/artifacts/1/zip", "https://evil.test", "repos/o/r/issues/1#x",
                 "repos/o/r/contents/other.json?ref=" + SOURCE,
                 "repos/o/r/contents/kavosh.project.json?ref=main", "repos/o/r/issues/1?x=y",
                 "repos/o/r/issues/%31", "repos/o/r/issues/1\n", "repos/o/r/git/ref/heads/main"]
        for path in paths:
            with self.subTest(path=path), self.assertRaises(ValueError): self.t(path)
        self.t._opener.open.assert_not_called()

    def test_known_verifier_endpoints_remain_usable(self):
        paths = [f"git/commits/{SOURCE}", f"git/trees/{SOURCE}", "branches/main",
                 f"compare/{SOURCE}...{SOURCE}", "pulls/1", "issues/2", "check-runs/3",
                 "actions/jobs/4", "actions/runs/5", "actions/runs/5/attempts/2",
                 f"contents/acceptance/security/receipt-policy.json?ref={SOURCE}",
                 f"contents/acceptance/scope.json?ref={SOURCE}", f"contents/kavosh.project.json?ref={SOURCE}"]
        for path in paths:
            with self.subTest(path=path):
                self.t._opener.open.return_value = Response()
                self.assertEqual(self.t("repos/o/r/" + path), {})

    def test_actual_redirect_request_has_no_credentials(self):
        self.t._opener.open.side_effect = [redirect(), Response(b"zip")]
        self.assertEqual(self.t.download(REPO, 1), b"zip")
        first, second = [call.args[0] for call in self.t._opener.open.call_args_list]
        self.assertIsNotNone(first.get_header("Authorization"))
        self.assertEqual(second.full_url, STORAGE)
        self.assertEqual(second.get_method(), "GET")
        for key in ("Authorization", "Cookie", "Referer", "X-github-api-version"):
            self.assertIsNone(second.get_header(key))

    def test_storage_redirect_allowlist(self):
        for url in [STORAGE, "https://results-receiver.actions.githubusercontent.com/x?sig=x"]:
            self.assertEqual(rt._storage_url(url), url)
        for url in ["http://example.blob.core.windows.net/x", "https://evil.test/x",
                    "https://example.blob.core.windows.net.evil.test/x", "https://127.0.0.1/x",
                    "https://169.254.169.254/x", "https://user:pwd@example.blob.core.windows.net/x",
                    "https://example.blob.core.windows.net:444/x", "https://example.blob.core.windows.net/x#f",
                    "https://example.blob.core.windows.net/\\evil", STORAGE + "\n", STORAGE + " " , None]:
            with self.subTest(url=url), self.assertRaises(rt.TransportError): rt._storage_url(url)

    def test_bad_redirect_stops_before_second_request(self):
        self.t._opener.open.side_effect = redirect("https://evil.test/secret")
        with self.assertRaises(rt.TransportError) as exc: self.t.download(REPO, 1)
        self.assertNotIn("evil.test", str(exc.exception))
        self.assertEqual(self.t._opener.open.call_count, 1)

    def test_second_redirect_and_api_redirect_are_not_followed(self):
        self.t._opener.open.side_effect = [redirect(), redirect()]
        with self.assertRaises(rt.TransportError): self.t.download(REPO, 1)
        self.assertEqual(self.t._opener.open.call_count, 2)
        self.t._opener.open.reset_mock()
        self.t._opener.open.side_effect = redirect()
        with self.assertRaises(rt.TransportError): self.t("repos/o/r/issues/1")
        self.assertEqual(self.t._opener.open.call_count, 1)

    def test_no_automatic_redirect_handler(self):
        handler = rt._NoRedirect()
        self.assertIsNone(handler.redirect_request(None, None, 302, None, {}, STORAGE))

    def test_no_proxy_or_cookie_handler_is_installed(self):
        transport = rt.GitHubReceiptTransport(REPO, TOKEN)
        handlers = transport._opener.handlers
        self.assertFalse(any(isinstance(h, rt.urllib.request.HTTPCookieProcessor) for h in handlers))
        for handler in handlers:
            if isinstance(handler, rt.urllib.request.ProxyHandler): self.assertEqual(handler.proxies, {})

    def test_identity_ids_and_limits_fail_before_network(self):
        for repo, aid, bound in [("x/y", 1, 100), (REPO, True, 100), (REPO, 0, 100),
                                  (REPO, 1, 0), (REPO, 1, True), (REPO, 1, rt.MAX_ARCHIVE + 1)]:
            with self.subTest(value=(repo, aid, bound)), self.assertRaises(ValueError):
                self.t.download(repo, aid, bound)
        self.t._opener.open.assert_not_called()

    def test_declared_and_streaming_size_bounds(self):
        for raw, headers in [(b"abcd", {}), (b"", {"Content-Length": "4"}),
                             (b"", {"Content-Length": "-1"}), (b"ab", {"Content-Length": "3"}),
                             (b"", {"Content-Encoding": "gzip"})]:
            with self.subTest(headers=headers), self.assertRaises(rt.TransportError):
                rt._read_bounded(Response(raw, headers), 3, float("inf"))
        self.assertEqual(rt._read_bounded(Response(b"abc", {"Content-Length": "3"}), 3, float("inf")), b"abc")

    def test_deadline_prevents_unbounded_stream(self):
        with self.assertRaises(rt.TransportError): rt._read_bounded(Response(), 3, -1)

    def test_error_diagnostics_do_not_leak_token_body_or_signed_url(self):
        for error in [urllib.error.URLError(STORAGE + TOKEN),
                      urllib.error.HTTPError(STORAGE, 403, TOKEN, {}, io.BytesIO(TOKEN.encode())),
                      rt.http.client.IncompleteRead(TOKEN.encode())]:
            self.t._opener.open.side_effect = error
            with self.assertRaises(rt.TransportError) as exc: self.t("repos/o/r/issues/1")
            self.assertNotIn(TOKEN, str(exc.exception)); self.assertNotIn("sig=", str(exc.exception))

    def test_malformed_duplicate_nonfinite_json_rejected(self):
        for raw in [b"not-json", b'\xff', b'{"id":1,"id":2}', b'{"x":NaN}', b'[]']:
            self.t._opener.open.return_value = Response(raw)
            with self.subTest(raw=raw), self.assertRaises(rt.TransportError): self.t("repos/o/r/issues/1")

    def test_readonly_is_default_and_other_writes_are_always_denied(self):
        for method, path in [("POST", "check-runs"), ("DELETE", "issues/1"), ("PATCH", "issues/1")]:
            with self.assertRaises(ValueError): self.t("repos/o/r/" + path, method, payload())
        self.t.publish = True
        for path in ("issues", "git/refs", "releases", "actions/workflows/x/dispatches"):
            with self.assertRaises(ValueError): self.t("repos/o/r/" + path, "POST", payload())
        self.t._opener.open.assert_not_called()

    def test_only_automated_evidence_can_be_published(self):
        self.t.publish = True
        for value in [payload("approval"), payload("defer"), {}, payload("unknown")]:
            with self.assertRaises(ValueError): self.t("repos/o/r/check-runs", "POST", value)
        self.t._opener.open.assert_not_called()
        self.t._opener.open.return_value = Response(b'{"id":9}', status=201)
        self.assertEqual(self.t("repos/o/r/check-runs", "POST", payload()), {"id": 9})
        self.assertEqual(self.t._opener.open.call_count, 1)

    def test_publication_never_retries_on_unknown_result(self):
        self.t.publish = True
        for error in [urllib.error.URLError("network"), redirect(code=503), TimeoutError("timeout")]:
            self.t._opener.open.reset_mock(); self.t._opener.open.side_effect = error
            with self.assertRaises(rt.PublicationUncertain): self.t("repos/o/r/check-runs", "POST", payload())
            self.assertEqual(self.t._opener.open.call_count, 1)

    def test_invalid_publication_response_is_uncertain(self):
        self.t.publish = True
        for raw in [b"not-json", b"[]"]:
            self.t._opener.open.return_value = Response(raw, status=201)
            with self.assertRaises(rt.PublicationUncertain): self.t("repos/o/r/check-runs", "POST", payload())

    def test_oversized_publication_rejected_locally(self):
        self.t.publish = True; body = payload(); body["extra"] = "x" * rt.MAX_REQUEST
        with self.assertRaises(ValueError): self.t("repos/o/r/check-runs", "POST", body)
        self.t._opener.open.assert_not_called()

    def test_constructor_rejects_ambiguous_scope_and_credentials(self):
        for repo, token, timeout in [("../r", TOKEN, 30), (REPO, "", 30), (REPO, "x\ny", 30),
                                      (REPO, TOKEN, 0), (REPO, TOKEN, float("nan")), (REPO, TOKEN, True)]:
            with self.assertRaises(ValueError): rt.GitHubReceiptTransport(repo, token, timeout=timeout)


class TransportSmoke(unittest.TestCase):
    def test_real_zip_parser_and_tamper_control(self):
        names = ("package", "migration", "infrastructure", "browser-ui", "desktop", "cms-wordpress")
        xml = '<testsuite tests="6">' + ''.join(f'<testcase classname="capability" name="{n}"/>' for n in names) + '</testsuite>'
        out = io.BytesIO()
        with zipfile.ZipFile(out, "w") as archive: archive.writestr("cross-domain.xml", xml)
        raw = out.getvalue(); digest = "sha256:" + hashlib.sha256(raw).hexdigest()
        transport = Mock(repository=REPO, return_value={"id": 1, "expired": False, "digest": digest, "workflow_run": {"id": 5}, "name": "cross-domain-5-1"})
        transport.download.return_value = raw
        self.assertEqual(smoke.check_artifact(transport, 1, 5, 1), 6)
        transport.assert_called_once_with("repos/o/r/actions/artifacts/1")
        self.assertEqual(transport.download.call_count, 1)
        transport.return_value["digest"] = "sha256:" + "0" * 64
        with self.assertRaises(ValueError): smoke.check_artifact(transport, 1, 5, 1)

    def test_missing_identity_or_expired_artifact_is_not_success(self):
        for meta in ({"id": 2, "expired": False}, {"id": 1, "expired": True}):
            transport = Mock(repository=REPO, return_value=meta)
            with self.assertRaises(ValueError): smoke.check_artifact(transport, 1, 5, 1)
            transport.download.assert_not_called()
