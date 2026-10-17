"""No private consumer repository identity may be added to the public standard."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
# The public standard itself is the only permitted named Kavosh repository.
# Generic refs, placeholders, public technology brands and the core project name are allowed.
PRIVATE_PROJECT_LIKE = re.compile(r"\bkavosh(?!start)[a-z][a-z0-9_-]+\b", re.IGNORECASE)


class PublicRepositoryBoundary(unittest.TestCase):
    def test_public_tree_contains_no_named_consumer_project(self):
        paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        findings = []
        for rel in paths:
            if not rel:
                continue
            p = ROOT / rel
            if not p.is_file():
                continue
            if PRIVATE_PROJECT_LIKE.search(rel):
                findings.append(f"filename: {rel}")
            content = p.read_text(encoding="utf-8", errors="replace")
            if PRIVATE_PROJECT_LIKE.search(content):
                findings.append(f"content: {rel}")
        self.assertEqual(findings, [], "Public standard includes a consumer-specific name")


if __name__ == "__main__":
    unittest.main()
