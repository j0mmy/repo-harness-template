# Observability

Runtime verification must leave enough signal for a later agent to understand what actually ran. Prefer `scripts/run_with_signals.py` for task verification commands:

```bash
python3 scripts/run_with_signals.py --task-id F001 --kind verification -- make check
```

The wrapper runs the command unchanged, records a runtime signal JSON, prints the signal path plus trace/span ids, and exits with the wrapped command's exit code so it can be chained inside `verification.command`.

## Required runtime signal fields

Each record under `.harness/runs/<task-id>/` contains:

- `task_id` — task id from `TASKS.json`
- `run_kind` — `verification|test|e2e|benchmark`
- `command` and `argv` — exactly what ran
- `started_at` / `ended_at` — UTC ISO-8601 timestamps
- `duration_ms` — integer wall-clock duration
- `exit_code` — integer process exit code
- `otel.trace_id` (32 hex chars), `otel.span_id` (16 hex chars), `otel.name`, `otel.status_code` (`OK`/`ERROR`)
- `attributes` — semantic attributes: `harness.task.id`, `harness.run.kind`, `process.exit_code`, `test.status`

## Storage

Generated runtime signal JSON goes under `.harness/runs/<task-id>/` and is ignored by git (`.harness/.gitignore`). Summarize the successful verification in `TASKS.json` (`verification.signals` with `exit_code`, and trace/span/duration when available); promote raw run files only when they are intentionally useful review artifacts.

## OpenTelemetry alignment

Use `.harness/otel_attributes.json` to keep local attribute names stable so harness traces can be compared across tools later. If you add attributes, register them there first.

## Failure loop

On a non-zero exit, the wrapper prints `fix:` and `rerun:` lines pointing at the signal JSON and the exact command to retry. Do not mark a task verified until a wrapped run records `exit_code=0`.
