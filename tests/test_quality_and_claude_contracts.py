"""Contract: knowledge placement stays correct — QUALITY.md is a first-class
register, CLAUDE.md stays a thin router, and Phase 0 lives in AGENTS.md."""

from __future__ import annotations

import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


class QualityAndClaudeContractsTest(unittest.TestCase):
    def test_quality_register_is_first_class_and_linked_from_harness_router_and_cockpit(self):
        quality = _read("QUALITY.md")
        agents = _read("AGENTS.md")
        progress = _read("PROGRESS.md")

        self.assertIn("# Quality Register", quality)
        self.assertIn("## Quality Dimensions", quality)
        self.assertIn("## Module Scores", quality)
        self.assertIn("## Repair Queue", quality)

        for required in (
            "Verification passing state",
            "Agent understandability",
            "Test stability",
            "Architecture-boundary compliance",
            "Code-convention compliance",
            "Known cleanup or repair action",
        ):
            self.assertIn(required, quality)

        self.assertIn("QUALITY.md", agents)
        self.assertIn("QUALITY.md", progress)

    def test_claude_md_is_a_thin_router_to_agents_md(self):
        claude = _read("CLAUDE.md")

        self.assertIn("AGENTS.md", claude)
        self.assertIn("canonical", claude.lower())
        self.assertLessEqual(len([line for line in claude.splitlines() if line.strip()]), 30)
        self.assertNotIn("## Work rules", claude)
        self.assertNotIn("## Session lifecycle", claude)
        self.assertNotIn("## Source-of-truth map", claude)

    def test_phase_zero_details_are_centralized_in_agents_not_progress(self):
        agents = _read("AGENTS.md")
        progress = _read("PROGRESS.md")

        self.assertIn("### Phase 0", agents)
        self.assertIn("make initialize", agents)
        self.assertNotIn("## Phase 0", progress)
        self.assertIn("AGENTS.md", progress)
        self.assertIn("make initialize", progress)
        self.assertIn("git status --short", progress)

    def test_session_exit_uses_repo_canonical_gate_without_npm_as_canonical(self):
        agents = _read("AGENTS.md")
        session_exit = agents.split("## Session Exit Checklist", maxsplit=1)[1].split("### Cleanup modes", maxsplit=1)[0]

        self.assertIn("make check", session_exit)
        self.assertNotIn("npm " + "run", session_exit)
        self.assertNotIn("npm " + "test", session_exit)


if __name__ == "__main__":
    unittest.main()
