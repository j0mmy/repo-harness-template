"""Contract: the three-layer termination validation holds — a verified task
needs passing status, evidence with an ISO-8601 timestamp, and a runtime
signal with integer exit_code == 0."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_FILE = ROOT / "TASKS.json"
VALIDATOR = ROOT / "scripts" / "validate_tasks.py"


def _run_validator(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _verified_task(**verification_overrides):
    verification = {
        "command": "python3 -m unittest -q tests.test_example",
        "status": "passing",
        "evidence": "unittest returned exit code 0 with the critical path exercised.",
        "last_run_at": "2026-06-09T19:55:15Z",
        "signals": {"exit_code": 0},
    }
    for key, value in verification_overrides.items():
        if value is None:
            verification.pop(key, None)
        else:
            verification[key] = value
    return {
        "id": "F999",
        "title": "Synthetic verified task",
        "done_behavior": "The synthetic task records runtime termination evidence.",
        "state": "verified",
        "verification": verification,
    }


class TaskTerminationSignalsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def _write_ledger(self, task, active_task=None) -> Path:
        activated = [task] if task["state"] in {"active", "verified"} else []
        verified = [
            entry
            for entry in activated
            if entry["state"] == "verified"
            and entry["verification"].get("status") == "passing"
            and isinstance(entry["verification"].get("signals"), dict)
            and entry["verification"].get("signals", {}).get("exit_code") == 0
        ]
        ledger = {
            "schema_version": 1,
            "active_task": active_task,
            "vcr": len(verified) / len(activated) if activated else 1.0,
            "tasks": [task],
        }
        path = self.tmp_path / "TASKS.json"
        path.write_text(json.dumps(ledger), encoding="utf-8")
        return path

    def test_task_ledger_records_runtime_signals_for_verified_tasks(self):
        data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))

        for task in data["tasks"]:
            if task["state"] != "verified":
                continue
            signals = task["verification"].get("signals")
            self.assertIsInstance(signals, dict, task["id"])
            self.assertEqual(signals.get("exit_code"), 0, task["id"])

    def test_verified_task_requires_runtime_signals(self):
        path = self._write_ledger(_verified_task(signals=None))

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("verification.signals", result.stderr)
        self.assertIn("runtime", result.stderr)

    def test_verified_task_rejects_nonzero_exit_code_as_premature_victory(self):
        path = self._write_ledger(_verified_task(signals={"exit_code": 1}))

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("premature victory", result.stderr)
        self.assertIn("exit_code=1", result.stderr)

    def test_verified_task_rejects_boolean_exit_code(self):
        path = self._write_ledger(_verified_task(signals={"exit_code": True}))

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("signals.exit_code must be an integer", result.stderr)

    def test_verified_task_rejects_string_exit_code(self):
        path = self._write_ledger(_verified_task(signals={"exit_code": "0"}))

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("signals.exit_code must be an integer", result.stderr)

    def test_verified_task_requires_iso8601_last_run_at(self):
        path = self._write_ledger(_verified_task(last_run_at="yesterday"))

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("last_run_at", result.stderr)
        self.assertIn("ISO-8601", result.stderr)

    def test_validator_prints_actionable_repair_hint_for_each_failure(self):
        path = self._write_ledger(_verified_task(signals={"exit_code": 1}, last_run_at="yesterday"))

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        lines = result.stderr.splitlines()
        failure_indexes = [index for index, line in enumerate(lines) if line.startswith("- ")]
        self.assertTrue(failure_indexes)
        for index in failure_indexes:
            self.assertLess(index + 1, len(lines))
            self.assertTrue(lines[index + 1].startswith("    fix: "), lines[index + 1])


if __name__ == "__main__":
    unittest.main()
