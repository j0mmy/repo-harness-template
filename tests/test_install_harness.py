"""Contract: install_harness.py copies the harness into a target repo,
refuses to overwrite differing files unless --force, supports --dry-run,
is idempotent, and never touches .git or runtime artifacts."""

from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSTALLER = ROOT / "scripts" / "install_harness.py"


def _run_installer(target: Path, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(INSTALLER), "--target", str(target), *flags],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


class InstallHarnessTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.target = Path(tmp.name)

    def test_install_into_empty_directory_creates_harness_files(self):
        result = _run_installer(self.target)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("create: AGENTS.md", result.stdout)
        for rel in (
            "AGENTS.md",
            "Makefile",
            "TASKS.json",
            ".harness/otel_attributes.json",
            ".harness/.gitignore",
            "scripts/validate_tasks.py",
            "tests/test_makefile_contract.py",
            ".github/workflows/check.yml",
        ):
            self.assertTrue((self.target / rel).is_file(), f"expected {rel} to be installed")

    def test_install_skips_git_and_runtime_artifacts(self):
        result = _run_installer(self.target)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((self.target / ".git").exists())
        self.assertFalse((self.target / ".harness" / "runs").exists())

    def test_reinstall_is_idempotent(self):
        first = _run_installer(self.target)
        second = _run_installer(self.target)

        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assertIn("created=0", second.stdout)
        self.assertIn("unchanged: AGENTS.md", second.stdout)
        self.assertNotIn("create: ", second.stdout)

    def test_refuses_to_overwrite_differing_file_and_writes_nothing(self):
        local = self.target / "TASKS.json"
        local.write_text('{"my": "ledger"}', encoding="utf-8")

        result = _run_installer(self.target)

        self.assertEqual(result.returncode, 1)
        self.assertIn("conflict: TASKS.json", result.stderr)
        self.assertIn("--force", result.stderr)
        # Fail-closed: the conflicting file is preserved and nothing else was written.
        self.assertEqual(local.read_text(encoding="utf-8"), '{"my": "ledger"}')
        self.assertEqual(sorted(p.name for p in self.target.iterdir()), ["TASKS.json"])

    def test_force_overwrites_differing_files(self):
        _run_installer(self.target)
        local = self.target / "TASKS.json"
        local.write_text('{"my": "ledger"}', encoding="utf-8")

        result = _run_installer(self.target, "--force")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("overwrite: TASKS.json", result.stdout)
        self.assertIn("overwritten=1", result.stdout)
        self.assertEqual(
            local.read_bytes(),
            (ROOT / "TASKS.json").read_bytes(),
            "--force must restore the template content",
        )

    def test_dry_run_plans_without_writing(self):
        result = _run_installer(self.target, "--dry-run")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("would create: AGENTS.md", result.stdout)
        self.assertIn("dry-run", result.stdout)
        self.assertEqual(list(self.target.iterdir()), [], "--dry-run must not write anything")

    def test_dry_run_still_reports_conflicts_with_failure_exit(self):
        (self.target / "Makefile").write_text("all:\n\ttrue\n", encoding="utf-8")

        result = _run_installer(self.target, "--dry-run")

        self.assertEqual(result.returncode, 1)
        self.assertIn("conflict: Makefile", result.stderr)
        self.assertEqual(sorted(p.name for p in self.target.iterdir()), ["Makefile"])

    def test_rejects_missing_target_directory(self):
        result = _run_installer(self.target / "does-not-exist")

        self.assertEqual(result.returncode, 2)
        self.assertIn("fix:", result.stderr)

    def test_rejects_installing_template_into_itself(self):
        result = _run_installer(ROOT)

        self.assertEqual(result.returncode, 2)
        self.assertIn("refusing to install the harness template into itself", result.stderr)


if __name__ == "__main__":
    unittest.main()
