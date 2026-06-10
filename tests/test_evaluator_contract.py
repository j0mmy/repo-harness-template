"""Contract: validate_evaluator.py keeps rubric semantics computable — weights
sum to 100, thresholds stay in the 1-5 scoring range, and the active rubric
pointer resolves."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_evaluator.py"


def _run_validator(path: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _rubric(**overrides):
    rubric = {
        "id": "synthetic_rubric",
        "title": "Synthetic rubric",
        "pass_threshold": 4.0,
        "dimensions": [
            {"id": "alpha", "weight": 60, "pass_threshold": 4, "criteria": ["alpha is satisfied"], "blockers": []},
            {"id": "beta", "weight": 40, "pass_threshold": 3, "criteria": ["beta is satisfied"], "blockers": []},
        ],
    }
    rubric.update(overrides)
    return rubric


class EvaluatorContractTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def _write(self, data) -> Path:
        path = self.tmp_path / "EVALUATOR.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        return path

    def test_evaluator_validator_accepts_canonical_rubrics(self):
        result = _run_validator(ROOT / "EVALUATOR.json")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("rubrics=", result.stdout)

    def test_evaluator_validator_rejects_weights_not_summing_to_100(self):
        rubric = _rubric()
        rubric["dimensions"][0]["weight"] = 50  # 50 + 40 = 90
        path = self._write({"schema_version": 1, "active_rubric": "synthetic_rubric", "rubrics": [rubric]})

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("weights sum to 90", result.stderr)
        self.assertIn("fix:", result.stderr)

    def test_evaluator_validator_rejects_threshold_outside_scoring_range(self):
        path = self._write(
            {"schema_version": 1, "active_rubric": "synthetic_rubric", "rubrics": [_rubric(pass_threshold=9)]}
        )

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("pass_threshold", result.stderr)

    def test_evaluator_validator_requires_active_rubric_to_resolve(self):
        path = self._write({"schema_version": 1, "active_rubric": "missing_rubric", "rubrics": [_rubric()]})

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("active_rubric", result.stderr)

    def test_evaluator_validator_rejects_empty_criteria(self):
        rubric = _rubric()
        rubric["dimensions"][1]["criteria"] = []
        path = self._write({"schema_version": 1, "active_rubric": "synthetic_rubric", "rubrics": [rubric]})

        result = _run_validator(path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("criteria", result.stderr)


if __name__ == "__main__":
    unittest.main()
