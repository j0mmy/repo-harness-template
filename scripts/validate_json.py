"""Validate JSON syntax for harness ledgers and any JSON under checked roots.

Generated runtime artifacts (.harness/runs/) and bytecode caches are skipped so
the gate stays deterministic from a fresh clone. Stdlib only.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_ROOTS = ("TASKS.json", "SPRINTS.json", "EVALUATOR.json", ".harness", "scripts", "src", "tests")
SKIP_PARTS = {".git", "__pycache__"}
SKIP_PREFIXES = (Path(".harness/runs"),)


def _skipped(path: Path) -> bool:
    if SKIP_PARTS.intersection(path.parts):
        return True
    return any(prefix in path.parents or path == prefix for prefix in SKIP_PREFIXES)


def iter_json_files(paths) -> list:
    files = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix == ".json" and not _skipped(path):
                files.append(path)
            continue
        files.extend(found for found in sorted(path.rglob("*.json")) if not _skipped(found))
    return sorted(set(files))


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    roots = [Path(arg) for arg in args] if args else [Path(root) for root in DEFAULT_ROOTS]
    failures = []

    files = iter_json_files(roots)
    for path in files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"{path}: line {exc.lineno} column {exc.colno}: {exc.msg}")

    if failures:
        print("Invalid JSON files:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print("fix: repair the listed JSON syntax errors or remove stale generated JSON from checked paths", file=sys.stderr)
        print("rerun: make validate-json", file=sys.stderr)
        return 1

    print(f"validated {len(files)} JSON files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
