# Project Progress

Root `PROGRESS.md` is the operational cockpit for this repo: current truth only. Detailed agent lifecycle rules live in `AGENTS.md`; durable decisions live in `DECISIONS.md`; task evidence lives in `TASKS.json`; module health and cleanup priorities live in `QUALITY.md`.

## Current State

- Consistency check: `make check` is the canonical gate (validators + stdlib unittest contract tests). Status: passing.
- Callable initialization phase: `make initialize` (`make init` alias) prints live branch/head state and runs `make check`; canonical Phase 0 steps live in `AGENTS.md`.
- Machine-readable task state: `TASKS.json` records active task, task state, done behavior, verification command, evidence, run timestamp, runtime exit signal, and VCR.
- VCR status: `1.000`; denominator includes only `active` and `verified` tasks.
- Quality register: `QUALITY.md` tracks module scores and the repair queue.
- Privacy checkpoint: tests use synthetic fixtures; secrets/private data stay out of git.
- Safe checkpoint: no task is intentionally half-edited; `active_task` is null.

Before editing, committing, or delegating, run:

```bash
git status --short
```

Do not trust stale status snapshots in docs; inspect the live working tree.

## Completed

- [x] `F000` — Harness scaffold bootstrapped: ledgers, validators, runtime signal wrapper, installer, contract tests, CI workflow.

## In Progress

- [ ] None intentionally active at this checkpoint.

`In Progress` means active WIP right now. Ordered follow-up work belongs in `TASKS.json`, not this prose file.

## Known Issues

- `format`, `format-check`, and `typecheck` are stdlib placeholders; wire your stack's real tools into those targets (keep the target names).

## Next Steps

See `TASKS.json` for canonical planned work and verification commands.

Current planned sequence:

1. `F001` — First feature (replace with your project's first real task).

## Cold Start

Canonical Phase 0 initialization lives in `AGENTS.md`. Use `make initialize` (`make init` alias) to establish live repo truth, then report branch/status/HEAD, verification result, VCR, active task id, active sprint, evaluator rubric, and the next atomic unit.
