"""Contract: the committed JSON ledgers parse, satisfy the minimal schema, and
pass their canonical validators."""

from __future__ import annotations

import json
import math
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_STATES = {"planned", "active", "blocked", "verified"}
VCR_ACTIVATED_STATES = {"active", "verified"}


def _load(name: str):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def _run_script(script: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


class TasksLedgerSchemaTest(unittest.TestCase):
    def test_task_ledger_minimal_schema_and_vcr(self):
        data = _load("TASKS.json")

        self.assertEqual(data["schema_version"], 1)
        self.assertIn("active_task", data)
        self.assertIsInstance(data["tasks"], list)
        self.assertTrue(data["tasks"])

        task_ids = set()
        for task in data["tasks"]:
            self.assertNotIn(task["id"], task_ids)
            task_ids.add(task["id"])
            self.assertTrue(task["title"].strip())
            self.assertTrue(task["done_behavior"].strip())
            self.assertIn(task["state"], ALLOWED_STATES)
            self.assertTrue(task["verification"]["command"].strip())
            if task["state"] == "verified":
                self.assertEqual(task["verification"]["status"], "passing")
                self.assertTrue(task["verification"]["evidence"].strip())

        active_tasks = [task for task in data["tasks"] if task["state"] == "active"]
        self.assertLessEqual(len(active_tasks), 1)
        expected_active = active_tasks[0]["id"] if active_tasks else None
        self.assertEqual(data["active_task"], expected_active)

        activated = [task for task in data["tasks"] if task["state"] in VCR_ACTIVATED_STATES]
        verified = [
            task
            for task in activated
            if task["state"] == "verified"
            and task["verification"]["status"] == "passing"
            and task["verification"].get("signals", {}).get("exit_code") == 0
        ]
        expected_vcr = len(verified) / len(activated) if activated else 1.0
        self.assertTrue(math.isclose(float(data["vcr"]), expected_vcr, abs_tol=5e-4))

    def test_sprint_contract_minimal_schema_and_cross_references(self):
        sprints = _load("SPRINTS.json")
        tasks = _load("TASKS.json")
        evaluator = _load("EVALUATOR.json")

        self.assertEqual(sprints["schema_version"], 1)
        self.assertTrue(sprints["sprints"])

        task_ids = {task["id"] for task in tasks["tasks"]}
        rubric_ids = {rubric["id"] for rubric in evaluator["rubrics"]}
        active = [sprint for sprint in sprints["sprints"] if sprint["state"] == "active"]
        self.assertLessEqual(len(active), 1)
        self.assertEqual(sprints["active_sprint"], active[0]["id"] if active else None)

        for sprint in sprints["sprints"]:
            self.assertTrue(sprint["goal"].strip())
            self.assertTrue(sprint["required_gates"])
            self.assertLessEqual(set(sprint["task_ids"]), task_ids)
            self.assertIn(sprint["evaluator_rubric_id"], rubric_ids)

    def test_evaluator_minimal_schema_weights_and_pointer(self):
        data = _load("EVALUATOR.json")

        self.assertEqual(data["schema_version"], 1)
        rubric_ids = {rubric["id"] for rubric in data["rubrics"]}
        self.assertIn(data["active_rubric"], rubric_ids)
        for rubric in data["rubrics"]:
            weights = sum(dimension["weight"] for dimension in rubric["dimensions"])
            self.assertTrue(math.isclose(weights, 100.0, abs_tol=1e-6), f"{rubric['id']}: weights sum to {weights}")
            for dimension in rubric["dimensions"]:
                self.assertTrue(dimension["criteria"])

    def test_canonical_validators_accept_committed_ledgers(self):
        for script, expect in (
            ("validate_json.py", "validated"),
            ("validate_tasks.py", "VCR="),
            ("validate_sprints.py", "sprints="),
            ("validate_evaluator.py", "rubrics="),
            ("validate_architecture.py", "architecture validation passed"),
        ):
            result = _run_script(script)
            self.assertEqual(result.returncode, 0, f"{script} failed:\n{result.stderr}")
            self.assertIn(expect, result.stdout)


if __name__ == "__main__":
    unittest.main()
