"""Run a command and record its runtime signal JSON under .harness/runs/<task-id>/.

The wrapper runs the command unchanged, writes a runtime signal record with
OpenTelemetry-aligned trace/span ids and harness attributes, prints the signal
path, and exits with the wrapped command's exit code so it can be chained
inside a task's verification.command.

Stdlib only. Usage:

    python3 scripts/run_with_signals.py --task-id F001 --kind verification -- make check
"""

from __future__ import annotations

import argparse
import json
import secrets
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

RUNS_DIR = Path(".harness/runs")


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Run a command and record its runtime signal JSON under .harness/runs/<task-id>/.",
    )
    parser.add_argument("--task-id", required=True, help="task id from TASKS.json, e.g. F001")
    parser.add_argument("--kind", default="verification", help="run kind, e.g. verification, test, e2e")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="command to wrap, after --")
    args = parser.parse_args(argv)

    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        parser.error("missing wrapped command; usage: run_with_signals.py --task-id F001 --kind verification -- <command>")

    trace_id = secrets.token_hex(16)
    span_id = secrets.token_hex(8)
    started = datetime.now(timezone.utc)
    clock_start = time.monotonic()
    try:
        exit_code = subprocess.run(command).returncode
    except FileNotFoundError:
        print(f"wrapped command not found: {command[0]}", file=sys.stderr)
        print("fix: check the command name/path given after --", file=sys.stderr)
        print(
            f"rerun: scripts/run_with_signals.py --task-id {args.task_id} --kind {args.kind} -- <corrected command>",
            file=sys.stderr,
        )
        return 127
    duration_ms = int((time.monotonic() - clock_start) * 1000)
    ended = datetime.now(timezone.utc)

    signal = {
        "task_id": args.task_id,
        "run_kind": args.kind,
        "started_at": started.isoformat(timespec="seconds"),
        "ended_at": ended.isoformat(timespec="seconds"),
        "duration_ms": duration_ms,
        "command": " ".join(command),
        "argv": command,
        "exit_code": exit_code,
        "otel": {
            "trace_id": trace_id,
            "span_id": span_id,
            "name": f"harness.{args.kind}",
            "status_code": "OK" if exit_code == 0 else "ERROR",
        },
        "attributes": {
            "harness.task.id": args.task_id,
            "harness.run.kind": args.kind,
            "process.exit_code": exit_code,
            "test.status": "passed" if exit_code == 0 else "failed",
        },
    }

    run_dir = RUNS_DIR / args.task_id
    run_dir.mkdir(parents=True, exist_ok=True)
    signal_path = run_dir / f"{started.strftime('%Y%m%dT%H%M%SZ')}-{span_id}.json"
    signal_path.write_text(json.dumps(signal, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(f"runtime signal: {signal_path}")
    print(f"trace_id={trace_id} span_id={span_id} exit_code={exit_code}")
    if exit_code != 0:
        print(
            "fix: inspect the failing command output and the runtime signal JSON, then repair the failing path before marking the task verified",
            file=sys.stderr,
        )
        print(
            f"rerun: scripts/run_with_signals.py --task-id {args.task_id} --kind {args.kind} -- {' '.join(command)}",
            file=sys.stderr,
        )
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
