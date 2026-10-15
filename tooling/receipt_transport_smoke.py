#!/usr/bin/env python3
"""Read this run's finalized conformance ZIP; verify bytes and reject tampering.

This is transport integration evidence, NOT an App attestation or human approval.
Only GET requests in the repository selected by the workflow are performed.
"""
import hashlib
import os

from artifact_receipt import artifact_assertions
from receipt_transport import GitHubReceiptTransport


def check_artifact(transport, artifact_id, run_id, attempt):
    metadata = transport(f"repos/{transport.repository}/actions/artifacts/{artifact_id}")
    if (metadata.get("id") != artifact_id or metadata.get("expired") is not False
            or (metadata.get("workflow_run") or {}).get("id") != run_id
            or metadata.get("name") != f"cross-domain-{run_id}-{attempt}"):
        raise ValueError("live conformance artifact identity or expiry invalid")
    raw = transport.download(transport.repository, artifact_id)
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
    except (KeyError, ValueError, RuntimeError, OSError):
        # Neither a signed URL nor a secret-bearing network exception is printed.
        raise SystemExit("Receipt transport integration failed; no acceptance or publication performed") from None
    print(f"Receipt transport: {count} live assertion groups read; digest verified; tampered bytes rejected; read-only")


if __name__ == "__main__":
    main()
