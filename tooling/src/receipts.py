"""ACC-2/3 receipt verifier shared by Health and Release; stdlib, read-only.

A reviewed policy trusts dedicated GitHub Apps, not editable owner markers or the
product's GITHUB_TOKEN. The attestor authenticates assertions/human decisions;
this verifier authenticates its publisher and checks scope/source/API bindings.
It never downloads or follows an arbitrary evidence URL.
"""
import base64
import hashlib
import json
import re
from datetime import datetime, timedelta, timezone

RECEIPT_KINDS = ("ci", "test", "ui", "security", "migration")
RECEIPT_MARKERS = {k: f"Acceptance-{k.title() if k != 'ui' else 'UI'}-Evidence" for k in RECEIPT_KINDS}
RECEIPT_MARKERS["ci"] = "Acceptance-CI-Receipt"
RECEIPT_POLICY = "acceptance/security/receipt-policy.json"
RECEIPT_SHA = re.compile(r"^[0-9a-f]{40}$")
RECEIPT_DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
# These shared identities are not independent evidence/approval authorities.
SHARED_APPS = {15368, 1144995}  # github-actions, chatgpt-codex-connector
CONTROL_PATHS = ("kavosh.project.json", "acceptance", ".github", ".gitattributes", ".gitmodules")



# Base source provenance is part of the SAME H/G proof evaluator.
ACCEPTANCE_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ACCEPTANCE_RELEASE_RE = re.compile(r"^v([0-9]+)[.]([0-9]+)[.]([0-9]+)$")
ACCEPTANCE_RUN_URL = re.compile(r"^https://github[.]com/([^/]+/[^/]+)/actions/runs/([0-9]+)(?:[/?#].*)?$")


def _json_file(repo, path, sha, api):
    raw = api(f"repos/{repo}/contents/{path}?ref={sha}")
    encoded = raw.get("content") if isinstance(raw, dict) else None
    if not encoded:
        raise RuntimeError(f"missing {path} at candidate SHA")
    try:
        return receipt_json(base64.b64decode(encoded).decode("utf-8"))
    except (ValueError, UnicodeDecodeError) as exc:
        raise RuntimeError(f"invalid JSON in {path}: {exc}") from exc


def _marker(body, name):
    # Horizontal whitespace only: an empty field must not consume the next line.
    # Duplicate values are ambiguous, even when both happen to agree.
    values = re.findall(rf"(?im)^[ \t]*{re.escape(name)}:[ \t]*([^\r\n]*)\r?$", body or "")
    return (values[0].strip() or None) if len(values) == 1 else None


def acceptance_run_problems(repo, merged_sha, body, workflow, api):
    """Bind base CI evidence to an approved workflow and the accepted source tree.

    This validates source provenance, not the semantic coverage of typed evidence
    URLs or the human identity behind an editable Accepted-By marker.
    """
    url = _marker(body, "Acceptance-Evidence-Run")
    match = ACCEPTANCE_RUN_URL.fullmatch(url or "")
    if not match or match.group(1).lower() != repo.lower():
        return ["missing same-repository Actions Acceptance-Evidence-Run"]
    if not isinstance(workflow, str) or not re.fullmatch(r"[.]github/workflows/[A-Za-z0-9._-]+[.]ya?ml", workflow):
        raise ValueError("invalid required workflow path")
    run = api(f"repos/{repo}/actions/runs/{match.group(2)}") or {}
    problems = []
    if run.get("status") != "completed" or run.get("conclusion") != "success":
        problems.append("referenced Actions evidence run is not successful")
    if str(run.get("id")) != match.group(2):
        problems.append("referenced Actions evidence run identity does not match")
    if (run.get("repository") or {}).get("full_name", "").lower() != repo.lower():
        problems.append("evidence run repository does not match")
    if (run.get("head_repository") or {}).get("full_name", "").lower() != repo.lower():
        problems.append("evidence source repository does not match")
    path = run.get("path")
    if not isinstance(path, str) or path.split("@", 1)[0] != workflow:
        problems.append("evidence run is not the declared required CI workflow")
    source = run.get("head_sha")
    if not isinstance(source, str) or not ACCEPTANCE_SHA_RE.fullmatch(source):
        return problems + ["evidence run has no valid source SHA"]
    if not isinstance(merged_sha, str) or not ACCEPTANCE_SHA_RE.fullmatch(merged_sha):
        return problems + ["cannot bind evidence without a valid accepted merged SHA"]
    if source == merged_sha:
        return problems

    # Squash changes commit identity. Permit a PR-head receipt only with explicit
    # merged-PR provenance AND identical full Git trees; ancestry alone is not proof.
    pr_number = _marker(body, "Acceptance-Evidence-PR")
    if not pr_number or not re.fullmatch(r"[1-9][0-9]*", pr_number):
        return problems + ["evidence source SHA differs from accepted merged SHA; verified Acceptance-Evidence-PR required"]
    pr = api(f"repos/{repo}/pulls/{pr_number}") or {}
    base, head = pr.get("base") or {}, pr.get("head") or {}
    if (not pr.get("merged_at") or pr.get("merge_commit_sha") != merged_sha
            or base.get("ref") != "main" or head.get("sha") != source
            or (base.get("repo") or {}).get("full_name", "").lower() != repo.lower()
            or (head.get("repo") or {}).get("full_name", "").lower() != repo.lower()):
        return problems + ["evidence PR does not prove the exact accepted squash/source relationship"]
    trees = []
    for commit_sha in (source, merged_sha):
        commit = api(f"repos/{repo}/git/commits/{commit_sha}") or {}
        tree = (commit.get("tree") or {}).get("sha")
        if commit.get("sha") != commit_sha or not isinstance(tree, str) or not ACCEPTANCE_SHA_RE.fullmatch(tree):
            return problems + ["source tree identity unavailable for evidence PR"]
        trees.append(tree)
    if trees[0] != trees[1]:
        problems.append("PR evidence tree differs from accepted merge; collect merged-source CI evidence")
    return problems


def acceptance_source_reasons(repo, sha, api):
    """ACC-3: release-readiness from versioned scope + live GitHub Issue/Actions evidence."""
    manifest = _json_file(repo, "kavosh.project.json", sha, api)
    if manifest.get("acceptance", {}).get("mode", "none") != "continuous":
        return []
    scope = _json_file(repo, "acceptance/scope.json", sha, api)
    reasons = []
    if scope.get("schemaVersion") != 1:
        reasons.append("acceptance scope schemaVersion must be 1")
    target = scope.get("targetRelease")
    tm = ACCEPTANCE_RELEASE_RE.fullmatch(target or "")
    if not tm:
        reasons.append("acceptance targetRelease must match vX.Y.Z")
    items = scope.get("items")
    if not isinstance(items, list) or not items:
        return reasons + ["continuous acceptance scope must contain at least one item"]
    target_tuple = tuple(map(int, tm.groups())) if tm else None
    seen = set()
    marker_for = {
        "test": "Acceptance-Test-Evidence",
        "ui": "Acceptance-UI-Evidence",
        "security": "Acceptance-Security-Evidence",
        "migration": "Acceptance-Migration-Evidence",
    }
    for item in items:
        if not isinstance(item, dict):
            reasons.append("acceptance scope contains a non-object item")
            continue
        aid = item.get("id") or "<missing-id>"
        if aid in seen:
            reasons.append(f"{aid}: duplicate acceptance ID")
            continue
        seen.add(aid)
        owner = item.get("owner")
        issue_no = item.get("issue")
        risk = item.get("risk")
        evidence = item.get("evidence") if isinstance(item.get("evidence"), list) else []
        if not isinstance(owner, str) or not owner:
            reasons.append(f"{aid}: invalid owner")
            continue
        if risk not in ("low", "medium", "high", "critical"):
            reasons.append(f"{aid}: invalid risk")
            continue
        if not evidence or "ci" not in evidence:
            reasons.append(f"{aid}: evidence must include ci")
            continue
        if risk in ("high", "critical") and "test" not in evidence:
            reasons.append(f"{aid}: high/critical risk requires test evidence")
            continue
        deferred = item.get("deferredTo")
        if deferred:
            dm = ACCEPTANCE_RELEASE_RE.fullmatch(deferred) if isinstance(deferred, str) else None
            defer_issue = item.get("deferIssue")
            if not dm or not target_tuple or tuple(map(int, dm.groups())) <= target_tuple:
                reasons.append(f"{aid}: invalid deferredTo")
                continue
            if not isinstance(defer_issue, int) or defer_issue <= 0:
                reasons.append(f"{aid}: deferIssue required")
                continue
            issue = api(f"repos/{repo}/issues/{defer_issue}")
            if issue.get("state") != "closed":
                reasons.append(f"{aid}: defer approval issue #{defer_issue} is not closed")
                continue
            approved = _marker(issue.get("body") or "", "Defer-Approved-By")
            if approved != f"@{owner}":
                reasons.append(f"{aid}: defer is not approved by @{owner}")
            continue

        if not isinstance(issue_no, int) or issue_no <= 0:
            reasons.append(f"{aid}: invalid canonical issue")
            continue
        issue = api(f"repos/{repo}/issues/{issue_no}")
        body = issue.get("body") or ""
        if issue.get("state") != "closed":
            reasons.append(f"{aid}: acceptance issue #{issue_no} is not closed")
            continue
        accepted_by = _marker(body, "Accepted-By")
        if accepted_by != f"@{owner}":
            reasons.append(f"{aid}: missing Accepted-By: @{owner}")
        merged_sha = _marker(body, "Acceptance-Merged-SHA")
        if not merged_sha or not ACCEPTANCE_SHA_RE.fullmatch(merged_sha):
            reasons.append(f"{aid}: missing valid Acceptance-Merged-SHA")
        else:
            cmp = api(f"repos/{repo}/compare/{merged_sha}...{sha}")
            if cmp.get("status") not in ("ahead", "identical"):
                reasons.append(f"{aid}: merged SHA is not an ancestor of candidate")
        workflow = (manifest.get("ci") or {}).get("requiredWorkflow") or ".github/workflows/ci.yml"
        for problem in acceptance_run_problems(repo, merged_sha, body, workflow, api):
            reasons.append(f"{aid}: {problem}")
        for ev in evidence:
            marker = marker_for.get(ev)
            if marker and not re.match(r"^https://\S+$", _marker(body, marker) or ""):
                reasons.append(f"{aid}: missing {marker}")
    return reasons

def receipt_digest(value):
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return "sha256:" + hashlib.sha256(raw.encode("utf-8")).hexdigest()


def receipt_marker(body, name):
    values = re.findall(rf"(?im)^[ \t]*{re.escape(name)}:[ \t]*([^\r\n]*)\r?$", body or "")
    return values[0].strip() if len(values) == 1 and values[0].strip() else None


def receipt_time(value):
    if not isinstance(value, str):
        raise ValueError("receipt timestamp missing")
    stamp = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if stamp.tzinfo is None:
        raise ValueError("receipt timestamp must include timezone")
    return stamp.astimezone(timezone.utc)


def receipt_json(raw):
    def unique(pairs):
        obj = {}
        for key, value in pairs:
            if key in obj:
                raise ValueError("duplicate receipt JSON key")
            obj[key] = value
        return obj
    def invalid(_):
        raise ValueError("non-finite receipt JSON number")
    return json.loads(raw, object_pairs_hook=unique, parse_constant=invalid)


def receipt_positive(value):
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def receipt_path(value):
    return (isinstance(value, str) and bool(value) and not value.startswith("/")
            and not any(x in value for x in ("\\", "*", "?", "[", "\x00"))
            and all(part not in ("", ".", "..") for part in value.split("/")))


def receipt_contract_problems(item):
    """Validate the proof contract before any attestor or product evidence is read."""
    if not isinstance(item, dict):
        return ["acceptance item must be an object"]
    problems = []
    if not re.fullmatch(r"AC-[0-9]{3,}", str(item.get("id", ""))):
        problems.append("invalid acceptance ID")
    kinds = item.get("evidence")
    if (not isinstance(kinds, list) or not kinds or any(k not in RECEIPT_KINDS for k in kinds)
            or len(kinds) != len(set(kinds)) or "ci" not in kinds):
        problems.append("invalid evidence kinds")
        kinds = []
    if "evidencePaths" in item:
        paths = item["evidencePaths"]
        if (not isinstance(paths, list) or not paths or len(paths) > 100
                or not all(receipt_path(p) for p in paths) or len(paths) != len(set(paths))):
            problems.append("evidencePaths must be unique literal repository paths")
    assertions = item.get("assertions", {})
    if not isinstance(assertions, dict):
        problems.append("assertions must map evidence kind to expected assertion IDs")
        assertions = {}
    for kind in kinds:
        values = assertions.get(kind)
        if (not isinstance(values, list) or not values or len(values) > 500
                or not all(isinstance(v, str) and v.strip() == v and 0 < len(v) <= 300 for v in values)
                or len(values) != len(set(values))):
            problems.append(f"{kind}: explicit unique assertion IDs required")
    return problems


class ReceiptVerifier:
    def __init__(self, repo, candidate, policy, api, now=None):
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repo):
            raise ValueError("invalid receipt repository")
        if not RECEIPT_SHA.fullmatch(candidate or ""):
            raise ValueError("invalid receipt candidate SHA")
        self.repo, self.candidate, self.policy, self.api = repo, candidate, policy, api
        self.now = now or datetime.now(timezone.utc)
        self.cache = {}
        self.valid_until = None
        self.evidence_completed = None
        if not isinstance(policy, dict) or type(policy.get("schemaVersion")) is not int or policy["schemaVersion"] != 1:
            raise ValueError("receipt policy schemaVersion must be 1")
        self.producers = policy.get("producers")
        if not isinstance(self.producers, dict) or not self.producers:
            raise ValueError("receipt policy needs reviewed dedicated App producers")
        age = policy.get("maxAgeDays")
        if not receipt_positive(age) or age > 365:
            raise ValueError("receipt policy maxAgeDays must be 1..365")
        self.max_age = timedelta(days=age)

    def get(self, suffix):
        if suffix not in self.cache:
            self.cache[suffix] = self.api(f"repos/{self.repo}/{suffix}")
        value = self.cache[suffix]
        if not isinstance(value, dict):
            raise ValueError("receipt API object unavailable")
        return value

    def tree(self, sha):
        if not isinstance(sha, str) or not RECEIPT_SHA.fullmatch(sha):
            raise ValueError("invalid receipt source SHA")
        commit = self.get(f"git/commits/{sha}")
        tree = (commit.get("tree") or {}).get("sha")
        if commit.get("sha") != sha or not RECEIPT_SHA.fullmatch(tree or ""):
            raise ValueError("source tree identity unavailable")
        return tree

    def entry(self, tree, path):
        current = tree
        parts = path.split("/")
        for index, part in enumerate(parts):
            data = self.get(f"git/trees/{current}")
            if data.get("sha") != current or data.get("truncated") is not False:
                raise ValueError("source tree incomplete or mismatched")
            matches = [x for x in data.get("tree", []) if x.get("path") == part]
            if not matches:
                return None
            if len(matches) != 1:
                raise ValueError("ambiguous source tree entry")
            node = matches[0]
            if node.get("mode") in ("120000", "160000"):
                raise ValueError("evidence paths cannot hide symlinks/submodules")
            current = node.get("sha")
            if not RECEIPT_SHA.fullmatch(current or ""):
                raise ValueError("invalid source entry identity")
            if index == len(parts) - 1:
                return (node.get("mode"), node.get("type"), current)
            if node.get("type") != "tree":
                raise ValueError("non-directory evidence path parent")
        raise ValueError("invalid evidence path")

    def unchanged(self, source, source_tree, item):
        if self.tree(source) != source_tree:
            raise ValueError("receipt source tree mismatch")
        current_tree = self.tree(self.candidate)
        if source != self.candidate:
            comparison = self.get(f"compare/{source}...{self.candidate}")
            if comparison.get("status") not in ("ahead", "identical"):
                raise ValueError("receipt source is not an ancestor of candidate")
        paths = item.get("evidencePaths")
        if source_tree == current_tree:
            for path in paths or []:
                if self.entry(source_tree, path) is None:
                    raise ValueError(f"declared evidence path does not exist: {path}")
            return
        if not paths:
            raise ValueError("candidate tree changed; fresh evidence or reviewed evidencePaths required")
        for path in sorted(set(paths) | set(CONTROL_PATHS)):
            before, after = self.entry(source_tree, path), self.entry(current_tree, path)
            if before != after or (path in paths and before is None):
                raise ValueError(f"evidence invalidated by source change: {path}")

    def verify(self, item, target, kind, link, bindings):
        producer = self.producers.get(kind)
        if not isinstance(producer, dict):
            raise ValueError(f"no reviewed producer for {kind}")
        app = producer.get("appId")
        if not receipt_positive(app) or app in SHARED_APPS or not producer.get("checkName"):
            raise ValueError("a dedicated, independently controlled App publisher is required")
        if kind in ("approval", "defer"):
            evidence_apps = {p.get("appId") for k, p in self.producers.items()
                             if k in RECEIPT_KINDS and isinstance(p, dict)}
            if app in evidence_apps:
                raise ValueError("decision publisher must be independent of evidence publishers")
        match = re.fullmatch(
            rf"https://api[.]github[.]com/repos/{re.escape(self.repo)}/check-runs/([1-9][0-9]*)#(sha256:[0-9a-f]{{64}})",
            link or "", re.I)
        if not match:
            raise ValueError("same-repository check-run URL with exact sha256 receipt digest required")
        check = self.get(f"check-runs/{match.group(1)}")
        if (check.get("id") != int(match.group(1)) or (check.get("app") or {}).get("id") != app
                or check.get("name") != producer["checkName"] or check.get("status") != "completed"
                or check.get("conclusion") != "success"):
            raise ValueError("receipt check identity/publisher/result mismatch")
        raw = (check.get("output") or {}).get("text")
        if not isinstance(raw, str) or len(raw.encode("utf-8")) > 60000:
            raise ValueError("receipt JSON text missing or oversized")
        receipt = receipt_json(raw)
        if not isinstance(receipt, dict) or receipt_digest(receipt) != match.group(2).lower():
            raise ValueError("receipt digest changed or payload invalid")
        expected = {"schemaVersion": 1, "repository": self.repo, "acceptanceId": item["id"],
                    "kind": kind, "targetRelease": target, "scopeDigest": receipt_digest(item),
                    "policyDigest": receipt_digest(self.policy), "outcome": "pass"}
        if type(receipt.get("schemaVersion")) is not int or any(receipt.get(k) != value for k, value in expected.items()):
            raise ValueError("receipt scope/kind/policy/outcome mismatch")
        issued, expires = receipt_time(receipt.get("issuedAt")), receipt_time(receipt.get("expiresAt"))
        completed = receipt_time(check.get("completed_at"))
        if not (issued <= completed <= self.now < expires and timedelta(0) < expires - issued <= self.max_age):
            raise ValueError("receipt expired, future-dated or validity window invalid")
        self.valid_until = min(self.valid_until, expires) if self.valid_until else expires
        source = receipt.get("sourceSha")
        if check.get("head_sha") != source:
            raise ValueError("receipt check source mismatch")
        if kind not in ("approval", "defer") and source != bindings.get("mergedSha"):
            raise ValueError("typed receipt must bind the accepted merged SHA")
        self.unchanged(source, receipt.get("sourceTree"), item)
        if kind in ("approval", "defer"):
            if (producer.get("mode") != "decision" or receipt.get("subject") != item.get("owner")
                    or receipt.get("decision") != ("accept" if kind == "approval" else "defer")
                    or receipt.get("bindingsDigest") != receipt_digest(bindings)):
                raise ValueError("independent decision is not bound to this owner/scope/evidence")
            if kind == "approval" and self.evidence_completed and issued < self.evidence_completed:
                raise ValueError("approval predates the bound evidence")
            return
        self.evidence_completed = max(self.evidence_completed, completed) if self.evidence_completed else completed
        assertions = receipt.get("assertions")
        if not isinstance(assertions, list) or not assertions or any(
                not isinstance(x, dict) or x.get("outcome") != "pass" or not isinstance(x.get("id"), str)
                for x in assertions):
            raise ValueError("receipt needs actual passing assertion outcomes")
        ids = [x["id"] for x in assertions]
        if len(ids) != len(set(ids)) or not set(item["assertions"][kind]).issubset(ids):
            raise ValueError("receipt does not cover the declared assertions")
        mode = producer.get("mode")
        if mode == "manual" and kind != "ci":
            # The trusted App attests externally held UAT. No arbitrary URL is fetched.
            if not RECEIPT_DIGEST.fullmatch(receipt.get("externalEvidenceDigest") or ""):
                raise ValueError("manual receipt needs immutable external evidence digest")
            return
        if mode != "actions":
            raise ValueError("unsupported evidence producer mode")
        for field in ("runId", "runAttempt", "jobId", "artifactId"):
            if not receipt_positive(receipt.get(field)):
                raise ValueError(f"invalid receipt {field}")
        run_id, attempt = receipt["runId"], receipt["runAttempt"]
        run = self.get(f"actions/runs/{run_id}/attempts/{attempt}")
        job = self.get(f"actions/jobs/{receipt['jobId']}")
        workflow = producer.get("workflow")
        if not isinstance(workflow, str) or not re.fullmatch(r"[.]github/workflows/[A-Za-z0-9._-]+[.]ya?ml", workflow):
            raise ValueError("invalid producer workflow path")
        if (run.get("id") != run_id or run.get("run_attempt") != attempt
                or (run.get("path") or "").split("@", 1)[0] != workflow
                or run.get("head_sha") != source or run.get("status") != "completed"
                or run.get("conclusion") != "success"
                or (run.get("repository") or {}).get("full_name") != self.repo
                or (run.get("head_repository") or {}).get("full_name") != self.repo):
            raise ValueError("receipt workflow/source/attempt/result mismatch")
        if (job.get("id") != receipt["jobId"] or job.get("run_id") != run_id
                or job.get("run_attempt") != attempt or job.get("head_sha") != source
                or job.get("name") != producer.get("job") or not producer.get("job")
                or job.get("status") != "completed" or job.get("conclusion") != "success"):
            raise ValueError("receipt job/source/attempt/result mismatch")
        artifact = self.get(f"actions/artifacts/{receipt['artifactId']}")
        if (artifact.get("id") != receipt["artifactId"] or artifact.get("expired") is not False
                or not receipt_positive(artifact.get("size_in_bytes"))
                or not RECEIPT_DIGEST.fullmatch(receipt.get("artifactDigest") or "")
                or artifact.get("digest") != receipt["artifactDigest"]
                or (artifact.get("workflow_run") or {}).get("id") != run_id
                or (artifact.get("workflow_run") or {}).get("head_sha") != source
                or artifact.get("name") != f"kavosh-evidence-{run_id}-{attempt}-{kind}"):
            raise ValueError("receipt artifact missing/expired/mismatched")
        if not (receipt_time(run.get("run_started_at")) <= receipt_time(artifact.get("created_at"))
                <= receipt_time(job.get("completed_at")) <= issued):
            raise ValueError("artifact/job/receipt chronology mismatch")
        artifact_expiry = receipt_time(artifact.get("expires_at"))
        if artifact_expiry <= self.now:
            raise ValueError("receipt artifact expired")
        self.valid_until = min(self.valid_until, artifact_expiry)


def receipt_scope_report(repo, candidate, manifest, scope, api, now=None):
    """Same typed-evidence + decision verdict in H and G. No network on non-continuous projects."""
    result = {"verified": [], "deferred": [], "problems": []}
    if (manifest.get("acceptance") or {}).get("mode") != "continuous":
        return result
    def problem(text):
        result["problems"].append(text)
    try:
        # Caller data must describe this exact candidate, not a moving default ref.
        exact_manifest = _json_file(repo, "kavosh.project.json", candidate, api)
        exact_scope = _json_file(repo, "acceptance/scope.json", candidate, api)
        if exact_manifest != manifest or exact_scope != scope:
            raise ValueError("acceptance contract changed during snapshot; refresh exact candidate")
        source_problems = acceptance_source_reasons(repo, candidate, api)
        result["problems"].extend(source_problems)
        raw = api(f"repos/{repo}/contents/{RECEIPT_POLICY}?ref={candidate}")
        policy = receipt_json(base64.b64decode(raw["content"], validate=False).decode("utf-8"))
        verifier = ReceiptVerifier(repo, candidate, policy, api, now)
        items = scope.get("items")
        target = scope.get("targetRelease")
        if type(scope.get("schemaVersion")) is not int or scope["schemaVersion"] != 1 or not re.fullmatch(r"v[0-9]+[.][0-9]+[.][0-9]+", target or ""):
            raise ValueError("invalid release scope version/target")
        if not isinstance(items, list) or not items:
            raise ValueError("nonempty receipt scope required")
        seen = set()
        for item in items:
            bad = receipt_contract_problems(item)
            if bad:
                problem("receipt contract: " + "; ".join(bad))
                continue
            aid = item["id"]
            if aid in seen:
                problem(f"{aid}: duplicate receipt scope ID")
                continue
            seen.add(aid)
            deferred = bool(item.get("deferredTo"))
            number = item.get("deferIssue") if deferred else item.get("issue")
            if not receipt_positive(number) or not isinstance(item.get("owner"), str) or not item["owner"]:
                problem(f"{aid}: invalid canonical issue/owner")
                continue
            issue = verifier.get(f"issues/{number}")
            if issue.get("state") != "closed" or "pull_request" in issue:
                problem(f"{aid}: canonical acceptance/decision Issue is not closed")
                continue
            body = issue.get("body") or ""
            bindings = {"mergedSha": receipt_marker(body, "Acceptance-Merged-SHA"),
                        "ciRun": receipt_marker(body, "Acceptance-Evidence-Run"),
                        "evidence": {k: receipt_marker(body, RECEIPT_MARKERS[k]) for k in item["evidence"]}}
            if deferred:
                future = item["deferredTo"]
                if (not isinstance(future, str) or not re.fullmatch(r"v[0-9]+[.][0-9]+[.][0-9]+", future)
                        or tuple(map(int, future[1:].split("."))) <= tuple(map(int, target[1:].split(".")))):
                    problem(f"{aid}: defer target is not a future release")
                    continue
                bindings = {"deferredTo": future, "deferIssue": number}
            before = len(result["problems"])
            verifier.evidence_completed = None
            kinds = ["defer"] if deferred else item["evidence"] + ["approval"]
            for kind in kinds:
                marker = ("Defer-Decision-Evidence" if kind == "defer" else "Acceptance-Decision-Evidence"
                          if kind == "approval" else RECEIPT_MARKERS[kind])
                try:
                    verifier.verify(item, target, kind, receipt_marker(body, marker), bindings)
                except (ValueError, TypeError, KeyError, AttributeError, RuntimeError, OSError) as exc:
                    # Error classes carry no remote response/URL contents into a report.
                    detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
                    problem(f"{aid}/{kind}: {detail}")
            if len(result["problems"]) == before and not source_problems:
                result["deferred" if deferred else "verified"].append(aid)
        if verifier.valid_until and verifier.valid_until <= (now or datetime.now(timezone.utc)):
            result["verified"], result["deferred"] = [], []
            problem("receipt expired during verification")
    except (ValueError, TypeError, KeyError, AttributeError, RuntimeError, OSError) as exc:
        detail = str(exc) if isinstance(exc, ValueError) else type(exc).__name__
        problem("receipt verification unavailable: " + detail)
    return result
