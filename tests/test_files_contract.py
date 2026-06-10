"""Contract: every harness file the installer ships exists, and the manifest
covers the required harness surface while never touching .git or runtime artifacts."""

from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_HARNESS_FILES = {
    "AGENTS.md",
    "CLAUDE.md",
    "CONSTRAINTS.md",
    "DECISIONS.md",
    "PROGRESS.md",
    "QUALITY.md",
    "ARCHITECTURE.md",
    "OBSERVABILITY.md",
    "TASKS.json",
    "SPRINTS.json",
    "EVALUATOR.json",
    "Makefile",
    ".harness/otel_attributes.json",
    ".harness/architecture_rules.json",
    ".github/workflows/check.yml",
    "scripts/run_with_signals.py",
    "scripts/validate_json.py",
    "scripts/validate_tasks.py",
    "scripts/validate_sprints.py",
    "scripts/validate_evaluator.py",
    "scripts/validate_architecture.py",
    "scripts/install_harness.py",
}


def _load_installer_module():
    spec = importlib.util.spec_from_file_location("install_harness", ROOT / "scripts" / "install_harness.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FilesContractTest(unittest.TestCase):
    def test_required_harness_files_exist(self):
        missing = sorted(rel for rel in REQUIRED_HARNESS_FILES if not (ROOT / rel).is_file())
        self.assertEqual(missing, [], f"missing required harness files: {missing}")

    def test_template_repo_extras_exist(self):
        # README.md and docs/HARNESS_SPEC.md are template-repository extras, not
        # retrofit-installed harness files. In an installed target, docs/HARNESS_SPEC.md
        # is intentionally absent; skip this template-only assertion there so the
        # shipped test suite remains self-consistent after installation.
        spec = ROOT / "docs" / "HARNESS_SPEC.md"
        if not spec.exists():
            self.skipTest("template-only docs are not installed into retrofit targets")
        self.assertTrue((ROOT / "README.md").is_file(), "README.md must exist in the template repo")

    def test_runtime_artifacts_are_gitignored(self):
        # Either the root .gitignore or the installed .harness/.gitignore must
        # keep .harness/runs/ out of git (retrofitted repos rely on the latter).
        root_ignore = ROOT / ".gitignore"
        harness_ignore = ROOT / ".harness" / ".gitignore"
        covered = (root_ignore.is_file() and ".harness/runs/" in root_ignore.read_text(encoding="utf-8")) or (
            harness_ignore.is_file() and "runs/" in harness_ignore.read_text(encoding="utf-8")
        )
        self.assertTrue(covered, ".harness/runs/ must be gitignored by .gitignore or .harness/.gitignore")

    def test_installer_manifest_files_all_exist(self):
        module = _load_installer_module()
        missing = sorted(rel for rel in module.HARNESS_FILES if not (ROOT / rel).is_file())
        self.assertEqual(missing, [], f"installer manifest lists files missing from the template: {missing}")

    def test_installer_manifest_covers_required_harness_files(self):
        module = _load_installer_module()
        manifest = set(module.HARNESS_FILES)
        # Root .gitignore stays template-local; .harness/.gitignore ships instead.
        expected = (REQUIRED_HARNESS_FILES - {".gitignore"}) | {".harness/.gitignore"}
        not_shipped = sorted(expected - manifest)
        self.assertEqual(not_shipped, [], f"installer manifest must ship the harness contract: {not_shipped}")

    def test_installer_manifest_never_ships_git_runtime_or_template_docs(self):
        module = _load_installer_module()
        for rel in module.HARNESS_FILES:
            parts = Path(rel).parts
            self.assertNotIn(".git", parts, f"manifest must not touch .git: {rel}")
            self.assertFalse(rel.startswith(".harness/runs"), f"manifest must skip runtime artifacts: {rel}")
            self.assertFalse(rel.startswith("docs/"), f"template docs are not part of the harness contract: {rel}")
            self.assertNotEqual(rel, "README.md", "template README is not part of the harness contract")


if __name__ == "__main__":
    unittest.main()
