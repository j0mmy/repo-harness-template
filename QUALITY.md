# Quality Register

Last assessed: 2026-06-10T23:03:25Z

`QUALITY.md` is the active quality register for modules and cleanup priorities. It is not a one-time audit; update it when verification, understandability, stability, boundaries, conventions, or repair priorities change.

## Quality Dimensions

- Verification passing state: whether the module's declared checks pass now.
- Agent understandability: whether a cold-start agent can locate the source of truth and safe edit points.
- Test stability: whether tests are deterministic, scoped, and representative.
- Architecture-boundary compliance: whether module dependencies and responsibilities follow `ARCHITECTURE.md` and executable boundary checks.
- Code-convention compliance: whether formatting, typing, linting, naming, and repo idioms are followed.
- Known cleanup or repair action: the next concrete action that would improve the module.

## Module Scores

### harness-scripts (`scripts/`)

Score: A

- Verification passing state: Passing under the latest recorded `make check`.
- Agent understandability: Clear; one script per gate, each with a module docstring and agent-oriented errors.
- Test stability: Stable; exercised by deterministic contract tests on every run.
- Architecture-boundary compliance: Compliant; stdlib-only rule enforced by `make validate-architecture`.
- Code-convention compliance: Followed.
- Known cleanup or repair action: None.

### harness-tests (`tests/`)

Score: A

- Verification passing state: Passing via `make test` (stdlib unittest discovery).
- Agent understandability: Clear; one contract file per harness concern, synthetic fixtures only.
- Test stability: Stable; temp-dir isolated, no network, no ordering dependence.
- Architecture-boundary compliance: Compliant; stdlib-only rule enforced.
- Code-convention compliance: Followed.
- Known cleanup or repair action: None.

### template-docs (root `*.md`, `docs/`)

Score: B

- Verification passing state: Placement contracts pass (`tests/test_quality_and_claude_contracts.py`).
- Agent understandability: Clear routers and ledgers; the long-form spec in `docs/HARNESS_SPEC.md` still shows stack-specific examples that adopters must map to their tools.
- Test stability: Stable (text contracts only).
- Architecture-boundary compliance: Compliant.
- Code-convention compliance: Followed.
- Known cleanup or repair action: Adopters should replace placeholder modules in this register with their real modules after the first feature lands.

## Repair Queue

- [ ] Convert the lowest-scoring module's top repair action into a scoped task in `TASKS.json` before starting quality-repair work.
- [ ] Promote recurring review feedback into an executable check or regression test.
