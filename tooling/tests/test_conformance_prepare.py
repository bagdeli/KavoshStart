"""Keep the pinned Terraform version probe immune to early pipe closure."""

import re
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREPARE = ROOT / "tooling" / "prepare_conformance.sh"


class ConformanceDependencyPreparation(unittest.TestCase):
    def test_terraform_version_probe_consumes_full_producer(self):
        source = PREPARE.read_text(encoding="utf-8")
        self.assertNotIn("./terraform version | head -1", source)
        match = re.search(
            r"^printf 'Terraform: '; ./terraform version \| sed -n '1p'$",
            source, re.M,
        )
        self.assertIsNotNone(match, "show the first version line without early-close SIGPIPE")
        with tempfile.TemporaryDirectory() as d:
            terraform = Path(d) / "terraform"
            terraform.write_text(
                "#!/usr/bin/env python3\n"
                "print('Terraform v1.9.8')\n"
                "for i in range(12000):\n"
                "    print(f'non-version detail {i}')\n",
                encoding="utf-8",
            )
            terraform.chmod(0o755)
            command = "set -euo pipefail\n" + match.group(0) + "\nprintf 'completed\\n'\n"
            result = subprocess.run(
                ["bash", "-c", command], cwd=d, capture_output=True, text=True,
                timeout=20, check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "Terraform: Terraform v1.9.8\ncompleted\n")


if __name__ == "__main__":
    unittest.main()
