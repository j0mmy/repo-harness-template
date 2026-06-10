"""Validate EVALUATOR.json rubric shape so evaluator semantics stay computable.

Dimensions are scored 1-5; the rubric score is the weight-weighted average and
weights must sum to 100. A rubric passes only when the weighted average meets
the rubric-level pass_threshold, every dimension meets its own pass_threshold,
and no blockers condition fires. Stdlib only.
"""

from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path

RERUN_HINT = "make validate-evaluator"
SCORE_MIN = 1.0
SCORE_MAX = 5.0
WEIGHT_TOTAL = 100.0


@dataclass(frozen=True)
class Failure:
    message: str
    hint: str


def _fail(message, hint):
    return Failure(message=message, hint=hint)


def _is_non_empty_string(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _is_string_list(value) -> bool:
    return isinstance(value, list) and all(_is_non_empty_string(item) for item in value)


def _validate_dimension(dimension, rubric_label, index, seen):
    if not isinstance(dimension, dict):
        return [
            _fail(
                f"{rubric_label}: dimensions[{index}] must be an object",
                "replace this dimension entry with a JSON object",
            )
        ]

    failures = []
    label = f"{rubric_label}.{dimension.get('id') or f'dimensions[{index}]'}"

    dimension_id = dimension.get("id")
    if not _is_non_empty_string(dimension_id):
        failures.append(
            _fail(f"{label}: id must be a non-empty string", "give the dimension a stable id like behavior_correctness")
        )
    elif dimension_id in seen:
        failures.append(
            _fail(f"{label}: id must be unique within the rubric", "rename or remove the duplicate dimension id")
        )
    else:
        seen.add(dimension_id)

    weight = dimension.get("weight")
    if not _is_number(weight) or weight <= 0:
        failures.append(
            _fail(f"{label}: weight must be a positive number", "set weight so all rubric weights sum to 100")
        )

    threshold = dimension.get("pass_threshold")
    if not _is_number(threshold) or not SCORE_MIN <= float(threshold) <= SCORE_MAX:
        failures.append(
            _fail(
                f"{label}: pass_threshold must be a number between {SCORE_MIN:g} and {SCORE_MAX:g}",
                "dimensions are scored 1-5; set the minimum score this dimension must reach",
            )
        )

    criteria = dimension.get("criteria")
    if not _is_string_list(criteria) or not criteria:
        failures.append(
            _fail(
                f"{label}: criteria must be a non-empty list of strings",
                "list the observable criteria evaluators score against",
            )
        )

    blockers = dimension.get("blockers")
    if blockers is not None and not _is_string_list(blockers):
        failures.append(
            _fail(
                f"{label}: blockers must be a list of strings when present",
                "describe each automatic-fail condition as a string, or use []",
            )
        )

    return failures


def _validate_rubric(rubric, index, seen_ids):
    if not isinstance(rubric, dict):
        return [_fail(f"rubrics[{index}] must be an object", "replace this rubric entry with a JSON object")]

    failures = []
    label = str(rubric.get("id") or f"rubrics[{index}]")

    rubric_id = rubric.get("id")
    if not _is_non_empty_string(rubric_id):
        failures.append(_fail(f"{label}: id must be a non-empty string", "give the rubric a stable id"))
    elif rubric_id in seen_ids:
        failures.append(_fail(f"{label}: id must be unique", "rename or remove the duplicate rubric id"))
    else:
        seen_ids.add(rubric_id)

    if not _is_non_empty_string(rubric.get("title")):
        failures.append(_fail(f"{label}: title must be a non-empty string", "add a concise rubric title"))

    threshold = rubric.get("pass_threshold")
    if not _is_number(threshold) or not SCORE_MIN <= float(threshold) <= SCORE_MAX:
        failures.append(
            _fail(
                f"{label}: pass_threshold must be a number between {SCORE_MIN:g} and {SCORE_MAX:g}",
                "the rubric passes when the weighted average of dimension scores (1-5) meets this threshold",
            )
        )

    dimensions = rubric.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        failures.append(
            _fail(f"{label}: dimensions must be a non-empty list", "add the weighted dimensions this rubric scores")
        )
        return failures

    seen_dimension_ids = set()
    for dimension_index, dimension in enumerate(dimensions):
        failures.extend(_validate_dimension(dimension, label, dimension_index, seen_dimension_ids))

    weights = [dimension.get("weight") for dimension in dimensions if isinstance(dimension, dict)]
    if weights and all(_is_number(weight) for weight in weights):
        total = sum(float(weight) for weight in weights)
        if not math.isclose(total, WEIGHT_TOTAL, abs_tol=1e-6):
            failures.append(
                _fail(
                    f"{label}: dimension weights sum to {total:g}, expected {WEIGHT_TOTAL:g}",
                    "adjust the weights so they sum to exactly 100",
                )
            )

    return failures


def validate_rubrics(data):
    if not isinstance(data, dict):
        return [_fail("EVALUATOR rubric file must be a JSON object", "replace EVALUATOR.json with a JSON object")], ""

    failures = []
    if data.get("schema_version") != 1:
        failures.append(_fail("schema_version must be 1", "set schema_version to 1"))

    rubrics = data.get("rubrics")
    if not isinstance(rubrics, list) or not rubrics:
        failures.append(_fail("rubrics must be a non-empty list", "add at least one rubric object to rubrics"))
        return failures, ""

    seen_ids = set()
    for index, rubric in enumerate(rubrics):
        failures.extend(_validate_rubric(rubric, index, seen_ids))

    active_rubric = data.get("active_rubric")
    if not _is_non_empty_string(active_rubric) or active_rubric not in seen_ids:
        failures.append(
            _fail(
                "active_rubric must name a rubric id defined in rubrics",
                "set active_rubric to the id of the rubric agents should score against",
            )
        )

    summary = f"rubrics={len(seen_ids)} active={active_rubric if isinstance(active_rubric, str) else 'none'}"
    return failures, summary


def main(argv=None):
    args = argv if argv is not None else sys.argv[1:]
    path = Path(args[0]) if args else Path("EVALUATOR.json")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"{path}: evaluator rubric file not found", file=sys.stderr)
        print("fix: create EVALUATOR.json from the starter template", file=sys.stderr)
        print(f"rerun: {RERUN_HINT}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"{path}: line {exc.lineno} column {exc.colno}: {exc.msg}", file=sys.stderr)
        print("fix: repair the JSON syntax error", file=sys.stderr)
        print(f"rerun: {RERUN_HINT}", file=sys.stderr)
        return 1

    failures, summary = validate_rubrics(data)
    if failures:
        print("Invalid evaluator rubric:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure.message}", file=sys.stderr)
            print(f"    fix: {failure.hint}", file=sys.stderr)
            print(f"    rerun: {RERUN_HINT}", file=sys.stderr)
        return 1

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
