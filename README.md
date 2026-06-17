# Agent Harness Template

Inspired by https://walkinglabs.github.io/learn-harness-engineering/en/

A reusable, repo-agnostic harness for agent-run software projects. It makes a repository self-governing for AI agents: machine-readable task state, one canonical quality gate, and runtime evidence for every completion claim.

```text
No agent can truthfully say "done" unless the repo contains machine-readable proof
that the declared verification command actually exited 0.
```

**Requirements:** GNU make + Python 3.9+ (standard library only). No package installs, no network.

The full design rationale lives in [`docs/HARNESS_SPEC.md`](docs/HARNESS_SPEC.md). This README is the operating manual.

## What you get

| Piece | Purpose |
| --- | --- |
| `AGENTS.md` / `CLAUDE.md` | Agent router + session lifecycle (thin Claude Code entrypoint) |
| `CONSTRAINTS.md`, `DECISIONS.md` | Durable law and decision ledger |
| `PROGRESS.md`, `QUALITY.md` | Operational cockpit + active module quality register |
| `TASKS.json`, `SPRINTS.json`, `EVALUATOR.json` | Machine-readable task/sprint/evaluator ledgers |
| `Makefile` | Canonical commands: `initialize`, `check`, `test`, `validate`, `e2e` |
| `scripts/validate_*.py` | Executable gates with agent-oriented `fix:`/`rerun:` errors |
| `scripts/run_with_signals.py` | Runtime signal collector (OpenTelemetry-aligned evidence) |
| `scripts/install_harness.py` | Retrofit installer for existing repositories |
| `tests/` | Stdlib-unittest contract tests that keep the harness honest |
| `.github/workflows/check.yml` | CI running the same `make initialize` / `make check` as local |

## Quickstart (new repo)

1. Click **Use this template** on GitHub (or clone this repo).
2. Establish repo truth:

   ```bash
   make initialize   # read-only Phase 0: prints branch/HEAD, then runs make check
   ```

3. Replace the placeholders with your project:
   - Re-plan or remove the `F000` bootstrap task in `TASKS.json`; describe your first real task as `F001` with a `done_behavior` and a `verification.command`.
   - Update `SPRINTS.json` goal/task ids, `PROGRESS.md`, and the module list in `QUALITY.md`.
   - Wire your real formatter/linter/type checker into the `format`, `format-check`, `lint`, `typecheck` targets (keep the target names; `make check` stays the canonical gate).
4. Run `make check` until green, then commit.

## Commands

```bash
make initialize   # Phase 0 cold start: git status + HEAD, then make check (alias: make init)
make check        # canonical gate: format-check, lint, typecheck, validate, test
make validate     # all ledger/config validators (json, tasks, sprints, evaluator, architecture)
make test         # stdlib unittest contract tests
make e2e          # end-to-end tests (installer -> installed copy -> make validate)
make validate-tasks            # just the task ledger / VCR guard
python3 scripts/run_with_signals.py --task-id F001 --kind verification -- make check
```

Every validator failure prints `fix:` and `rerun:` lines, so a failing gate tells the next agent exactly what to change.

## Retrofit an existing repo

```bash
python3 scripts/install_harness.py --target /path/to/your/repo --dry-run   # preview
python3 scripts/install_harness.py --target /path/to/your/repo            # install
cd /path/to/your/repo && make initialize
```

Installer guarantees:

- **Refuses to overwrite** existing files that differ; pass `--force` to overwrite. On any conflict without `--force`, nothing is written.
- **Idempotent:** byte-identical files count as `unchanged`, so re-running is safe.
- **Skips `.git` and runtime artifacts** (`.harness/runs/`) by construction; never deletes anything.
- Does not copy this template's `README.md`/`docs/`; your repo keeps its own docs. The installed `.harness/.gitignore` keeps runtime artifacts out of your git history.

If your repo already has a `Makefile`, the conflict report will list it — merge the harness targets manually (keep the target names stable) and re-run with the remaining files.

## How completion evidence works

`TASKS.json` is the canonical work-state database. Task states: `planned`, `active`, `blocked`, `verified`. A task counts as **verified** only after three termination layers pass:

1. **Structural** — `state: "verified"` and `verification.status: "passing"`.
2. **Evidence** — non-empty `verification.evidence` and an ISO-8601 `verification.last_run_at`.
3. **Runtime signal** — `verification.signals.exit_code` is integer `0` from the actual run (not `true`, not `"0"`).

**VCR (Verified Completion Rate)** counts active work only:

```text
VCR = verified / (active + verified)
```

`planned` and `blocked` tasks are excluded from the denominator — a blocked task is a suspended record: it never inflates VCR and does not occupy the single active-task lane. At most one task may be `active`; if VCR < 1.0, finish, verify, or block the current task before activating another. `make validate-tasks` enforces all of this and rejects premature victory.

## How runtime observability works

Run any verification through the signal collector:

```bash
python3 scripts/run_with_signals.py --task-id F001 --kind verification -- make check
```

It runs the command unchanged, writes a JSON record under `.harness/runs/<task-id>/` (command, argv, timestamps, `duration_ms`, `exit_code`, OpenTelemetry `trace_id`/`span_id`, and `harness.*` attributes), prints the signal path, and exits with the wrapped command's exit code. Runs are gitignored; summarize the successful result into `TASKS.json` (`verification.signals`). Details: `OBSERVABILITY.md` and `.harness/otel_attributes.json`.

## Architecture rules as executable checks

Declare boundaries in `ARCHITECTURE.md`, encode durable rules in `.harness/architecture_rules.json` (`forbidden_import` supported out of the box), and `make validate-architecture` enforces them with agent-oriented errors. The template ships one real rule: harness `scripts/` and `tests/` must stay stdlib-only.

## CI

`.github/workflows/check.yml` runs `make initialize` and `make check` on every push/PR — the same core truth as local work, on a bare runner with no installs.

## Adapting to another stack

Keep the harness contract (file names, Makefile target names, ledger schemas) and swap recipe bodies: point `format`/`format-check`/`lint`/`typecheck` at your stack's tools and extend `test`/`e2e` with your real suites. The shipped validators and contract tests stay as-is — they are what keeps future sessions honest. See `docs/HARNESS_SPEC.md` for the full pattern, anti-patterns it blocks, and the adaptation checklist.
