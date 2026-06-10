# Global Constraints

These constraints apply to all work in this repository. Domain-specific constraints belong closer to the code they govern.

## Knowledge placement

- Keep durable knowledge near the code it describes.
- Keep this root file limited to global constraints.
- Put roadmap/status in `PROGRESS.md`, not `AGENTS.md` or this file.
- Put module design in the nearest `ARCHITECTURE.md`.
- Put module status/TODOs in the nearest `PROGRESS.md`.
- Put module-specific constraints in the nearest `CONSTRAINTS.md` when needed.
- Do not duplicate long explanations across files; point to the source of truth.

## ACID principles for agent state

- Atomicity: code, tests, and relevant docs must be updated together.
- Consistency: reconcile contradictions between code, tests, docs, and generated artifacts before completion.
- Isolation: keep changes narrow; avoid unrelated edits; parallel agents should own non-overlapping paths.
- Durability: critical decisions, constraints, and verification results must be written to repo files, not left only in chat.

## Verification

- Tests are executable specifications.
- Done means the declared behavior verification passed, not merely that code or docs were written.
- Verified tasks must clear three termination layers: structural status, evidence plus ISO-8601 timestamp, and runtime signal `verification.signals.exit_code == 0`.
- Cross-component tasks must define architectural boundaries before e2e tests are written, and must pass the declared e2e/full-pipeline test before completion.
- Architectural rules must become executable checks whenever possible.
- Validators must reject premature victory and print actionable `fix:` (and preferably `rerun:`) guidance for each failure.
- Repeated review comments must be promoted into automated checks and regression/e2e tests.
- Session exit must run immediate cleanup, update `QUALITY.md` when module health changes, then run final `make check`; cleanup after final verification invalidates the verification and requires a rerun.
- Cleanup operations must be idempotent; periodic cleanup belongs in explicit cleanup tasks, not hidden side work.
- Every task in the feature list must appear in `TASKS.json` with `done_behavior` and `verification.command`.
- VCR-activated tasks are tasks in `active` or `verified` state; `planned` and `blocked` are excluded from the VCR denominator. VCR is verified tasks divided by the sum of active plus verified tasks.
- Do not activate a second active task. If current work cannot proceed, record it as `blocked` with a blocker reason; blocked tasks are suspended records and do not occupy the active lane.
- Run the narrowest useful test first after a behavior change, then the canonical full verification before claiming completion.
- If verification cannot run, record the blocker explicitly.

## Tooling

- The harness gates shipped by this template (`make initialize/check/test/validate`) must keep running with GNU make and the Python standard library only — no package installs and no network access.
- Adopters may wire real formatters/linters/type checkers into the `format`, `format-check`, `lint`, and `typecheck` targets, but the target names must stay stable.

## Privacy and secrets

- Do not commit API keys, tokens, credentials, private user data, or private customer data.
- Redact secrets as `[REDACTED]` in docs, logs, fixtures, and examples.
- Use synthetic fixtures for tests unless real data is explicitly sanitized and approved.
