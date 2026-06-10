"""Contract: VCR counts active tasks only. Blocked/suspended tasks are excluded
from the denominator, never count as verified completions, and do not occupy
the single active lane."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_tasks.py"


def _run_validator(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _task(task_id: str, state: str, status=None, signals=None):
    verification = {
        "command": "python3 -m unittest -q tests.test_example",
        "status": status or ("passing" if state == "verified" else "not_run"),
        "evidence": "unittest returned exit code 0." if state == "verified" else "",
        "last_run_at": "2026-06-10T00:00:00Z" if state == "verified" else "",
    }
    if signals is not None:
        verification["signals"] = signals
    elif state == "verified":
        verification["signals"] = {"exit_code": 0}
    return {
        "id": task_id,
        "title": f"Synthetic {task_id}",
        "done_behavior": "Synthetic task for VCR semantics.",
        "state": state,
        "verification": verification,
    }


class BlockedVcrSemanticsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def _write_ledger(self, tasks, active_task, vcr) -> Path:
        path = self.tmp_path / "TASKS.json"
        path.write_text(
            json.dumps({"schema_version": 1, "active_task": active_task, "vcr": vcr, "tasks": tasks}),
            encoding="utf-8",
        )
        return path

    def test_blocked_tasks_are_suspended_records_excluded_from_vcr_and_active_lane(self):
        path = self._write_ledger(
            [
                _task("F001", "verified"),
                _task("F002", "blocked", status="blocked"),
                _task("F003", "active"),
            ],
            active_task="F003",
            vcr=0.5,
        )

        result = _run_validator(path)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("activated=2", result.stdout)
        self.assertIn("verified=1", result.stdout)
        self.assertIn("VCR=0.500", result.stdout)

    def test_blocked_task_does_not_count_as_verified_completion(self):
        # A blocked task that wrongly declares vcr as if it completed must fail.
        path = self._write_ledger(
            [
                _task("F001", "verified"),
                _task("F002", "blocked", status="blocked"),
            ],
            active_task=None,
            vcr=0.5,  # wrong: blocked is excluded, so activated=1 verified=1 -> 1.0
        )

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("vcr must equal verified/activated", result.stderr)

    def test_only_blocked_tasks_leave_vcr_at_one_and_no_active_lane(self):
        path = self._write_ledger([_task("F002", "blocked", status="blocked")], active_task=None, vcr=1.0)

        result = _run_validator(path)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("activated=0", result.stdout)
        self.assertIn("verified=0", result.stdout)
        self.assertIn("VCR=1.000", result.stdout)

    def test_two_active_tasks_are_rejected(self):
        path = self._write_ledger([_task("F001", "active"), _task("F002", "active")], active_task=None, vcr=0.0)

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertTrue(
            "more than one active task" in result.stderr or "cannot activate more than one" in result.stderr,
            result.stderr,
        )

    def test_validator_declares_the_vcr_denominator_states_explicitly(self):
        text = VALIDATOR.read_text(encoding="utf-8")

        self.assertIn("VCR_ACTIVATED_STATES", text)
        self.assertTrue('{"active", "verified"}' in text or "{'active', 'verified'}" in text)


if __name__ == "__main__":
    unittest.main()
