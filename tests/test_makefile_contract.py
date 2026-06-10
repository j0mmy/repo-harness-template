"""Contract: the Makefile keeps exposing the canonical harness entrypoints
(initialize/check/test/validate and friends) wired to the real gates."""

from __future__ import annotations

import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _make_dry_run(target: str) -> str:
    result = subprocess.run(
        ["make", "--dry-run", target],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


class MakefileContractTest(unittest.TestCase):
    def test_make_check_wires_quality_gates(self):
        output = _make_dry_run("check")

        self.assertIn("format-check", output)
        self.assertIn("lint", output.lower())
        self.assertIn("typecheck", output.lower())
        self.assertIn("scripts/validate_json.py", output)
        self.assertIn("scripts/validate_tasks.py", output)
        self.assertIn("scripts/validate_sprints.py", output)
        self.assertIn("scripts/validate_evaluator.py", output)
        self.assertIn("scripts/validate_architecture.py", output)
        self.assertIn("unittest", output)

    def test_make_validate_runs_every_harness_validator(self):
        output = _make_dry_run("validate")

        for script in (
            "scripts/validate_json.py",
            "scripts/validate_tasks.py",
            "scripts/validate_sprints.py",
            "scripts/validate_evaluator.py",
            "scripts/validate_architecture.py",
        ):
            self.assertIn(script, output)

    def test_make_test_uses_stdlib_unittest(self):
        output = _make_dry_run("test")

        self.assertIn("unittest", output)
        self.assertNotIn("pytest", output)

    def test_make_initialize_is_callable_phase_zero(self):
        output = _make_dry_run("initialize")

        status_index = output.index("git status --short --branch")
        head_index = output.index("git --no-pager log -1 --decorate --oneline || true")
        self.assertLess(status_index, head_index)
        self.assertIn("check", output[head_index:], "initialize must run the canonical gate after reporting state")

    def test_make_init_aliases_initialize(self):
        output = _make_dry_run("init")

        self.assertIn("git status --short --branch", output)
        self.assertIn("git --no-pager log -1 --decorate --oneline || true", output)

    def test_make_e2e_target_exists(self):
        output = _make_dry_run("e2e")

        self.assertIn("unittest", output)
        self.assertIn("tests/e2e", output)


if __name__ == "__main__":
    unittest.main()
