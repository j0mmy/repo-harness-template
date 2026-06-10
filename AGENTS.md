# AGENTS.md

Router for AI agents working in this repository.
This file is an index, not an encyclopedia or roadmap.

## Session lifecycle

### Phase 0 — Initialization

Call this phase when the user says "initialize", "cold start", "resume", or asks to establish repo truth before work.

User-facing calls:

- Agent: "initialize this repo" or "run Phase 0".
- Shell: `make initialize` (`make init` alias).

Agent steps:

1. Confirm repo root and live branch status.
2. Read `AGENTS.md`, `PROGRESS.md`, `QUALITY.md`, `TASKS.json`, `SPRINTS.json`, `EVALUATOR.json`, `OBSERVABILITY.md`, `DECISIONS.md`, and `CONSTRAINTS.md`.
3. Read module-local docs for the area being touched.
4. Run `make initialize` to print branch/head state and execute `make check`.
5. Return branch/status/HEAD, verification result, VCR, active task id, active sprint, evaluator rubric, and the next atomic unit.

`make initialize` is read-only. It must not install dependencies, download data, create commits, or touch private artifacts.

### Phase 1 — Work

1. Select the next planned task from the active sprint scope first, then `TASKS.json` order.
2. Classify the task scope (`single_component`, `cross_component`, `architecture_rule`, `docs_only`); for cross-component work, define architectural boundaries in `ARCHITECTURE.md` before writing e2e tests.
3. Activate exactly one task, set `active_task`, recompute VCR, and follow the Work rules below.
4. Turn each `done_behavior` claim into tests; write failing tests first, watch them fail for the expected reason, implement minimally, then re-run.

### Phase 2 — Clock-out

1. Run the task's declared verification command, preferably through `scripts/run_with_signals.py`, and capture the exit code.
2. Update `TASKS.json` with task state, verification status, evidence, run timestamp, runtime signal, and VCR.
3. Update `PROGRESS.md`.
4. Run immediate cleanup for temporary artifacts created during the session.
5. Update `QUALITY.md` if module quality, stability, boundaries, or cleanup priority changed.
6. Complete the Session Exit Checklist.
7. Run final `make check` after cleanup/checklist/quality updates.
8. Ensure every completed atomic unit is committed; do not batch unrelated completed work together.

## Session Exit Checklist

Session completion requires both task verification and a clean state check. At the end of every session, confirm:

- [ ] Canonical gate passes: `make check`.
- [ ] Touched-area build/test command passes when the repo defines one separately from `make check` (for example `make test` or a service-specific smoke test).
- [ ] Feature/task state updated (`TASKS.json`, and `PROGRESS.md` when project state changed).
- [ ] Immediate cleanup completed for temporary artifacts created this session.
- [ ] `QUALITY.md` updated if module quality, stability, boundaries, or cleanup priority changed.
- [ ] No debug code remains (stray print/log statements, breakpoints, temporary TODOs, scratch artifacts).
- [ ] Standard startup path is documented and still works, or is explicitly unchanged.

### Cleanup modes

- Immediate cleanup, at the end of every session: remove temporary artifacts created during the session, update feature-list state, and ensure build/tests pass. This is reference-counting cleanup: clean something up as soon as the session is done using it.
- Periodic cleanup, weekly: run a full-system scan, handle accumulated structural issues, update quality documents, and run benchmark tests to detect drift. This is tracing cleanup: a comprehensive maintenance pass on a regular cadence.

### Quality document

Maintain `QUALITY.md` as an active artifact that continuously scores each module. Normal feature selection follows active sprint scope and `TASKS.json` order; `QUALITY.md` drives periodic-cleanup task creation and explicitly scoped quality repair work.

### Idempotent cleanup

Cleanup scripts must be safe to run repeatedly. Running a cleanup script one more time must not produce unintended side effects; cleanup operations should converge on the same clean state after retries or partial failures.

## Work rules

- Work on one feature at a time.
- Active task state lives in `TASKS.json`.
- Done means the task's declared behavior verification command passed and `TASKS.json` records status, evidence, run timestamp, and `verification.signals.exit_code=0`.
- For cross-component changes, define architectural boundaries before writing e2e tests, and pass the declared e2e/full-pipeline test before completion.
- Turn architectural rules into executable checks whenever possible (`.harness/architecture_rules.json`).
- Design validator/test errors for agents: include concrete `fix:` and `rerun:` guidance.
- Promote recurring review feedback into automated checks and regression/e2e tests.
- Do not activate a second active task. Blocked tasks are suspended records; they do not occupy the active lane or the VCR denominator. Run `make validate-tasks` before and after changing task state.
- Do not "also refactor" unrelated feature B while implementing feature A.

## Atomic commit rule

- Commit after each completed atomic unit of work.
- Commit only files in that atomic scope.
- Leave unrelated dirty work unstaged.
- Commit messages must state what changed and why.

## Read order before editing

1. Read root `CONSTRAINTS.md`.
2. Read root `PROGRESS.md`.
3. Read root `SPRINTS.json` and `EVALUATOR.json`, if present.
4. Read root `DECISIONS.md`, if present.
5. Read nearest module/service `CONSTRAINTS.md`, `ARCHITECTURE.md`, and `PROGRESS.md`, if present.
6. Inspect nearby tests for executable specifications.

## Source-of-truth map

- User-facing overview: `README.md`
- Global constraints: `CONSTRAINTS.md`
- Project status and next steps: `PROGRESS.md`
- Module quality scores and cleanup priorities: `QUALITY.md`
- Durable decisions: `DECISIONS.md`
- Canonical consistency check: `make check`
- Machine-readable task state and completion evidence: `TASKS.json`
- Sprint contracts, goals, required gates, and observability requirements: `SPRINTS.json`
- Evaluator scoring rubric and blocker criteria: `EVALUATOR.json`
- Runtime observability standard: `OBSERVABILITY.md` and `.harness/otel_attributes.json`
- Task ledger validation/VCR guard: `make validate-tasks`
- Three-layer termination evidence: `verification.status`, `verification.evidence`/`last_run_at`, and `verification.signals.exit_code`
- Architecture boundaries: root or module-local `ARCHITECTURE.md`
- Executable architecture checks: `make validate-architecture`
- End-to-end/full-pipeline tests: `make e2e` or task-specific `tests/e2e/...`
- Test policy: existing test files under `tests/`

## Canonical check command

```bash
make check
```

## Operating rule

Keep knowledge near the code it governs. Do not duplicate long explanations across files. A change is complete only when code, tests, and relevant nearby docs are updated together.

Do not store active roadmap, detailed architecture, private data, or secrets in this file.
