"""Turn architecture-boundary rules into executable checks with agent-oriented errors.

Rules live in .harness/architecture_rules.json. The starter supports
`forbidden_import` rules; unknown rule types fail loudly so they cannot be
silently ignored. When no manifest exists the validator passes, keeping the
gate usable before any boundaries are defined. Stdlib only.
"""

from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path

RULES_FILE = Path(".harness/architecture_rules.json")
DEFAULT_RERUN = "make validate-architecture"


@dataclass(frozen=True)
class Failure:
    rule_id: str
    path: Path
    message: str
    why: str
    fix: str
    rerun: str = DEFAULT_RERUN


def _load_rules(path=RULES_FILE):
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError(".harness/architecture_rules.json field `rules` must be a list")
    return [rule for rule in rules if isinstance(rule, dict)]


def _iter_rule_files(patterns):
    files = set()
    for pattern in patterns:
        files.update(Path().glob(pattern))
    return sorted(path for path in files if path.is_file())


def _python_imports(source):
    imports = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _text_imports(source):
    imports = set(re.findall(r"from\s+['\"]([^'\"]+)['\"]", source))
    imports.update(re.findall(r"import\s+[^'\"]*['\"]([^'\"]+)['\"]", source))
    imports.update(re.findall(r"require\(['\"]([^'\"]+)['\"]\)", source))
    return imports


def _imports_for(path):
    source = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".py":
        return _python_imports(source)
    return _text_imports(source)


def _check_forbidden_import(rule):
    rule_id = str(rule.get("id") or "unnamed_rule")
    patterns = [str(item) for item in rule.get("paths", [])]
    forbidden = {str(item) for item in rule.get("modules", [])}
    why = str(rule.get("why") or "This dependency violates an architectural boundary.")
    fix = str(rule.get("fix") or "Move the dependency behind the approved boundary/interface.")
    rerun = str(rule.get("rerun") or DEFAULT_RERUN)

    failures = []
    for path in _iter_rule_files(patterns):
        imports = _imports_for(path)
        bad = sorted(module for module in forbidden if module in imports)
        for module in bad:
            failures.append(
                Failure(
                    rule_id=rule_id,
                    path=path,
                    message=f"{rule_id} violation: {path} imports `{module}`",
                    why=why,
                    fix=fix,
                    rerun=rerun,
                )
            )
    return failures


def validate(rules):
    failures = []
    for rule in rules:
        rule_type = rule.get("type")
        if rule_type == "forbidden_import":
            failures.extend(_check_forbidden_import(rule))
        else:
            failures.append(
                Failure(
                    rule_id=str(rule.get("id") or "unnamed_rule"),
                    path=RULES_FILE,
                    message=f"unsupported architecture rule type: {rule_type}",
                    why="Unknown rule types are ignored by agents unless the validator fails loudly.",
                    fix="Implement this rule type in scripts/validate_architecture.py or remove it from the manifest.",
                    rerun=DEFAULT_RERUN,
                )
            )
    return failures


def main():
    try:
        failures = validate(_load_rules())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Invalid architecture rules: {exc}", file=sys.stderr)
        print("fix: repair .harness/architecture_rules.json or remove invalid rules", file=sys.stderr)
        print(f"rerun: {DEFAULT_RERUN}", file=sys.stderr)
        return 1

    if failures:
        print("Architecture validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure.message}", file=sys.stderr)
            print(f"    why: {failure.why}", file=sys.stderr)
            print(f"    fix: {failure.fix}", file=sys.stderr)
            print(f"    rerun: {failure.rerun}", file=sys.stderr)
        return 1

    print("architecture validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
