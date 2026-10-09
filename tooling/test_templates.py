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


def manifest(tier, runtime, method, ui, envs, runner=None):
    m = json.loads(json.dumps(EXAMPLE))
    m["repo"] = "bagdeli/Example"
    m.update(tier=tier, runtime=runtime)
    m["deploy"] = {"method": method, "environments": envs}
    m["ui"] = {"kind": ui, "kavoshui": None if ui == "none" else "1.0.0", "locales": ["fa-IR"]}
    m["ci"]["monthlyMinutesBudget"] = 0
    if tier == "T0":  # a public tool: GitHub-hosted runners (CI-1)
        m["visibility"] = "public"
        m["ci"] = {"runner": "github-hosted", "monthlyMinutesBudget": 0}
        m["data"] = {"sensitivity": "none", "regulatedIntegrations": [], "multiTenant": False}
        m["size"] = {"domains": 1, "lifetime": "weeks", "parallelStreams": 1}
    else:
        m["ci"]["runnerLabels"] = ["self-hosted", "linux", "x64", "example"]
    if tier == "T1":
        m["data"] = {"sensitivity": "internal", "regulatedIntegrations": [], "multiTenant": False}
        m["size"] = {"domains": 2, "lifetime": "months", "parallelStreams": 1}
    if runner is not None:
        m["ci"]["runner"] = runner
        m["ci"].pop("runnerLabels", None)
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
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
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
            rc_path = repo / ".github/workflows/rc.yml"
            if combo[1] in ("server", "static"):
                if not rc_path.exists():
                    problems.append("REL-7 rc.yml missing")
                else:
                    rc_text = rc_path.read_text(encoding="utf-8")
                    if (f"kavosh-rc.yml@{pin}" not in rc_text or "workflow_dispatch:" not in rc_text or
                            "expected-sha:" not in rc_text or "authorization-confirmed:" not in rc_text):
                        problems.append("REL-7 exact RC dispatch contract")
            elif rc_path.exists():
                problems.append("REL-7 rc.yml should only scaffold for server/static")
            if problems:
                print(f"FAIL release contract {combo}: {', '.join(problems)}")
                failures += 1
            if combo[1] in ("server", "static") and combo[2] != "custom":
                deployer = (repo / "deploy/kavosh-deploy.sh").read_text(encoding="utf-8")
                deploy_env = (repo / "deploy/deploy.env.example").read_text(encoding="utf-8")
                runbook = (repo / "docs/runbooks/deploy.md").read_text(encoding="utf-8")
                required_deployer = ("--verify-environment", "VERSION_URL", "HEALTH_URL", "PUBLIC_BASE_URL",
                                     "ENVIRONMENT_CONFORMANCE=PASS", 'if [ "$target" = "$current" ]')
                missing = [marker for marker in required_deployer if marker not in deployer]
                if missing:
                    print(f"FAIL DEP-7/8 deployer contract {combo}: missing {missing}")
                    failures += 1
                for marker in ("DEPLOY_METHOD=", "VERSION_URL=", "HEALTH_URL=", "PUBLIC_BASE_URL=", "ARTIFACT_VERIFY_CMD="):
                    if marker not in deploy_env:
                        print(f"FAIL DEP-7/9 deploy env contract {combo}: missing {marker}")
                        failures += 1
                if "kavosh-deploy-{{SLUG}}" in runbook:
                    print(f"FAIL rendered runbook kept an unresolved slug placeholder {combo}")
                    failures += 1
                if f"kavosh-deploy-example.timer" not in runbook or "--verify-environment" not in runbook:
                    print(f"FAIL DEP-7 project-scoped admission runbook {combo}")
                    failures += 1
                if combo[2] == "pull-image" and "pull-image requires ARTIFACT_VERIFY_CMD" not in deployer:
                    print(f"FAIL DEP-9 pull-image provenance gate {combo}")
                    failures += 1
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            (repo / "gov.py").write_text(gov, encoding="utf-8")
            env = dict(os.environ, REPO="bagdeli/Example", ENFORCE="true", GITHUB_EVENT_PATH="",
                       KAVOSH_REPORT=str(repo / "report.md"), GITHUB_STEP_SUMMARY="", PYTHONIOENCODING="utf-8")
            r = subprocess.run([sys.executable, "gov.py"], cwd=repo, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
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
            m["ci"] = {"runner": "self-hosted", "runnerLabels": ["self-hosted", "linux", "x64", "example"],
                       "monthlyMinutesBudget": 0}
            (repo / "kavosh.project.json").write_text(json.dumps(m), encoding="utf-8")
            wf = repo / ".github" / "workflows" / "ci.yml"
            text = wf.read_text(encoding="utf-8")
            wf.write_text(text.replace("runs-on: [self-hosted, linux, x64, example]", "runs-on: ubuntu-latest"), encoding="utf-8")
            (repo / ".githooks" / "pre-push").unlink()
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            r = subprocess.run([sys.executable, "gov.py"], cwd=repo, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace")
            report = (repo / "report.md").read_text(encoding="utf-8")
            expected = ["SRC-3", "SRC-2", "AI-1", "DOC-1", "SRC-5", "CI-1", "AI-4"]
            caught = [rid for rid in expected if any(l.startswith("| ❌") and f"| {rid} |" in l for l in report.splitlines())]
            missed = sorted(set(expected) - set(caught))
            print(f"{'ok  ' if not missed and r.returncode == 1 else 'FAIL'} negative test caught {len(caught)}/{len(expected)} {missed or ''}")
            if missed or r.returncode != 1:
                failures += 1
    # CI-1: a T1/static local-only project must scaffold no Actions workflows and pass governance locally.
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        local_manifest = manifest("T1", "static", "pull-build", "admin", ["production"], runner="none")
        (repo / "kavosh.project.json").write_text(json.dumps(local_manifest, indent=2), encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "scaffold.py"), str(repo)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        workflows = list((repo / ".github" / "workflows").glob("*.yml")) if (repo / ".github" / "workflows").exists() else []
        if r.returncode != 0 or workflows:
            print(f"FAIL T1/static local-only scaffold: return={r.returncode}, workflows={workflows}\\n{r.stdout}{r.stderr}")
            failures += 1
        else:
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            (repo / "gov.py").write_text(gov, encoding="utf-8")
            env = dict(os.environ, REPO="bagdeli/Example", ENFORCE="true", GITHUB_EVENT_PATH="",
                       KAVOSH_REPORT=str(repo / "report.md"), GITHUB_STEP_SUMMARY="", PYTHONIOENCODING="utf-8")
            r = subprocess.run([sys.executable, "gov.py"], cwd=repo, env=env,
                               capture_output=True, text=True, encoding="utf-8", errors="replace")
            report = (repo / "report.md").read_text(encoding="utf-8") if (repo / "report.md").exists() else r.stderr
            if r.returncode != 0 or any(line.startswith("| ❌") for line in report.splitlines()):
                print(f"FAIL T1/static local-only governance:\\n{report}")
                failures += 1
            else:
                print("ok  T1/static local-only scaffold has no Actions workflows; local governance PASS")
    # Private GitHub-hosted CI must be opted in per run and bind the dispatch to the current PR head.
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        private_manifest = manifest("T1", "server", "pull-build", "admin", [], runner="github-hosted")
        (repo / "kavosh.project.json").write_text(json.dumps(private_manifest, indent=2), encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "scaffold.py"), str(repo)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0:
            print(f"FAIL private hosted scaffold:\n{r.stdout}{r.stderr}")
            failures += 1
        else:
            for name in ("ci.yml", "kavosh.yml", "release.yml", "rc.yml"):
                text = (repo / ".github/workflows" / name).read_text(encoding="utf-8")
                if "PRIVATE_HOSTED_DISPATCH_REQUIRED" not in text or "workflow_dispatch" not in text:
                    print(f"FAIL private hosted dispatch guard missing in {name}")
                    failures += 1
            ci_text = (repo / ".github/workflows/ci.yml").read_text(encoding="utf-8")
            if "(github.event_name == 'push' && !true)" not in ci_text or "github.event_name == 'workflow_dispatch'" not in ci_text:
                print("FAIL private hosted CI dispatch is not the only runner path")
                failures += 1
            if (repo / "deploy/kavosh-deploy.sh").exists() is False:
                print("FAIL default pull deploy scaffold missing")
                failures += 1
    # Custom deployment is opt-in by ADR and must not ship the pull-based deployer as if it matched that method.
    with tempfile.TemporaryDirectory() as d:
        repo = Path(d)
        subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
        custom_manifest = manifest("T1", "server", "pull-build", "admin", [], runner="self-hosted")
        custom_manifest["deploy"]["method"] = "custom"
        custom_manifest["deploy"]["authorizationADR"] = "docs/decisions/0002-custom-deploy.md"
        (repo / "kavosh.project.json").write_text(json.dumps(custom_manifest, indent=2), encoding="utf-8")
        r = subprocess.run([sys.executable, str(ROOT / "scripts" / "scaffold.py"), str(repo)],
                           capture_output=True, text=True, encoding="utf-8", errors="replace")
        if r.returncode != 0 or (repo / "deploy/kavosh-deploy.sh").exists():
            print(f"FAIL custom deploy scaffold kept the pull deployer:\n{r.stdout}{r.stderr}")
            failures += 1
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
