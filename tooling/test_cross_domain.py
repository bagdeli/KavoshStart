#!/usr/bin/env python3
"""Executable capability boundary fixtures; no cloud/site/product credentials.

Every selected profile runs real tools, a passing control and seeded defects.
Missing tools fail instead of silently skipping. See tooling/fixtures/README.md.
"""
import argparse
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import traceback
import xml.etree.ElementTree as ET
import zipapp

from junit_receipt import assertion_outcomes

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))
from governance import capability_profile_problems

PROFILES = ("package", "migration", "infrastructure", "browser-ui", "desktop", "cms-wordpress")


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def tool(name, env=None, alternatives=()):
    selected = os.environ.get(env, "") if env else ""
    value = selected or next((shutil.which(n) for n in (name, *alternatives) if shutil.which(n)), None)
    if not value or not Path(value).is_file():
        raise RuntimeError(f"missing tool {name}; configure {env or 'PATH'}; no profile is skipped")
    return value


def command(args, cwd, expected=(0,), timeout=60, env=None):
    result = subprocess.run([str(x) for x in args], cwd=cwd, env=env, text=True,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout)
    if result.returncode not in expected:
        raise AssertionError(f"{args[0]} exited {result.returncode}, expected {expected}\n"
                             f"{result.stdout[-6000:]}\n{result.stderr[-4000:]}")
    return result


def put(root, path, text):
    dest = root / path
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(text, encoding="utf-8")
    return dest


@contextmanager
def isolated(prefix):
    with tempfile.TemporaryDirectory(prefix=f"kavosh-{prefix}-") as directory:
        root = Path(directory)
        # Only child processes receive this environment. No user npm/TF config,
        # production credentials, providers, external backends or global writes.
        home = root / "home"
        home.mkdir()
        env = {k: v for k, v in os.environ.items() if k in ("PATH", "SYSTEMROOT", "LANG", "LC_ALL")}
        env.update(HOME=str(home), TMPDIR=str(root), CI="true", TF_IN_AUTOMATION="1",
                   CHECKPOINT_DISABLE="1", npm_config_cache=str(root / "npm-cache"),
                   npm_config_userconfig=str(root / "empty-npmrc"), npm_config_audit="false",
                   npm_config_fund="false", npm_config_update_notifier="false")
        yield root, env


def package_fixture():
    node, npm = tool("node"), tool("npm")
    with isolated("package") as (root, env):
        ws = root / "workspace"
        put(ws, "package.json", json.dumps({"name": "fixture-workspace", "private": True,
                                            "workspaces": ["packages/*"]}))
        metadata = {"name": "@fixture/math", "version": "1.0.0", "type": "module",
                    "exports": "./index.js", "files": ["index.js"]}
        put(ws, "packages/math/package.json", json.dumps(metadata))
        source = put(ws, "packages/math/index.js", "export const add=(a,b)=>a+b;\n")
        put(ws, "packages/client/package.json", json.dumps({"name": "@fixture/client", "version": "1.0.0",
                "type": "module", "dependencies": {"@fixture/math": "1.0.0"}}))
        probe = "import {add} from '@fixture/math'; if(add(2,3)!==5)process.exit(7); console.log('API_OK');"
        put(ws, "packages/client/probe.mjs", probe)
        command([npm, "install", "--offline", "--ignore-scripts", "--no-audit", "--no-fund"], ws, env=env)
        command([node, "probe.mjs"], ws / "packages/client", env=env)
        packed = json.loads(command([npm, "pack", "--json", "--ignore-scripts"], ws / "packages/math", env=env).stdout)[0]
        consumer = root / "consumer"
        put(consumer, "package.json", '{"name":"isolated-consumer","version":"1.0.0","private":true}')
        put(consumer, "probe.mjs", probe)
        archive = ws / "packages/math" / packed["filename"]
        command([npm, "install", "--offline", "--ignore-scripts", "--no-audit", "--no-fund", archive], consumer, env=env)
        require("API_OK" in command([node, "probe.mjs"], consumer, env=env).stdout,
                "packaged consumer did not execute the installed API")
        source.write_text("export const add=(a,b)=>a-b;\n")
        command([node, "probe.mjs"], ws / "packages/client", expected=(7,), env=env)
        # The installed artifact must be independent of its now-broken workspace.
        command([node, "probe.mjs"], consumer, env=env)
        (consumer / "node_modules/@fixture/math/index.js").write_text("export const add=()=>0;\n")
        command([node, "probe.mjs"], consumer, expected=(7,), env=env)
        return "workspace resolution; isolated packed consumer; two real API mutations rejected"


def migration_fixture():
    with isolated("migration") as (root, _env):
        with sqlite3.connect(root / "database.sqlite") as db:
            db.execute("PRAGMA foreign_keys=ON")
            db.execute("CREATE TABLE documents(id INTEGER PRIMARY KEY, title TEXT NOT NULL)")
            db.execute("INSERT INTO documents VALUES(1,'retained')")
            db.commit()
            with db:
                db.execute("ALTER TABLE documents ADD COLUMN storage_key TEXT")
                db.execute("UPDATE documents SET storage_key='external/1' WHERE id=1")
            require(db.execute("SELECT title,storage_key FROM documents").fetchone() == ("retained", "external/1"),
                    "expand migration lost data")
            try:
                with db:
                    db.execute("UPDATE documents SET title='must-rollback'")
                    db.execute("INSERT INTO documents(file_data) VALUES('retired-schema')")
            except sqlite3.OperationalError as error:
                require("file_data" in str(error), "wrong negative control")
            else:
                raise AssertionError("removed-column query unexpectedly succeeded")
            require(db.execute("SELECT title FROM documents").fetchone()[0] == "retained", "failed transaction did not roll back")
            try:
                with db:
                    db.execute("INSERT INTO documents(id,title) VALUES(2,NULL)")
            except sqlite3.IntegrityError:
                pass
            else:
                raise AssertionError("NOT NULL mutation accepted")
        return "real SQL schema expansion/data retention; retired column and invalid data rejected; rollback checked"


def infrastructure_fixture():
    terraform = tool("terraform", "KAVOSH_TERRAFORM")
    with isolated("infrastructure") as (root, env):
        config = '''terraform { required_version = "= 1.9.8" }
variable "environment" {
  type = string
  default = "fixture"
  validation {
    condition = var.environment == "fixture"
    error_message = "Only the disposable fixture environment is permitted."
  }
}
resource "terraform_data" "contract" { input = var.environment }
output "environment" { value = terraform_data.contract.output }
'''
        put(root, "main.tf", config)
        # No remote backend, provider installation or provisioner is configured.
        command([terraform, "init", "-backend=false", "-input=false", "-no-color"], root, env=env)
        command([terraform, "apply", "-auto-approve", "-input=false", "-no-color"], root, env=env)
        actual = json.loads(command([terraform, "output", "-json"], root, env=env).stdout)
        require(actual["environment"]["value"] == "fixture", "applied state did not match declared contract")
        command([terraform, "plan", "-detailed-exitcode", "-input=false", "-no-color"], root, env=env)
        # Changed desired state is a real nonempty Terraform plan, not a regex test.
        put(root, "main.tf", config.replace('input = var.environment', 'input = "changed"'))
        command([terraform, "plan", "-detailed-exitcode", "-input=false", "-no-color"], root, expected=(2,), env=env)
        put(root, "main.tf", config)
        command([terraform, "plan", "-input=false", "-no-color", "-var=environment=production"], root, expected=(1,), env=env)
        return "real local Terraform apply; no-change idempotence; drift and forbidden environment detected"


def browser_fixture():
    from playwright.sync_api import sync_playwright
    chrome = tool("google-chrome", "KAVOSH_CHROME", ("chromium", "chromium-browser"))
    with isolated("browser") as (root, env), sync_playwright() as engine:
        browser = engine.chromium.launch(executable_path=chrome, headless=True, env=env,
                    # Cold hosted-runner Chrome startup sometimes exceeds 20s even when the
                    # browser itself is healthy. Keep real executable, RTL, keyboard,
                    # injection and overflow checks mandatory; timeout remains a FAIL.
                    args=["--no-sandbox", "--disable-dev-shm-usage"], timeout=60000)
        try:
            page = browser.new_page(viewport={"width": 320, "height": 800})
            page.route("**/*", lambda route: route.abort())
            page.set_default_timeout(5000)
            html = """<!doctype html><html lang="fa" dir="rtl"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>body{margin:0}main{box-sizing:border-box;width:100%;padding:16px}button{min-width:44px;min-height:44px}</style>
<main><label for="name">نام</label><input id="name"><button id="save" type="button">ذخیره</button>
<output id="result" aria-live="polite"></output></main>
<script>(()=>{const input=document.getElementById('name'), result=document.getElementById('result');
document.getElementById('save').addEventListener('click',()=>{result.textContent=input.value;});})();</script></html>"""
            def verify(source):
                page.set_content(source)
                require(page.evaluate("getComputedStyle(document.documentElement).direction") == "rtl", "rtl")
                require(page.evaluate("document.documentElement.scrollWidth<=window.innerWidth"), "overflow")
                require(page.locator("#save").bounding_box()["height"] >= 44, "touch target")
                page.get_by_label("نام").fill("<b>untrusted</b>")
                page.keyboard.press("Tab")
                require(page.evaluate("document.activeElement.id") == "save", "keyboard focus")
                page.keyboard.press("Enter")
                require(page.locator("#result").text_content() == "<b>untrusted</b>" and
                        page.locator("#result > *").count() == 0, "text injection")
                require(page.locator("#result").get_attribute("aria-live") == "polite", "feedback")
            for width in (320, 1280):
                page.set_viewport_size({"width": width, "height": 800})
                verify(html)
            for source, error in ((html.replace("result.textContent=input.value", "result.innerHTML=input.value"), "text injection"),
                                  (html.replace("width:100%", "width:1600px"), "overflow")):
                page.set_viewport_size({"width": 320, "height": 800})
                try:
                    verify(source)
                except AssertionError as caught:
                    require(str(caught) == error, f"wrong browser counterexample: {caught}")
                else:
                    raise AssertionError(f"rendered mutation was not detected: {error}")
            return f"Chrome {browser.version}; real keyboard/RTL/responsive feedback; injection and overflow mutations rejected"
        finally:
            browser.close()


def desktop_fixture():
    with isolated("desktop") as (root, env):
        app = root / "app"
        source = put(app, "__main__.py", "import json\nfrom pathlib import Path\nprint(json.dumps({'version':'1.0.0','answer':42}))\n")
        artifact = root / "fixture.pyz"
        zipapp.create_archive(app, artifact, interpreter="/usr/bin/env python3")
        first = hashlib.sha256(artifact.read_bytes()).hexdigest()
        # Launch outside the source directory, then remove the source entirely.
        shutil.rmtree(app)
        result = json.loads(command([sys.executable, artifact], root, env=env).stdout)
        require(result == {"version": "1.0.0", "answer": 42}, "standalone artifact failed")
        require(hashlib.sha256(artifact.read_bytes()).hexdigest() == first, "execution mutated artifact")
        put(app, "__main__.py", "raise RuntimeError('seeded broken entry point')\n")
        broken = root / "broken.pyz"
        zipapp.create_archive(app, broken)
        bad = command([sys.executable, broken], root, expected=(1,), env=env)
        require("seeded broken entry point" in bad.stderr, "wrong desktop negative control")
        return "standalone desktop-distributable archive launches without source; broken entry point rejected (not GUI UAT)"


def wordpress_fixture():
    php = tool("php")
    wp = Path(os.environ.get("KAVOSH_WORDPRESS_ROOT", "")).resolve()
    require((wp / "wp-includes/plugin.php").is_file(), "missing pinned WordPress core; no CMS test stub is substituted")
    with isolated("wordpress") as (root, env):
        plugin = '''<?php
/* Plugin Name: Kavosh isolated conformance fixture
Version: 1.0.0
*/
function kavosh_fixture_render($value) {
    return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
}
add_filter('kavosh_fixture_render', 'kavosh_fixture_render', 10, 1);
'''
        put(root, "plugin.php", plugin)
        harness = '''<?php
require $argv[1] . '/wp-includes/plugin.php';
require __DIR__ . '/plugin.php';
$input = '<script>alert("x")</script>';
$wanted = htmlspecialchars($input, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');
if (has_filter('kavosh_fixture_render', 'kavosh_fixture_render') !== 10) { exit(11); }
if (apply_filters('kavosh_fixture_render', $input) !== $wanted) { exit(12); }
remove_filter('kavosh_fixture_render', 'kavosh_fixture_render', 10);
if (apply_filters('kavosh_fixture_render', $input) !== $input) { exit(13); }
echo "WORDPRESS_HOOK_OK\n";
'''
        put(root, "verify.php", harness)
        require("WORDPRESS_HOOK_OK" in command([php, "verify.php", wp], root, env=env).stdout,
                "real WordPress callback lifecycle failed")
        put(root, "plugin.php", plugin.replace("return htmlspecialchars($value, ENT_QUOTES | ENT_SUBSTITUTE, 'UTF-8');", "return $value;"))
        command([php, "verify.php", wp], root, expected=(12,), env=env)
        put(root, "plugin.php", plugin.replace("add_filter(", "// add_filter("))
        command([php, "verify.php", wp], root, expected=(11,), env=env)
        return "real WordPress hook engine: registration, escaped output, removal; unsafe output and missing registration rejected"


FIXTURES = dict(zip(PROFILES, (package_fixture, migration_fixture, infrastructure_fixture,
                            browser_fixture, desktop_fixture, wordpress_fixture)))


def capability_contract(profile):
    samples = {
        "package": {"projectKind": "library", "capabilities": ["package"]},
        "migration": {"stack": {"database": "sqlite"}, "capabilities": ["persistent-data", "migration"]},
        "infrastructure": {"capabilities": ["infrastructure"]},
        "browser-ui": {"ui": {"kind": "web"}, "capabilities": ["browser-ui"]},
        "desktop": {"runtime": "desktop", "deploy": {"method": "release-artifact"}, "capabilities": ["desktop", "release-artifact"]},
        "cms-wordpress": {"stack": {"frameworks": ["wordpress"]}, "capabilities": ["cms-wordpress"]},
    }
    manifest = samples[profile]
    require(not any(row[0] == "fail" for row in capability_profile_problems(manifest)), "valid profile rejected")
    for missing in manifest["capabilities"]:
        mutation = dict(manifest, capabilities=[c for c in manifest["capabilities"] if c != missing])
        require(any(row[0] == "fail" for row in capability_profile_problems(mutation)),
                f"missing {missing} capability was not detected")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--profiles", nargs="+", choices=PROFILES, default=list(PROFILES))
    parser.add_argument("--junit", type=Path, default=Path("cross-domain.xml"))
    args = parser.parse_args(argv)
    suite = ET.Element("testsuite", name="cross-domain", tests=str(len(args.profiles)), failures="0", errors="0", skipped="0")
    failures = 0
    for profile in args.profiles:
        start = time.monotonic()
        case = ET.SubElement(suite, "testcase", classname="capability", name=profile)
        try:
            capability_contract(profile)
            detail = FIXTURES[profile]()
            ET.SubElement(case, "system-out").text = detail
            print(f"PASS {profile}: {detail}", flush=True)
        except Exception as error:
            failures += 1
            ET.SubElement(case, "failure", message=str(error)).text = traceback.format_exc()
            print(f"FAIL {profile}: {error}", file=sys.stderr, flush=True)
        case.set("time", f"{time.monotonic()-start:.3f}")
    suite.set("failures", str(failures))
    raw = ET.tostring(suite, encoding="utf-8", xml_declaration=True)
    args.junit.parent.mkdir(parents=True, exist_ok=True)
    args.junit.write_bytes(raw)
    rows = assertion_outcomes(raw)
    require(len(rows) == len(args.profiles), "receipt adapter dropped a fixture result")
    require(sum(r["outcome"] == "pass" for r in rows) == len(args.profiles)-failures,
            "receipt adapter hid a fixture failure")
    return 1 if failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
