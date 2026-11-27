#!/usr/bin/env python3
"""Read this run's finalized conformance ZIP; verify bytes and reject tampering.

This is transport integration evidence, NOT an App attestation or human approval.
Only GET requests in the repository selected by the workflow are performed.
"""
import hashlib
import os
import re
import time

from artifact_receipt import artifact_assertions
from receipt_transport import GitHubReceiptTransport, TransportError


class ReadbackError(RuntimeError):
    """Only a fixed-stage, sanitized transport category; never a remote response body."""


def _transport_category(error):
    # HTTP status is already a bounded integer from our own TransportError.
    # Never log a raw exception, token, storage redirect or signed download URL.
    match = re.fullmatch(r"GitHub receipt request failed \(HTTP ([1-5][0-9]{2})\)", str(error))
    if match:
        return "http-" + match.group(1)
    return "transport-unavailable"



# GitHub can briefly return 404 after a real artifact has been finalized.
# Only the two observed read-only stages of this live smoke check retry exact
# HTTP 404. Each stage has five attempts and at most 5.5 seconds of delays.
# The shared receipt transport and all identity/digest/ZIP/approval checks,
# non-404 errors and publication operations remain unchanged and fail closed.
_READBACK_404_DELAYS = (0.25, 0.75, 1.5, 3.0)


def _read_finalized_artifact(operation, stage, sleep=None):
    sleep = time.sleep if sleep is None else sleep
    delays = (0,) + _READBACK_404_DELAYS
    for index, delay in enumerate(delays):
        if delay:
            sleep(delay)
        try:
            return operation()
        except TransportError as error:
            category = _transport_category(error)
            if category == "http-404" and index < len(delays) - 1:
                continue
            raise ReadbackError(stage + "/" + category) from None


def _read_metadata(transport, artifact_id, sleep=None):
    path = f"repos/{transport.repository}/actions/artifacts/{artifact_id}"
    return _read_finalized_artifact(lambda: transport(path), "metadata", sleep)


def check_artifact(transport, artifact_id, run_id, attempt):
    metadata = _read_metadata(transport, artifact_id)
    if (metadata.get("id") != artifact_id or metadata.get("expired") is not False
            or (metadata.get("workflow_run") or {}).get("id") != run_id
            or metadata.get("name") != f"cross-domain-{run_id}-{attempt}"):
        raise ValueError("live conformance artifact identity or expiry invalid")
    # Each attempt starts at the verified artifact's API endpoint; the
    # transport validates a fresh storage redirect without forwarding credentials.
    raw = _read_finalized_artifact(
        lambda: transport.download(transport.repository, artifact_id), "archive")
    expected = "sha256:" + hashlib.sha256(raw).hexdigest()
    if metadata.get("digest") != expected:
        raise ValueError("live conformance artifact digest mismatch")
    rows = artifact_assertions(raw, expected, "cross-domain.xml")
    ids = {row["id"] for row in rows}
    wanted = {"capability::" + name for name in
              ("package", "migration", "infrastructure", "browser-ui", "desktop", "cms-wordpress")}
    if ids != wanted:
        raise ValueError("live report is not the expected six-profile conformance result")
    try:
        artifact_assertions(raw + b"tampered", expected, "cross-domain.xml")
    except ValueError:
        return len(rows)
    raise AssertionError("tampered live artifact was not rejected")


def main():
    try:
        transport = GitHubReceiptTransport(os.environ["GITHUB_REPOSITORY"], os.environ["GH_TOKEN"])
        count = check_artifact(transport, int(os.environ["KAVOSH_ARTIFACT_ID"]),
                               int(os.environ["GITHUB_RUN_ID"]), int(os.environ["GITHUB_RUN_ATTEMPT"]))
    except ReadbackError as error:
        # Only the fixed transport stage and sanitized status class escape.
        raise SystemExit(
            f"Receipt transport integration failed ({error}); no acceptance or publication performed"
        ) from None
    except (KeyError, ValueError, RuntimeError, OSError):
        # Never leak a signed URL or secret-bearing arbitrary exception.
        raise SystemExit("Receipt transport integration failed; no acceptance or publication performed") from None
    print(f"Receipt transport: {count} live assertion groups read; digest verified; tampered bytes rejected; read-only")


if __name__ == "__main__":
    main()
