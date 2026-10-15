"""One-time exact-source materialization, removed before checks/final commit.
Only creates verified unreferenced blobs; no refs, merges, tags or releases.
"""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

REPO = 'bagdeli/KavoshStart'
BASE = 'ba7319b17fbaa2b6eb92cdadde0fd07872f1c386'
TREE = '67a9427b6ba0fd26033f8fffdb6ebabe6c67e29b'
EXPECTED = {
 'tooling/build_workflows.py': '41fb66dee92ac0171fc4b14d4a4a9b57ddba2ee1',
 'tooling/templates/kavosh-release.yml': '0c6711b4781ee219bd6171090403a8c0f0f98f32',
 'tooling/tests/test_literal_workflows.py': '295fa9daa426ac977e2bcc3c6801e4fef1c6d75d',
 '.github/workflows/kavosh-release.yml': '9c21f702d9589bb0a6747f21563354d7e2ceffe8'}

def git(*args):
 return subprocess.check_output(['git', *args], text=True).strip()

def verify():
 for path, expected in EXPECTED.items():
  raw=Path(path).read_bytes()
  assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()==expected,path
 assert git('write-tree')==TREE

assert os.environ['GITHUB_REPOSITORY']==REPO
assert os.environ['GITHUB_REF']=='refs/heads/fix/125-literal-release-workflow'
assert os.environ['GITHUB_EVENT_NAME']=='push'
assert git('rev-parse','HEAD^')==BASE
if sys.argv[1]=='prepare':
 p=Path('tooling/templates/kavosh-release.yml');s=p.read_text()
 s=s.replace('          REQUIRED: ${{ inputs.required-checks }}\n','          REQUIRED: ${{ inputs.required-checks }}\n          DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}\n',1)
 s=s.replace('--branch "${{ github.event.repository.default_branch }}"','--branch "$DEFAULT_BRANCH"',1)
 p.write_text(s)
 p=Path('tooling/build_workflows.py');s=p.read_text()
 helper='''def validate_embedded_blocks(template: str, source: str) -> None:
    """Embedded Python stays a literal scalar; GitHub expressions belong in env.

    GitHub converts a scalar containing interpolation into a format expression.
    A large inlined source can exceed its expression parser limit before any job
    starts. This structural invariant prevents that without arbitrary truncation.
    """
    if "${{" in source:
        raise ValueError("embedded source contains GitHub interpolation; pass context through env")
    lines = template.splitlines()
    for index, line in enumerate(lines):
        match = re.match(r"^( +)run: [|>][-+]?[ \\t]*$", line)
        if not match:
            continue
        indent = len(match.group(1))
        block = []
        for child in lines[index + 1:]:
            if child.strip() and len(child) - len(child.lstrip()) <= indent and child != "__PYTHON__":
                break
            block.append(child)
        text = "\\n".join(block)
        if "__PYTHON__" in text and "${{" in text:
            raise ValueError("embedded run block contains GitHub interpolation; move context to step env")


'''
 s=s.replace('def build(template: str, source) -> str:\n',helper+'def build(template: str, source) -> str:\n')
 s=s.replace('    return tpl.replace("__PYTHON__", body)','    validate_embedded_blocks(tpl, code)\n    return tpl.replace("__PYTHON__", body)')
 p.write_text(s)
 tests='''"""Executable generator regression: large embedded scripts must remain literals."""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tooling"))
import build_workflows as builder


class LiteralEmbeddedWorkflows(unittest.TestCase):
    def test_positive_all_current_embedded_templates_build(self):
        for template, source in builder.PAIRS.items():
            with self.subTest(template=template):
                builder.build(template, source)

    def test_positive_context_in_env_not_in_script(self):
        template = """      - env:
          BRANCH: ${{ github.event.repository.default_branch }}
        run: |
          python3 - <<'PYTHON'
__PYTHON__
          PYTHON
          echo "$BRANCH"
"""
        builder.validate_embedded_blocks(template, "print('ok')\\n" * 3000)

    def test_negative_inline_context_in_large_release_script(self):
        template = (ROOT / "tooling/templates/kavosh-release.yml").read_text()
        old = template.replace('--branch "$DEFAULT_BRANCH"',
                               '--branch "${{ github.event.repository.default_branch }}"')
        self.assertNotEqual(old, template)
        with self.assertRaisesRegex(ValueError, "move context to step env"):
            builder.validate_embedded_blocks(old, "print('ok')\\n" * 3000)

    def test_negative_interpolation_introduced_in_python_source(self):
        with self.assertRaisesRegex(ValueError, "embedded source"):
            builder.validate_embedded_blocks("", 'print("${{ github.token }}")')

    def test_positive_separate_short_run_can_use_context(self):
        template = """      - run: |
          python3 - <<'PYTHON'
__PYTHON__
          PYTHON
      - run: echo '${{ github.sha }}'
"""
        builder.validate_embedded_blocks(template, "pass")

    def test_positive_release_branch_preserved_in_environment(self):
        template = (ROOT / "tooling/templates/kavosh-release.yml").read_text()
        self.assertIn('DEFAULT_BRANCH: ${{ github.event.repository.default_branch }}', template)
        self.assertIn('--branch "$DEFAULT_BRANCH"', template)
        self.assertNotIn('--branch "${{', template)


if __name__ == "__main__":
    unittest.main()
'''
 # Keep byte-for-byte local test source, whose multiline literals use single quotes.
 tests=tests.replace('template = """','template = '+"'"*3).replace('\n"""\n        builder','\n'+"'"*3+'\n        builder')
 Path('tooling/tests/test_literal_workflows.py').write_text(tests)
 subprocess.run(['python3','tooling/build_workflows.py'],check=True)
 subprocess.run(['git','rm','--','.literal-repair.py','.github/workflows/literal-repair.yml'],check=True)
 subprocess.run(['git','add','--',*EXPECTED],check=True)
 verify()
 print('EXACT_FINAL_TREE',TREE,flush=True)
elif sys.argv[1]=='publish':
 verify()
 for path, expected in EXPECTED.items():
  payload=json.dumps({'encoding':'base64','content':base64.b64encode(Path(path).read_bytes()).decode()}).encode()
  req=urllib.request.Request('https://api.github.com/repos/'+REPO+'/git/blobs',data=payload,method='POST',headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/vnd.github+json','Content-Type':'application/json','X-GitHub-Api-Version':'2022-11-28'})
  with urllib.request.urlopen(req,timeout=30) as resp:
   assert json.load(resp)['sha']==expected
  print('VERIFIED_BLOB',path,expected,flush=True)
else:
 raise SystemExit('invalid mode')
