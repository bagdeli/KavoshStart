"""One-time exact-source transport for PR 122; removed from the final PR tree.

Only creates unreferenced Git blobs after reproducing the locally verified tree
and full tests. Never creates commits, updates refs, merges, releases, deploys,
or handles credentials outside this public repository's ordinary job token.
"""
import base64
import gzip
import hashlib
import json
import os
from pathlib import Path
import subprocess
import urllib.request

REPO = "bagdeli/KavoshStart"
BRANCH = "refs/heads/fix/121-evidence-integrity"
assert os.environ["GITHUB_REPOSITORY"] == REPO
assert os.environ["GITHUB_REF"] == BRANCH
assert os.environ["GITHUB_EVENT_NAME"] == "push"

def git(*args):
    return subprocess.check_output(["git", *args], text=True).strip()

packet = json.loads(Path(".receipt-transport/packet.json").read_text())
assert packet["schemaVersion"] == 1
# This retry changes only the transport's verification order. Source is unchanged.
assert git("rev-parse", "HEAD^") == "2bc0de4c86e1174be24cce181ea8496eedafca51"
assert git("rev-parse", "HEAD^^") == packet["baseHead"]
assert git("rev-parse", packet["baseHead"] + "^{tree}") == packet["baseTree"]
bootstrap = [f".receipt-transport/part{i}.b64" for i in range(4)] + [
    ".receipt-transport/packet.json", ".receipt-transport/materialize.py",
    ".github/workflows/receipt-materialize.yml"]
assert set(git("diff", "--name-only", packet["baseHead"], "HEAD").splitlines()) == set(bootstrap)
parts = [Path(f".receipt-transport/part{i}.b64").read_text().strip() for i in range(4)]
# Repair two known transfer transcription insertions, never source semantics.
# The complete decoded patch and every resulting blob are verified below.
assert parts[0].count("Yqiuu9") == 1
parts[0] = parts[0].replace("Yqiuu9", "Yqiu9")
assert parts[3].count("T9sfDfbj") == 1
parts[3] = parts[3].replace("T9sfDfbj", "T9Q8fbj")
raw = gzip.decompress(base64.b64decode("".join(parts), validate=True))
assert len(raw) < 200000
assert hashlib.sha256(raw).hexdigest() == packet["patchSha256"]
subprocess.run(["git", "apply", "--check", "-"], input=raw, check=True)
subprocess.run(["git", "apply", "-"], input=raw, check=True)
subprocess.run(["python3", "tooling/rule_registry.py", "--write"], check=True)
subprocess.run(["python3", "tooling/build_workflows.py"], check=True)
expected = packet["expected"]
changed = set(git("diff", "--name-only", "HEAD").splitlines())
changed.update(git("ls-files", "--others", "--exclude-standard").splitlines())
assert changed == set(expected), (changed, set(expected))
subprocess.run(["git", "add", "--", *expected], check=True)
# Test the intended final source, not the one-time transport workflow. Remove
# exactly our seven bootstrap files from this disposable checkout and index.
subprocess.run(["git", "rm", "--", *bootstrap], check=True)
assert git("write-tree") == packet["expectedFinalTree"]
subprocess.run(["make", "check"], check=True)

def blob_id(raw):
    return hashlib.sha1(b"blob " + str(len(raw)).encode() + b"\0" + raw).hexdigest()

for path, sha in expected.items():
    assert blob_id(Path(path).read_bytes()) == sha, path
assert git("write-tree") == packet["expectedFinalTree"]
# POST /git/blobs only. No branch or commit mutation from this workflow.
for path, sha in expected.items():
    body = json.dumps({"content": base64.b64encode(Path(path).read_bytes()).decode(), "encoding": "base64"}).encode()
    request = urllib.request.Request(f"https://api.github.com/repos/{REPO}/git/blobs", data=body,
        headers={"Authorization": "Bearer " + os.environ["GH_TOKEN"],
                 "Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28",
                 "Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(request, timeout=30) as response:
        actual = json.load(response)["sha"]
    assert actual == sha, path
    print("VERIFIED_BLOB", path, actual, flush=True)
print("MATERIALIZED_TREE=" + packet["expectedFinalTree"], flush=True)
