"""BR-4 parent metadata must be fetched from PR detail, not list response."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import governance as g

PARENT = [{"number": 44, "base": {"ref": "main"}, "head": {"ref": "feat/44-upgrade"}}]

def gh(mergeable=True, state="open", branch="feat/44-upgrade", base="main"):
    def fetch(op, path):
        assert op == "api" and path == "repos/o/r/pulls/44"
        return {"number": 44, "state": state, "head": {"ref": branch},
                "base": {"ref": base}, "mergeable": mergeable}
    return fetch

class StackedParent(unittest.TestCase):
    def test_list_entry_without_mergeable_uses_detail(self):
        self.assertTrue(g.immediately_mergeable_parent("o/r", PARENT, "feat/44-upgrade", "main", gh()))

    def test_missing_wrong_or_closed_parent_fails_closed(self):
        for opts in ({"mergeable": None}, {"mergeable": False}, {"state": "closed"},
                     {"branch": "feat/another"}, {"base": "develop"}):
            with self.subTest(options=opts):
                self.assertFalse(g.immediately_mergeable_parent("o/r", PARENT, "feat/44-upgrade", "main", gh(**opts)))

    def test_missing_or_ambiguous_list_fails_closed(self):
        self.assertFalse(g.immediately_mergeable_parent("o/r", [], "feat/44-upgrade", "main", gh()))
        self.assertFalse(g.immediately_mergeable_parent("o/r", PARENT + PARENT, "feat/44-upgrade", "main", gh()))
