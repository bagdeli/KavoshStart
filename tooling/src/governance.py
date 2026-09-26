# KavoshStart governance check (layer P). Embedded into .github/workflows/kavosh-governance.yml
# by tooling/build_workflows.py — edit this file, then run `python3 tooling/build_workflows.py`.
# Runs in the product repository checkout. Needs python3 (stdlib only) and, for PR checks, gh.
import json
import math
import os
import re
import subprocess
import sys
from pathlib import Path

SCHEMA = json.loads(r"""__SCHEMA_JSON__""")

TIER_BUDGET = {"T0": 100, "T1": 300, "T2": 700}
TIER_ORDER = {"T0": 0, "T1": 1, "T2": 2}
SHA_RE = re.compile(r"\b[0-9a-f]{40}\b")
ISSUE_REF_RE = re.compile(r"(?<![\w&])#\d{2,}\b")
DATE_RE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
FORBIDDEN_RE = re.compile(r"(^|/)(STATUS|HANDOFF|PROJECT_STATE|CURRENT_STATE)\.md$|^(docs/)?archive/")
SHA_ALLOWED_RE = re.compile(r"(^|/)CHANGELOG\.md$|^docs/decisions/|^audits/")
CC_RE = re.compile(r"^(feat|fix|docs|refactor|perf|test|ci|build|chore|revert)(\([a-z0-9._/-]+\))?!?: \S.{2,}$")
BRANCH_RE = re.compile(r"^(feat|fix|docs|refactor|test|ci|chore|perf|build|hotfix|revert)/[0-9]+-[a-z0-9][a-z0-9._-]*$")
EXEMPT_BRANCH_RE = re.compile(r"^(dependabot/|release-please--|renovate/)")
LINK_RE = re.compile(r"(?i)\b(close[sd]?|fix(e[sd])?|resolve[sd]?|refs?)\s+([\w.-]+/[\w.-]+)?#\d+")
IGNORE_SIZE_RE = re.compile(
    r"(^|/)(package-lock\.json|pnpm-lock\.yaml|yarn\.lock|poetry\.lock|uv\.lock|Cargo\.lock|go\.sum)$"
    r"|(^|/)(generated|__snapshots__|dist)/|\.min\.(js|css)$|^CHANGELOG\.md$"
)
AGENT_WORDS = re.compile(r"(?i)\b(claude|codex|copilot|gemini|gpt|cursor|agent)\b")

results = []  # (level, rule_id, title, detail)


def add(level, rule, title, detail=""):
    results.append((level, rule, title, str(detail)))


# ---------------------------------------------------------------- manifest
def validate(node, schema, path="$"):
    errs = []
    if "enum" in schema and node not in schema["enum"]:
        errs.append(f"{path}: {node!r} not in {schema['enum']}")
        return errs
    t = schema.get("type")
    types = t if isinstance(t, list) else ([t] if t else [])
    pytypes = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool, "null": type(None)}
    if types and not any(isinstance(node, pytypes[x]) and not (x == "integer" and isinstance(node, bool)) for x in types):
        return [f"{path}: expected {'/'.join(types)}"]
    if isinstance(node, dict):
        for k in schema.get("required", []):
            if k not in node:
                errs.append(f"{path}.{k}: required")
        props = schema.get("properties", {})
        for k, v in node.items():
            if k in props:
                errs += validate(v, props[k], f"{path}.{k}")
            elif schema.get("additionalProperties") is False:
                errs.append(f"{path}.{k}: unknown field")
            elif isinstance(schema.get("additionalProperties"), dict):
                errs += validate(v, schema["additionalProperties"], f"{path}.{k}")
    if isinstance(node, list):
        if len(node) < schema.get("minItems", 0):
            errs.append(f"{path}: needs at least {schema['minItems']} item(s)")
        for i, v in enumerate(node):
            errs += validate(v, schema.get("items", {}), f"{path}[{i}]")
    if isinstance(node, str):
        if len(node) < schema.get("minLength", 0) or len(node) > schema.get("maxLength", 10**9):
            errs.append(f"{path}: length out of range")
        if "pattern" in schema and not re.search(schema["pattern"], node):
            errs.append(f"{path}: does not match {schema['pattern']}")
    if isinstance(node, int) and not isinstance(node, bool):
        if node < schema.get("minimum", -(10**18)) or node > schema.get("maximum", 10**18):
            errs.append(f"{path}: out of range")
    return errs


def expected_tier(m):
    d, s, u = m.get("data", {}), m.get("size", {}), m.get("users", {})
    big_scale = u.get("scale") in ("100-1000", "1000+")
    if (d.get("regulatedIntegrations") or d.get("sensitivity") == "financial" or d.get("multiTenant")
            or s.get("domains", 1) >= 4 or s.get("parallelStreams", 1) >= 3
            or (u.get("audience") == "customers" and big_scale)):
        return "T2"
    if (m.get("runtime") == "server" or d.get("sensitivity") == "personal" or 2 <= s.get("domains", 1) <= 3
            or s.get("lifetime") != "weeks" or m.get("ui", {}).get("kind") in ("web", "admin")):
        return "T1"
    return "T0"


def check_manifest():
    p = Path("kavosh.project.json")
    if not p.exists():
        add("fail", "SRC-5", "kavosh.project.json exists", "missing — run the KavoshStart intake (START.md §1)")
        return {}
    try:
        m = json.loads(p.read_text(encoding="utf-8"))
    except ValueError as e:
        add("fail", "SRC-5", "kavosh.project.json is valid JSON", e)
        return {}
    errs = validate(m, SCHEMA)
    add("fail" if errs else "ok", "SRC-5", "Manifest matches schema", "; ".join(errs[:8]) or "valid")
    if errs:
        return m
    exp = expected_tier(m)
    if TIER_ORDER[m["tier"]] < TIER_ORDER[exp] and not (m.get("tierOverride") and Path(m["tierOverride"]).exists()):
        add("fail", "SRC-5", "Tier consistent with CLASSIFICATION.md", f"manifest {m['tier']} < classified {exp}; raise tier or add tierOverride ADR")
    else:
        add("ok", "SRC-5", "Tier consistent with CLASSIFICATION.md", f"{m['tier']} (classified {exp})")
    rt, method = m["runtime"], m["deploy"]["method"]
    if rt in ("server", "static") and method not in ("pull-build", "pull-image"):
        add("fail", "DEP-1", "Deploy method fits runtime", f"runtime {rt} needs pull-build or pull-image, got {method}")
    elif rt in ("none", "desktop") and method not in ("none", "release-artifact"):
        add("fail", "DEP-1", "Deploy method fits runtime", f"runtime {rt} needs none or release-artifact, got {method}")
    else:
        add("ok", "DEP-1", "Deploy method fits runtime", f"{rt} → {method}")
    if m["ui"]["kind"] != "none" and not m["ui"].get("kavoshui"):
        add("fail", "UI-1", "KavoshUI version pinned", "ui.kind is set but ui.kavoshui is empty")
    budget = m["ci"]["monthlyMinutesBudget"]
    add("warn" if budget > TIER_BUDGET[m["tier"]] else "ok", "CI-3", "Minutes budget within tier default",
        f"{budget} (tier default {TIER_BUDGET[m['tier']]})")
    if m["ci"]["runner"] == "self-hosted-deploy-only":
        ok = m["tier"] == "T2" and m["ci"].get("runnerAdr") and Path(m["ci"]["runnerAdr"]).exists()
        add("ok" if ok else "fail", "CI-2", "Self-hosted runner justified", "T2 + ADR required")
    return m


# ---------------------------------------------------------------- repository files
def git_files():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return [f for f in out.splitlines() if f]


def read(f):
    try:
        return Path(f).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_files(m):
    files = git_files()
    md = [f for f in files if f.lower().endswith(".md")]

    if "AGENTS.md" not in files:
        add("fail", "AI-1", "Root AGENTS.md exists", "missing")
    for f in [x for x in files if Path(x).name == "AGENTS.md"]:
        t = read(f)
        n, b = t.count("\n") + 1, len(t.encode("utf-8"))
        add("fail" if (f == "AGENTS.md" and (n > 150 or b > 12288)) else "ok", "AI-1", f"{f} size", f"{n} lines / {b} bytes (limit 150 / 12288)")
        if SHA_RE.search(t):
            add("fail", "SRC-2", f"{f} has no commit SHAs", f"{len(SHA_RE.findall(t))} found")
        refs = sorted(set(ISSUE_REF_RE.findall(t)))
        dates = sorted(set(DATE_RE.findall(t)))
        if refs or dates:
            add("warn", "SRC-4", f"{f} has no live-state references", ", ".join(refs[:8] + dates[:4]))
    for bridge in ("CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md"):
        if bridge in files and "AGENTS.md" not in read(bridge):
            add("warn", "AI-1", f"{bridge} points to AGENTS.md", "should import/reference AGENTS.md, not duplicate it")

    bad = [f for f in files if FORBIDDEN_RE.search(f)]
    add("fail" if bad else "ok", "SRC-3", "No status-tracker files or archive/", ", ".join(bad[:10]) or "none")

    offenders = []
    for f in md:
        if SHA_ALLOWED_RE.search(f) or Path(f).name == "AGENTS.md":
            continue
        c = len(SHA_RE.findall(read(f)))
        if c:
            offenders.append(f"{f} ({c})")
    add("fail" if offenders else "ok", "SRC-2", "No commit SHAs in Markdown", ", ".join(offenders[:10]) or "none")

    big = [f"{f} ({Path(f).stat().st_size // 1024}KB)" for f in md
           if not f.endswith("CHANGELOG.md") and Path(f).exists() and Path(f).stat().st_size > 61440]
    add("fail" if big else "ok", "DOC-1", "Markdown files ≤ 60KB", ", ".join(big) or "none")

    add("ok" if ".githooks/pre-push" in files else "fail", "AI-4", "Agent guard hook committed", ".githooks/pre-push")
    claude = read(".claude/settings.json")
    add("ok" if "git push" in claude and "deny" in claude else "warn", "AI-4", "Claude deny rules present", ".claude/settings.json")

    self_hosted_ok = m.get("ci", {}).get("runner") == "self-hosted-deploy-only"
    wf = [f for f in files if f.startswith(".github/workflows/") and f.endswith((".yml", ".yaml"))]
    sh = [f for f in wf if re.search(r"^\s*runs-on:.*self-hosted", read(f), re.M)]
    add("fail" if sh and not self_hosted_ok else "ok", "CI-1", "Only GitHub-hosted runners", ", ".join(sh) or "ok")
    noperm = [f for f in wf if not re.search(r"^permissions:", read(f), re.M)]
    add("warn" if noperm else "ok", "SEC-3", "Workflows declare top-level permissions", ", ".join(noperm) or "ok")
    noto = [f for f in wf if "runs-on" in read(f) and "timeout-minutes" not in read(f)]
    add("warn" if noto else "ok", "CI-3", "Jobs set timeout-minutes", ", ".join(noto) or "ok")


# ---------------------------------------------------------------- pull request
def gh(*args):
    out = subprocess.run(["gh", *args], check=True, capture_output=True, text=True, encoding="utf-8").stdout
    return json.loads(out) if out.strip() else None


def check_pr(m, event, repo):
    pr = event["pull_request"]
    default = event["repository"]["default_branch"]
    head, base = pr["head"]["ref"], pr["base"]["ref"]
    title, body = pr["title"] or "", pr.get("body") or ""
    limits = m.get("limits", {}) if m else {}
    max_lines = int(limits.get("prMaxLines", 400))
    max_ready = int(limits.get("maxOpenReadyPRs", 3))
    bot = pr["user"]["type"] == "Bot" or bool(EXEMPT_BRANCH_RE.search(head))

    add("ok" if CC_RE.match(title) else "fail", "PR-2", "Title is a Conventional Commit", title)
    add("ok" if bot or BRANCH_RE.match(head) else "fail", "BR-2", "Branch name <type>/<issue>-<slug>", head)
    add("ok" if bot or LINK_RE.search(body) else "fail", "PR-1", "Linked issue (Closes/Refs #n)", "found" if LINK_RE.search(body) else "missing")

    files, page = [], 1
    while True:
        batch = gh("api", f"repos/{repo}/pulls/{pr['number']}/files?per_page=100&page={page}") or []
        files += batch
        if len(batch) < 100 or page >= 30:
            break
        page += 1
    counted = [f for f in files if not IGNORE_SIZE_RE.search(f["filename"])]
    lines = sum(f["additions"] + f["deletions"] for f in counted)
    labels = {l["name"] for l in pr.get("labels", [])}
    hard = math.ceil(max_lines * 2.5)
    if "size:exception" in labels:
        add("warn", "PR-3", "PR size", f"{lines} lines / {len(counted)} files — size:exception label")
    elif lines > hard or len(counted) > 50:
        add("fail", "PR-3", "PR size", f"{lines} lines / {len(counted)} files > {hard} / 50 — split it")
    elif lines > max_lines:
        add("warn", "PR-3", "PR size", f"{lines} lines > target {max_lines}")
    else:
        add("ok", "PR-3", "PR size", f"{lines} lines / {len(counted)} files")

    if base == default:
        add("ok", "BR-4", "Targets main (stack depth)", base)
    else:
        owner = repo.split("/")[0]
        parents = gh("api", f"repos/{repo}/pulls?state=open&head={owner}:{base}") or []
        if parents and parents[0]["base"]["ref"] == default:
            add("warn", "BR-4", "Targets main (stack depth)", f"stacked on {base} (depth 2 — maximum)")
        else:
            add("fail", "BR-4", "Targets main (stack depth)", f"base {base} is a long-lived or deep branch")

    ai = re.search(r"(?ims)^#+\s*AI involvement\s*$(.*?)(^#+\s|\Z)", body)
    if bot:
        add("ok", "PR-4", "AI involvement section", "bot PR")
    elif not ai:
        add("fail", "PR-4", "AI involvement section", "add `## AI involvement` (PR template)")
    else:
        section = ai.group(1)
        agent_used = AGENT_WORDS.search(re.sub(r"(?i)e\.g\..*", "", section)) and not re.search(r"(?i)\bnone\b|human only", section)
        if agent_used and not re.search(r"(?im)^Co-Authored-By:\s*\S+", body):
            add("fail", "AI-3", "Agent attribution trailer in PR body", "agent listed but no `Co-Authored-By:` line (it becomes the squash commit trailer)")
        else:
            add("ok", "PR-4", "AI involvement section", "present")

    open_prs = gh("api", f"repos/{repo}/pulls?state=open&per_page=100") or []
    ready = [p for p in open_prs if not p["draft"] and p["user"]["type"] != "Bot"]
    add("warn" if len(ready) > max_ready else "ok", "PR-8", "Open ready PRs (WIP)", f"{len(ready)} (limit {max_ready})")


# ---------------------------------------------------------------- main
def main():
    enforce = os.environ.get("ENFORCE", "true") == "true"
    repo = os.environ["REPO"]
    m = check_manifest()
    check_files(m or {})
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    event = json.load(open(event_path, encoding="utf-8")) if event_path and Path(event_path).exists() else {}
    if "pull_request" in event:
        check_pr(m or {}, event, repo)

    icon = {"ok": "✅", "warn": "⚠️", "fail": "❌"}
    failed = [r for r in results if r[0] == "fail"]
    out = ["## KavoshStart governance", "",
           f"**{'FAIL' if failed else 'PASS'}** — {len(failed)} failing, {sum(r[0] == 'warn' for r in results)} warnings. "
           "Rules: [standard/RULES.md](https://github.com/bagdeli/KavoshStart/blob/main/standard/RULES.md)", "",
           "| | Rule | Check | Detail |", "|---|---|---|---|"]
    out += [f"| {icon[l]} | {r} | {t} | {d.replace('|', '/')} |" for l, r, t, d in sorted(results, key=lambda x: "fwo".index(x[0][0]))]
    if failed and not enforce:
        out += ["", "_Report-only mode (`enforce: false`) — failures do not fail the job._"]
    text = "\n".join(out) + "\n"
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a", encoding="utf-8") as fh:
            fh.write(text)
    Path(os.environ.get("KAVOSH_REPORT", "kavosh-report.md")).write_text(text, encoding="utf-8")
    for l, r, t, d in results:
        if l != "ok":
            print(f"::{'error' if l == 'fail' and enforce else 'warning'} title={r} {t}::{d}")
    sys.exit(1 if failed and enforce else 0)


if __name__ == "__main__":
    main()
