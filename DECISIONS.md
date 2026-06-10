# Design Decisions

Durable project decisions that future agents should preserve unless explicitly superseded.
Keep each entry concise: decision, reason, rejected alternative, and active constraint.

## 2026-06-11: Commit after each atomic unit of completed work

- Reason: Commits are free, automatically versioned state snapshots. They make recovery, review, bisection, and cold starts safer.
- Rejected alternative: Batch unrelated completed work into larger commits.
- Constraint: Commit only completed work in the current atomic scope; do not sweep unrelated dirty work into the commit. Commit messages must explain what changed and why.

## 2026-06-11: Use `make check` as the canonical quality gate

- Reason: Agents need one stable command that checks formatting, lint, types, data syntax, task state, and tests before claiming consistency.
- Rejected alternative: Ad hoc test-only verification.
- Constraint: `make check` must run all required repo gates and must include `scripts/validate_tasks.py`.

## 2026-06-11: Treat repo initialization as callable Phase 0

- Reason: Agents and users need one named preflight that establishes live repo truth before choosing or editing an atomic unit.
- Rejected alternative: Ambiguous cold-start prose without a shell target.
- Constraint: `make initialize` (`make init` alias) is read-only: it reports live branch/head state and runs `make check`.

## 2026-06-11: Treat clean session exit as part of completion

- Reason: Future agents inherit artifacts, stale ledgers, and quality drift when cleanup is skipped after behavior verification.
- Rejected alternative: Run tests, claim completion, and leave cleanup/quality updates for an unspecified later pass.
- Constraint: Clock-out order is immediate cleanup, `QUALITY.md` upkeep, Session Exit Checklist, final `make check`, then atomic commit/handoff.

## 2026-06-11: Define completion by verified behavior evidence

- Reason: Agents need a durable, machine-readable task ledger that states what behavior counts as done and what command proved it.
- Rejected alternative: Treat code or docs being written as completion, or keep task state only in prose checklists.
- Constraint: `TASKS.json` is the canonical feature/task state file. Each task must include `done_behavior` and `verification.command`. `make check` must run `scripts/validate_tasks.py`.

## 2026-06-11: Treat blocked tasks as suspended records

- Reason: Blocked work should remain visible without occupying the single active-task lane or distorting Verified Completion Rate.
- Rejected alternative: Count blocked tasks in the VCR denominator, which prevents pivots and makes VCR report suspended records as current work.
- Constraint: VCR denominator includes only `active` and `verified` tasks. `blocked` tasks require a blocker reason/status but are excluded from VCR until reactivated or verified.

## 2026-06-11: Require three-layer termination validation before verified state

- Reason: Agents can declare victory from code-level confidence or prose evidence even when no runtime signal proves the declared verification command succeeded.
- Rejected alternative: Trust `verification.status="passing"` and free-form evidence text without a machine-readable signal from the actual run.
- Constraint: A task may count as verified only when it clears structural status, evidence plus ISO-8601 timestamp, and runtime signal `verification.signals.exit_code == 0`.

## 2026-06-11: Require e2e/full-pipeline verification for cross-component changes

- Reason: Unit tests miss interface mismatches, state propagation errors, resource lifecycle issues, and environment dependencies that only appear when components run together.
- Rejected alternative: Allow cross-component tasks to complete after isolated unit tests only.
- Constraint: Cross-component tasks must define boundaries first and include the relevant e2e/full-pipeline command in `verification.command` before they can be marked verified.

## 2026-06-11: Design harness errors for agent self-correction

- Reason: Agents can repair failures faster when validators provide concrete fix steps and rerun commands.
- Rejected alternative: Human-oriented diagnostics that only say what failed.
- Constraint: Custom validators and architecture checks must emit actionable `fix:` guidance, and preferably `rerun:` guidance, for each failure.

## 2026-06-11: Promote recurring review feedback into executable checks

- Reason: Reviewers should not repeatedly catch the same issue by hand.
- Rejected alternative: Keep recurring review comments as tribal knowledge or prose-only guidance.
- Constraint: Repeated review findings must become architecture rules, validator checks, regression tests, or e2e scenarios.

## 2026-06-11: Ship harness gates on the Python standard library only

- Reason: The template must verify itself on a fresh machine (and in CI) with `make` and `python3` alone, so adoption never starts with dependency setup or network installs.
- Rejected alternative: Depend on pytest/ruff/mypy out of the box, which would make `make check` fail on clean systems and couple the harness contract to one stack.
- Constraint: `scripts/` and `tests/` must import stdlib modules only (enforced by `.harness/architecture_rules.json`); stack-specific tools belong in the `format`/`format-check`/`lint`/`typecheck` recipe bodies that adopters replace.
