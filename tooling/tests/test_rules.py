"""Contract test (#7): every MUST in standard/RULES.md that claims a machine layer (P, M, G, H, O) must have at least
one positive and one negative offline test. Keeps RULES.md, documentation and code from drifting apart.

How a test declares coverage (either works):
  - its name:      test_<RULEID>_positive_… / test_<RULEID>_negative_…   (RULEID without hyphen, e.g. REL5, BR6)
  - its docstring: "Covers: AI-4, REL-6 (negative)"   — "(positive)"/"(negative)" or taken from the test name
A rule whose layer text says "via X-1, Y-2" is enforced through those rules and needs no own tests.
"""
import ast
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
RULES = ROOT / "standard" / "RULES.md"
MACHINE = {"P", "M", "G", "H", "O"}
ROW = re.compile(r"^\|\s*([A-Z]+-\d+)\s*\|(.*)\|\s*(MUST|SHOULD|MAY)\s*\|([^|]*)\|([^|]*)\|\s*$")
NAME = re.compile(r"^test_([A-Z]+)(\d+)_(positive|negative)")
COVERS = re.compile(r"Covers:\s*([^\n]+)")


def machine_musts():
    out = {}
    for line in RULES.read_text(encoding="utf-8").splitlines():
        m = ROW.match(line)
        if not m or m.group(3) != "MUST":
            continue
        layers = m.group(5)
        if "via" in layers:
            continue
        tokens = set(re.findall(r"(?<![A-Za-z])([A-Z])(?![A-Za-z-])", layers))
        if tokens & MACHINE:
            out[m.group(1)] = layers.strip()
    return out


def declared_coverage():
    cov = {}
    for f in sorted((ROOT / "tooling" / "tests").glob("test_*.py")):
        tree = ast.parse(f.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef) or not node.name.startswith("test_"):
                continue
            kind_from_name = "negative" if "_negative" in node.name else "positive" if "_positive" in node.name else None
            m = NAME.match(node.name)
            if m:
                cov.setdefault(f"{m.group(1)}-{m.group(2)}", set()).add(m.group(3))
            doc = ast.get_docstring(node) or ""
            for c in COVERS.findall(doc):
                line_kind = "negative" if c.rstrip().endswith("(negative)") else "positive" if c.rstrip().endswith("(positive)") else None
                for part in c.split(","):
                    rid = re.search(r"([A-Z]+-\d+)", part)
                    if not rid:
                        continue
                    kind = ("negative" if "(negative)" in part else "positive" if "(positive)" in part
                            else line_kind or kind_from_name)
                    if kind:
                        cov.setdefault(rid.group(1), set()).add(kind)
    return cov


class RulesContract(unittest.TestCase):
    def test_every_machine_enforced_must_has_positive_and_negative_tests(self):
        cov = declared_coverage()
        gaps = [f"{rid} [{layers}]: missing {', '.join(sorted({'positive', 'negative'} - cov.get(rid, set())))}"
                for rid, layers in sorted(machine_musts().items())
                if {"positive", "negative"} - cov.get(rid, set())]
        self.assertEqual(gaps, [], "machine-enforced MUSTs without tests:\n  " + "\n  ".join(gaps))

    def test_rules_table_parses(self):
        self.assertGreater(len(machine_musts()), 10)

    def test_contract_detects_an_untested_rule(self):
        import tempfile
        global RULES
        original = RULES
        with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
            f.write("| ZZ-1 | a rule nobody tests | MUST | All | P |\n| ZZ-2 | delegated | MUST | All | via ZZ-1 |\n")
        try:
            RULES = Path(f.name)
            musts = machine_musts()
            self.assertIn("ZZ-1", musts)
            self.assertNotIn("ZZ-2", musts)
            self.assertNotIn("ZZ-1", declared_coverage())
        finally:
            RULES = original
            Path(f.name).unlink()

    def test_layer_O_uses_repository_token_without_shared_secret(self):
        """Deliberately 'break' Layer O: without its secret the workflow fails red; if it stops running entirely,
        nothing automated notices — the standard must say so honestly (#7)."""
        wf = (ROOT / ".github" / "workflows" / "kavosh-portfolio.yml").read_text(encoding="utf-8")
        self.assertIn("GH_TOKEN: ${{ github.token }}", wf)
        self.assertNotIn("KAVOSH_PUBLIC_PORTFOLIO_TOKEN", wf)
        doc = (ROOT / "standard" / "01-free-plan-operating-model.md").read_text(encoding="utf-8")
        self.assertIn("فقط انسان متوجه می‌شود", doc)


if __name__ == "__main__":
    unittest.main()
