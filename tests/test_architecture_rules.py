"""Contract: validate_architecture.py turns boundary rules into executable
checks, rejects violations with agent-oriented errors, and fails loudly on
unsupported rule types."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_architecture.py"

FORBIDDEN_FS_RULE = {
    "id": "renderer_to_preload_file_ops",
    "type": "forbidden_import",
    "paths": ["src/renderer/**/*.ts"],
    "modules": ["fs", "node:fs"],
    "why": "Renderer code must not access filesystem APIs directly.",
    "fix": "Move filesystem code behind the preload bridge.",
    "rerun": "make validate-architecture && make e2e",
}


def _run_validator(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


class ArchitectureRulesTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp_path = Path(tmp.name)

    def _write_rules(self, rules) -> None:
        harness_dir = self.tmp_path / ".harness"
        harness_dir.mkdir(parents=True, exist_ok=True)
        (harness_dir / "architecture_rules.json").write_text(json.dumps({"rules": rules}), encoding="utf-8")

    def test_validator_passes_when_no_rules_manifest_exists(self):
        result = _run_validator(self.tmp_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("architecture validation passed", result.stdout)

    def test_validator_rejects_forbidden_import_with_agent_oriented_error(self):
        self._write_rules([FORBIDDEN_FS_RULE])
        renderer_dir = self.tmp_path / "src" / "renderer"
        renderer_dir.mkdir(parents=True)
        (renderer_dir / "export.ts").write_text("import fs from 'fs';\n", encoding="utf-8")

        result = _run_validator(self.tmp_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("renderer_to_preload_file_ops violation", result.stderr)
        self.assertIn("export.ts", result.stderr)
        self.assertIn("why:", result.stderr)
        self.assertIn("fix:", result.stderr)
        self.assertIn("rerun:", result.stderr)

    def test_validator_rejects_forbidden_python_import(self):
        self._write_rules(
            [
                {
                    "id": "stdlib_only",
                    "type": "forbidden_import",
                    "paths": ["pkg/**/*.py"],
                    "modules": ["pytest"],
                    "why": "Gates must run on stdlib only.",
                    "fix": "Use unittest.",
                    "rerun": "make validate-architecture",
                }
            ]
        )
        pkg = self.tmp_path / "pkg"
        pkg.mkdir(parents=True)
        (pkg / "conftest.py").write_text("import pytest\n", encoding="utf-8")

        result = _run_validator(self.tmp_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("stdlib_only violation", result.stderr)
        self.assertIn("pytest", result.stderr)

    def test_validator_accepts_compliant_code(self):
        self._write_rules([FORBIDDEN_FS_RULE])
        renderer_dir = self.tmp_path / "src" / "renderer"
        renderer_dir.mkdir(parents=True)
        (renderer_dir / "export.ts").write_text(
            "import { api } from './bridge';\nexport const run = () => api.exportFile();\n", encoding="utf-8"
        )

        result = _run_validator(self.tmp_path)

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("architecture validation passed", result.stdout)

    def test_validator_fails_loudly_on_unsupported_rule_type(self):
        self._write_rules([{"id": "exotic_rule", "type": "telepathy"}])

        result = _run_validator(self.tmp_path)

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("unsupported architecture rule type", result.stderr)
        self.assertIn("fix:", result.stderr)


if __name__ == "__main__":
    unittest.main()
