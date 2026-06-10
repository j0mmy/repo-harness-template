"""Contract: validate_tasks.py rejects completion claims that lack declared
verification commands, evidence, or required cross-component e2e verification."""

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


class TaskCompletionEvidenceTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def _write_ledger(self, ledger) -> Path:
        path = self.tmp_path / "TASKS.json"
        path.write_text(json.dumps(ledger), encoding="utf-8")
        return path

    def test_task_validator_accepts_canonical_task_ledger(self):
        result = _run_validator(ROOT / "TASKS.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("VCR", result.stdout)

    def test_task_validator_requires_verification_commands(self):
        path = self._write_ledger(
            {
                "schema_version": 1,
                "active_task": None,
                "vcr": 1.0,
                "tasks": [
                    {
                        "id": "F999",
                        "title": "Missing verification command",
                        "done_behavior": "The task cannot be completed without an explicit verification command.",
                        "state": "planned",
                        "verification": {"command": "", "status": "not_run", "evidence": ""},
                    }
                ],
            }
        )

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("verification.command", result.stderr)

    def test_task_validator_rejects_verified_task_without_evidence(self):
        path = self._write_ledger(
            {
                "schema_version": 1,
                "active_task": None,
                "vcr": 1.0,
                "tasks": [
                    {
                        "id": "F996",
                        "title": "Completed without evidence",
                        "done_behavior": "A verified task must carry evidence of the run that proved it.",
                        "state": "verified",
                        "verification": {
                            "command": "make check",
                            "status": "passing",
                            "evidence": "   ",
                            "last_run_at": "2026-06-10T00:00:00Z",
                            "signals": {"exit_code": 0},
                        },
                    }
                ],
            }
        )

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("verification.evidence", result.stderr)
        self.assertIn("fix:", result.stderr)

    def test_task_validator_requires_e2e_for_cross_component_tasks(self):
        path = self._write_ledger(
            {
                "schema_version": 1,
                "active_task": None,
                "vcr": 1.0,
                "tasks": [
                    {
                        "id": "F998",
                        "title": "Cross-component task without e2e",
                        "change_scope": "cross_component",
                        "components_touched": ["ui", "api"],
                        "boundaries_touched": ["ui_to_api"],
                        "e2e_required": True,
                        "done_behavior": "The UI calls the API and renders the saved result.",
                        "state": "planned",
                        "verification": {
                            "command": "python3 -m unittest -q tests.test_api && make check",
                            "status": "not_run",
                            "evidence": "",
                        },
                    }
                ],
            }
        )

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("e2e/full-pipeline", result.stderr)
        self.assertIn("fix:", result.stderr)

    def test_task_validator_requires_boundary_metadata_for_cross_component_tasks(self):
        path = self._write_ledger(
            {
                "schema_version": 1,
                "active_task": None,
                "vcr": 1.0,
                "tasks": [
                    {
                        "id": "F997",
                        "title": "Cross-component task without boundary metadata",
                        "change_scope": "cross_component",
                        "e2e_required": True,
                        "done_behavior": "The UI calls the API and renders the saved result.",
                        "state": "planned",
                        "verification": {
                            "command": "python3 -m unittest -q tests.e2e.test_ui_api && make check",
                            "status": "not_run",
                            "evidence": "",
                        },
                    }
                ],
            }
        )

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("components_touched", result.stderr)
        self.assertIn("boundaries_touched", result.stderr)


if __name__ == "__main__":
    unittest.main()
