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
PLACEHOLDER = re.compile(r"\{\{([A-Z_]+)\}\}")
EXECUTABLE = {".githooks/pre-push", ".githooks/pre-commit", "deploy/kavosh-deploy.sh"}


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
    # CI-1: private → self-hosted runner registered to this repository; public → GitHub-hosted
    if m.get("visibility", "private") == "private":
        labels = m.get("ci", {}).get("runnerLabels") or ["self-hosted", "linux", "x64", slug]
    else:
        labels = ["ubuntu-latest"]
    return {
        "NAME": m["name"],
        "REPO": m["repo"],
        "SLUG": slug,
        "OWNER": m.get("owner") or m["repo"].split("/")[0],
        "SUMMARY": m["summary"],
        "TIER": m["tier"],
        "RUNTIME": m["runtime"],
        "KAVOSHSTART": m["kavoshStart"],
        "KAVOSHUI": ui.get("kavoshui") or "(not used)",
        "UI_KIND": ui.get("kind", "none"),
        "DEPLOY_METHOD": m.get("deploy", {}).get("method", "none"),
        "BUDGET": str(m.get("ci", {}).get("monthlyMinutesBudget", "")),
        "PR_MAX_LINES": str(m.get("limits", {}).get("prMaxLines", 400)),
        "PACKAGE": "true" if m["runtime"] in ("none", "desktop") else "false",
        "RUNS_ON_JSON": json.dumps(labels, separators=(",", ":")),
        "RUNS_ON_YAML": ("[" + ", ".join(labels) + "]") if labels != ["ubuntu-latest"] else "ubuntu-latest",
    }


def render(text: str, vals: dict, rel: str) -> str:
    missing = sorted({k for k in PLACEHOLDER.findall(text) if k not in vals})
    if missing:
        raise SystemExit(f"{rel}: unknown placeholders {missing}")
    return PLACEHOLDER.sub(lambda mt: vals[mt.group(1)], text)


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    adopt, dry = "--adopt" in sys.argv, "--dry-run" in sys.argv
    if len(args) != 1:
        print(__doc__)
        return 2
    target = Path(args[0]).resolve()
    mpath = target / "kavosh.project.json"
    if not mpath.exists():
        raise SystemExit(f"{mpath} not found — complete the intake first (START.md §1 steps 1–3)")
    manifest = json.loads(mpath.read_text(encoding="utf-8"))
    vals = values(manifest)

    plan = {}  # rel -> source file (later layers override earlier ones)
    for layer in layers(manifest):
        base = TEMPLATES / layer
        if base.exists():
            for f in sorted(base.rglob("*")):
                if f.is_file():
                    rel = f.relative_to(base).as_posix()
                    if manifest.get("ci", {}).get("runner") == "none" and rel.startswith(".github/workflows/"):
                        continue
                    plan[rel] = f

    created, conflicts = [], []
    for rel, src in sorted(plan.items()):
        text = render(src.read_text(encoding="utf-8"), vals, rel)
        dest = target / rel
        if dest.exists():
            if not adopt:
                conflicts.append(rel)
                continue
            dest = dest.with_name(dest.name + ".kavosh-new")
            conflicts.append(rel)
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
    return 1 if conflicts and not adopt else 0


if __name__ == "__main__":
    sys.exit(main())
