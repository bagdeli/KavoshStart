"""Evidence-App adapter: verified artifact bytes -> source-bound check receipt.

Run only inside the separately administered evidence service. Its authenticated
API and bounded artifact downloader are injected, never taken from product jobs.
The operator pins a reviewed policy digest OUTSIDE the product repository. This
module does not install an App, authenticate a human, or update an Issue/branch.
"""
import hashlib
import io
import json
import re
from pathlib import Path
import stat
import sys
import zipfile
from datetime import datetime, timezone

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
import receipts as rv
from junit_receipt import MAX_BYTES, assertion_outcomes

MAX_ARCHIVE = 32 * 1024 * 1024
MAX_EXPANDED = 64 * 1024 * 1024
MAX_MEMBERS = 1000


def artifact_assertions(archive, digest, report_path):
    """Inspect one policy-selected JUnit member; never extract or execute ZIP data."""
    if not isinstance(archive, bytes) or not archive or len(archive) > MAX_ARCHIVE:
        raise ValueError("artifact ZIP is missing or exceeds 32 MiB")
    if not isinstance(digest, str) or digest != "sha256:" + hashlib.sha256(archive).hexdigest():
        raise ValueError("downloaded artifact digest mismatch")
    if not rv.receipt_path(report_path):
        raise ValueError("policy reportPath must be a literal relative file path")
    try:
        with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
            members = bundle.infolist()
            if len(members) > MAX_MEMBERS or sum(m.file_size for m in members) > MAX_EXPANDED:
                raise ValueError("artifact ZIP expands beyond the evidence limit")
            names = set()
            for member in members:
                name = member.filename.rstrip("/") if member.is_dir() else member.filename
                mode = member.external_attr >> 16
                if (not rv.receipt_path(name) or name in names or member.flag_bits & 1
                        or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)):
                    raise ValueError("artifact ZIP has unsafe, encrypted or duplicate members")
                names.add(name)
            chosen = [m for m in members if m.filename == report_path and not m.is_dir()]
            if len(chosen) != 1 or not 0 < chosen[0].file_size <= MAX_BYTES:
                raise ValueError("policy-selected JUnit report missing, ambiguous or oversized")
            with bundle.open(chosen[0]) as stream:
                raw = stream.read(MAX_BYTES + 1)
            if len(raw) != chosen[0].file_size:
                raise ValueError("JUnit member size mismatch")
            outcomes = assertion_outcomes(raw)
    except (zipfile.BadZipFile, NotImplementedError, RuntimeError) as exc:
        raise ValueError("artifact ZIP could not be inspected safely") from exc
    if any(row["outcome"] != "pass" for row in outcomes):
        raise ValueError("failed or skipped assertions cannot produce a successful receipt")
    return outcomes


def _context(repo, source, acceptance_id, kind, trusted_policy_digest, api, now):
    manifest = rv._json_file(repo, "kavosh.project.json", source, api)
    scope = rv._json_file(repo, "acceptance/scope.json", source, api)
    policy = rv._json_file(repo, rv.RECEIPT_POLICY, source, api)
    if (not isinstance(trusted_policy_digest, str)
            or not rv.RECEIPT_DIGEST.fullmatch(trusted_policy_digest)
            or rv.receipt_digest(policy) != trusted_policy_digest):
        raise ValueError("candidate policy is not the externally admitted policy")
    verifier = rv.ReceiptVerifier(repo, source, policy, api, now)
    if (manifest.get("acceptance") or {}).get("mode") != "continuous":
        raise ValueError("continuous acceptance is not enabled")
    if (type(scope.get("schemaVersion")) is not int or scope["schemaVersion"] != 1
            or not rv.ACCEPTANCE_RELEASE_RE.fullmatch(scope.get("targetRelease") or "")):
        raise ValueError("invalid acceptance scope version or target")
    items = scope.get("items")
    if not isinstance(items, list) or any(not isinstance(i, dict) for i in items):
        raise ValueError("invalid acceptance scope items")
    selected = [item for item in items if item.get("id") == acceptance_id]
    if len(selected) != 1:
        raise ValueError("acceptance item missing or ambiguous")
    item = selected[0]
    problems = rv.receipt_contract_problems(item)
    if problems or item.get("deferredTo") or kind not in item.get("evidence", []):
        raise ValueError("item is deferred or has an invalid assertion/kind contract")
    if kind not in rv.RECEIPT_KINDS:
        raise ValueError("evidence publisher cannot create an acceptance decision")
    producer = verifier.producers.get(kind)
    if (not isinstance(producer, dict) or producer.get("mode") != "actions"
            or not rv.receipt_positive(producer.get("appId"))
            or producer["appId"] in rv.SHARED_APPS):
        raise ValueError("dedicated actions evidence producer required")
    branch = verifier.get("branches/main")
    current_main = (branch.get("commit") or {}).get("sha")
    if not isinstance(current_main, str) or not rv.RECEIPT_SHA.fullmatch(current_main):
        raise ValueError("main provenance unavailable")
    if verifier.get(f"compare/{source}...{current_main}").get("status") not in ("ahead", "identical"):
        raise ValueError("evidence source is not integrated into main")
    return verifier, scope, item, producer


def prepare_evidence(repo, source, acceptance_id, kind, run_id, attempt, job_id,
                     artifact_id, trusted_policy_digest, api, download, now=None):
    """Read real metadata and ZIP bytes; return an UNPUBLISHED check request.

    api(path) reads GitHub JSON; download(repo, artifact_id, max_bytes) returns
    bytes from the authenticated Actions artifact endpoint. The service must
    bound its download and must not forward authorization to storage redirects.
    The externally admitted policy is configuration of that service, NOT a
    value the product can supply to authorize itself.
    """
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("publisher clock must include timezone")
    # GitHub check timestamps have second precision; do not issue a receipt
    # later than its own API-rounded completed_at value.
    now = now.astimezone(timezone.utc).replace(microsecond=0)
    if not isinstance(repo, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
        raise ValueError("invalid repository")
    if not isinstance(source, str) or not rv.RECEIPT_SHA.fullmatch(source):
        raise ValueError("invalid source SHA")
    if any(not rv.receipt_positive(n) for n in (run_id, attempt, job_id, artifact_id)):
        raise ValueError("positive run, attempt, job and artifact IDs required")
    verifier, scope, item, producer = _context(repo, source, acceptance_id, kind, trusted_policy_digest, api, now)
    artifact = verifier.get(f"actions/artifacts/{artifact_id}")
    # ReceiptVerifier performs the remaining exact run/job/attempt/artifact checks
    # before download and again after publication. Reuse the contract, not a fork.
    expiry = min(now + verifier.max_age, rv.receipt_time(artifact.get("expires_at")))
    receipt = {"schemaVersion": 1, "repository": repo, "acceptanceId": acceptance_id,
               "kind": kind, "targetRelease": scope["targetRelease"], "sourceSha": source,
               "sourceTree": verifier.tree(source), "scopeDigest": rv.receipt_digest(item),
               "policyDigest": trusted_policy_digest, "issuedAt": now.isoformat(),
               "expiresAt": expiry.isoformat(), "outcome": "pass", "runId": run_id,
               "runAttempt": attempt, "jobId": job_id, "artifactId": artifact_id,
               "artifactDigest": artifact.get("digest"),
               "assertions": [{"id": x, "outcome": "pass"} for x in item["assertions"][kind]]}

    def validate_unpublished():
        # Synthetic envelope is ONLY local metadata preflight, never published
        # or used to claim real App identity/human acceptance.
        check = {"id": 1, "head_sha": source, "name": producer.get("checkName"),
                 "app": {"id": producer["appId"]}, "status": "completed", "conclusion": "success",
                 "completed_at": now.isoformat(), "output": {"text": json.dumps(receipt)}}
        verifier.cache["check-runs/1"] = check
        link = f"https://api.github.com/repos/{repo}/check-runs/1#{rv.receipt_digest(receipt)}"
        verifier.verify(item, scope["targetRelease"], kind, link, {"mergedSha": source})

    validate_unpublished()
    archive = download(repo, artifact_id, MAX_ARCHIVE)
    receipt["assertions"] = artifact_assertions(archive, artifact.get("digest"), producer.get("reportPath"))
    validate_unpublished()
    return {"name": producer["checkName"], "head_sha": source, "status": "completed",
            "conclusion": "success", "completed_at": now.isoformat(),
            "output": {"title": "Source-bound artifact evidence", "summary": "Artifact bytes and declared assertions verified; not human acceptance.",
                       "text": json.dumps(receipt, ensure_ascii=False, separators=(",", ":"))}}


def publish_evidence(repo, source, acceptance_id, kind, run_id, attempt, job_id,
                     artifact_id, trusted_policy_digest, api, download, now=None):
    """Publish once, then read back and verify the ACTUAL App and exact payload.

    api supports method/payload for the single POST /check-runs. No automatic
    retry: ambiguous writes need operator reconciliation. No Issue, ref, merge,
    release or human-decision writes occur. Wrong publisher identity fails.
    """
    request = prepare_evidence(repo, source, acceptance_id, kind, run_id, attempt,
                               job_id, artifact_id, trusted_policy_digest, api, download, now)
    response = api(f"repos/{repo}/check-runs", method="POST", payload=request)
    check_id = response.get("id") if isinstance(response, dict) else None
    if not rv.receipt_positive(check_id):
        raise ValueError("publication identity unavailable; reconcile before retry")
    receipt = rv.receipt_json(request["output"]["text"])
    link = f"https://api.github.com/repos/{repo}/check-runs/{check_id}#{rv.receipt_digest(receipt)}"
    verifier, scope, item, _ = _context(repo, source, acceptance_id, kind, trusted_policy_digest,
                                       api, now or datetime.now(timezone.utc))
    verifier.verify(item, scope["targetRelease"], kind, link, {"mergedSha": source})
    return link
