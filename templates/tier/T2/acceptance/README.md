# Acceptance receipts — producer contract v1 (attested items)

New future-standard consumers may select `acceptance.assurance=risk-based` to verify low/medium CI-only scoped items through exact-source GitHub Actions without independent publisher services. The accepted owner marker is only a declared identity, **not independent human verification**. High/critical, deferred or specialist evidence still uses this full attested contract. Omitting assurance retains strict attested behavior.

`scope.json` declares release intent only. It never stores acceptance status.
`security/receipt-policy.json` is a reviewed trust policy, not a status ledger.
The scaffold deliberately has **no trusted producers**. It cannot release a
continuous-acceptance project until real producer identities and receipts exist.
Do not invent App IDs, authentication, artifacts, assertions, or accepted states.

## Trust and operating boundary

The reference adapter accepts digest-pinned JSON in a dedicated GitHub App check's
`output.text`. Product Actions tokens and agent connector identities are not
independent publishers. The decision publisher is separate from evidence publishers.
An owner must select/install and review the real services; this template does not
install an App or grant it credentials. Never put the attestor's private key/token
in product jobs or an agent-accessible workspace.

The evidence publisher must read actual immutable run artifacts, derive assertion
outcomes, and verify their source. The decision publisher must authenticate the
human outside the agent's credentials and bind their actual decision to the exact
scope and evidence digests. An API that stamps caller-provided `pass` JSON without
checking the evidence is **not** a conforming attestor. The gate verifies App
identity and bindings; it does not independently prove the truth of a dishonest
attestor or automatically understand every product requirement.

Policy edits require security/control-plane review. A maintainer who can bypass
that review can replace the trust policy; this protocol is not a substitute for
protecting repository administration, the merge path, and attestor credentials.

## Optional Test staging

An owner may opt into the guarded REL-7 Test staging path by declaring
`release.testStaging` in the exact main manifest. Presence activates the guard;
there is no dispatch input that can disable it. The caller must be the exact
workflow declared by the manifest, and the live dispatch actor and
`triggering_actor` must both match the manifest owner. The target is fixed to
Test. Prerequisites refer to existing scope assertions, for example:

The supported profile also requires `acceptance.mode=continuous`,
`release.strategy=release-please`, and a Test-capable server deployment with
`deploy.method` set to `pull-build` or `pull-image`. Other profiles fail as
`NOT_SUPPORTED`; custom adapters are not implicitly covered.

To opt in, change the caller's reusable workflow reference to
`kavosh-test-staging.yml` and grant that caller `actions: read` and `issues: read`
alongside its existing `contents: write` and `checks: read`. The default
`kavosh-rc.yml` keeps its original permission contract and rejects a manifest
that opts into staging; the Test-staging wrapper requires the manifest opt-in.
This is an explicit caller change, not a default scaffold change.
Update the existing dispatchable `.github/workflows/rc.yml` in the same reviewed
opt-in change. Preserve its `workflow_dispatch` inputs and job `with` arguments;
the fragment below shows only the permissions and reusable-reference changes.
Replace `<reviewed-ref>` with an exact released version before consumption.

```yaml
permissions:
  contents: write
  checks: read
  actions: read
  issues: read

jobs:
  rc:
    uses: bagdeli/KavoshStart/.github/workflows/kavosh-test-staging.yml@<reviewed-ref>
```

```json
{
  "release": {
    "strategy": "release-please",
    "testStaging": {
      "schemaVersion": 1,
      "target": "test",
      "callerWorkflow": ".github/workflows/rc.yml",
      "prerequisites": {
        "full": {"acceptanceId": "AC-001", "assertion": "runtime::staging-readiness"},
        "originals": {"acceptanceId": "AC-001", "assertion": "runtime::staging-readiness"},
        "recovery": {"acceptanceId": "AC-001", "assertion": "runtime::staging-readiness"},
        "capacity": {"acceptanceId": "AC-001", "assertion": "runtime::staging-readiness"}
      }
    }
  }
}
```

Each referenced assertion must be declared under that item's `assertions.test`
in `acceptance/scope.json`, and its actual test contract must check each mapped
prerequisite. Repeating an integrated assertion ID does not itself prove
coverage. For every scope item, the gate also verifies all
declared test/security/migration receipts and a successful required CI run on
the exact staging SHA. Issues may remain open and use `Staging-Merged-SHA`,
`Staging-CI-Run`, `Staging-Test-Evidence`, `Staging-Security-Evidence`, and
`Staging-Migration-Evidence` markers. Staging rejects deferred scope items.
It does not complete final acceptance: UI and independent owner approval remain
pending, and the existing ACC-3 gate stays unchanged.

## Policy

Each `producers` key is `ci`, `test`, `ui`, `security`, `migration`, `approval` or
`defer`. Configure only actual required kinds, with:

- `appId`: the real dedicated GitHub App's numeric ID, never a user ID;
- `checkName`: the exact check name published by that App;
- `mode`: `actions`, `actions-external`, `manual`, or `decision`;
- `workflow` and `job`: exact repository workflow path and native job name for
  `actions` and `actions-external`; `ci` always requires native successful CI.

The optional `actions-external` mode is CI-only. It keeps the same dedicated-App,
exact workflow/run/attempt/job/source/status and chronology checks as `actions`,
but replaces the Actions artifact lookup with a required immutable
`externalEvidenceDigest`. The independent App must itself inspect the exact
source run and attest that required artifacts and original evidence were kept
under owner-held custody and passed readback. The verifier does not fetch a supplied
URL. Default `actions` mode and the final ACC-3 decision flow are unchanged.

`approval` and `defer` require `decision` mode and their App ID must differ from
all evidence App IDs. `maxAgeDays` is a reviewed finite validity bound (1..365).
The same evidence App may serve multiple evidence kinds. A manual UAT attestor
may use `manual` for a non-CI kind. No URL from an Issue is followed externally.

## Scope assertions and reuse

Every item declares `assertions`, mapping each required evidence kind to a
nonempty list of exact assertion IDs. These are **expected** checks, not results.
Example shape (replace with real product acceptance criteria):

```json
{
  "id": "AC-001", "issue": 123, "owner": "github-login",
  "risk": "high", "evidence": ["ci", "test"],
  "assertions": {
    "ci": ["repository::required"],
    "test": ["document::reject-cross-tenant-read"]
  }
}
```

The conservative reuse default requires identical complete Git trees. Optional
`evidencePaths` lists literal existing files/directories and their transitive
inputs; no globs or parent traversal. Review dependencies, lockfiles, schemas,
fixtures, config and external-input validity. Changes to these paths, or to the
manifest, `acceptance`, `.github`, `.gitattributes` or `.gitmodules`, invalidate
old receipts. Missing/truncated tree metadata fails closed. A path declaration
is a reviewed dependency contract, not automatic dependency discovery.

## Receipt and marker format

A canonical Issue retains `Accepted-By`, `Acceptance-Merged-SHA` and
`Acceptance-Evidence-Run` (the required CI run) for base provenance. It additionally
needs `Acceptance-CI-Receipt`, the applicable `Acceptance-Test-Evidence`,
`Acceptance-UI-Evidence`, `Acceptance-Security-Evidence`,
`Acceptance-Migration-Evidence`, and `Acceptance-Decision-Evidence`.
All these receipt markers use exactly:

```text
https://api.github.com/repos/OWNER/REPO/check-runs/ID#sha256:HEX
```

`HEX` hashes the canonical JSON object in the App check's `output.text` using
`json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False,
allow_nan=False).encode('utf-8')`. It is not a hash of Markdown or a URL.
Use `tooling/src/receipts.py::receipt_digest` rather than reimplementing this.
Duplicate JSON keys/markers, malformed links, shared publishers and missing,
changed, failed, expired or deleted receipts are not accepted. Canonicalization
allows harmless JSON whitespace, not content changes. A check ID alone is mutable;
the digest and independent decision bind the accepted content.

The JSON object has these required fields:

```text
schemaVersion: 1
repository: exact owner/repo
acceptanceId: AC-NNN
kind: ci | test | ui | security | migration | approval | defer
targetRelease: same release as scope
scopeDigest: receipt_digest(the entire scope item)
policyDigest: receipt_digest(the complete receipt policy)
sourceSha: accepted merged commit (40 hex)
sourceTree: exact Git tree (40 hex)
issuedAt: timezone-aware ISO timestamp
expiresAt: timezone-aware ISO timestamp, within policy maxAgeDays
outcome: pass
```

The check's `head_sha`, publisher, name, success and completion time must match.
Evidence receipts bind the accepted merged SHA; base CI separately supports the
explicit verified PR-head/squash bridge. Do not relabel pre-merge evidence as
post-merge typed evidence. A decision may attest a later candidate only when the
reviewed source-reuse contract is satisfied.

### Automated evidence

Also include `assertions: [{"id": "exact-assertion-id", "outcome": "pass"}, ...]`
covering all required IDs; duplicates and non-passing results are rejected.
Include positive integers `runId`, `runAttempt`, `jobId`, `artifactId`, and
`artifactDigest` in `sha256:HEX` format. The gate reads GitHub metadata to verify
same repository/source, exact approved workflow/job/attempt, success, digest,
non-expiry, and artifact -> job -> receipt chronology.

The retained artifact name is exactly
`kavosh-evidence-RUNID-ATTEMPT-KIND`. The publisher must inspect the actual artifact
bytes and assertion outcomes before publishing. The gate confirms the retained
artifact identity/digest; it does not redownload arbitrary artifacts from Issues.
`tooling/junit_receipt.py` is an offline JUnit assertion adapter, not a publisher
or approval tool. Empty reports, contradictory counters and ambiguous duplicate
IDs fail; failed/skipped assertions never become passing ones.

### Manual/external evidence

A `manual` producer includes the same scope/source/assertion fields and
`externalEvidenceDigest: sha256:HEX`. Its trusted App certifies the underlying
external evidence and retention, without exposing private UAT material or asking
the gate to fetch arbitrary URLs. The App, not an editable `Accepted-By` line,
is the trust boundary. CI cannot use this manual adapter.

### Independent acceptance decision

An `approval` receipt includes `subject` equal to the item's owner, `decision`
set to `accept`, and `bindingsDigest` computed from exactly:

```text
{
  "mergedSha": Acceptance-Merged-SHA marker,
  "ciRun": Acceptance-Evidence-Run marker,
  "evidence": { required kind: exact corresponding receipt marker value }
}
```

Its issuance must follow the bound evidence's completion. Changing a receipt,
release scope, or policy requires a new actual decision, not editing a marker.

A defer keeps the future `deferredTo` and `deferIssue` in the versioned scope. The
closed defer Issue has `Defer-Approved-By` and `Defer-Decision-Evidence`; the App
receipt has `kind: defer`, `subject: owner`, `decision: defer`, and
`bindingsDigest = receipt_digest({"deferredTo": item.deferredTo,
"deferIssue": item.deferIssue})`. The same source, policy and expiry checks apply.

## Migration and proof limits

Do not promote historical work from Issue closure or the presence of code. Keep
existing granular product ledgers; choose independently decidable acceptance
units rather than making one Issue per tiny test or one item for the entire ERP.
Prepare scope assertions and reviewed publisher policy, obtain genuine evidence
and decisions, and verify Health and Release using the same source version.
Health distinguishes declared marker closure from verified receipts.

These validators and fixtures do not install an attestor, certify real UAT, prove
all transitive inputs automatically, or authorize release/deployment. A missing
trusted service remains an explicit rollout blocker. The change tightens the
proof contract for upgraded consumers; do not silently upgrade unrelated projects
or pin a version that has not actually been released.

## Reference evidence-publisher integration

`tooling/artifact_receipt.py` closes the automated artifact-to-receipt path. Use
it only in the independently administered evidence service, not product CI. The
service supplies an authenticated GitHub JSON API, a bounded artifact downloader,
and a **reviewed policy digest pinned outside the product repository**. Taking
that digest from an untrusted request would let the product admit its own policy.
An `actions` producer also configures `reportPath`, the exact relative JUnit file
inside the artifact ZIP. This is a reviewed producer input, not a caller-selected
file that can hide the failing report.

`prepare_evidence` reads the exact source's manifest/scope/policy, verifies that
source is integrated into main, checks run/job/artifact provenance with the shared
verifier, verifies the downloaded ZIP's SHA-256, and derives actual outcomes from
its policy-selected JUnit member. ZIP paths, duplicates, links, encryption,
expanded size and member count are bounded; no archive entry is extracted or
executed. A failed/skipped assertion, missing expected ID or unrelated successful
report cannot produce a success request. Preparation is read-only and its output
is **unpublished**, not accepted evidence.

`publish_evidence` additionally performs exactly one `POST /check-runs`, then
reads back and verifies the actual publisher, source, digest and evidence through
the shared verifier. It returns the digest-bound marker only after that readback.
It does not update Issues, branches, tags, releases or acceptance decisions. An
ambiguous network write is not blindly retried: reconcile the already-created
check first. A wrong publisher or failed readback never returns a trusted marker.

The service's downloader receives only `(repo, artifact_id, max_bytes)`, never an
Issue URL. It must use GitHub's artifact download endpoint, bound streaming bytes,
validate HTTPS storage redirects, and **not forward GitHub credentials to a
storage redirect**. Authentication, transport, installation and secret custody
remain responsibilities of the admitted service. This adapter does not silently
install a service or provide a human-decision authentication implementation.

Before operational admission, run a genuine service test for each admitted kind:
real artifact and exact workflow/job; tampered/failed artifact rejection; actual
App publisher readback; independent owner decision bound to the new evidence;
then matching Health and Release verdicts. Keep these real checks separate from
the offline fixtures, whose transport/App identities are deliberately synthetic.
