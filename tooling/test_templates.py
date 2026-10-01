#!/usr/bin/env python3
"""Self-test: scaffold every tier × runtime combination into a temp git repo and run the governance
checks (file + manifest layer) on it. A template that violates KavoshStart's own rules fails here.

    python3 tooling/test_templates.py
"""
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
try:
    import yaml
except ImportError:  # Installed by the repository self-check; local scaffold checks stay stdlib-friendly.
    yaml = None

ROOT = Path(__file__).resolve().parent.parent
EXAMPLE = json.loads((ROOT / "intake" / "kavosh.project.example.json").read_text(encoding="utf-8"))
COMBOS = [
    ("T0", "none", "release-artifact", "none", []),
    ("T1", "server", "pull-build", "admin", []),
    ("T1", "desktop", "release-artifact", "desktop", []),
    ("T2", "server", "pull-image", "web", ["test", "production"]),
    ("T2", "static", "pull-build", "web", ["production"]),
]


def manifest(tier, runtime, method, ui, envs):
    m = json.loads(json.dumps(EXAMPLE))
    m.update(tier=tier, runtime=runtime)
    m["deploy"] = {"method": method, "environments": envs}
    m["ui"] = {"kind": ui, "kavoshui": None if ui == "none" else "1.0.0", "locales": ["fa-IR"]}
    m["ci"]["monthlyMinutesBudget"] = 0
    if tier == "T0":  # a public tool: GitHub-hosted runners (CI-1)
        m["visibility"] = "public"
        m["ci"] = {"runner": "github-hosted", "monthlyMinutesBudget": 0}
        m["data"] = {"sensitivity": "none", "regulatedIntegrations": [], "multiTenant": False}
        m["size"] = {"domains": 1, "lifetime": "weeks", "parallelStreams": 1}
    if tier == "T1":
        m["data"] = {"sensitivity": "internal", "regulatedIntegrations": [], "multiTenant": False}
        m["size"] = {"domains": 2, "lifetime": "months", "parallelStreams": 1}
    return m


def gov_source():
    code = (ROOT / "tooling" / "src" / "governance.py").read_text(encoding="utf-8")
    schema = (ROOT / "intake" / "kavosh.project.schema.json").read_text(encoding="utf-8")
    return code.replace("__SCHEMA_JSON__", json.dumps(json.loads(schema)))


def main():
    failures = 0
    gov = gov_source()
    for combo in COMBOS:
        with tempfile.TemporaryDirectory() as d:
            repo = Path(d)
            subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
            (repo / "kavosh.project.json").write_text(json.dumps(manifest(*combo), indent=2), encoding="utf-8")
            r = subprocess.run([sys.executable, str(ROOT / "scripts" / "scaffold.py"), str(repo)],
                               capture_output=True, text=True, encoding="utf-8")
            if r.returncode != 0:
                print(f"FAIL scaffold {combo}:\n{r.stdout}{r.stderr}")
                failures += 1
                continue
            if yaml is not None:
                try:
                    for path in repo.rglob("*"):
                        if path.is_file() and path.suffix in (".yml", ".yaml"):
                            yaml.safe_load(path.read_text(encoding="utf-8"))
                        elif path.is_file() and path.suffix == ".json":
                            json.loads(path.read_text(encoding="utf-8"))
                except Exception as e:
                    print(f"FAIL rendered YAML/JSON {combo}: {path}: {e}")
                    failures += 1
                    continue
            # REL-4/5/6: gated release in every repo, exact KavoshStart pins, package only for artifact runtimes
            pin = EXAMPLE["kavoshStart"]
            rel = (repo / ".github/workflows/release.yml").read_text(encoding="utf-8")
            kav = (repo / ".github/workflows/kavosh.yml").read_text(encoding="utf-8")
            want_pkg = "true" if combo[1] in ("none", "desktop") else "false"
            problems = []
            if f"kavosh-release.yml@{pin}" not in rel or f"package: {want_pkg}" not in rel:
                problems.append("REL-4/5 release.yml")
            if kav.count(f"@{pin}") != 3 or "@v1\n" in kav + rel:
                problems.append("REL-6 exact pins")
            if want_pkg == "true" and "\npackage: " not in (repo / "Makefile").read_text(encoding="utf-8"):
                problems.append("CI-8 make package target")
            if problems:
                print(f"FAIL release contract {combo}: {', '.join(problems)}")
                failures += 1
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            (repo / "gov.py").write_text(gov, encoding="utf-8")
            env = dict(os.environ, REPO="bagdeli/Example", ENFORCE="true", GITHUB_EVENT_PATH="",
                       KAVOSH_REPORT=str(repo / "report.md"), GITHUB_STEP_SUMMARY="", PYTHONIOENCODING="utf-8")
            r = subprocess.run([sys.executable, "gov.py"], cwd=repo, env=env, capture_output=True, text=True, encoding="utf-8")
            report = (repo / "report.md").read_text(encoding="utf-8") if (repo / "report.md").exists() else r.stderr
            fails = [l for l in report.splitlines() if l.startswith("| ❌")]
            status = "ok  " if r.returncode == 0 and not fails else "FAIL"
            files = sum(1 for p in repo.rglob("*") if p.is_file() and ".git" not in p.parts)
            print(f"{status} {combo[0]}/{combo[1]:8} files={files:3} governance={'PASS' if not fails else 'FAIL'}")
            for l in fails:
                print("     ", l)
            if status == "FAIL":
                failures += 1
                continue
            if combo[0] != "T1" or combo[1] != "server":
                continue
            # Negative test: inject known violations and require each rule to fail.
            (repo / "docs" / "STATUS.md").write_text("current head 4c9c17d816b936e176bc81b48a0eca093ae6e599\n", encoding="utf-8")
            agents = (repo / "AGENTS.md").read_text(encoding="utf-8")
            (repo / "AGENTS.md").write_text(agents + "\nRead Issue #51 first.\n" + "x\n" * 150, encoding="utf-8")
            (repo / "big.md").write_text("a" * 70000, encoding="utf-8")
            m = json.loads((repo / "kavosh.project.json").read_text(encoding="utf-8"))
            m["tier"] = "T0"
            (repo / "kavosh.project.json").write_text(json.dumps(m), encoding="utf-8")
            wf = repo / ".github" / "workflows" / "ci.yml"
            text = wf.read_text(encoding="utf-8")
            wf.write_text(text.replace("runs-on: [self-hosted, linux, x64, kavoshsms]", "runs-on: ubuntu-latest"), encoding="utf-8")
            (repo / ".githooks" / "pre-push").unlink()
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            r = subprocess.run([sys.executable, "gov.py"], cwd=repo, env=env, capture_output=True, text=True, encoding="utf-8")
            report = (repo / "report.md").read_text(encoding="utf-8")
            expected = ["SRC-3", "SRC-2", "AI-1", "DOC-1", "SRC-5", "CI-1", "AI-4"]
            caught = [rid for rid in expected if any(l.startswith("| ❌") and f"| {rid} |" in l for l in report.splitlines())]
            missed = sorted(set(expected) - set(caught))
            print(f"{'ok  ' if not missed and r.returncode == 1 else 'FAIL'} negative test caught {len(caught)}/{len(expected)} {missed or ''}")
            if missed or r.returncode != 1:
                failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
