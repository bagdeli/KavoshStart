"""Bounded GitHub.com transport for the reference receipt publisher (stdlib).

One instance is confined to one repository. Reads are the verifier's exact API
endpoints; the only optional write is an automated evidence check. Redirects are
never automatic, credentials never leave api.github.com, and writes never retry.
Installation-token issuance and human authentication are deliberately external.
"""
import http.client
import json
import re
import ssl
import time
import urllib.error
import urllib.parse
import urllib.request

from artifact_receipt import MAX_ARCHIVE
from src.receipts import RECEIPT_KINDS, receipt_json

MAX_JSON = 8 * 1024 * 1024
MAX_REQUEST = 64 * 1024
SHA = r"[0-9a-f]{40}"
NUMBER = r"[1-9][0-9]*"
READ_PATH = re.compile(
    rf"(?:contents/(?:kavosh[.]project[.]json|acceptance/scope[.]json|"
    rf"acceptance/security/receipt-policy[.]json)[?]ref={SHA}|"
    rf"git/(?:commits|trees)/{SHA}|branches/main|compare/{SHA}[.]{{3}}{SHA}|"
    rf"(?:pulls|issues|check-runs)/{NUMBER}|actions/jobs/{NUMBER}|"
    rf"actions/artifacts/{NUMBER}|actions/runs/{NUMBER}(?:/attempts/{NUMBER})?)"
)


class TransportError(RuntimeError):
    """Safe diagnostic: never includes remote bodies, signed URLs or tokens."""


class PublicationUncertain(TransportError):
    """A write may already have happened. Reconcile it; never blindly retry."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _storage_url(value):
    if (not isinstance(value, str) or len(value) > 8192
            or any(ord(c) < 33 or ord(c) > 126 for c in value)):
        raise TransportError("invalid artifact storage redirect") from None
    try:
        url = urllib.parse.urlsplit(value)
        host = url.hostname or ""
        allowed = (re.fullmatch(r"[a-z0-9-]+[.]blob[.]core[.]windows[.]net", host)
                   or re.fullmatch(r"[a-z0-9.-]+[.]actions[.]githubusercontent[.]com", host))
        valid = (url.scheme == "https" and allowed and url.port in (None, 443)
                 and url.username is None and url.password is None and not url.fragment
                 and "\\" not in value and url.path.startswith("/"))
    except ValueError:
        valid = False
    if not valid:
        raise TransportError("artifact redirect is not an approved HTTPS storage host") from None
    return value


def _read_bounded(response, maximum, deadline):
    encoding = response.headers.get("Content-Encoding", "identity").lower()
    if encoding != "identity":
        raise TransportError("unexpected compressed HTTP response")
    length = response.headers.get("Content-Length")
    if length is not None and (not re.fullmatch(r"[0-9]+", length) or int(length) > maximum):
        raise TransportError("response Content-Length exceeds the transport bound or is invalid")
    chunks, size = [], 0
    while True:
        if time.monotonic() > deadline:
            raise TransportError("response exceeded the transport deadline")
        chunk = response.read(min(65536, maximum + 1 - size))
        if time.monotonic() > deadline:
            raise TransportError("response exceeded the transport deadline")
        if not chunk:
            break
        size += len(chunk)
        if size > maximum:
            raise TransportError("response exceeded the streaming byte bound")
        chunks.append(chunk)
    if length is not None and size != int(length):
        raise TransportError("response length does not match Content-Length")
    return b"".join(chunks)


class GitHubReceiptTransport:
    """api + download callables for prepare_evidence/publish_evidence.

    token is an independently held, short-lived installation token. Merely
    passing a token does NOT enable writes. Never expose a publishing instance
    to product jobs or use this class to manufacture independent approval.
    """
    def __init__(self, repository, token, *, publish=False, timeout=30):
        segment = r"[A-Za-z0-9][A-Za-z0-9_.-]{0,99}"
        if not isinstance(repository, str) or not re.fullmatch(segment + "/" + segment, repository):
            raise ValueError("canonical owner/repository required")
        if (not isinstance(token, str) or not 1 <= len(token) <= 8192
                or any(ord(c) < 33 or ord(c) > 126 for c in token)):
            raise ValueError("nonempty credential required")
        if type(publish) is not bool or type(timeout) not in (int, float) or not 0 < timeout <= 60:
            raise ValueError("invalid publication flag or timeout")
        self.repository, self._token, self.publish, self.timeout = repository, token, publish, timeout
        # Do not silently route credentials through ambient HTTP proxy settings.
        self._opener = urllib.request.build_opener(
            urllib.request.ProxyHandler({}), _NoRedirect(),
            urllib.request.HTTPSHandler(context=ssl.create_default_context()))

    def _exchange(self, url, *, maximum, storage=False, payload=None, redirect=False):
        headers = {"User-Agent": "KavoshStart-receipt-transport", "Accept-Encoding": "identity"}
        if storage:
            headers["Accept"] = "application/zip"
        else:
            headers.update({"Authorization": "Bearer " + self._token,
                            "Accept": "application/vnd.github+json",
                            "X-GitHub-Api-Version": "2022-11-28"})
        if payload is not None:
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=payload, headers=headers,
                                         method="POST" if payload is not None else "GET")
        deadline = time.monotonic() + self.timeout
        try:
            with self._opener.open(request, timeout=self.timeout) as response:
                if response.status != (201 if payload is not None else 200):
                    raise TransportError("unexpected HTTP success status")
                return _read_bounded(response, maximum, deadline)
        except urllib.error.HTTPError as exc:
            status = exc.code
            location = exc.headers.get("Location") if redirect and status == 302 else None
            exc.close()
            if location is not None:
                return _storage_url(location)
            if payload is not None:
                raise PublicationUncertain("publication did not verify; reconcile before retry") from None
            raise TransportError(f"GitHub receipt request failed (HTTP {status})") from None
        except (OSError, urllib.error.URLError, http.client.HTTPException, TransportError) as exc:
            if payload is not None:
                raise PublicationUncertain("publication outcome unknown; reconcile before retry") from None
            if isinstance(exc, TransportError):
                raise
            raise TransportError("GitHub receipt transport unavailable") from None

    def __call__(self, path, method="GET", payload=None):
        prefix = f"repos/{self.repository}/"
        if not isinstance(path, str) or not path.startswith(prefix):
            raise ValueError("request is outside the configured repository")
        suffix = path[len(prefix):]
        data = None
        if method == "GET" and payload is None and READ_PATH.fullmatch(suffix):
            pass
        elif method == "POST" and self.publish and suffix == "check-runs":
            try:
                receipt = receipt_json(payload["output"]["text"])
                valid = (receipt.get("repository") == self.repository
                         and receipt.get("kind") in RECEIPT_KINDS
                         and re.fullmatch(SHA, receipt.get("sourceSha", ""))
                         and payload.get("head_sha") == receipt["sourceSha"]
                         and payload.get("status") == "completed" and payload.get("conclusion") == "success")
                data = json.dumps(payload, ensure_ascii=False, allow_nan=False).encode("utf-8")
            except (ValueError, TypeError, KeyError, AttributeError):
                raise ValueError("invalid automated evidence publication") from None
            if not valid or len(data) > MAX_REQUEST:
                raise ValueError("automated evidence request is invalid or oversized")
        else:
            raise ValueError("API method or endpoint is not admitted by the receipt transport")
        raw = self._exchange("https://api.github.com/" + path, maximum=MAX_JSON, payload=data)
        try:
            value = receipt_json(raw.decode("utf-8"))
        except (ValueError, UnicodeError, RecursionError):
            if data is not None:
                raise PublicationUncertain("publication response invalid; reconcile before retry") from None
            raise TransportError("invalid GitHub JSON response") from None
        if not isinstance(value, dict):
            if data is not None:
                raise PublicationUncertain("publication response invalid; reconcile before retry") from None
            raise TransportError("GitHub receipt endpoint did not return an object")
        return value

    def download(self, repository, artifact_id, maximum=MAX_ARCHIVE):
        if repository != self.repository or type(artifact_id) is not int or artifact_id <= 0:
            raise ValueError("artifact must belong to the configured repository")
        if type(maximum) is not int or not 0 < maximum <= MAX_ARCHIVE:
            raise ValueError("artifact byte bound must be within 32 MiB")
        url = f"https://api.github.com/repos/{self.repository}/actions/artifacts/{artifact_id}/zip"
        redirect = self._exchange(url, maximum=maximum, redirect=True)
        # GitHub documents a 302 to storage. Fail closed on an unexpected shape.
        if not isinstance(redirect, str):
            raise TransportError("artifact endpoint did not supply the expected storage redirect")
        # A fresh request carries NO authorization, cookies, referer or API headers.
        # A second redirect is rejected, not followed.
        return self._exchange(redirect, maximum=maximum, storage=True)
