# KavoshStart governance check (layer P). Embedded into .github/workflows/kavosh-governance.yml
# by tooling/build_workflows.py — edit this file, then run `python3 tooling/build_workflows.py`.
# Runs in the product repository checkout. Needs python3 stdlib and git only; GitHub API access uses GITHUB_TOKEN.
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

_SCHEMA_SRC = r"""__SCHEMA_JSON__"""
# Embedded by build_workflows.py; when imported from the repo (tests) read the schema file instead.
SCHEMA = (json.loads(_SCHEMA_SRC) if not _SCHEMA_SRC.startswith("__") else
          json.loads((Path(__file__).resolve().parents[2] / "intake" / "kavosh.project.schema.json").read_text(encoding="utf-8")))

TIER_BUDGET = {"T0": 100, "T1": 300, "T2": 700}
TIER_ORDER = {"T0": 0, "T1": 1, "T2": 2}
SELF_STANDARD_REPO = "bagdeli/KavoshStart"
KAVOSHSTART_TAG_RE = re.compile(r"^v[0-9]+[.][0-9]+[.][0-9]+$")
SHA_RE = re.compile(r"\b[0-9a-f]{40}\b")
ISSUE_REF_RE = re.compile(
    r"(?i)\b(?:issues?|pr|pull requests?)\s+#\d+\b"
    r"|https://github[.]com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/(?:issues|pull)/\d+\b"
)
DATE_RE = re.compile(r"\b20\d\d-\d\d-\d\d\b")
FORBIDDEN_RE = re.compile(r"(^|/)(STATUS|HANDOFF|PROJECT_STATE|CURRENT_STATE)\.md$|^(docs/)?archive/")
SHA_ALLOWED_RE = re.compile(
    r"(^|/)CHANGELOG\.md$|^docs/decisions/|^(?:docs/)?audits/"
    r"|^docs/release/RELEASE_NOTES_[^/]+\.md$",
    re.I,
)
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


def standard_pin_problems(m, actual_repo=None):
    """STD-1: consumers pin exact releases; only KavoshStart itself may use the reserved self identity."""
    trusted_repo = actual_repo or m.get("repo")
    declared_repo = m.get("repo")
    pin = m.get("kavoshStart")
    is_standard = trusted_repo == SELF_STANDARD_REPO and declared_repo == SELF_STANDARD_REPO
    if pin == "self":
        if is_standard:
            return [("ok", "STD-1", "KavoshStart self-hosting identity", "self → checked-out canonical source")]
        return [("fail", "STD-1", "Reserved KavoshStart self identity",
                 f"'self' is valid only for {SELF_STANDARD_REPO}; consumers must pin vX.Y.Z")]
    if is_standard:
        return [("fail", "STD-1", "KavoshStart self-hosting identity",
                 "canonical KavoshStart must use kavoshStart: self, not a previous/future release tag")]
    if not isinstance(pin, str) or not KAVOSHSTART_TAG_RE.fullmatch(pin):
        return [("fail", "STD-1", "Consumer KavoshStart exact pin",
                 f"expected vX.Y.Z, got {pin!r}")]
    return [("ok", "STD-1", "Consumer KavoshStart exact pin", pin)]


def standard_lifecycle_problems(m):
    """STD-2 / ACC-1: normal operation cannot remain in legacy adoption and T2 uses continuous acceptance."""
    out = []
    adoption = m.get("adoptionPhase") is True
    out.append(("fail" if adoption else "ok", "STD-2", "Legacy adoption mode is closed",
                "remove adoptionPhase: true; record bounded exceptions instead" if adoption else "normal enforcing operation"))
    if m.get("tier") == "T2":
        mode = m.get("acceptance", {}).get("mode", "none")
        out.append(("ok" if mode == "continuous" else "fail", "ACC-1", "T2 uses continuous acceptance",
                    mode if mode == "continuous" else "set acceptance.mode=continuous and bootstrap acceptance/scope.json"))
    return out


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
    for level, rule, title, detail in standard_pin_problems(m, actual_repo):
        add(level, rule, title, detail)
    exp = expected_tier(m)
    if TIER_ORDER[m["tier"]] < TIER_ORDER[exp] and not (m.get("tierOverride") and Path(m["tierOverride"]).exists()):
        add("fail", "SRC-5", "Tier consistent with CLASSIFICATION.md", f"manifest {m['tier']} < classified {exp}; raise tier or add tierOverride ADR")
    else:
        add("ok", "SRC-5", "Tier consistent with CLASSIFICATION.md", f"{m['tier']} (classified {exp})")
    for level, rule, title, detail in standard_lifecycle_problems(m):
        add(level, rule, title, detail)
    rt, method = m["runtime"], m["deploy"]["method"]
    if rt in ("server", "static") and method not in ("pull-build", "pull-image", "custom"):
        add("fail", "DEP-1", "Deploy method fits runtime", f"runtime {rt} needs pull-build, pull-image or ADR-backed custom, got {method}")
    elif rt in ("none", "desktop") and method not in ("none", "release-artifact"):
        add("fail", "DEP-1", "Deploy method fits runtime", f"runtime {rt} needs none or release-artifact, got {method}")
    elif method == "custom":
        problem = decision_adr_problem(m.get("deploy", {}).get("authorizationADR"),
                                       ("safety and release gates", "rel-5", "least privilege", "tag", "rollback", "database"))
        add("fail" if problem else "ok", "DEP-1", "Custom deploy preserves equivalent gates",
            problem or m["deploy"]["authorizationADR"])
    else:
        add("ok", "DEP-1", "Deploy method fits runtime", f"{rt} → {method}")
    migration_mode = m.get("deploy", {}).get("migrationMode", "expand-contract")
    if migration_mode == "maintenance-window":
        problem = decision_adr_problem(m.get("deploy", {}).get("migrationADR"),
                                       ("migration and recovery", "maintenance window", "backup", "restore test", "rollback"))
        if m.get("tier") != "T1" or rt != "server":
            problem = "maintenance-window is limited to T1 server projects"
        add("fail" if problem else "ok", "DEP-5", "Maintenance-window migration is T1 and ADR-backed",
            problem or m["deploy"]["migrationADR"])
    else:
        add("ok", "DEP-5", "Migration strategy", "expand-contract (default)")
    ui = m.get("ui", {})
    if ui.get("kind") != "none" and not ui.get("kavoshui"):
        problem = decision_adr_problem(ui.get("exceptionADR"),
                                       ("ui exception", "scope", "rtl", "accessibility", "tests"))
        add("fail" if problem else "ok", "UI-1", "KavoshUI pin or approved exception ADR",
            problem or ui["exceptionADR"])
    budget = m.get("ci", {}).get("monthlyMinutesBudget")
    if budget not in (None, 0):
        add("warn", "CI-3", "Portfolio budget hint is not a core authorization",
            f"monthlyMinutesBudget={budget}; billable execution still follows owner/account policy")
    for level, rule, title, detail in runner_manifest_problems(m):
        add(level, rule, title, detail)
    for level, rule, title, detail in release_adapter_problems(m):
        add(level, rule, title, detail)
    return m


def release_adapter_problems(m):
    """REL-3/4/5: release tools are adapters, but must prove the same release outcomes."""
    release = m.get("release", {}) or {}
    strategy = release.get("strategy", "release-please")
    out = []

    deploy_method = (m.get("deploy", {}) or {}).get("method", "none")
    if strategy == "release-please" and deploy_method == "release-artifact":
        artifact = release.get("artifact")
        interface = (m.get("automation", {}) or {}).get("interface", "make")
        if artifact:
            out.append(("ok", "REL-4", "Release artifact adapter",
                        f"{interface}: explicit command + {len(artifact.get('paths', []))} path(s)"))
        elif interface == "make":
            out.append(("ok", "REL-4", "Release artifact adapter",
                        "default Make adapter: make setup && make package → dist/*"))
        else:
            out.append(("fail", "REL-4", "Release artifact adapter",
                        f"automation.interface={interface} requires release.artifact.command + paths"))
    if strategy == "release-please":
        return out
    workflow = release.get("workflow")
    if not workflow:
        out.append(("fail", "REL-4", "Declared release workflow adapter",
                    f"release.strategy={strategy} requires release.workflow"))
    elif not Path(workflow).exists():
        out.append(("fail", "REL-4", "Declared release workflow adapter", f"{workflow} does not exist"))
    else:
        out.append(("ok", "REL-4", "Declared release workflow adapter", f"{strategy} → {workflow}"))

    adr_problem = decision_adr_problem(
        release.get("strategyADR"),
        ("release strategy", "semver", "vX.Y.Z", "exact source", "provenance", "release gate", "immutable"),
    )
    if adr_problem:
        out.append(("fail", "REL-4", "Equivalent non-default release contract", adr_problem))
        out.append(("fail", "REL-3", "Repository release tag contract",
                    "non-default release strategy ADR must explicitly preserve immutable vX.Y.Z tags"))
    else:
        out.append(("ok", "REL-4", "Equivalent non-default release contract", release["strategyADR"]))
        out.append(("ok", "REL-3", "Repository release tag contract", "ADR preserves immutable vX.Y.Z tags"))
    if strategy == "changesets":
        out.append(("ok" if Path(".changeset/config.json").exists() else "fail", "REL-4",
                    "Changesets adapter configuration",
                    ".changeset/config.json" if Path(".changeset/config.json").exists() else "missing .changeset/config.json"))
    return out


def decision_adr_problem(ref, required_terms):
    """Require an in-repository decision record with the stated safety evidence, not a free-form exemption flag."""
    if not isinstance(ref, str) or not re.fullmatch(r"docs/decisions/[0-9]{4}-[a-z0-9-]+\.md", ref):
        return "an ADR path under docs/decisions/ is required"
    path = Path(ref)
    if not path.is_file():
        return f"ADR does not exist: {ref}"
    body = path.read_text(encoding="utf-8", errors="replace").lower()
    missing = [term for term in required_terms if term.lower() not in body]
    return f"ADR {ref} is missing: {', '.join(missing)}" if missing else None


def runner_trust_adr_problem(ref, visibility):
    """Self-hosted runners need an explicit trust/containment model without prescribing one implementation."""
    if not isinstance(ref, str) or not re.fullmatch(r"docs/decisions/[0-9]{4}-[a-z0-9-]+\.md", ref):
        return "an ADR path under docs/decisions/ is required"
    path = Path(ref)
    if not path.is_file():
        return f"ADR does not exist: {ref}"
    body = path.read_text(encoding="utf-8", errors="replace").lower()
    missing = [term for term in ("runner trust model", "isolation", "untrusted code", "credential boundary")
               if term not in body]
    strategies = ("rootless", "disposable", "ephemeral", "sandbox", "container", "virtual machine", "dedicated")
    if not any(term in body for term in strategies):
        missing.append("a concrete containment strategy")
    if visibility == "public" and not any(term in body for term in ("fork", "same-repository", "same repository")):
        missing.append("fork/same-repository PR boundary")
    return f"ADR {ref} is missing: {', '.join(missing)}" if missing else None


def runner_labels(m):
    slug = re.sub(r"[^a-z0-9]+", "-", m.get("repo", "x/x").split("/")[-1].lower()).strip("-")
    return m.get("ci", {}).get("runnerLabels") or ["self-hosted", "linux", "x64", slug]


def runner_manifest_problems(m):
    """CI-1 / CI-2: runner choice follows trust and cost; private hosted runs are manual and scoped."""
    vis, runner = m.get("visibility"), m.get("ci", {}).get("runner")
    if vis not in ("public", "private"):
        return [("fail", "CI-1", "Known repository visibility", f"got {vis}")]
    if runner == "none":
        eligible = m.get("tier") == "T1" and m.get("runtime") == "static"
        if not eligible:
            return [("fail", "CI-1", "Local-only validation is limited to the T1/static profile",
                     f"got tier={m.get('tier')}, runtime={m.get('runtime')}")]
        return [("ok", "CI-1", "Local-only T1/static validation profile",
                 "no GitHub Actions workflows; the project's semantic check contract runs locally and its result is recorded in the PR")]
    if runner not in ("github-hosted", "self-hosted"):
        return [("fail", "CI-1", "Known runner mode", f"got {runner}")]
    out = [("ok", "CI-1", "Runner selected by trust/cost policy", f"{vis} → {runner}")]
    if vis == "private" and runner == "github-hosted":
        out.append(("ok", "CI-3", "Private hosted run is authorization-gated",
                    "workflow_dispatch must name an open PR and its exact current head SHA"))
    if runner == "self-hosted":
        problem = runner_trust_adr_problem(m.get("ci", {}).get("trustModelADR"), vis)
        out.append(("fail" if problem else "ok", "CI-2", "Self-hosted runner has an isolated trust model",
                    problem or m["ci"]["trustModelADR"]))
        labels = runner_labels(m)
        slug = re.sub(r"[^a-z0-9]+", "-", m.get("repo", "").split("/")[-1].lower()).strip("-")
        expected = ["self-hosted", "linux", "x64", slug]
        if not slug or labels != expected:
            out.append(("fail", "CI-2", "Self-hosted labels are repo-specific", f"expected exactly {expected}; got {labels}"))
        else:
            out.append(("ok", "CI-2", "Self-hosted runner profile", f"labels exactly {expected}"))
    return out

RUNS_ON_RE = re.compile(r"^[ \t]*runs-on:[ \t]*(.*)$", re.M)  # [ \t], not \s: must not run into the next line


def runs_on_values(text):
    """Values of every `runs-on:` line (job runners and reusable-workflow inputs), comments removed."""
    return [v.split("#", 1)[0].strip() for v in RUNS_ON_RE.findall(text)]


JOB_LINE_RE = re.compile(r"^  ([A-Za-z0-9_-]+):[ \\t]*(?:#.*)?$")


def jobs_without_timeout(text):
    """Return local job ids that declare runs-on but omit timeout-minutes.

    Reusable-workflow caller jobs use job-level uses and no runs-on. Ignore
    workflow_call input names and nested with.runs-on values outside job scope.
    """
    lines = text.splitlines()
    try:
        start = next(i for i, line in enumerate(lines)
                     if re.fullmatch(r"jobs:[ \\t]*(?:#.*)?", line))
    except StopIteration:
        return []

    missing = []
    current = None
    block = []

    def finish():
        if current is None:
            return
        body = "\n".join(block)
        local = bool(re.search(r"^    runs-on:[ \\t]*", body, re.M))
        bounded = bool(re.search(r"^    timeout-minutes:[ \\t]*", body, re.M))
        if local and not bounded:
            missing.append(current)

    for line in lines[start + 1:]:
        if line and not line[0].isspace() and not line.lstrip().startswith("#"):
            break
        match = JOB_LINE_RE.match(line)
        if match:
            finish()
            current = match.group(1)
            block = []
        elif current is not None:
            block.append(line)
    finish()
    return missing


def is_hosted(value):
    return bool(re.search(r"(ubuntu|windows|macos)-", value)) and "self-hosted" not in value


def runner_workflow_problems(workflows, m):
    """CI-1: check every workflow runner against the manifest and fail closed for private hosted automation."""
    vis, runner = m.get("visibility"), m.get("ci", {}).get("runner")
    if vis not in ("public", "private"):
        return []
    hosted = {"ubuntu-latest", "ubuntu-24.04", "ubuntu-22.04", "windows-latest", "windows-2025",
              "windows-2022", "macos-latest", "macos-15", "macos-14", "macos-13"}
    bad = []
    for f, text in workflows.items():
        for value in runs_on_values(text):
            value = value.strip("\"'")
            if not value or value.startswith("$"):
                continue
            if value.startswith("[") and value.endswith("]"):
                labels = [label.strip().strip("\"'") for label in value[1:-1].split(",") if label.strip()]
            else:
                try:
                    labels = json.loads(value)
                except (ValueError, TypeError):
                    labels = [value]
            labels = labels if isinstance(labels, list) else [value]
            is_self = "self-hosted" in labels
            is_standard = bool(labels) and all(x in hosted for x in labels)
            if runner == "github-hosted" and not is_standard:
                bad.append(f"{f}: {value} (manifest selects GitHub-hosted)")
            elif runner == "self-hosted" and not is_self:
                bad.append(f"{f}: {value} (manifest selects self-hosted)")
    out = [("fail" if bad else "ok", "CI-1", "Workflow runners match the manifest", ", ".join(bad) or f"{vis} → {runner}")]
    if vis == "private" and runner == "github-hosted":
        required = (".github/workflows/ci.yml", ".github/workflows/kavosh.yml", ".github/workflows/release.yml")
        absent = [f for f in required if f not in workflows]
        unsafe = [f for f in required if f in workflows and
                  (not re.search(r"^  workflow_dispatch\s*:", workflows[f], re.M)
                   or "PRIVATE_HOSTED_DISPATCH_REQUIRED" not in workflows[f]
                   or "github.event_name == 'workflow_dispatch'" not in workflows[f]
                   or "!true" not in workflows[f])]
        problem = absent + unsafe
        out.append(("fail" if problem else "ok", "CI-3", "Private hosted jobs require an owner-initiated scoped dispatch",
                    ", ".join(problem) or "ci, governance/health, and release dispatch guards are present"))
    if runner == "self-hosted":
        unsafe = [f for f, text in workflows.items() if "pull_request:" in text and
                  "github.event.pull_request.head.repo.full_name == github.repository" not in text]
        out.append(("fail" if unsafe else "ok", "CI-2", "Self-hosted PR jobs exclude fork code",
                    ", ".join(unsafe) or "fork pull requests cannot reach self-hosted runners"))
    return out


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

    for level, rule, title, detail in acceptance_scope_problems(m):
        add(level, rule, title, detail)

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
        no_timeout = []
        for f in wf:
            no_timeout += [f"{f}: {job}" for job in jobs_without_timeout(read(f))]
        add("warn" if no_timeout else "ok", "CI-3", "Jobs set timeout-minutes",
            ", ".join(no_timeout) or "ok")

        unpinned = unpinned_uses({f: read(f) for f in wf}, m)
        add("fail" if unpinned else "ok", "SEC-2", "Actions pinned to full SHA; KavoshStart to exact tag",
            "; ".join(unpinned[:8]) or "ok")

    add("ok" if "PROJECT.md" in files else "fail", "SRC-7", "PROJECT.md exists", "one-page project brief (START.md §1 step 3)")
    if m.get("release", {}).get("strategy", "release-please") == "release-please":
        level, detail = release_tag_config(read("release-please-config.json") if "release-please-config.json" in files else None)
        add(level, "REL-3", "Release tags are plain vX.Y.Z", detail)
    add("ok" if ".github/dependabot.yml" in files else "fail", "SEC-4", "Dependabot configured", ".github/dependabot.yml")
    if m.get("ci", {}).get("runner") != "none":
        trusted_repo = actual_repo or m.get("repo")
        for level, rule, title, detail in wiring_problems({f: read(f) for f in wf}, m, trusted_repo):
            add(level, rule, title, detail)


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
EXACT_TAG_RE = KAVOSHSTART_TAG_RE
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
    ci_path = m.get("ci", {}).get("requiredWorkflow")
    if not ci_path:
        ci_path = ".github/workflows/ci.yml" if ".github/workflows/ci.yml" in workflows else ".github/workflows/self-check.yml"
    ci = workflows.get(ci_path, "")
    if not ci:
        problems.append(("fail", "CI-7", "Declared required CI workflow exists", f"missing {ci_path}"))
    elif not re.search(r"^  required:\s*$", ci, re.M):
        problems.append(("fail", "CI-7", "CI has a job named `required`", f"{ci_path} must define job `required`"))

    release = m.get("release", {}) or {}
    strategy = release.get("strategy", "release-please")
    rel_path = release.get("workflow") or ".github/workflows/release.yml"
    rel = workflows.get(rel_path, "")
    if not rel:
        problems.append(("fail", "REL-5", "Declared release workflow exists", f"missing {rel_path}"))
    elif strategy == "release-please" and prefix + "kavosh-release.yml" not in rel:
        problems.append(("fail", "REL-5", "Default release workflow uses gated kavosh-release",
                         f"expected uses: {prefix}kavosh-release.yml"))
    return problems or [("ok", "AI-4", "Guard workflows and declared CI/release adapters are wired",
                         f"kavosh.yml, {ci_path}, {rel_path}")]


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


# ---------------------------------------------------------------- continuous acceptance
ACCEPTANCE_ID_RE = re.compile(r"^AC-[0-9]{3,}$")
ACCEPTANCE_RELEASE_RE = re.compile(r"^v([0-9]+)[.]([0-9]+)[.]([0-9]+)$")
ACCEPTANCE_OWNER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?$")
ACCEPTANCE_EVIDENCE = {"ci", "test", "ui", "security", "migration"}
ACCEPTANCE_LIVE_KEYS = {"status", "state", "accepted", "done", "passed", "complete", "completed"}


def acceptance_scope():
    path = Path("acceptance/scope.json")
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, OSError):
        return False


def acceptance_scope_problems(m):
    if m.get("acceptance", {}).get("mode", "none") != "continuous":
        return []
    scope = acceptance_scope()
    if scope is None:
        return [("fail", "ACC-1", "Acceptance scope contract", "acceptance/scope.json is required")]
    if scope is False or not isinstance(scope, dict):
        return [("fail", "ACC-1", "Acceptance scope contract", "scope is not valid JSON object")]
    problems = []
    if scope.get("schemaVersion") != 1:
        problems.append("schemaVersion must be 1")
    target = scope.get("targetRelease")
    tm = ACCEPTANCE_RELEASE_RE.fullmatch(target or "")
    if not tm:
        problems.append("targetRelease must match vX.Y.Z")
    if ACCEPTANCE_LIVE_KEYS & set(scope):
        problems.append("scope root contains live status fields")
    items = scope.get("items")
    if not isinstance(items, list):
        problems.append("items must be an array")
        items = []
    ids, issues = set(), set()
    target_tuple = tuple(map(int, tm.groups())) if tm else None
    for index, item in enumerate(items):
        prefix = f"items[{index}]"
        if not isinstance(item, dict):
            problems.append(f"{prefix} must be an object")
            continue
        if ACCEPTANCE_LIVE_KEYS & set(item):
            problems.append(f"{prefix} contains live status fields")
        aid = item.get("id")
        if not isinstance(aid, str) or not ACCEPTANCE_ID_RE.fullmatch(aid):
            problems.append(f"{prefix}.id must match AC-NNN")
        elif aid in ids:
            problems.append(f"duplicate acceptance id {aid}")
        else:
            ids.add(aid)
        issue = item.get("issue")
        if not isinstance(issue, int) or isinstance(issue, bool) or issue <= 0:
            problems.append(f"{prefix}.issue must be a positive GitHub issue number")
        elif issue in issues:
            problems.append(f"duplicate canonical issue #{issue}")
        else:
            issues.add(issue)
        owner = item.get("owner")
        if not isinstance(owner, str) or not ACCEPTANCE_OWNER_RE.fullmatch(owner):
            problems.append(f"{prefix}.owner must be a GitHub login without @")
        risk = item.get("risk")
        if risk not in ("low", "medium", "high", "critical"):
            problems.append(f"{prefix}.risk must be low/medium/high/critical")
        evidence = item.get("evidence")
        if not isinstance(evidence, list) or not evidence or any(x not in ACCEPTANCE_EVIDENCE for x in evidence):
            problems.append(f"{prefix}.evidence must be a non-empty subset of {sorted(ACCEPTANCE_EVIDENCE)}")
        else:
            if len(evidence) != len(set(evidence)):
                problems.append(f"{prefix}.evidence has duplicates")
            if "ci" not in evidence:
                problems.append(f"{prefix}.evidence must include ci")
            if risk in ("high", "critical") and "test" not in evidence:
                problems.append(f"{prefix} high/critical risk requires test evidence")
        deferred = item.get("deferredTo")
        if deferred is not None:
            dm = ACCEPTANCE_RELEASE_RE.fullmatch(deferred) if isinstance(deferred, str) else None
            if not dm:
                problems.append(f"{prefix}.deferredTo must match vX.Y.Z")
            elif target_tuple and tuple(map(int, dm.groups())) <= target_tuple:
                problems.append(f"{prefix}.deferredTo must be newer than targetRelease")
            if not isinstance(item.get("deferIssue"), int) or isinstance(item.get("deferIssue"), bool) or item.get("deferIssue", 0) <= 0:
                problems.append(f"{prefix}.deferIssue is required for a defer")
    return [("fail" if problems else "ok", "ACC-1", "Acceptance scope contract",
             "; ".join(problems[:12]) if problems else f"{len(items)} scoped item(s), target {target}")]


def acceptance_mapping_problems(m, body, bot=False):
    if m.get("acceptance", {}).get("mode", "none") != "continuous" or bot:
        return []
    sec = re.search(r"(?ims)^#+\s*Acceptance mapping\s*$(.*?)(?=^#+\s|\Z)", body or "")
    if not sec:
        return [("fail", "ACC-1", "Acceptance mapping", "add ## Acceptance mapping with AC-* IDs or not-applicable reason")]
    text = re.sub(r"<!--.*?-->", "", sec.group(1), flags=re.S).strip()
    na = re.search(r"(?im)^\s*not-applicable:\s*(\S.+)$", text)
    ids = sorted(set(re.findall(r"\bAC-[0-9]{3,}\b", text)))
    if na and ids:
        return [("fail", "ACC-1", "Acceptance mapping", "cannot combine AC-* mappings with not-applicable")]
    if na:
        reason = na.group(1).strip()
        return [("ok" if len(reason) >= 12 else "fail", "ACC-1", "Acceptance mapping",
                 reason if len(reason) >= 12 else "not-applicable needs a specific reason (>=12 chars)")]
    if not ids:
        return [("fail", "ACC-1", "Acceptance mapping", "no AC-* ID and no justified not-applicable")]
    scope = acceptance_scope()
    known = {item.get("id") for item in scope.get("items", []) if isinstance(item, dict)} if isinstance(scope, dict) else set()
    unknown = [aid for aid in ids if aid not in known]
    return [("fail" if unknown else "ok", "ACC-1", "Acceptance mapping",
             f"unknown: {', '.join(unknown)}" if unknown else ", ".join(ids))]


# ---------------------------------------------------------------- pull request
def github_api(path, method="GET", payload=None, allow_missing=False):
    """GitHub REST through Python stdlib; consumer runners do not need the GitHub CLI."""
    base = os.environ.get("GITHUB_API_URL", "https://api.github.com").rstrip("/")
    token = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GitHub API token is unavailable")
    url = path if path.startswith("https://") else f"{base}/{path.lstrip('/')}"
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        url, data=data, method=method,
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
    return json.loads(raw) if raw.strip() else None


def gh(*args):
    """Compatibility seam for offline tests; only the old gh('api', path) shape is accepted."""
    if len(args) == 2 and args[0] == "api":
        return github_api(args[1])
    raise RuntimeError(f"unsupported GitHub API compatibility call: {args!r}")


def ui_render_files(files):
    """Paths that can affect rendered UI; dependency/API-only changes do not require screenshots."""
    visual_suffixes = (".css", ".scss", ".sass", ".less", ".html", ".svg", ".vue", ".svelte")
    visual_suffixes += (".tsx", ".jsx")
    out = []
    for item in files:
        name = item.get("filename", "") if isinstance(item, dict) else str(item)
        lower = name.lower()
        parts = lower.split("/")
        if lower.endswith(visual_suffixes) or any(part in ("ui", "components", "styles", "views") for part in parts):
            out.append(name)
    return out


RISK_ORDER = {"low": 0, "medium": 1, "high": 2, "critical": 3}
HIGH_RISK_PATH_RE = re.compile(
    r"(^|/)(migrations?|deploy|security|auth|permissions?|\.github/workflows)(/|$)"
    r"|(^|/)(kavosh\.project\.json|standard/RULES\.md|release-please-config\.json)$",
    re.I,
)


BREAKING_CC_RE = re.compile(r"^[a-z]+(?:\([^)]+\))?!:", re.I)
CONTROL_PLANE_ARCH_RE = re.compile(
    r"(^|/)(standard/RULES\.md|intake/kavosh\.project\.schema\.json|release-please-config\.json)$"
    r"|^tooling/src/(governance|release_gate|main_guard|health)\.py$",
    re.I,
)
ADR_PATH_RE = re.compile(r"^docs/decisions/[0-9]{4}-[a-z0-9-]+\.md$", re.I)


def architectural_decision_problems(title, files):
    """DOC-2: a breaking control-plane Conventional Commit must carry its ADR in the same PR."""
    names = [item.get("filename", "") if isinstance(item, dict) else str(item) for item in files]
    breaking = bool(BREAKING_CC_RE.match(title or ""))
    control = [name for name in names if CONTROL_PLANE_ARCH_RE.search(name)]
    if not breaking or not control:
        return [("ok", "DOC-2", "Breaking control-plane ADR", "not required for this PR shape")]
    adrs = [name for name in names if ADR_PATH_RE.fullmatch(name)]
    if not adrs:
        return [("fail", "DOC-2", "Breaking control-plane ADR",
                 f"breaking control-plane change requires a changed docs/decisions ADR; paths: {', '.join(control[:5])}")]
    return [("ok", "DOC-2", "Breaking control-plane ADR", ", ".join(adrs[:3]))]


def change_risk_problems(body, files, bot=False):
    """CR-1/2: declare change risk independently of diff size; sensitive paths impose a high-risk floor."""
    if bot:
        return [("ok", "CR-1", "Automated dependency/change risk", "bot PR uses its automation policy")], "medium"
    risk_match = re.search(r"(?im)^Risk:\s*(low|medium|high|critical)\s*$", body or "")
    cap_match = re.search(r"(?im)^Capabilities:\s*(\S.+)$", body or "")
    if not risk_match or not cap_match:
        return [("fail", "CR-1", "Declared change risk and capabilities",
                 "add Risk: low|medium|high|critical and a non-empty Capabilities: line")], None
    risk = risk_match.group(1).lower()
    out = [("ok", "CR-1", "Declared change risk and capabilities",
            f"{risk}; {cap_match.group(1).strip()}")]
    sensitive = []
    for item in files:
        name = item.get("filename", "") if isinstance(item, dict) else str(item)
        if HIGH_RISK_PATH_RE.search(name):
            sensitive.append(name)
    if sensitive and RISK_ORDER[risk] < RISK_ORDER["high"]:
        out.append(("fail", "CR-2", "Sensitive/control-plane change risk floor",
                    f"{risk} is below high for {', '.join(sensitive[:5])}"))
    else:
        out.append(("ok", "CR-2", "Risk floor", "high-sensitive paths respected" if sensitive else "no machine-detected high-risk path"))
    return out, risk


def check_pr(m, event, repo):
    pr = event["pull_request"]
    default = event["repository"]["default_branch"]
    head, base = pr["head"]["ref"], pr["base"]["ref"]
    title, body = pr["title"] or "", pr.get("body") or ""
    limits = m.get("limits", {}) if m else {}
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
    lines = sum(f.get("additions", 0) + f.get("deletions", 0) for f in counted)
    risk_results, _declared_risk = change_risk_problems(body, files, bot)
    for level, rule, t, d in risk_results:
        add(level, rule, t, d)
    for level, rule, t, d in architectural_decision_problems(title, files):
        add(level, rule, t, d)
    visual_files = ui_render_files(files)
    if m.get("ui", {}).get("kind", "none") != "none" and visual_files:
        evidence = re.search(r"(?im)^ui evidence:\s*(https?://\S+|\S.+)$", body)
        add("ok" if evidence else "fail", "UI-2", "Render evidence for visual UI changes",
            evidence.group(1) if evidence else f"required for {len(visual_files)} visual file(s)")
    else:
        add("ok", "UI-2", "No render evidence needed", "PR has no visual UI changes")

    add("ok", "PR-3", "Diff-size telemetry",
        f"{lines} review-counted lines / {len(counted)} review-counted files; no universal size gate")

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
    for level, rule, t, d in acceptance_mapping_problems(m, body, bot):
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
