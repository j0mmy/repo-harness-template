"""Validate SPRINTS.json: sprint shape, single-active-sprint, and cross-references.

When sibling TASKS.json / EVALUATOR.json files exist, task_ids and
evaluator_rubric_id are checked against them. Stdlib only.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

ALLOWED_SPRINT_STATES = {"planned", "active", "completed"}
RERUN_HINT = "make validate-sprints"


@dataclass(frozen=True)
class Failure:
    message: str
    hint: str


def _fail(message, hint):
    return Failure(message=message, hint=hint)


def _is_non_empty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_non_empty_string_list(value) -> bool:
    return isinstance(value, list) and bool(value) and all(_is_non_empty_string(item) for item in value)


def _sibling_ids(path, list_key):
    """Collect ids from a sibling ledger; None skips the cross-check when the ledger is absent or unreadable."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    items = data.get(list_key) if isinstance(data, dict) else None
    if not isinstance(items, list):
        return None
    return {item["id"] for item in items if isinstance(item, dict) and _is_non_empty_string(item.get("id"))}


def _validate_sprint(sprint, index, seen_ids, task_ids, rubric_ids):
    if not isinstance(sprint, dict):
        return [_fail(f"sprint[{index}] must be an object", "replace this sprint entry with a JSON object")]

    failures = []
    label = str(sprint.get("id") or f"sprint[{index}]")

    sprint_id = sprint.get("id")
    if not _is_non_empty_string(sprint_id):
        failures.append(_fail(f"{label}: id must be a non-empty string", "give the sprint a stable id like S001"))
    elif sprint_id in seen_ids:
        failures.append(_fail(f"{label}: id must be unique", "rename or remove the duplicate sprint id"))
    else:
        seen_ids.add(sprint_id)

    if not _is_non_empty_string(sprint.get("title")):
        failures.append(_fail(f"{label}: title must be a non-empty string", "add a concise sprint title"))

    if not _is_non_empty_string(sprint.get("goal")):
        failures.append(
            _fail(f"{label}: goal must be a non-empty string", "state the observable outcome this sprint must reach")
        )

    if sprint.get("state") not in ALLOWED_SPRINT_STATES:
        failures.append(
            _fail(
                f"{label}: state must be one of {sorted(ALLOWED_SPRINT_STATES)}",
                "use planned, active, or completed",
            )
        )

    task_ids_field = sprint.get("task_ids")
    if not _is_non_empty_string_list(task_ids_field):
        failures.append(
            _fail(
                f"{label}: task_ids must be a non-empty list of task ids",
                "list the TASKS.json ids that belong to this sprint",
            )
        )
    elif task_ids is not None:
        unknown = sorted(set(task_ids_field) - task_ids)
        if unknown:
            failures.append(
                _fail(
                    f"{label}: task_ids reference unknown tasks: {', '.join(unknown)}",
                    "add these tasks to TASKS.json or remove them from the sprint",
                )
            )

    if not _is_non_empty_string_list(sprint.get("required_gates")):
        failures.append(
            _fail(
                f"{label}: required_gates must be a non-empty list of commands",
                'declare the gates that must pass for this sprint, e.g. ["make check"]',
            )
        )

    rubric_id = sprint.get("evaluator_rubric_id")
    if not _is_non_empty_string(rubric_id):
        failures.append(
            _fail(
                f"{label}: evaluator_rubric_id must be a non-empty string",
                "reference a rubric id defined in EVALUATOR.json",
            )
        )
    elif rubric_ids is not None and rubric_id not in rubric_ids:
        failures.append(
            _fail(
                f"{label}: evaluator_rubric_id '{rubric_id}' is not defined in EVALUATOR.json",
                "add the rubric to EVALUATOR.json or reference an existing rubric id",
            )
        )

    observability = sprint.get("observability")
    if observability is not None and not isinstance(observability, dict):
        failures.append(
            _fail(
                f"{label}: observability must be an object when present",
                'use {"runtime_signal_required": true, "otel_semconv": "OBSERVABILITY.md"}',
            )
        )
    elif isinstance(observability, dict) and "runtime_signal_required" in observability:
        if not isinstance(observability["runtime_signal_required"], bool):
            failures.append(
                _fail(
                    f"{label}: observability.runtime_signal_required must be a boolean",
                    "set runtime_signal_required to true or false",
                )
            )

    return failures


def validate_contract(data, task_ids, rubric_ids):
    if not isinstance(data, dict):
        return [_fail("SPRINTS contract must be a JSON object", "replace SPRINTS.json with a JSON object")], ""

    failures = []
    if data.get("schema_version") != 1:
        failures.append(_fail("schema_version must be 1", "set schema_version to 1"))

    sprints = data.get("sprints")
    if not isinstance(sprints, list) or not sprints:
        failures.append(_fail("sprints must be a non-empty list", "add at least one sprint object to sprints"))
        return failures, ""

    seen_ids = set()
    for index, sprint in enumerate(sprints):
        failures.extend(_validate_sprint(sprint, index, seen_ids, task_ids, rubric_ids))

    valid_sprints = [sprint for sprint in sprints if isinstance(sprint, dict)]
    active_sprints = [sprint for sprint in valid_sprints if sprint.get("state") == "active"]
    if len(active_sprints) > 1:
        failures.append(
            _fail(
                "more than one sprint is active",
                "keep at most one sprint in state='active'; complete or re-plan the others",
            )
        )

    expected_active = active_sprints[0].get("id") if len(active_sprints) == 1 else None
    if data.get("active_sprint") != expected_active:
        failures.append(
            _fail(
                "active_sprint must equal the sole active sprint id, or null when no sprint is active",
                "set active_sprint to the one sprint in state='active', or null",
            )
        )

    summary = f"sprints={len(valid_sprints)} active={expected_active or 'none'}"
    return failures, summary


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    path = Path(args[0]) if args else Path("SPRINTS.json")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"{path}: sprint contract not found", file=sys.stderr)
        print("fix: create SPRINTS.json from the starter template", file=sys.stderr)
        print(f"rerun: {RERUN_HINT}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"{path}: line {exc.lineno} column {exc.colno}: {exc.msg}", file=sys.stderr)
        print("fix: repair the JSON syntax error", file=sys.stderr)
        print(f"rerun: {RERUN_HINT}", file=sys.stderr)
        return 1

    task_ids = _sibling_ids(path.parent / "TASKS.json", "tasks")
    rubric_ids = _sibling_ids(path.parent / "EVALUATOR.json", "rubrics")
    failures, summary = validate_contract(data, task_ids, rubric_ids)
    if failures:
        print("Invalid sprint contract:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure.message}", file=sys.stderr)
            print(f"    fix: {failure.hint}", file=sys.stderr)
            print(f"    rerun: {RERUN_HINT}", file=sys.stderr)
        return 1

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
