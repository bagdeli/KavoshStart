"""Regression tests for control-plane runtime portability (#94)."""
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class RuntimeDependencies(unittest.TestCase):
    def test_control_plane_does_not_require_github_cli(self):
        paths = [
            ROOT / "tooling/src/governance.py",
            ROOT / "tooling/src/main_guard.py",
            ROOT / "tooling/src/health.py",
            ROOT / "tooling/src/release_gate.py",
            ROOT / "tooling/src/rc_gate.py",
            ROOT / "tooling/templates/kavosh-governance.yml",
        ]
        forbidden = (
            'subprocess.run(["gh"',
            "subprocess.run(['gh'",
            '["gh", "api"]',
            "['gh', 'api']",
            "gh api ",
        )
        for path in paths:
            text = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, f"{path}: hidden GitHub CLI dependency {token!r}")


if __name__ == "__main__":
    unittest.main()
