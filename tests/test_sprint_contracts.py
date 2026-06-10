"""Contract: validate_sprints.py enforces sprint shape, required gates,
single-active-sprint, and cross-references into TASKS.json/EVALUATOR.json."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_sprints.py"


def _run_validator(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _sprint(**overrides):
    sprint = {
        "id": "S900",
        "title": "Synthetic sprint",
        "state": "active",
        "goal": "Prove the sprint validator enforces the contract.",
        "task_ids": ["F900"],
        "required_gates": ["make check"],
        "evaluator_rubric_id": "default_harness_rubric",
        "observability": {"runtime_signal_required": True, "otel_semconv": "OBSERVABILITY.md"},
    }
    for key, value in overrides.items():
        if value is None:
            sprint.pop(key, None)
        else:
            sprint[key] = value
    return sprint


class SprintContractsTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def _write_contract(self, sprints, active_sprint="S900") -> Path:
        contract = {"schema_version": 1, "active_sprint": active_sprint, "sprints": sprints}
        path = self.tmp_path / "SPRINTS.json"
        path.write_text(json.dumps(contract), encoding="utf-8")
        return path

    def test_sprint_validator_accepts_canonical_sprint_contract(self):
        result = _run_validator(ROOT / "SPRINTS.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("sprints=", result.stdout)

    def test_sprint_validator_requires_required_gates(self):
        path = self._write_contract([_sprint(required_gates=None)])

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("required_gates", result.stderr)
        self.assertIn("fix:", result.stderr)
        self.assertIn("rerun:", result.stderr)

    def test_sprint_validator_rejects_task_ids_missing_from_task_ledger(self):
        tasks = {
            "schema_version": 1,
            "active_task": None,
            "vcr": 1.0,
            "tasks": [
                {
                    "id": "F900",
                    "title": "Synthetic task",
                    "state": "planned",
                    "done_behavior": "Synthetic behavior.",
                    "verification": {"command": "make check", "status": "not_run", "evidence": "", "last_run_at": None},
                }
            ],
        }
        (self.tmp_path / "TASKS.json").write_text(json.dumps(tasks), encoding="utf-8")
        path = self._write_contract([_sprint(task_ids=["F900", "F999"])])

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unknown tasks", result.stderr)
        self.assertIn("F999", result.stderr)

    def test_sprint_validator_enforces_single_active_sprint(self):
        path = self._write_contract([_sprint(), _sprint(id="S901", title="Second active sprint")])

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("more than one sprint is active", result.stderr)

    def test_sprint_validator_requires_active_sprint_pointer_to_match(self):
        path = self._write_contract([_sprint(state="completed")], active_sprint="S900")

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active_sprint", result.stderr)


if __name__ == "__main__":
    unittest.main()
