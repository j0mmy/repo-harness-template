"""Install the agent harness into an existing repository.

Copies the harness contract files (docs, ledgers, validators, Makefile, tests,
CI workflow) from this template into a target repository:

    python3 scripts/install_harness.py --target /path/to/repo [--dry-run] [--force]

Behavior:
- Deterministic: an explicit sorted manifest is copied byte-for-byte; output
  lines are stable and sorted by path.
- Safe / fail-closed: existing files with different content are conflicts. If
  any conflict exists and --force is not passed, nothing is written and the
  conflicts are listed. Byte-identical files count as "unchanged", so rerunning
  the installer is idempotent.
- Skips .git and generated runtime artifacts (.harness/runs/) by construction:
  the manifest never includes them, and nothing in the target is ever deleted.
- Does not copy the template's own README.md, docs/, or root .gitignore; the
  installed .harness/.gitignore keeps .harness/runs/ out of the target's git.

Stdlib only.
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]

# Harness contract files, relative to the repo root. Never list .git, anything
# under .harness/runs/, or template-only docs (README.md, docs/) here.
HARNESS_FILES = (
    ".github/workflows/check.yml",
    ".harness/.gitignore",
    ".harness/architecture_rules.json",
    ".harness/otel_attributes.json",
    "AGENTS.md",
    "ARCHITECTURE.md",
    "CLAUDE.md",
    "CONSTRAINTS.md",
    "DECISIONS.md",
    "EVALUATOR.json",
    "Makefile",
    "OBSERVABILITY.md",
    "PROGRESS.md",
    "QUALITY.md",
    "SPRINTS.json",
    "TASKS.json",
    "scripts/install_harness.py",
    "scripts/run_with_signals.py",
    "scripts/validate_architecture.py",
    "scripts/validate_evaluator.py",
    "scripts/validate_json.py",
    "scripts/validate_sprints.py",
    "scripts/validate_tasks.py",
    "tests/e2e/__init__.py",
    "tests/e2e/test_harness_pipeline.py",
    "tests/test_architecture_rules.py",
    "tests/test_blocked_vcr_semantics.py",
    "tests/test_evaluator_contract.py",
    "tests/test_files_contract.py",
    "tests/test_harness_observability.py",
    "tests/test_install_harness.py",
    "tests/test_ledger_schemas.py",
    "tests/test_makefile_contract.py",
    "tests/test_quality_and_claude_contracts.py",
    "tests/test_sprint_contracts.py",
    "tests/test_task_completion_evidence.py",
    "tests/test_task_termination_signals.py",
)

CREATE, OVERWRITE, UNCHANGED, CONFLICT = "create", "overwrite", "unchanged", "conflict"


def plan_install(source_root: Path, target: Path, force: bool):
    """Return (plan, missing_sources): plan is a sorted list of (relpath, action)."""
    plan = []
    missing = []
    for rel in sorted(HARNESS_FILES):
        src = source_root / rel
        if not src.is_file():
            missing.append(rel)
            continue
        dst = target / rel
        if not dst.exists():
            plan.append((rel, CREATE))
        elif dst.is_file() and dst.read_bytes() == src.read_bytes():
            plan.append((rel, UNCHANGED))
        elif force:
            plan.append((rel, OVERWRITE))
        else:
            plan.append((rel, CONFLICT))
    return plan, missing


def apply_plan(source_root: Path, target: Path, plan) -> None:
    for rel, action in plan:
        if action in (CREATE, OVERWRITE):
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_root / rel, dst)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Install the agent harness files into a target repository.")
    parser.add_argument("--target", required=True, help="path to the repository to install the harness into")
    parser.add_argument("--force", action="store_true", help="overwrite existing files that differ from the template")
    parser.add_argument("--dry-run", action="store_true", help="print the plan without writing anything")
    args = parser.parse_args(argv)

    target = Path(args.target).resolve()
    if not target.is_dir():
        print(f"target is not an existing directory: {target}", file=sys.stderr)
        print("fix: create the target repository directory first (e.g. mkdir + git init), then reinstall", file=sys.stderr)
        print(f"rerun: python3 scripts/install_harness.py --target {target}", file=sys.stderr)
        return 2
    if target == SOURCE_ROOT:
        print("refusing to install the harness template into itself", file=sys.stderr)
        print("fix: pass --target pointing at the repository that should receive the harness", file=sys.stderr)
        print("rerun: python3 scripts/install_harness.py --target /path/to/other-repo", file=sys.stderr)
        return 2

    plan, missing = plan_install(SOURCE_ROOT, target, force=args.force)
    if missing:
        print("harness source files are missing from the template:", file=sys.stderr)
        for rel in missing:
            print(f"- {rel}", file=sys.stderr)
        print("fix: restore the listed files in the template checkout (or update HARNESS_FILES) before installing", file=sys.stderr)
        print(f"rerun: python3 scripts/install_harness.py --target {target}", file=sys.stderr)
        return 2

    conflicts = [rel for rel, action in plan if action == CONFLICT]
    if conflicts:
        print("refusing to overwrite existing files (no files were written):", file=sys.stderr)
        for rel in conflicts:
            print(f"- conflict: {rel} already exists with different content", file=sys.stderr)
        print("fix: move the conflicting files aside, or pass --force to overwrite them with the template versions", file=sys.stderr)
        print(f"rerun: python3 scripts/install_harness.py --target {target} --force", file=sys.stderr)
        return 1

    if not args.dry_run:
        apply_plan(SOURCE_ROOT, target, plan)

    prefix = "would " if args.dry_run else ""
    counts = {CREATE: 0, OVERWRITE: 0, UNCHANGED: 0}
    for rel, action in plan:
        counts[action] += 1
        label = action if action == UNCHANGED else f"{prefix}{action}"
        print(f"{label}: {rel}")
    print(
        f"{'dry-run: ' if args.dry_run else ''}install summary: "
        f"created={counts[CREATE]} overwritten={counts[OVERWRITE]} unchanged={counts[UNCHANGED]} target={target}"
    )
    if not args.dry_run and (counts[CREATE] or counts[OVERWRITE]):
        print("next: cd into the target repo and run `make initialize` to establish repo truth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
