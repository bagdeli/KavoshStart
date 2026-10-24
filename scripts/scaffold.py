#!/usr/bin/env python3
"""Scaffold a Kavosh project from KavoshStart templates (START.md §1 step 4, §2 step 4).

    python3 scripts/scaffold.py <repo-dir>            # NEW: target must contain kavosh.project.json
    python3 scripts/scaffold.py <repo-dir> --adopt    # ADOPT: existing files get a *.kavosh-new sibling
    python3 scripts/scaffold.py <repo-dir> --dry-run  # show what would happen

Layers, later wins inside the template set (never over existing files in the target):
    common  →  tier/T1 (for T1 and T2)  →  tier/T2 (for T2)  →  runtime/server (server, static)
(runtime none/desktop: release.yml gets package: true — assets are built by kavosh-release)
"""
import json
import re
import stat
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = ROOT / "templates"
SELF_STANDARD_REPO = "bagdeli/KavoshStart"
KAVOSHSTART_TAG_RE = re.compile(r"^v[0-9]+[.][0-9]+[.][0-9]+$")
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")
EXECUTABLE = {".githooks/pre-push", ".githooks/pre-commit", "deploy/kavosh-deploy.sh"}


def validate_standard_pin(manifest: dict) -> None:
    """Fail closed before rendering templates if the standard identity/pin is ambiguous."""
    repo, pin = manifest.get("repo"), manifest.get("kavoshStart")
    if repo == SELF_STANDARD_REPO:
        if pin != "self":
            raise SystemExit("canonical KavoshStart must use kavoshStart 'self'")
        return
    if pin == "self":
        raise SystemExit(f"kavoshStart 'self' is reserved for {SELF_STANDARD_REPO}; consumers must pin vX.Y.Z")
    if not isinstance(pin, str) or not KAVOSHSTART_TAG_RE.fullmatch(pin):
        raise SystemExit(f"consumer kavoshStart must be an exact release tag vX.Y.Z, got {pin!r}; resolve the latest stable release before scaffold")


def layers(manifest: dict) -> list:
    out = ["common"]
    if manifest["tier"] in ("T1", "T2"):
        out.append("tier/T1")
    if manifest["tier"] == "T2":
        out.append("tier/T2")
    if manifest["runtime"] in ("server", "static"):
        out.append("runtime/server")
    return out


def values(m: dict) -> dict:
    ui = m.get("ui", {})
    slug = re.sub(r"[^a-z0-9]+", "-", m["repo"].split("/")[-1].lower()).strip("-")
    # CI-1: the manifest selects the runner; private GitHub-hosted jobs require per-run authorization.
    runner = m.get("ci", {}).get("runner", "github-hosted")
    if runner == "self-hosted":
        labels = m.get("ci", {}).get("runnerLabels") or (
            ["self-hosted", "linux", "x64"]
            if m.get("visibility") == "private" and not (m.get("review") or {}).get("teamProcess")
            else ["self-hosted", "linux", "x64", slug])
    else:
        labels = ["ubuntu-latest"]
    return {
        "NAME": m["name"],
        "REPO": m["repo"],
        "SLUG": slug,
        "OWNER": m.get("owner") or m["repo"].split("/")[0],
        "SUMMARY": m["summary"],
        "TIER": m["tier"],
        "CI_TIMEOUT": {"T0": "10", "T1": "15", "T2": "20"}.get(m.get("tier"), "10"),
        "RUNTIME": m["runtime"],
        "KAVOSHSTART": m["kavoshStart"],
        "DESIGN_SYSTEM": (
            f"{ui['designSystem']['package']}@{ui['designSystem']['version']}"
            if isinstance(ui.get("designSystem"), dict) else "(not selected)"
        ),
        "UI_KIND": ui.get("kind", "none"),
        "DEPLOY_METHOD": m.get("deploy", {}).get("method", "none"),
        "BUDGET": str(m.get("ci", {}).get("monthlyMinutesBudget", "")),
        "PACKAGE": "true" if m.get("deploy", {}).get("method") == "release-artifact" else "false",
        "CI_WORKFLOW": m.get("ci", {}).get("requiredWorkflow") or ".github/workflows/ci.yml",
        "RUNS_ON_JSON": json.dumps(labels, separators=(",", ":")),
        "RUNS_ON_YAML": ("[" + ", ".join(labels) + "]") if labels != ["ubuntu-latest"] else "ubuntu-latest",
        "PRIVATE_HOSTED": "true" if m.get("visibility") == "private" and m.get("ci", {}).get("runner") == "github-hosted" else "false",
        "SELF_HOSTED": "true" if m.get("ci", {}).get("runner") == "self-hosted" else "false",
    }


def include_template(layer: str, rel: str, manifest: dict) -> bool:
    """Opt-in complexity only: no default App, second AI or licence ledger."""
    if rel == ".github/workflows/ai-review.yml":
        return False  # Optional team example; never auto-install a paid reviewer.
    if layer == "common" and rel == "docs/THIRD_PARTY.md":
        return False  # Optional inventory only for an actual distribution/legal use case.
    if layer == "tier/T2" and rel.startswith("acceptance/"):
        return (manifest.get("acceptance") or {}).get("mode") == "continuous"
    # Keep architecture facts in PROJECT.md; a template library is not a task list.
    team = (manifest.get("review") or {}).get("teamProcess") is True
    if not team and (rel.startswith("specs/") or rel.startswith("docs/architecture/")
                     or (rel.startswith(".github/ISSUE_TEMPLATE/") and not rel.endswith(("bug.yml", "config.yml")))
                     or rel in ("docs/decisions/0000-template.md", "docs/decisions/0001-adopt-kavoshstart.md")):
        return False
    if layer == "runtime/server" and (manifest.get("deploy") or {}).get("method") not in ("pull-build", "pull-image"):
        # Custom/native adapters own their runtime; do not install Compose, .env,
        # systemd or the standard pull-deployer's runbook under another adapter.
        return rel.startswith(".github/workflows/")
    if rel == "docs/runbooks/local-validation.md":
        return (manifest.get("ci") or {}).get("runner") == "none"
    return True


def render(text: str, vals: dict, rel: str) -> str:
    missing = sorted({k for k in PLACEHOLDER.findall(text) if k not in vals})
    if missing:
        raise SystemExit(f"{rel}: unknown placeholders {missing}")
    return PLACEHOLDER.sub(lambda mt: vals[mt.group(1)], text)


def render_job_runners(text: str, rel: str, manifest: dict) -> str:
    """Honor selected per-job labels in generated callers without changing other jobs."""
    overrides = (manifest.get("ci") or {}).get("runnerJobLabels") or {}
    for key, labels in overrides.items():
        path, separator, job = key.rpartition("#")
        if not separator or path != rel:
            continue  # A consumer-owned workflow may be added after scaffold.
        pattern = re.compile(r"(?ms)^  " + re.escape(job) + r":.*?(?=^  [A-Za-z0-9_-]+:|\Z)")
        def replace(match):
            block = match.group(0)
            selector = json.dumps(labels, separators=(",", ":"))
            # A reusable workflow input is JSON text; a concrete job uses an array.
            value = "'" + selector + "'" if re.search(r"(?m)^    uses:", block) else selector
            return re.sub(r"(?m)^( +runs-on:).*$", lambda m: m.group(1) + " " + value, block)
        text = pattern.sub(replace, text)
    return text


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    adopt, dry = "--adopt" in sys.argv, "--dry-run" in sys.argv
    unknown = [a for a in sys.argv[1:] if a.startswith("--") and a not in ("--adopt", "--dry-run")]
    if unknown:
        raise SystemExit("unknown scaffold option: " + ", ".join(unknown))
    if len(args) != 1:
        print(__doc__)
        return 2
    target = Path(args[0]).resolve()
    mpath = target / "kavosh.project.json"
    if not mpath.exists():
        raise SystemExit(f"{mpath} not found — complete the intake first (START.md §1 steps 1–3)")
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    validate_standard_pin(manifest)
    runner = manifest.get("ci", {}).get("runner")
    if manifest.get("visibility") == "private" and runner != "self-hosted" and (
            set(manifest.get("ci", {})) & {"runnerLabels", "runners", "trustModelADR"}):
        raise SystemExit("CI-1: hosted/local-only CI cannot contain self-hosted runner fields")
    if runner == "none" and not (manifest.get("tier") == "T1" and manifest.get("runtime") == "static"):
        raise SystemExit("CI-1: local-only 'none' is supported only for T1/static")
    vals = values(manifest)

    plan = {}  # rel -> source file (later layers override earlier ones)
    for layer in layers(manifest):
        base = TEMPLATES / layer
        if base.exists():
            for f in sorted(base.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(base).as_posix()
                    if not include_template(layer, rel, manifest):
                        continue
                    if manifest.get("ci", {}).get("runner") == "none" and rel.startswith(".github/workflows/"):
                        continue
                    if rel == ".github/workflows/rc.yml" and "test" not in manifest.get("deploy", {}).get("environments", []):
                        continue
                    if manifest.get("deploy", {}).get("method") == "custom" and layer == "runtime/server" and rel.startswith("deploy/"):
                        continue
                    plan[rel] = f

    created, conflicts = [], []
    blocked_review = False
    for rel, src in sorted(plan.items()):
        text = render(src.read_text(encoding="utf-8"), vals, rel)
        if rel == ".github/dependabot.yml":
            # Actions only by default; add native ecosystems when their real
            # dependency files exist, not merely because a Tier is T1/T2.
            text = render((TEMPLATES / "common" / rel).read_text(encoding="utf-8"), vals, rel)
        text = render_job_runners(text, rel, manifest)
        dest = target / rel
        if dest.exists():
            if not adopt:
                conflicts.append(rel)
                continue
            dest = dest.with_name(dest.name + ".kavosh-new")
            conflicts.append(rel)
            if dest.exists():
                blocked_review = True
                print("  ! preserved existing review file:", dest.relative_to(target).as_posix())
                continue
        if not dry:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(text, encoding="utf-8", newline="\n")
            if rel in EXECUTABLE:
                dest.chmod(dest.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        created.append(dest.relative_to(target).as_posix())

    print(f"KavoshStart {manifest['kavoshStart']} · {manifest['tier']} / {manifest['runtime']} · layers: {', '.join(layers(manifest))}")
    print(f"{'would write' if dry else 'written'}: {len(created)} files")
    for c in created:
        print("  +", c)
    if conflicts:
        verb = "merge by hand (see *.kavosh-new)" if adopt else "SKIPPED — already exist (use --adopt to write *.kavosh-new)"
        print(f"{len(conflicts)} existing files, {verb}:")
        for c in conflicts:
            print("  !", c)
    todo = [p.relative_to(target).as_posix() for p in target.rglob("*")
            if p.is_file() and ".git" not in p.parts and "TODO(kavosh)" in p.read_text(encoding="utf-8", errors="ignore")] if not dry else []
    if todo:
        print(f"Next: replace TODO(kavosh) markers in {len(todo)} files, make `make check` pass, then run install-agent-guards.sh")
    return 1 if blocked_review or (conflicts and not adopt) else 0


if __name__ == "__main__":
    sys.exit(main())
