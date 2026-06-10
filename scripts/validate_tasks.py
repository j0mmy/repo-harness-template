"""Validate TASKS.json: task shape, single-active-lane, VCR, and termination evidence.

This validator prevents premature victory: a task counts as verified only when
it clears three termination layers (structural status, evidence + ISO-8601
timestamp, and runtime signal exit_code == 0). VCR counts active tasks only:

    VCR = verified / (active + verified)

`planned` and `blocked` tasks are excluded from the denominator, so suspended
work never inflates or deflates the completion rate. Stdlib only.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

ALLOWED_STATES = {"planned", "active", "blocked", "verified"}
VCR_ACTIVATED_STATES = {"active", "verified"}
ALLOWED_VERIFICATION_STATUSES = {"not_run", "passing", "failing", "blocked"}
ALLOWED_CHANGE_SCOPES = {"single_component", "cross_component", "architecture_rule", "docs_only"}
VERIFIED_STATE = "verified"
GENERIC_FIX_HINT = "update this field to match the TASKS.json completion-evidence schema"


@dataclass(frozen=True)
class Failure:
    message: str
    hint: str = GENERIC_FIX_HINT


def _fail(message, hint=GENERIC_FIX_HINT):
    return Failure(message=message, hint=hint)


def _task_label(task, index):
    return str(task.get("id") or f"task[{index}]")


def _has_zero_exit_signal(verification) -> bool:
    if not isinstance(verification, dict):
        return False
    signals = verification.get("signals")
    if not isinstance(signals, dict):
        return False
    exit_code = signals.get("exit_code")
    return isinstance(exit_code, int) and not isinstance(exit_code, bool) and exit_code == 0


def _is_verified(task) -> bool:
    verification = task.get("verification", {})
    return (
        task.get("state") == VERIFIED_STATE
        and isinstance(verification, dict)
        and verification.get("status") == "passing"
        and _has_zero_exit_signal(verification)
    )


def _is_iso8601(value) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return True


def _is_non_empty_string_list(value) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _command_mentions_e2e(command) -> bool:
    markers = ("e2e", "end-to-end", "full-pipeline", "full_pipeline")
    return any(marker in command for marker in markers)


def _task_requires_e2e(task) -> bool:
    return task.get("change_scope") == "cross_component" or task.get("e2e_required") is True


def _validate_termination(task, label):
    if task.get("state") != VERIFIED_STATE:
        return []

    failures = []
    verification = task.get("verification")
    if not isinstance(verification, dict):
        return failures

    if verification.get("status") != "passing":
        failures.append(
            _fail(
                f"{label}: verified tasks must have verification.status='passing'",
                "only set state='verified' after the declared verification command exits 0; otherwise keep the task active or blocked",
            )
        )

    evidence = verification.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        failures.append(
            _fail(
                f"{label}: verified tasks must include verification.evidence",
                "record the command output, test counts, and critical runtime path that proved done_behavior",
            )
        )

    if not _is_iso8601(verification.get("last_run_at")):
        failures.append(
            _fail(
                f"{label}: verified tasks must record verification.last_run_at as ISO-8601",
                "set last_run_at to the timestamp when the verification command actually ran",
            )
        )

    signals = verification.get("signals")
    if not isinstance(signals, dict):
        failures.append(
            _fail(
                f"{label}: verified tasks must include verification.signals (runtime exit signal)",
                'add "signals": {"exit_code": 0} captured from the actual verification command run',
            )
        )
        return failures

    exit_code = signals.get("exit_code")
    if isinstance(exit_code, bool) or not isinstance(exit_code, int):
        failures.append(
            _fail(
                f"{label}: verification.signals.exit_code must be an integer",
                "record the integer process exit code from the declared verification command",
            )
        )
    elif exit_code != 0:
        failures.append(
            _fail(
                f"{label}: premature victory — verified task has non-zero signals.exit_code={exit_code}",
                "do not mark the task verified until the declared verification command exits 0; keep it active and fix the failure",
            )
        )

    return failures


def _validate_task(task, index, seen_ids):
    failures = []
    if not isinstance(task, dict):
        return [_fail(f"task[{index}] must be an object", "replace this task entry with a JSON object")]

    label = _task_label(task, index)
    task_id = task.get("id")
    if not isinstance(task_id, str) or not task_id.strip():
        failures.append(_fail(f"{label}: id must be a non-empty string", "give the task a stable id like F001"))
    elif task_id in seen_ids:
        failures.append(_fail(f"{label}: id must be unique", "rename or remove the duplicate task id"))
    else:
        seen_ids.add(task_id)

    title = task.get("title")
    if not isinstance(title, str) or not title.strip():
        failures.append(_fail(f"{label}: title must be a non-empty string", "add a concise human-readable title"))

    done_behavior = task.get("done_behavior")
    if not isinstance(done_behavior, str) or not done_behavior.strip():
        failures.append(
            _fail(
                f"{label}: done_behavior must be a non-empty string",
                "describe the observable behavior that proves the task is done",
            )
        )

    state = task.get("state")
    if state not in ALLOWED_STATES:
        failures.append(
            _fail(
                f"{label}: state must be one of {sorted(ALLOWED_STATES)}",
                "use planned, active, blocked, or verified",
            )
        )

    change_scope = task.get("change_scope", "single_component")
    if change_scope not in ALLOWED_CHANGE_SCOPES:
        failures.append(
            _fail(
                f"{label}: change_scope must be one of {sorted(ALLOWED_CHANGE_SCOPES)}",
                "set change_scope to single_component, cross_component, architecture_rule, or docs_only",
            )
        )

    if "e2e_required" in task and not isinstance(task.get("e2e_required"), bool):
        failures.append(
            _fail(
                f"{label}: e2e_required must be a boolean when present",
                "set e2e_required to true for cross-component tasks or remove the field",
            )
        )

    if _task_requires_e2e(task):
        if not _is_non_empty_string_list(task.get("components_touched")):
            failures.append(
                _fail(
                    f"{label}: cross-component tasks must list components_touched",
                    "add components_touched with the concrete components/services/processes this task crosses",
                )
            )
        if not _is_non_empty_string_list(task.get("boundaries_touched")):
            failures.append(
                _fail(
                    f"{label}: cross-component tasks must list boundaries_touched",
                    "define the architectural boundary in ARCHITECTURE.md and reference its id in boundaries_touched",
                )
            )

    verification = task.get("verification")
    if not isinstance(verification, dict):
        failures.append(
            _fail(
                f"{label}: verification must be an object",
                "add verification.command/status/evidence/last_run_at and runtime signals when verified",
            )
        )
        return failures

    command = verification.get("command")
    if not isinstance(command, str) or not command.strip():
        failures.append(
            _fail(
                f"{label}: verification.command must be a non-empty string",
                "declare the exact command that proves done_behavior",
            )
        )
    elif _task_requires_e2e(task) and not _command_mentions_e2e(command):
        failures.append(
            _fail(
                f"{label}: cross-component tasks must include e2e/full-pipeline verification in verification.command",
                "append the relevant e2e command, e.g. `&& make e2e`, `tests/e2e/test_flow.py`, or `make full-pipeline`",
            )
        )

    status = verification.get("status")
    if status not in ALLOWED_VERIFICATION_STATUSES:
        failures.append(
            _fail(
                f"{label}: verification.status must be one of {sorted(ALLOWED_VERIFICATION_STATUSES)}",
                "use not_run, passing, failing, or blocked",
            )
        )

    failures.extend(_validate_termination(task, label))
    return failures


def validate_ledger(data):
    failures = []
    if not isinstance(data, dict):
        return [_fail("TASKS ledger must be a JSON object", "replace TASKS.json with a JSON object")], ""

    if data.get("schema_version") != 1:
        failures.append(_fail("schema_version must be 1", "set schema_version to 1"))

    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        failures.append(_fail("tasks must be a non-empty list", "add at least one task object to tasks"))
        return failures, ""

    seen_ids = set()
    for index, task in enumerate(tasks):
        failures.extend(_validate_task(task, index, seen_ids))

    valid_task_dicts = [task for task in tasks if isinstance(task, dict)]
    active_tasks = [task for task in valid_task_dicts if task.get("state") == "active"]
    active_task = data.get("active_task")
    expected_active = active_tasks[0].get("id") if len(active_tasks) == 1 else None
    if len(active_tasks) > 1:
        failures.append(
            _fail(
                "cannot have more than one active task",
                "finish, block, or revert the current active task before activating another one",
            )
        )
    if active_task != expected_active:
        failures.append(
            _fail(
                "active_task must equal the sole active task id, or null when no task is active",
                "set active_task to the one active task id, or null if no task state is active",
            )
        )

    activated = [task for task in valid_task_dicts if task.get("state") in VCR_ACTIVATED_STATES]
    verified = [task for task in activated if _is_verified(task)]
    computed_vcr = len(verified) / len(activated) if activated else 1.0

    declared_vcr = data.get("vcr")
    if (
        isinstance(declared_vcr, bool)
        or not isinstance(declared_vcr, (int, float))
        or not math.isclose(float(declared_vcr), computed_vcr, abs_tol=5e-4)
    ):
        failures.append(
            _fail(
                f"vcr must equal verified/activated = {computed_vcr!r} (declared values within ±0.0005 pass, so {computed_vcr:.3f} is accepted)",
                f"set vcr to {computed_vcr!r} or the 3-decimal rounding {computed_vcr:.3f}; only verified tasks with passing status and signals.exit_code=0 count as verified",
            )
        )

    non_verified_activated = [task for task in activated if not _is_verified(task)]
    if len(non_verified_activated) > 1:
        failures.append(
            _fail(
                "VCR is below 1.0; cannot activate more than one unverified task",
                "verify or block the existing active task before activating a new task",
            )
        )

    summary = f"tasks={len(valid_task_dicts)} activated={len(activated)} verified={len(verified)} VCR={computed_vcr:.3f}"
    return failures, summary


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    path = Path(args[0]) if args else Path("TASKS.json")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"{path}: task ledger not found", file=sys.stderr)
        print("fix: create TASKS.json from the starter template", file=sys.stderr)
        print("rerun: make validate-tasks", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"{path}: line {exc.lineno} column {exc.colno}: {exc.msg}", file=sys.stderr)
        print("fix: repair the JSON syntax error in TASKS.json", file=sys.stderr)
        print("rerun: make validate-tasks", file=sys.stderr)
        return 1

    failures, summary = validate_ledger(data)
    if failures:
        print("Invalid task ledger:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure.message}", file=sys.stderr)
            print(f"    fix: {failure.hint}", file=sys.stderr)
            print("    rerun: make validate-tasks", file=sys.stderr)
        return 1

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
