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

_SCHEMA_SRC = r"""__SCHEMA_JSON__"""
# Embedded by build_workflows.py; when imported from the repo (tests) read the schema file instead.
SCHEMA = (json.loads(_SCHEMA_SRC) if not _SCHEMA_SRC.startswith("__") else
          json.loads((Path(__file__).resolve().parents[2] / "intake" / "kavosh.project.schema.json").read_text(encoding="utf-8")))

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
    if (m.get("runtime") == "server" or m.get("projectKind") == "library" or d.get("sensitivity") == "personal" or 2 <= s.get("domains", 1) <= 3
            or s.get("lifetime") != "weeks" or m.get("ui", {}).get("kind") in ("web", "admin")):
        return "T1"
    return "T0"


def check_manifest(actual_repo=None):
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
    if actual_repo and m.get("repo") != actual_repo:
        add("fail", "SRC-5", "Manifest identity matches GitHub event",
            f"manifest repo {m.get('repo')} does not match trusted repository {actual_repo}")
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
    if m["visibility"] == "private" and budget > 0:
        add("fail", "CI-3", "Shared hosted quota disabled by default on private repos",
            f"budget {budget}; a manifest is not authorization")
    for level, rule, title, detail in runner_manifest_problems(m):
        add(level, rule, title, detail)
    return m


def runner_labels(m):
    slug = re.sub(r"[^a-z0-9]+", "-", m.get("repo", "x/x").split("/")[-1].lower()).strip("-")
    return m.get("ci", {}).get("runnerLabels") or ["self-hosted", "linux", "x64", slug]


def runner_manifest_problems(m):
    """CI-1 / CI-2: enforce runner, cost and local-only eligibility."""
    vis, runner = m.get("visibility"), m.get("ci", {}).get("runner")
    if vis not in ("public", "private"):
        return [("fail", "CI-1", "Known repository visibility", f"got {vis}")]
    if runner == "none":
        eligible = m.get("tier") == "T1" and m.get("runtime") == "static"
        zero_budget = m.get("ci", {}).get("monthlyMinutesBudget", 0) == 0
        if not eligible or not zero_budget:
            return [("fail", "CI-1", "Local-only validation is T1/static with zero budget",
                     f"got tier={m.get('tier')}, runtime={m.get('runtime')}, monthlyMinutesBudget={m.get('ci', {}).get('monthlyMinutesBudget')}")]
        return [("ok", "CI-1", "Local-only T1/static validation profile",
                 "no GitHub Actions workflows; make check runs locally and its result is recorded in the PR")]
    if vis == "private" and runner == "github-hosted":
        return [("fail", "CI-1", "Private hosted execution requires direct authorization",
                 "private GitHub-hosted CI is disabled by default; manifest configuration is not authorization")]
    want = "github-hosted" if vis == "public" else "self-hosted"
    if runner != want:
        return [("fail", "CI-1", "Runner matches cost and visibility policy", f"{vis} repository needs ci.runner = {want}, got {runner}")]
    out = [("ok", "CI-1", "Runner matches cost and visibility policy", f"{vis} → {runner}")]
    if runner == "self-hosted":
        labels = runner_labels(m)
        slug = re.sub(r"[^a-z0-9]+", "-", m.get("repo", "").split("/")[-1].lower()).strip("-")
        expected = ["self-hosted", "linux", "x64", slug]
        if not slug or any(label not in labels for label in expected) or len(set(labels)) != len(labels):
            out.append(("fail", "CI-2", "Self-hosted labels match this repository", f"expected {expected}; got {labels}"))
        else:
            out.append(("ok", "CI-2", "Self-hosted runner profile", f"labels {labels} include {expected}"))
    return out

RUNS_ON_RE = re.compile(r"^[ \t]*runs-on:[ \t]*(.*)$", re.M)  # [ \t], not \s: must not run into the next line


def runs_on_values(text):
    """Values of every `runs-on:` line (job runners and reusable-workflow inputs), comments removed."""
    return [v.split("#", 1)[0].strip() for v in RUNS_ON_RE.findall(text)]


def is_hosted(value):
    return bool(re.search(r"(ubuntu|windows|macos)-", value)) and "self-hosted" not in value


def runner_workflow_problems(workflows, m):
    """CI-1 in workflow files: no hosted runs-on in private repos, no self-hosted in public repos;
    callers of KavoshStart reusable workflows in private repos pass a self-hosted runs-on input."""
    vis = m.get("visibility")
    if vis == "public":
        allowed = {"ubuntu-latest", "ubuntu-24.04", "ubuntu-22.04", "windows-latest", "windows-2025",
                   "windows-2022", "macos-latest", "macos-15", "macos-14", "macos-13"}
        def standard_hosted(value):
            if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
                value = value[1:-1]
            if value in allowed or value.startswith("$" + "{{"):
                return True
            try:
                labels = json.loads(value)
                return isinstance(labels, list) and bool(labels) and all(x in allowed for x in labels)
            except (ValueError, TypeError):
                return False
        bad = [f"{f}: {v}" for f, t in workflows.items() for v in runs_on_values(t)
               if v and not standard_hosted(v)]
        return [("fail" if bad else "ok", "CI-1", "Public repository uses standard GitHub-hosted runners only", ", ".join(bad) or "ok")]
    if vis == "private":
        bad = [f"{f}: {v}" for f, t in workflows.items() for v in runs_on_values(t)
               if "self-hosted" not in v]
        callers = [f for f, t in workflows.items()
                   if KAVOSH_WF in t and not any("self-hosted" in v for v in runs_on_values(t))]
        out = [("fail" if bad else "ok", "CI-1", "Private repository never uses GitHub-hosted runners", ", ".join(bad) or "ok")]
        if callers:
            out.append(("fail", "CI-1", "KavoshStart workflows get a self-hosted runs-on input", ", ".join(callers)))
        return out
    return []


# ---------------------------------------------------------------- repository files
def git_files():
    out = subprocess.run(["git", "ls-files"], capture_output=True, text=True, encoding="utf-8", check=True).stdout
    return [f for f in out.splitlines() if f]


def read(f):
    try:
        return Path(f).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def check_files(m, actual_repo=None):
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

    wf = [f for f in files if f.startswith(".github/workflows/") and f.endswith((".yml", ".yaml"))]
    if m.get("ci", {}).get("runner") == "none":
        add("fail" if wf else "ok", "CI-1", "Local-only project has no GitHub Actions workflows",
            ", ".join(wf[:8]) if wf else "make check is run locally; attach the successful output to each PR")
    else:
        for level, rule, title, detail in runner_workflow_problems({f: read(f) for f in wf}, m):
            add(level, rule, title, detail)
        noperm = [f for f in wf if not re.search(r"^permissions:", read(f), re.M)]
        add("fail" if noperm else "ok", "SEC-3", "Workflows declare top-level permissions", ", ".join(noperm) or "ok")
        noto = [f for f in wf if "runs-on" in read(f) and "timeout-minutes" not in read(f)]
        add("warn" if noto else "ok", "CI-3", "Jobs set timeout-minutes", ", ".join(noto) or "ok")

        unpinned = unpinned_uses({f: read(f) for f in wf}, m)
        add("fail" if unpinned else "ok", "SEC-2", "Actions pinned to full SHA; KavoshStart to exact tag",
            "; ".join(unpinned[:8]) or "ok")


def release_tag_config(text):
    """REL-3: release-please must tag vX.Y.Z — include-v-in-tag true and include-component-in-tag false
    (otherwise tags look like 'name-v1.2.0', which pins (REL-6) and the deploy script (DEP-2) reject)."""
    if text is None:
        return "fail", "release-please-config.json missing"
    try:
        cfg = json.loads(text)
    except ValueError as e:
        return "fail", f"release-please-config.json invalid: {e}"
    if cfg.get("include-v-in-tag") is not True or cfg.get("include-component-in-tag") is not False:
        return "fail", "set include-v-in-tag: true and include-component-in-tag: false"
    return "ok", "vX.Y.Z"


USES_RE = re.compile(r"^\s*(?:-\s*)?uses:\s*['\"]?([^'\"\s#]+)", re.M)
EXACT_TAG_RE = re.compile(r"^v[0-9]+\.[0-9]+\.[0-9]+$")
FULL_SHA_RE = re.compile(r"^[0-9a-f]{40}$")
KAVOSH_WF = "bagdeli/KavoshStart/.github/workflows/"


def unpinned_uses(workflows, m):
    """SEC-2 / REL-6: third-party actions by full SHA; KavoshStart workflows by the manifest's exact tag."""
    pin = m.get("kavoshStart")
    out = []
    for f, text in workflows.items():
        for ref in USES_RE.findall(text):
            if ref.startswith("./"):
                continue
            if ref.startswith("docker://"):
                image = ref[len("docker://"):]
                if not re.search(r"@sha256:[0-9a-f]{64}$", image):
                    out.append(f"{f}: {ref} (container actions must use an immutable sha256 digest)")
                continue
            target, _, version = ref.partition("@")
            if target.startswith(KAVOSH_WF):
                if not EXACT_TAG_RE.match(version) or (pin and version != pin):
                    out.append(f"{f}: {ref} (must be @{pin or 'vX.Y.Z'}, REL-6)")
            elif not FULL_SHA_RE.match(version):
                out.append(f"{f}: {ref}")
    return out


def wiring_problems(workflows, m, actual_repo=None):
    """Best-effort in-repo check that the guard workflows are present and wired. A PR can still neuter this
    check together with the workflow — Layer O (portfolio guard) is the control that sees that."""
    own = actual_repo == "bagdeli/KavoshStart" if actual_repo is not None else m.get("repo") == "bagdeli/KavoshStart"
    prefix = "./.github/workflows/" if own else KAVOSH_WF
    kav = workflows.get(".github/workflows/kavosh.yml", "")
    problems = []
    if not kav:
        return [("fail", "AI-4", "Guard workflow kavosh.yml present", "missing .github/workflows/kavosh.yml")]
    for name in ("kavosh-governance.yml", "kavosh-main-guard.yml", "kavosh-health.yml"):
        if prefix + name not in kav:
            problems.append(("fail", "AI-4", f"kavosh.yml calls {name}", f"expected uses: {prefix}{name}"))
    if re.search(r"^\s*enforce:\s*false", kav, re.M):
        problems.append(("fail", "AI-4", "Governance cannot be downgraded by repository config",
                         "enforce: false cannot authorize a report-only bypass"))
    ci = workflows.get(".github/workflows/ci.yml", "") or workflows.get(".github/workflows/self-check.yml", "")
    if not re.search(r"^  required:\s*$", ci, re.M):
        problems.append(("fail", "CI-7", "CI has a job named `required`", "ci.yml must define job `required`"))
    rel = workflows.get(".github/workflows/release.yml", "")
    if prefix + "kavosh-release.yml" not in rel:
        problems.append(("fail", "REL-5", "release.yml uses the gated kavosh-release", f"expected uses: {prefix}kavosh-release.yml"))
    return problems or [("ok", "AI-4", "Guard workflows present and wired", "kavosh.yml, ci.yml, release.yml")]


PLACEHOLDER_RE = re.compile(r"<[^@>\n]*>|example\.com", re.I)  # <Agent>, <email> … but not <a@b.c>
TRAILER_RE = re.compile(r"(?im)^Co-Authored-By:\s*(.+)$")


def ai_section_problems(body):
    """PR-4 / AI-3: the AI involvement section must be filled in; if an agent is named, a real trailer is required."""
    sec = re.search(r"(?ims)^#+\s*AI involvement\s*$(.*?)(?=^#+\s|\Z)", body)
    if not sec:
        return [("fail", "PR-4", "AI involvement section", "add `## AI involvement` (PR template)")]
    text = re.sub(r"<!--.*?-->", "", sec.group(1), flags=re.S)
    agent = re.search(r"(?im)^\s*-\s*Agent\s*/\s*model:\s*(.*)$", text)
    value = agent.group(1).strip() if agent else ""
    trailers = TRAILER_RE.findall(body)
    real = [t for t in trailers if not PLACEHOLDER_RE.search(t) and re.search(r"<[^@>\s]+@[^>\s]+>", t)]
    fake = [t for t in trailers if t not in real]
    problems = []
    if not value or PLACEHOLDER_RE.search(value):
        problems.append(("fail", "PR-4", "AI involvement filled in", "write the agent and model, or `none`"))
    elif re.fullmatch(r"(?i)none|human( only)?", value):
        if fake:
            problems.append(("fail", "AI-3", "No placeholder trailer", "remove the template `Co-Authored-By:` line"))
    elif not real:
        problems.append(("fail", "AI-3", "Agent attribution trailer", f"agent `{value}` named but no real `Co-Authored-By: Name <email>` line"))
    elif fake:
        problems.append(("fail", "AI-3", "No placeholder trailer", "remove the template `Co-Authored-By:` line"))
    return problems or [("ok", "PR-4", "AI involvement section", value)]


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

    actual = "private" if event["repository"].get("private") else "public"
    if m.get("visibility") and m["visibility"] != actual:
        add("fail", "CI-1", "Manifest visibility matches the repository",
            f"repository is {actual}, manifest says {m['visibility']} — a public repo must never run on self-hosted runners")
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
    exception_requested = "size:exception" in labels
    approved_size = False
    if exception_requested:
        reason = re.search(r"(?im)^size exception reason:\s*(\S.+)$", body)
        reviews = gh("api", f"repos/{repo}/pulls/{pr['number']}/reviews") or []
        owner = repo.split("/")[0].lower()
        approved_size = bool(reason and any(
            (r.get("user") or {}).get("login", "").lower() == owner
            and r.get("state") == "APPROVED" and r.get("commit_id") == pr["head"].get("sha")
            for r in reviews))
    if (lines > hard or len(counted) > 50) and not approved_size:
        add("fail", "PR-3", "PR size", f"{lines} lines / {len(counted)} files > {hard} / 50 — split it")
    elif exception_requested and (lines > max_lines) and not approved_size:
        add("fail", "PR-3", "Size exception authorization", "requires a written reason and owner approval on the current head")
    elif exception_requested:
        add("warn", "PR-3", "Owner-authorized size exception", f"{lines} lines / {len(counted)} files; reason and current-head owner approval recorded")
    elif lines > max_lines:
        add("warn", "PR-3", "PR size", f"{lines} lines > target {max_lines}")
    else:
        add("ok", "PR-3", "PR size", f"{lines} lines / {len(counted)} files")

    if base == default:
        add("ok", "BR-4", "Targets main (stack depth)", base)
    else:
        owner = repo.split("/")[0]
        parents = gh("api", f"repos/{repo}/pulls?state=open&head={owner}:{base}") or []
        if parents and pr.get("draft"):
            add("warn", "BR-4", "Draft stack depth", f"Draft stacked on {base}; normalize before Ready")
        elif parents and parents[0]["base"]["ref"] == default and parents[0].get("mergeable") is True:
            add("warn", "BR-4", "Ready PR has an immediately mergeable parent", f"stacked on {base}")
        else:
            add("fail", "BR-4", "Ready PR is normalized to a shallow stack", f"base {base} is not main or an immediately mergeable parent")

    if bot:
        add("ok", "PR-4", "AI involvement section", "bot PR")
    else:
        for level, rule, t, d in ai_section_problems(body):
            add(level, rule, t, d)

    open_prs = gh("api", f"repos/{repo}/pulls?state=open&per_page=100") or []
    ready = [p for p in open_prs if not p["draft"] and p["user"]["type"] != "Bot"]
    add("warn" if len(ready) > max_ready else "ok", "PR-8", "Open ready PRs (WIP)", f"{len(ready)} (limit {max_ready})")


# ---------------------------------------------------------------- main
def main():
    enforce = os.environ.get("ENFORCE", "true") == "true"
    report_only_forbidden = not enforce
    repo = os.environ["REPO"]
    m = check_manifest(repo)
    check_files(m or {}, repo)
    if report_only_forbidden:
        add("fail", "AI-4", "Report-only enforcement bypass is forbidden",
            "enforce: false cannot produce a successful governance check")
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
    sys.exit(1 if report_only_forbidden or (failed and enforce) else 0)


if __name__ == "__main__":
    main()
