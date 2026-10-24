# OPTIONAL receipt integration for explicitly opted-in continuous projects

No project needs independent GitHub Apps, a second person, an external evidence store or this transport simply because it is T2, financially sensitive or managed by a solo owner. This reference code remains available only when the owner deliberately adopts an attested continuous contract and accepts the operational costs. `acceptance.mode=none` uses actual source CI plus owner-controlled release decisions without invoking this tool.

The repository delivers a verifier, artifact/JUnit publisher library and bounded
GitHub.com transport. It does not run a hosted attestation or human-login service.
The full receipt protocol is in the T2 acceptance README. Existing consumers are
not upgraded by publishing this tooling or running these tests.

## Automated artifact transport

`receipt_transport.GitHubReceiptTransport(repository, installation_token)` supplies
both callbacks required by `artifact_receipt.prepare_evidence`: use the instance
as `api` and its `download` method as `download`. The default is read-only. For a
separately admitted evidence service, explicitly set `publish=True` and call
`publish_evidence`, which performs its existing post-write App/payload verification.

```python
from artifact_receipt import prepare_evidence
from receipt_transport import GitHubReceiptTransport

# Values come from the trusted operator/service, never from a product's claimed
# approval. Load the short-lived installation token through its secret store;
# do not put it in source, arguments, output, product jobs or stored receipts.
def inspect_request(repository, installation_token, admitted_digest, request):
    transport = GitHubReceiptTransport(repository, installation_token)
    return prepare_evidence(
        repository, request["source"], request["acceptance_id"], request["kind"],
        request["run_id"], request["attempt"], request["job_id"],
        request["artifact_id"], admitted_digest, api=transport,
        download=transport.download,
    )  # An unpublished request, not an approval or proof of publisher identity.
```

Read access needs repository metadata, contents, issues, pull requests, Actions
and checks. Only an admitted publisher needs `checks: write`. Request only the
repositories and permissions actually needed. The transport neither obtains nor
refreshes installation tokens and never uses the product's token as independent
attestation authority. It does not implement manual evidence or human decisions.

The client is fixed to the configured repository and documented GitHub.com API
paths. Metadata redirects are rejected. An artifact request is constructed from
its numeric ID, not an Issue URL. Only GitHub's initial HTTPS storage redirect is
accepted; storage receives a fresh request without authorization, API headers,
cookies or referer. A second redirect is rejected. Ambient proxies are disabled.
Responses have streaming byte and time bounds; ZIP inspection remains in the
publisher. Signed URLs, response bodies and tokens are absent from diagnostics.

The only optional write is a new automated evidence check. No update/delete,
Issue, ref, release, workflow dispatch or decision mutation is supported. Writes
are attempted once. `PublicationUncertain` requires reconciliation by the service
operator: a created check may already exist; re-running publication is not safe.

## Repository verification versus installation acceptance

Unit tests exercise valid calls, endpoint confinement, redirect credential
separation, limits, malformed JSON and ambiguous writes. The required self-check
also downloads its own finalized six-profile conformance artifact with read-only
permissions, verifies the real digest and report, and rejects a modified copy.
It does not create an attestation check or alter the default empty producer policy.
The live smoke is transport proof, not a synthetic claim of independent approval.

Completion of this repository's engineering work does not complete installation:
real App admission, external policy-digest custody, short-lived credentials and
independent human authentication remain explicit installation prerequisites.
Consumer-specific assertion mappings, evidence and adoption are owned by each
separately authorized project. They are not a prerequisite for delivering the
reference library, and must never be marked performed merely to close code work.

## Primary API contracts

- Artifact endpoint, redirect and permissions: https://docs.github.com/en/rest/actions/artifacts
- Check publication permissions: https://docs.github.com/en/rest/checks/runs
- Artifact storage domains: https://docs.github.com/en/actions/reference/runners/github-hosted-runners

GitHub Enterprise hosts and storage domains outside the explicit allowlist are
not silently accepted. An installation needing them requires a reviewed adapter.
