"""End-to-end: the installer, Makefile, and validators work together.

Installs the harness into a fresh directory with scripts/install_harness.py,
then runs `make validate` inside the installed copy. This crosses the real
component boundaries (installer -> installed tree -> make -> validators)
instead of testing each piece in isolation.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
INSTALLER = ROOT / "scripts" / "install_harness.py"


class HarnessPipelineE2ETest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.target = Path(tmp.name)

    def test_installed_harness_validates_end_to_end(self):
        install = subprocess.run(
            [sys.executable, str(INSTALLER), "--target", str(self.target)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(install.returncode, 0, install.stderr)

        parse = subprocess.run(
            ["make", "--dry-run", "check"],
            cwd=self.target,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(parse.returncode, 0, f"installed Makefile must parse:\n{parse.stderr}")

        validate = subprocess.run(
            ["make", "validate"],
            cwd=self.target,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(validate.returncode, 0, f"make validate failed in installed copy:\n{validate.stderr}")
        self.assertIn("VCR=", validate.stdout)
        self.assertIn("sprints=", validate.stdout)
        self.assertIn("rubrics=", validate.stdout)
        self.assertIn("architecture validation passed", validate.stdout)


if __name__ == "__main__":
    unittest.main()
