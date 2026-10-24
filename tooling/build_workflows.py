#!/usr/bin/env python3
"""Build the reusable workflows from tooling/src/*.py + tooling/templates/*.yml.

    python3 tooling/build_workflows.py          # write .github/workflows/kavosh-*.yml
    python3 tooling/build_workflows.py --check  # exit 1 if generated files are stale (used by self-check)

Why: the Python lives in normal files (testable, lintable) while the workflows stay self-contained,
because a reusable workflow running in a product repo cannot read files from private KavoshStart.
"""
import json
import re
import sys
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAIRS = {
    "kavosh-governance.yml": "governance.py",
    "kavosh-main-guard.yml": "main_guard.py",
    "kavosh-health.yml": "health.py",
    "kavosh-release.yml": "release_gate.py",
    "kavosh-rc.yml": "rc_gate.py",
    "kavosh-test-staging.yml": "rc_gate.py",
    "kavosh-portfolio.yml": None,  # static wrapper; its logic is scripts/portfolio_guard.py
}
INDENT = " " * 10


def validate_embedded_blocks(template: str, source: str) -> None:
    """Embedded Python stays a literal scalar; GitHub expressions belong in env.

    GitHub converts a scalar containing interpolation into a format expression.
    A large inlined source can exceed its expression parser limit before any job
    starts. This structural invariant prevents that without arbitrary truncation.
    """
    if "${{" in source:
        raise ValueError("embedded source contains GitHub interpolation; pass context through env")
    lines = template.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^( +)run: [|>][-+]?[ \t]*$", line)
        if not match:
            continue
        indent = len(match.group(1))
        block = []
        for child in lines[index + 1:]:
            if child.strip() and len(child) - len(child.lstrip()) <= indent and child != "__PYTHON__":
                break
            block.append(child)
        text = "\n".join(block)
        if "__PYTHON__" in text and "${{" in text:
            raise ValueError("embedded run block contains GitHub interpolation; move context to step env")


def build(template: str, source) -> str:
    if source is None:
        return (ROOT / "tooling" / "templates" / template).read_text(encoding="utf-8")
    code = (ROOT / "tooling" / "src" / source).read_text(encoding="utf-8")
    receipt_import = r"^from receipts import [^\n]+ # __EMBED_RECEIPTS__$"
    if re.search(receipt_import, code, flags=re.M):
        shared = (ROOT / "tooling" / "src" / "receipts.py").read_text(encoding="utf-8")
        code = re.sub(receipt_import, lambda _: "# BEGIN shared receipt verifier\n" + shared.rstrip() + "\n# END shared receipt verifier", code, flags=re.M)
    if "__SCHEMA_JSON__" in code:
        schema = json.loads((ROOT / "intake" / "kavosh.project.schema.json").read_text(encoding="utf-8"))
        compact = json.dumps(schema, ensure_ascii=False, separators=(",", ":"))
        if '"""' in compact:
            raise SystemExit("schema must not contain triple quotes")
        code = code.replace("__SCHEMA_JSON__", compact)
    for line in code.splitlines():
        if line.strip() == "PY":
            raise SystemExit(f"{source}: a line consisting of 'PY' would end the heredoc")
    body = textwrap.indent(code.rstrip("\n"), INDENT, lambda l: l.strip() != "")
    tpl = (ROOT / "tooling" / "templates" / template).read_text(encoding="utf-8")
    validate_embedded_blocks(tpl, code)
    return tpl.replace("__PYTHON__", body)


def main() -> int:
    check = "--check" in sys.argv
    stale = []
    out_dir = ROOT / ".github" / "workflows"
    out_dir.mkdir(parents=True, exist_ok=True)
    for template, source in PAIRS.items():
        content = build(template, source)
        target = out_dir / template
        current = target.read_text(encoding="utf-8") if target.exists() else None
        if current != content:
            stale.append(template)
            if not check:
                target.write_text(content, encoding="utf-8", newline="\n")
    if check and stale:
        print("stale generated workflows:", ", ".join(stale), "— run python3 tooling/build_workflows.py")
        return 1
    print("up to date" if not stale else "written: " + ", ".join(stale))
    return 0


if __name__ == "__main__":
    sys.exit(main())
