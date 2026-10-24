#!/usr/bin/env python3
"""REL-7: create an immutable release-candidate only from exact current main with required checks green."""
import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
import urllib.error
import urllib.request
from receipts import ReceiptVerifier, _json_file, receipt_marker, RECEIPT_SHA, receipt_positive, receipt_contract_problems # __EMBED_RECEIPTS__

RC_RE = re.compile(r"^v([0-9]+)[.]([0-9]+)[.]([0-9]+)-rc[.]([0-9]+)$")
FINAL_RE = re.compile(r"^v([0-9]+)[.]([0-9]+)[.]([0-9]+)$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
DEFAULT_REQUIRED = ("required", "main-guard / main-guard")
RUN_URL = re.compile(r"^https://github[.]com/([^/]+/[^/]+)/actions/runs/([1-9][0-9]*)/?$")


def staging_contract_present(manifest):
    """Distinguish a valid legacy manifest from a malformed release object."""
    if not isinstance(manifest, dict):
        raise ValueError("manifest must be an object")
    if "release" not in manifest:
        return False
    release = manifest["release"]
    if not isinstance(release, dict):
        raise ValueError("manifest release must be an object")
    return "testStaging" in release


def staging_reasons(repo, sha, api, run_id, attempt, tag, env, now_fn=None):
    """Validate opt-in Test staging. Open canonical Issues are valid evidence locations."""
    manifest = _json_file(repo, "kavosh.project.json", sha, api)
    if not isinstance(manifest, dict):
        return ["staging manifest is not an object"]
    try:
        enabled = staging_contract_present(manifest)
    except ValueError as exc:
        return [str(exc)]
    required = env.get("KAVOSH_RC_REQUIRE_TEST_STAGING") == "1"
    if required and not enabled:
        return ["Test staging reusable workflow requires release.testStaging in the exact manifest"]
    if enabled and not required:
        return ["opt-in Test staging requires kavosh-test-staging reusable workflow"]
    if not enabled:
        return []
    release = manifest["release"]
    contract = release["testStaging"]
    if not isinstance(contract, dict):
        return ["invalid release.testStaging contract"]
    reasons = []
    owner = manifest.get("owner")
    if (not isinstance(owner, str) or not re.fullmatch(r"[A-Za-z0-9-]+", owner)
            or type(contract.get("schemaVersion")) is not int or contract["schemaVersion"] != 1
            or contract.get("target") != "test"):
        return ["invalid release.testStaging contract or manifest owner"]
    acceptance = manifest.get("acceptance")
    if not isinstance(acceptance, dict) or acceptance.get("mode") != "continuous":
        return ["release.testStaging is NOT_SUPPORTED unless acceptance.mode is continuous"]
    if release.get("strategy") != "release-please":
        return ["release.testStaging is NOT_SUPPORTED unless release.strategy is release-please"]
    deploy = manifest.get("deploy") or {}
    if (not isinstance(deploy, dict) or manifest.get("runtime") != "server"
            or "test" not in (deploy.get("environments") or [])):
        return ["release.testStaging requires a Test-capable server manifest"]
    if deploy.get("method") not in ("pull-build", "pull-image"):
        return ["release.testStaging is NOT_SUPPORTED unless deploy.method is pull-build or pull-image"]
    if (not isinstance(run_id, (str, int)) or not str(run_id).isdigit() or int(run_id) <= 0
            or not isinstance(attempt, (str, int)) or not str(attempt).isdigit() or int(attempt) <= 0
            or str(env.get("GITHUB_RUN_ID")) != str(run_id)
            or str(env.get("GITHUB_RUN_ATTEMPT")) != str(attempt)):
        return ["Test staging run identity is missing or inconsistent"]
    run = api(f"repos/{repo}/actions/runs/{run_id}/attempts/{attempt}") or {}
    actor = (run.get("actor") or {}).get("login")
    trigger = (run.get("triggering_actor") or {}).get("login")
    workflow = contract.get("callerWorkflow")
    if (run.get("id") != int(run_id) or run.get("run_attempt") != int(attempt)
            or run.get("event") != "workflow_dispatch" or run.get("status") != "in_progress"
            or run.get("head_branch") != "main"
            or run.get("head_sha") != sha or (run.get("repository") or {}).get("full_name") != repo
            or (run.get("head_repository") or {}).get("full_name") != repo
            or actor != owner or trigger != owner
            or (run.get("actor") or {}).get("type") != "User"
            or (run.get("triggering_actor") or {}).get("type") != "User"
            or (run.get("path") or "").split("@", 1)[0] != workflow
            or not isinstance(workflow, str)
            or not re.fullmatch(r"[.]github/workflows/[A-Za-z0-9._-]+[.]ya?ml", workflow)
            or env.get("GITHUB_REF") != "refs/heads/main"):
        reasons.append("Test staging requires the manifest owner dispatching the declared workflow on exact current main")
    scope = _json_file(repo, "acceptance/scope.json", sha, api)
    if not isinstance(scope, dict):
        return reasons + ["staging acceptance scope is not an object"]
    if type(scope.get("schemaVersion")) is not int or scope.get("schemaVersion") != 1:
        reasons.append("staging acceptance scope schemaVersion must be integer 1")
    target = scope.get("targetRelease")
    tag_match = RC_RE.fullmatch(tag or "")
    if env.get("TAG") is not None and env.get("TAG") != tag:
        reasons.append("Test staging tag does not match the actual RC candidate")
    if not tag_match or target != "v" + ".".join(tag_match.groups()[:3]):
        reasons.append("staging RC base must exactly match acceptance scope targetRelease")
    items = scope.get("items")
    prereq = contract.get("prerequisites")
    if not isinstance(items, list) or not items or not isinstance(prereq, dict):
        return reasons + ["staging needs a nonempty exact acceptance scope and prerequisite map"]
    if set(prereq) != {"full", "originals", "recovery", "capacity"}:
        reasons.append("staging prerequisite map must contain exactly full, originals, recovery, and capacity")
    if any(not isinstance(item, dict) or not isinstance(item.get("id"), str) for item in items):
        return reasons + ["staging acceptance scope contains a malformed item"]
    by_id = {item.get("id"): item for item in items if isinstance(item, dict)}
    for category in ("full", "originals", "recovery", "capacity"):
        entry = prereq.get(category)
        item = by_id.get(entry.get("acceptanceId")) if isinstance(entry, dict) else None
        assertions = item.get("assertions") if isinstance(item, dict) else None
        test_ids = assertions.get("test") if isinstance(assertions, dict) else None
        kinds = item.get("evidence") if isinstance(item, dict) else None
        if (not isinstance(entry, dict) or set(entry) != {"acceptanceId", "assertion"}
                or not item or not isinstance(kinds, list) or "test" not in kinds
                or not isinstance(test_ids, list) or entry.get("assertion") not in test_ids):
            reasons.append(f"staging prerequisite {category} must map to a declared test assertion")
    policy = _json_file(repo, "acceptance/security/receipt-policy.json", sha, api)
    now_fn = now_fn or (lambda: datetime.now(timezone.utc))
    verifier = ReceiptVerifier(repo, sha, policy, api, now_fn())
    markers = {"test": "Staging-Test-Evidence", "security": "Staging-Security-Evidence",
               "migration": "Staging-Migration-Evidence"}
    seen = set()
    ci_cache = {}
    for item in items:
        if not isinstance(item, dict) or item.get("id") in seen:
            reasons.append("staging acceptance scope contains an invalid or duplicate item")
            continue
        seen.add(item.get("id"))
        bad_contract = receipt_contract_problems(item)
        if bad_contract:
            reasons.append(f"{item.get('id')}: invalid receipt scope contract")
            continue
        if (not isinstance(item.get("owner"), str) or not item["owner"].strip()
                or item.get("risk") not in ("low", "medium", "high", "critical")):
            reasons.append(f"{item.get('id')}: staging scope requires a nonempty owner and valid risk")
            continue
        if item.get("deferredTo"):
            reasons.append(f"{item.get('id')}: deferred scope items are unsupported for Test staging")
            continue
        issue_no = item.get("issue")
        if not receipt_positive(issue_no):
            reasons.append(f"{item.get('id')}: invalid canonical acceptance Issue")
            continue
        issue = api(f"repos/{repo}/issues/{issue_no}") or {}
        if "pull_request" in issue or issue.get("state") not in ("open", "closed"):
            reasons.append(f"{item.get('id')}: canonical acceptance Issue is unavailable")
            continue
        body = issue.get("body") or ""
        merged = receipt_marker(body, "Staging-Merged-SHA")
        if not isinstance(merged, str) or not RECEIPT_SHA.fullmatch(merged) or merged != sha:
            reasons.append(f"{item.get('id')}: Staging-Merged-SHA must equal exact staging candidate")
            continue
        bindings = {"mergedSha": sha, "stagingRun": str(run_id), "target": "test"}
        for kind in item.get("evidence", []):
            if kind == "ci":
                url = receipt_marker(body, "Staging-CI-Run")
                match = RUN_URL.fullmatch(url or "")
                if not match or match.group(1).lower() != repo.lower():
                    reasons.append(f"{item['id']}: missing same-repository Staging-CI-Run")
                    continue
                run_key = match.group(2)
                if run_key not in ci_cache:
                    ci_run = api(f"repos/{repo}/actions/runs/{run_key}") or {}
                    required = (manifest.get("ci") or {}).get("requiredWorkflow") or ".github/workflows/ci.yml"
                    ci_attempt = ci_run.get("run_attempt")
                    if (ci_run.get("id") != int(run_key) or not receipt_positive(ci_attempt)
                            or ci_run.get("event") not in ("push", "workflow_dispatch")
                            or ci_run.get("status") != "completed" or ci_run.get("conclusion") != "success"
                            or ci_run.get("head_sha") != sha or ci_run.get("head_branch") != "main"
                            or (ci_run.get("repository") or {}).get("full_name") != repo
                            or (ci_run.get("head_repository") or {}).get("full_name") != repo
                            or (ci_run.get("path") or "").split("@", 1)[0] != required):
                        ci_cache[run_key] = "Staging-CI-Run is not successful required-workflow evidence for the bound source"
                    else:
                        # Enumerate the exact latest API-reported attempt. A partial job list
                        # or an older attempt can never stand in for its required job.
                        job_rows, page, complete = [], 1, False
                        while page <= 10:
                            job_page = api(
                                f"repos/{repo}/actions/runs/{run_key}/attempts/{ci_attempt}/jobs?per_page=100&page={page}") or {}
                            batch = job_page.get("jobs") if isinstance(job_page, dict) else None
                            if not isinstance(batch, list):
                                break
                            job_rows.extend(batch)
                            if len(batch) < 100:
                                complete = True
                                break
                            page += 1
                        if not complete:
                            ci_cache[run_key] = "could not completely enumerate Staging-CI-Run jobs"
                        elif not any(isinstance(job, dict) and job.get("name") == "required"
                                     and job.get("run_id") == int(run_key) and job.get("run_attempt") == ci_attempt
                                     and job.get("head_sha") == sha and job.get("status") == "completed"
                                     and job.get("conclusion") == "success" for job in job_rows):
                            ci_cache[run_key] = "required job in Staging-CI-Run did not succeed"
                        else:
                            ci_cache[run_key] = None
                if ci_cache[run_key]:
                    reasons.append(f"{item['id']}: {ci_cache[run_key]}")
                continue
            if kind == "ui":
                # Test staging never substitutes for UI evidence or final acceptance.
                continue
            if kind not in ("test", "security", "migration"):
                reasons.append(f"{item['id']}: unsupported staging evidence kind {kind}")
                continue
            link = receipt_marker(body, markers.get(kind, ""))
            try:
                verifier.verify(item, target, kind, link, bindings)
            except (ValueError, TypeError, KeyError, RuntimeError, OSError) as exc:
                reasons.append(f"{item.get('id')}/{kind}: {str(exc) if isinstance(exc, ValueError) else type(exc).__name__}")
    if verifier.valid_until and verifier.valid_until <= now_fn():
        reasons.append("staging receipts expired during verification")
    return reasons


def parse_rc(tag):
    m = RC_RE.fullmatch(tag or "")
    return tuple(map(int, m.groups())) if m else None


def parse_final(tag):
    m = FINAL_RE.fullmatch(tag or "")
    return tuple(map(int, m.groups())) if m else None


def evaluate_checks(runs, required):
    latest = {}
    pending = {}
    for run in runs:
        name = run.get("name", "")
        if run.get("status") != "completed":
            pending[name] = run
        stamp = run.get("started_at") or run.get("created_at") or ""
        old = latest.get(name)
        old_stamp = (old or {}).get("started_at") or (old or {}).get("created_at") or ""
        pending_now = run.get("status") != "completed"
        pending_old = (old or {}).get("status") != "completed"
        if (old is None or stamp > old_stamp or
                (pending_now and not pending_old and (not stamp or stamp == old_stamp))):
            latest[name] = run
    latest.update(pending)
    reasons = []
    for name in required:
        run = latest.get(name)
        if run is None:
            reasons.append(f"missing required check '{name}'")
        elif run.get("status") != "completed":
            reasons.append(f"'{name}' is {run.get('status')}")
        elif run.get("conclusion") != "success":
            reasons.append(f"'{name}' concluded {run.get('conclusion')}")
    return reasons


def candidate_reasons(tag, sha, required, current_head, runs, tag_names):
    rc = parse_rc(tag)
    reasons = []
    if not rc:
        reasons.append("tag must match vX.Y.Z-rc.N")
        return reasons
    if not SHA_RE.fullmatch(sha or ""):
        reasons.append("expected SHA must be 40 lowercase hex")
    if current_head != sha:
        reasons.append("expected SHA is not the current main head")
    required = list(dict.fromkeys(required))
    if not set(DEFAULT_REQUIRED).issubset(required):
        reasons.append("required checks must include required and main-guard / main-guard")
    reasons += evaluate_checks(runs, required)

    base = rc[:3]
    rc_number = rc[3]
    names = set(tag_names)
    if tag in names:
        reasons.append("RC tag already exists")
    final_name = "v" + ".".join(map(str, base))
    if final_name in names:
        reasons.append("final tag for this version already exists")

    finals = [v for name in names if (v := parse_final(name))]
    if finals and max(finals) >= base:
        reasons.append("RC base version must be newer than the latest final version")

    same_base = [r[3] for name in names if (r := parse_rc(name)) and r[:3] == base]
    if same_base and rc_number <= max(same_base):
        reasons.append("RC number must be greater than every existing RC for this version")
    return reasons


def gh_api(path, method="GET", payload=None, allow_missing=False):
    base = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GitHub API token is unavailable")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"{base}/{path.lstrip('/')}", data=data, method=method,
        headers={"Authorization": f"Bearer {token}",
                 "Accept": "application/vnd.github+json",
                 "X-GitHub-Api-Version": "2022-11-28",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        if allow_missing and exc.code == 404:
            return None
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub API {method} {path}: HTTP {exc.code} {detail}") from exc
    return json.loads(raw) if raw.strip() else {}


def paged(repo, suffix, key=None):
    out = []
    for page in range(1, 11):
        sep = "&" if "?" in suffix else "?"
        data = gh_api(f"repos/{repo}/{suffix}{sep}per_page=100&page={page}")
        batch = data.get(key, []) if key else data
        out += batch
        if len(batch) < 100:
            break
    return out


def run_gate(repo, tag, sha, required, run_id=None, attempt=None, env=None):
    head = gh_api(f"repos/{repo}/branches/main").get("commit", {}).get("sha")
    runs = paged(repo, f"commits/{sha}/check-runs", key="check_runs")
    tags = [item.get("name", "") for item in paged(repo, "tags")]
    reasons = candidate_reasons(tag, sha, required, head, runs, tags)
    if run_id and attempt:
        reasons.extend(staging_reasons(repo, sha, gh_api, run_id, attempt, tag, env or {}))
    else:
        try:
            candidate_manifest = _json_file(repo, "kavosh.project.json", sha, gh_api)
            enabled = staging_contract_present(candidate_manifest)
            if (enabled and (env or {}).get("KAVOSH_RC_REQUIRE_TEST_STAGING") != "1"):
                reasons.append("opt-in Test staging requires kavosh-test-staging reusable workflow")
            elif (not enabled and (env or {}).get("KAVOSH_RC_REQUIRE_TEST_STAGING") == "1"):
                reasons.append("Test staging reusable workflow requires release.testStaging in the exact manifest")
            elif enabled:
                reasons.append("Test staging identity is unavailable; refusing opt-in RC")
        except (ValueError, RuntimeError, KeyError, TypeError, AttributeError) as exc:
            reasons.append(f"manifest staging check unavailable: {type(exc).__name__}")
    if gh_api(f"repos/{repo}/releases/tags/{tag}", allow_missing=True) is not None:
        reasons.append("GitHub Release for this RC already exists")
    return list(dict.fromkeys(reasons))


def create_prerelease(repo, tag, sha):
    release = gh_api(f"repos/{repo}/releases", method="POST", payload={
        "tag_name": tag,
        "target_commitish": sha,
        "name": tag,
        "prerelease": True,
        "draft": False,
        "generate_release_notes": True,
    })
    ref = gh_api(f"repos/{repo}/git/ref/tags/{tag}")
    actual = ref.get("object", {}).get("sha")
    if actual != sha or release.get("tag_name") != tag or release.get("prerelease") is not True:
        raise RuntimeError(f"post-create RC verification failed: tag points to {actual or '?'}")
    return release


def main(argv=None):
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True)
    p.add_argument("--tag", required=True)
    p.add_argument("--sha", required=True)
    p.add_argument("--required", default=",".join(DEFAULT_REQUIRED))
    p.add_argument("--run-id", default=os.environ.get("GITHUB_RUN_ID"))
    p.add_argument("--run-attempt", default=os.environ.get("GITHUB_RUN_ATTEMPT"))
    args = p.parse_args(argv)
    required = [x.strip() for x in args.required.split(",") if x.strip()]
    try:
        reasons = run_gate(args.repo, args.tag, args.sha, required, args.run_id, args.run_attempt, os.environ)
    except RuntimeError as exc:
        print(f"REL-7 gate CLOSED: {exc}")
        return 1
    if reasons:
        print("REL-7 gate CLOSED:")
        for reason in reasons:
            print(f"  - {reason}")
        return 1
    # Re-read the exact main/check/tag state immediately before mutation. The owner authorization
    # is capability-scoped to this tag + SHA and expires if main/check state moved.
    try:
        reasons = run_gate(args.repo, args.tag, args.sha, required, args.run_id, args.run_attempt, os.environ)
    except RuntimeError as exc:
        print(f"REL-7 pre-create gate CLOSED: {exc}")
        return 1
    if reasons:
        print("REL-7 pre-create gate CLOSED:")
        for reason in reasons:
            print(f"  - {reason}")
        return 1
    try:
        release = create_prerelease(args.repo, args.tag, args.sha)
    except RuntimeError as exc:
        print(f"REL-7 creation FAILED: {exc}")
        return 1
    print(f"REL-7 RC CREATED {release.get('html_url', args.tag)}")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a", encoding="utf-8") as fh:
            fh.write(f"tag={args.tag}\n")
            fh.write(f"release-url={release.get('html_url', '')}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
