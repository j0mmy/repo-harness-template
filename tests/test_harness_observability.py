"""Contract: run_with_signals.py records a runtime signal JSON with command,
exit code, duration, OpenTelemetry trace/span ids, and harness attributes, and
propagates the wrapped command's exit code."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "run_with_signals.py"


def _run_wrapper(cwd: Path, wrapped, task_id="F900", kind="verification") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(WRAPPER), "--task-id", task_id, "--kind", kind, "--", *wrapped],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _signal_files(cwd: Path, task_id="F900"):
    return sorted((cwd / ".harness" / "runs" / task_id).glob("*.json"))


class HarnessObservabilityTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def test_wrapper_records_runtime_signal_with_otel_attributes(self):
        result = _run_wrapper(self.tmp_path, [sys.executable, "-c", "print('ok')"])

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("runtime signal:", result.stdout)
        self.assertIn("exit_code=0", result.stdout)

        files = _signal_files(self.tmp_path)
        self.assertEqual(len(files), 1)
        signal = json.loads(files[0].read_text(encoding="utf-8"))

        self.assertEqual(signal["task_id"], "F900")
        self.assertEqual(signal["run_kind"], "verification")
        self.assertEqual(signal["exit_code"], 0)
        self.assertIsInstance(signal["exit_code"], int)
        self.assertNotIsInstance(signal["exit_code"], bool)
        self.assertIsInstance(signal["duration_ms"], int)
        self.assertTrue(signal["command"].strip())
        self.assertTrue(signal["argv"])
        self.assertTrue(signal["started_at"])
        self.assertTrue(signal["ended_at"])

        otel = signal["otel"]
        self.assertEqual(len(otel["trace_id"]), 32)
        self.assertEqual(len(otel["span_id"]), 16)
        int(otel["trace_id"], 16)
        int(otel["span_id"], 16)
        self.assertEqual(otel["status_code"], "OK")

        attributes = signal["attributes"]
        self.assertEqual(attributes["harness.task.id"], "F900")
        self.assertEqual(attributes["harness.run.kind"], "verification")
        self.assertEqual(attributes["process.exit_code"], 0)
        self.assertEqual(attributes["test.status"], "passed")

    def test_wrapper_propagates_failure_exit_code_and_prints_repair_hints(self):
        result = _run_wrapper(self.tmp_path, [sys.executable, "-c", "raise SystemExit(3)"])

        self.assertEqual(result.returncode, 3)
        self.assertIn("exit_code=3", result.stdout)
        self.assertIn("fix:", result.stderr)
        self.assertIn("rerun:", result.stderr)

        files = _signal_files(self.tmp_path)
        self.assertEqual(len(files), 1)
        signal = json.loads(files[0].read_text(encoding="utf-8"))
        self.assertEqual(signal["exit_code"], 3)
        self.assertEqual(signal["otel"]["status_code"], "ERROR")
        self.assertEqual(signal["attributes"]["test.status"], "failed")

    def test_wrapper_reports_missing_wrapped_command(self):
        result = _run_wrapper(self.tmp_path, ["definitely-not-a-real-command-xyz"])

        self.assertEqual(result.returncode, 127)
        self.assertIn("fix:", result.stderr)
        self.assertIn("rerun:", result.stderr)


if __name__ == "__main__":
    unittest.main()
