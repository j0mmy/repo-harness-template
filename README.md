# Portable Agent Harness Template

A reusable, repo-agnostic harness for agent-run software projects.

This document extracts the **raw harness pattern** from an existing repo and removes the domain-specific application logic. Use it as a template for any repository where agents must work safely, resume across sessions, and prove completion with runtime evidence instead of prose confidence.

## Purpose

The harness makes a repo self-governing for agents by adding:

- a repo router for agents
- global constraints and knowledge-placement law
- durable decision ledger
- operational progress cockpit
- active quality document for module scores and cleanup priorities
- machine-readable task ledger
- canonical `make check` quality gate
- callable initialization / cold-start phase
- session exit clean-state checklist
- immediate and periodic cleanup modes
- VCR: Verified Completion Rate
- three-layer termination validation
- contract tests proving the harness stays wired

The goal is simple:

```text
No agent can truthfully say "done" unless the repo contains machine-readable proof
that the declared verification command actually exited 0.
```

## Non-goals

This harness does **not** define your app architecture, business domain, API model, or feature implementation details. Those belong in your normal source tree and module-local docs.

The harness only defines how agents:

1. discover repo truth
2. choose work
3. activate one atomic task
4. test and implement it
5. verify it through a canonical gate
6. record durable evidence
7. commit a clean atomic unit

---

# 1. Harness file map

Recommended root files:

```text
.
├── AGENTS.md                     # agent router and session lifecycle
├── CLAUDE.md                     # thin Claude Code router to AGENTS.md
├── CONSTRAINTS.md                # global non-negotiable rules
├── DECISIONS.md                  # durable decision ledger
├── PROGRESS.md                   # operational cockpit / current status
├── QUALITY.md                    # active module quality scores + cleanup priorities
├── TASKS.json                    # machine-readable task state + evidence
├── SPRINTS.json                  # sprint contract: scope, gates, evaluator, observability
├── EVALUATOR.json                # weighted evaluator rubric + blocker criteria
├── OBSERVABILITY.md              # runtime signal and OpenTelemetry convention
├── ARCHITECTURE.md               # optional root-level boundary map for cross-component systems
├── .gitignore                    # ignores generated harness runtime artifacts
├── .harness/
│   ├── otel_attributes.json      # repo-local OpenTelemetry attribute registry
│   ├── architecture_rules.json   # optional executable architecture-rule manifest
│   └── runs/                     # generated runtime signal JSON; gitignored by default
├── Makefile                      # canonical commands: initialize/check/test/e2e/etc.
├── scripts/
│   ├── run_with_signals.py       # wraps commands and records runtime signal JSON
│   ├── validate_json.py          # JSON syntax validation
│   ├── validate_tasks.py         # task ledger, VCR, termination validator
│   ├── validate_sprints.py       # sprint contract validator
│   ├── validate_evaluator.py     # evaluator rubric validator
│   └── validate_architecture.py  # optional executable architecture-boundary checks
└── tests/
    ├── e2e/                      # end-to-end / full-pipeline scenarios
    ├── test_harness_observability.py
    ├── test_sprint_contracts.py
    ├── test_makefile_contract.py
    ├── test_task_completion_evidence.py
    ├── test_task_termination_signals.py
    ├── test_blocked_vcr_semantics.py
    ├── test_quality_and_claude_contracts.py
    └── test_architecture_rules.py    # proves architecture checkers reject violations
```

Optional module-local docs:

```text
src/<package>/<module>/
├── ARCHITECTURE.md               # stable local design and boundaries
├── CONSTRAINTS.md                # module-specific law
└── PROGRESS.md                   # module-local current status / known gaps
```

## Responsibility split

- `AGENTS.md`: router, lifecycle, source-of-truth map, canonical commands. Not a roadmap.
- `CLAUDE.md`: thin Claude Code entrypoint that points to `AGENTS.md`; not a duplicate rulebook.
- `CONSTRAINTS.md`: durable global law. Not mutable status.
- `DECISIONS.md`: compact durable decisions. Not chat transcript.
- `PROGRESS.md`: current repo cockpit. Not architecture encyclopedia.
- `QUALITY.md`: active module quality scores and cleanup priorities. Not a one-time audit.
- `TASKS.json`: task state, done behavior, verification command, evidence, VCR.
- `SPRINTS.json`: sprint scope, task ids, required gates, evaluator rubric id, observability requirements.
- `EVALUATOR.json`: weighted evaluator rubric and automatic blocker criteria.
- `OBSERVABILITY.md`: runtime signal policy and OpenTelemetry attribute convention.
- `.harness/otel_attributes.json`: machine-readable OpenTelemetry-aligned attribute registry.
- `.harness/architecture_rules.json`: optional executable architecture-rule manifest consumed by `scripts/validate_architecture.py`.
- `.harness/runs/`: generated runtime signal records; ignore this directory by default unless a specific run artifact is intentionally promoted.
- `ARCHITECTURE.md`: stable boundary map for cross-component flows and forbidden dependencies.
- `Makefile`: executable truth. If humans/agents should trust a command, wire it here.
- `scripts/run_with_signals.py`: records command runtime signals for self-correcting retries and handoff.
- `scripts/validate_tasks.py`: prevents premature victory.
- `scripts/validate_sprints.py`: validates sprint contracts.
- `scripts/validate_evaluator.py`: validates evaluator rubrics.
- `scripts/validate_architecture.py`: turns architecture rules into executable checks when the repo has boundary constraints.
- `tests/e2e/`: proves full pipeline behavior across component boundaries.
- `tests/test_*contract*.py`: prevents future edits from silently weakening the harness.

---

# 2. Operating principles

## ACID for agent state

Use database-style ACID principles for repo state:

- **Atomicity:** one task = one atomic unit. Code, tests, docs, and task evidence move together.
- **Consistency:** code, tests, docs, ledgers, and generated artifacts must not contradict each other.
- **Isolation:** only one active feature at a time unless you explicitly split non-overlapping paths.
- **Durability:** decisions, constraints, task state, sprint contracts, evaluator rubrics, observability conventions, and verification evidence live in repo files, not only in chat.

## Completion standard

```text
Written code is not completion.
Updated docs are not completion.
A plausible agent summary is not completion.
Completion = declared behavior verification passed + evidence recorded in TASKS.json.
For cross-component changes, declared behavior verification must include an end-to-end/full-pipeline check.
For observability-sensitive tasks, declared verification should run through the runtime signal collector and record exit signals.
Session completion = task verification passed + clean state check passed.
```

## Clean state and cleanup modes

Every session must leave the repo easier for the next agent to understand. Missing cleanup means the session is not done, even if the feature works.

Use two cleanup modes:

- **Immediate cleanup** at the end of every session: remove temporary artifacts created during the session, update feature-list state, and ensure build/tests pass. This is reference-counting cleanup: clean something up as soon as the session is done using it.
- **Periodic cleanup** weekly: run a full-system scan, handle accumulated structural issues, update quality documents, and run benchmark tests to detect drift. This is tracing cleanup: a comprehensive maintenance pass on a regular cadence.

Maintain `QUALITY.md` as an active artifact that continuously scores each module. Cleanup and quality-repair work targets the lowest-scoring module first; normal feature selection still follows the active sprint scope and `TASKS.json` order.

Cleanup scripts must be idempotent: safe to run repeatedly, converging on the same clean state after retries or partial failures.

Source: <https://walkinglabs.github.io/learn-harness-engineering/en/lectures/lecture-12-why-every-session-must-leave-a-clean-state/>.

## End-to-end verification changes agent behavior

Unit tests prove isolated pieces. They do not prove that those pieces actually work together.

For any task that touches more than one component, boundary, process, service, persistence layer, or user-visible flow, completion requires an end-to-end or full-pipeline run. This requirement changes how agents code: they must consider upstream/downstream interfaces, error paths, environment assumptions, and resource lifecycle instead of optimizing for the fastest isolated test.

Use this adequacy gradient:

```text
unit tests <= integration tests <= end-to-end tests <= real full-pipeline verification
```

The farther right the verification sits, the more boundary defects it can catch.

## Observability belongs inside the harness

Runtime state is evidence. If the harness does not capture what command ran, when it ran, how long it took, and what exit code it returned, future agents are forced to retry blindly.

Build runtime signal collection into the harness:

```bash
python scripts/run_with_signals.py --task-id F001 --kind verification -- make check
```

The signal collector should write JSON under `.harness/runs/` with:

- task id
- run kind
- started/ended timestamps
- duration
- command and argv
- integer exit code
- OpenTelemetry `trace_id` and `span_id`
- semantic attributes such as `harness.task.id`, `harness.run.kind`, `process.exit_code`, and `test.status`

Do not commit raw runtime traces unless explicitly desired; summarize verified evidence in `TASKS.json` and ignore `.harness/runs/` by default.

## Sprint contracts and evaluator rubrics

Long-running work needs explicit scope and scoring.

- `SPRINTS.json` defines sprint goal, task ids, required gates, evaluator rubric id, and observability requirements.
- `EVALUATOR.json` defines weighted dimensions and automatic blockers.
- `make validate-sprints` and `make validate-evaluator` turn these into executable checks.

Default evaluator dimensions:

1. behavior correctness
2. verification evidence
3. architecture boundaries
4. runtime observability
5. privacy/security

Every validator error should include `fix:` and `rerun:` guidance.

## Standardize with OpenTelemetry

Use OpenTelemetry conventions so harness traces can be compared across tools later. At minimum, runtime signal JSON should include:

```json
{
  "otel": {
    "trace_id": "32 hex chars",
    "span_id": "16 hex chars",
    "name": "harness.verification",
    "status_code": "OK"
  },
  "attributes": {
    "harness.task.id": "F001",
    "harness.run.kind": "verification",
    "process.exit_code": 0,
    "test.status": "passed"
  }
}
```

Keep the local semantic convention in `.harness/otel_attributes.json` and explain it in `OBSERVABILITY.md`.

## Agent-oriented error messages

Harness errors are instructions to the next agent, not just diagnostics for humans.

Every executable check should emit:

1. what failed
2. why it matters
3. the concrete file/path/API to change
4. the command to rerun

Bad:

```text
Direct filesystem access in renderer.
```

Good:

```text
Direct filesystem access in renderer: src/renderer/export.ts imports fs.
Renderer code must not access the filesystem directly. Move file operations to src/preload/file-ops.ts, expose them through window.api.exportFile, and rerun `make validate-architecture && make e2e`.
```

This creates a self-correcting feedback loop: the agent reads the failure and knows the next edit.

## Architecture before end-to-end tests

Define the architectural boundaries before writing e2e tests. Otherwise the e2e test may encode the wrong design.

Minimum boundary definition for a cross-component feature:

- components touched
- allowed dependency direction
- forbidden imports/calls
- public interface or contract between components
- error paths crossing the boundary
- state/resource lifecycle expectations
- e2e scenario that proves the boundary works in the real flow

Turn each durable boundary rule into an executable check when possible.

## Review feedback promotion

Recurring review comments must be promoted into the harness:

```text
review comment -> architectural rule -> executable check -> agent-oriented error -> contract/e2e test
```

Do not rely on reviewers repeatedly catching the same issue. Once an issue recurs, encode it as a rule that fails automatically with a concrete fix hint.

## Knowledge placement

Keep knowledge near the code it governs:

- global law -> `CONSTRAINTS.md`
- active repo status -> `PROGRESS.md`
- module quality scores / cleanup priorities -> `QUALITY.md`
- durable decisions -> `DECISIONS.md`
- module design -> nearest `ARCHITECTURE.md`
- module status -> nearest `PROGRESS.md`
- machine-readable work state -> `TASKS.json`
- executable verification -> `Makefile`, tests, scripts

Avoid copying the same long explanation into multiple files. Prefer pointers.

---

# 3. Session lifecycle

## Phase 0 — Initialization / cold start

Callable forms:

```bash
make initialize
make init
```

Agent behavior:

1. Confirm repo root and live git status.
2. Read root harness docs:
   - `AGENTS.md`
   - `PROGRESS.md`
   - `QUALITY.md`
   - `TASKS.json`
   - `SPRINTS.json`
   - `EVALUATOR.json`
   - `DECISIONS.md`
   - `CONSTRAINTS.md`
3. Read local docs for the area being touched.
4. Run `make initialize`.
5. Report:
   - branch/status/HEAD
   - whether `make check` passed
   - VCR
   - active task id
   - next atomic unit

Important: `make initialize` is read-only. It should not install dependencies, download data, create commits, or modify private artifacts.

## Phase 1 — Work

1. Select the next planned task from the active sprint scope first, then `TASKS.json` order. `QUALITY.md` creates or prioritizes periodic-cleanup tasks only when cleanup/quality work is explicitly in scope.
2. Classify the task scope:
   - `single_component`
   - `cross_component`
   - `architecture_rule`
   - `docs_only`
3. If the task is cross-component, define or update architectural boundaries before writing e2e tests.
4. Mark the task `active` and set top-level `active_task` to its id.
5. Recompute `vcr`.
6. Turn each `done_behavior` claim into tests.
7. Turn each durable architecture rule into an executable check.
8. Write failing tests first.
9. Watch them fail for the expected reason.
10. Implement the minimum code to pass.
11. Run the narrow test.
12. For cross-component changes, run the required e2e/full-pipeline test.
13. Run `make check`.

## Phase 2 — Clock-out

Before claiming completion:

1. Run the task's declared verification command through `scripts/run_with_signals.py` when possible, or capture equivalent runtime signals manually.
2. Capture timestamp and process exit code.
3. If exit code is 0, update `TASKS.json`:
   - `state: "verified"`
   - `verification.status: "passing"`
   - non-empty `verification.evidence`
   - ISO-8601 `verification.last_run_at`
   - `verification.signals.exit_code: 0`
4. Set top-level `active_task: null`.
5. Recompute `vcr`.
6. Update `PROGRESS.md`.
7. Run immediate cleanup for artifacts created during the session.
8. Update `QUALITY.md` if module quality, test stability, or cleanup priority changed.
9. Complete the Session Exit Checklist:
   - canonical gate passes (`make check`)
   - narrow tests/build command for the touched area passed, if separate from `make check`
   - feature/task state updated in `TASKS.json` and `PROGRESS.md`
   - no debug code, temporary breakpoints, scratch files, or stale TODOs remain
   - documented startup path still works or is explicitly unchanged
10. Run final `make check` after cleanup/checklist/quality updates.
11. Commit only the atomic scope.

---

# 4. Task ledger model

`TASKS.json` is the canonical work-state database.

## Task states

Allowed task states:

- `planned`: not activated yet; does not count against VCR
- `active`: currently being worked
- `blocked`: suspended record that cannot proceed due to an external blocker; excluded from the active lane and VCR denominator until reactivated or verified
- `verified`: completed with runtime evidence

Allowed verification statuses:

- `not_run`
- `passing`
- `failing`
- `blocked`

## VCR: Verified Completion Rate

```text
VCR = verified / (active + verified)
```

Where:

```text
activated = tasks where state is "active" or "verified"
verified = activated tasks that satisfy verified-state rules
```

Store `vcr` at full float precision or rounded to three decimals: the validator accepts any declared value within ±0.0005 of the computed ratio (so `0.667` passes when the ratio is 2/3) and prints the full-precision expected value when the declared value does not match.

Operational rule:

```text
If VCR < 1.0, finish, verify, or block the current active task before activating another one.
```

This prevents agents from opening multiple loose threads and then narrating progress without closing anything.

Blocking the current task suspends it: a blocked task is excluded from the active lane and VCR denominator. A different task may become active while the blocked record remains in the ledger, but there may still be at most one `state="active"` task at a time. Reactivate blocked work by moving it back to `active`, or re-plan it to `planned` with `verification.status="not_run"`.

## Runtime signal metadata

Runtime signals can be summarized into each verified task:

```json
"verification": {
  "command": "python scripts/run_with_signals.py --task-id F001 --kind verification -- make check",
  "status": "passing",
  "evidence": "Runtime signal collected trace_id=... span_id=...; make check passed.",
  "last_run_at": "2026-06-10T03:30:00Z",
  "signals": {
    "exit_code": 0,
    "trace_id": "32 hex chars",
    "span_id": "16 hex chars",
    "duration_ms": 1234
  }
}
```

Minimum validator requirement remains `signals.exit_code == 0`; trace/span/duration fields are recommended for handoff and evaluator scoring.

## Cross-component task metadata

For tasks that cross architectural boundaries, add explicit metadata so the validator and future agents know e2e verification is required.

```json
{
  "id": "F010",
  "title": "Export file from UI",
  "state": "planned",
  "change_scope": "cross_component",
  "components_touched": ["renderer", "preload", "export_service"],
  "boundaries_touched": ["renderer_to_preload_file_ops"],
  "e2e_required": true,
  "done_behavior": "Clicking Export writes the chosen file through the preload bridge, updates progress, handles cancellation, and reports errors without direct renderer filesystem access.",
  "verification": {
    "command": ".venv/bin/python -m pytest -q tests/test_export_service.py tests/e2e/test_export_flow.py && make validate-architecture && make check",
    "status": "not_run",
    "evidence": "",
    "last_run_at": null
  }
}
```

Recommended `change_scope` values:

- `single_component`: one module/service boundary; narrow tests plus `make check` are usually enough
- `cross_component`: crosses a boundary; e2e/full-pipeline verification is required
- `architecture_rule`: changes harness boundaries; requires executable architecture checks and contract tests
- `docs_only`: no behavior change; still requires doc lint/diff check and `make check`

## Three-layer termination validation

A task may count as verified only after all three layers pass.

### Layer 1 — Structural

```json
"state": "verified",
"verification": {
  "status": "passing"
}
```

### Layer 2 — Evidence

```json
"verification": {
  "evidence": "Specific command output summary and behavior proof.",
  "last_run_at": "2026-06-09T21:05:00Z"
}
```

`last_run_at` must be ISO-8601 and must represent when the verification command actually ran.

### Layer 3 — Runtime signal

```json
"verification": {
  "signals": {
    "exit_code": 0
  }
}
```

`exit_code` must be integer `0`. Boolean `true`, string `"0"`, missing signals, and non-zero codes are invalid.

---

# 5. Quality document model

`QUALITY.md` is the active quality ledger for modules and cleanup priorities. It is not a one-time assessment; it should change as verification, understandability, stability, boundaries, and conventions improve or regress.

Minimum shape:

```markdown
# Quality Register

Last assessed: YYYY-MM-DDTHH:MM:SSZ

## Quality Dimensions

- Verification passing state
- Agent understandability
- Test stability
- Architecture-boundary compliance
- Code-convention compliance
- Known cleanup or repair action

## Module Scores

### user-auth

Score: A

- Verification passing state: Passing
- Agent understandability: Clear
- Test stability: Stable
- Architecture-boundary compliance: Compliant
- Code-convention compliance: Followed
- Known cleanup or repair action: None

### payments

Score: C

- Verification passing state: Partial — callback flow untested
- Agent understandability: Difficult — logic split across unrelated files
- Test stability: Unstable — two flaky tests
- Architecture-boundary compliance: Violations present
- Code-convention compliance: Partially followed
- Known cleanup or repair action: Add callback e2e test and isolate provider adapter

## Repair Queue

- [ ] Add callback e2e test for payments.
- [ ] Isolate provider adapter boundary.
```

Rules:

- New sessions read `QUALITY.md` during initialization.
- When cleanup or quality-repair work is in scope, fix the lowest-scoring module first; normal feature selection follows the active sprint scope and `TASKS.json` order.
- Periodic cleanup updates quality scores after full-system scans and benchmark runs.
- Immediate cleanup updates affected module scores when a session changes quality state.

---

# 6. New feature workflow

For each new feature:

## Step 0 — Classify scope and define boundaries

Before tests, classify the task:

```text
single_component | cross_component | architecture_rule | docs_only
```

If it is `cross_component`, define boundaries before writing e2e tests:

```markdown
## Boundary: renderer_to_preload_file_ops

- Renderer may call `window.api.exportFile(payload)`.
- Renderer must not import `fs`, `path`, or direct Node filesystem APIs.
- Preload owns filesystem access and normalizes paths.
- Export service reports progress events through the preload bridge.
- E2E proof: clicking Export writes a file, updates progress, and handles invalid paths.
```

Then convert those rules into executable checks, for example:

```text
"Renderer must not import fs/path"
  -> scripts/validate_architecture.py rejects src/renderer/** imports from fs/path

"Export flow must use preload bridge"
  -> tests/e2e/test_export_flow.py clicks Export and asserts bridge-mediated file write
```

## Step 1 — Define completion behavior

Write `done_behavior` as observable behavior, not implementation activity.

Bad:

```text
Added the auth module.
```

Good:

```text
Users can create an account with a unique email, invalid emails are rejected, duplicate emails produce a deterministic error, and the login endpoint returns a token for valid credentials.
```

## Step 2 — Generate termination validations

Convert every falsifiable claim in `done_behavior` into executable tests.

```text
done_behavior claim -> test
```

Example:

```text
"invalid emails are rejected"
  -> test_signup_rejects_invalid_email()

"duplicate emails produce a deterministic error"
  -> test_signup_rejects_duplicate_email_with_stable_error()

"login endpoint returns a token for valid credentials"
  -> test_login_returns_token_for_valid_credentials()
```

## Step 3 — Declare the verification command

Use the narrowest useful tests plus the full gate.

For cross-component work, the command must include the relevant e2e/full-pipeline scenario and architecture validation.

```json
"verification": {
  "command": ".venv/bin/python -m pytest -q tests/test_auth.py && make check",
  "status": "not_run",
  "evidence": "",
  "last_run_at": null
}
```

Do not add `signals.exit_code` before the command has actually succeeded.

Cross-component example:

```json
"verification": {
  "command": ".venv/bin/python -m pytest -q tests/test_export_service.py tests/e2e/test_export_flow.py && make validate-architecture && make check",
  "status": "not_run",
  "evidence": "",
  "last_run_at": null
}
```

## Step 4 — Use TDD

```bash
# RED
.venv/bin/python -m pytest -q tests/test_auth.py

# implement minimally

# GREEN
.venv/bin/python -m pytest -q tests/test_auth.py

# full gate
make check
```

## Step 5 — Capture runtime signal

Preferred: run the declared command through the signal collector so the runtime evidence is recorded automatically:

```bash
python scripts/run_with_signals.py --task-id F00X --kind verification -- bash -lc '.venv/bin/python -m pytest -q tests/test_auth.py && make check'
```

Manual fallback when the wrapper is unavailable:

```bash
(.venv/bin/python -m pytest -q tests/test_auth.py && make check)
code=$?
date -Iseconds
echo "exit_code=$code"
exit "$code"
```

Only if `exit_code=0`, mark the task verified.

## Step 6 — Promote repeated review feedback

When review finds a repeated or architectural class of issue, do not leave it as a comment. Promote it:

```text
review finding -> rule in ARCHITECTURE.md/CONSTRAINTS.md -> executable check -> agent-oriented failure message -> contract/e2e test
```

Example:

```text
Review finding: renderer accessed fs directly again.
Rule: renderer must not import fs/path.
Check: scripts/validate_architecture.py scans src/renderer/** imports.
Error: tells agent the exact import, the target preload file, and rerun command.
Test: tests/test_architecture_rules.py proves the checker rejects the violation.
```

---

# 7. Architecture boundaries, e2e gates, observability, and agent-oriented errors

## Runtime signal collection template

Use a command wrapper instead of asking agents to manually copy terminal output.

```bash
python scripts/run_with_signals.py --task-id F001 --kind verification -- bash -lc 'pytest -q tests/test_feature.py && make check'
```

Agent-oriented failure output:

```text
runtime signal: .harness/runs/F001/<run>.json
trace_id=<trace> span_id=<span> exit_code=1
fix: inspect the failing command output and runtime signal JSON, then repair the failing path before marking verified
rerun: scripts/run_with_signals.py --task-id F001 --kind verification -- <same command>
```

## `SPRINTS.json`

Sprint contract template.

```json
{
  "schema_version": 1,
  "active_sprint": "S001",
  "sprints": [
    {
      "id": "S001",
      "title": "Harness observability baseline",
      "state": "active",
      "goal": "Make completion evidence observable and evaluable.",
      "task_ids": ["F001"],
      "required_gates": ["make check"],
      "evaluator_rubric_id": "default_harness_rubric",
      "observability": {
        "runtime_signal_required": true,
        "otel_semconv": "OBSERVABILITY.md"
      }
    }
  ]
}
```

## `EVALUATOR.json`

Evaluator rubric template.

```json
{
  "schema_version": 1,
  "active_rubric": "default_harness_rubric",
  "rubrics": [
    {
      "id": "default_harness_rubric",
      "title": "Default harness evaluator rubric",
      "pass_threshold": 4.0,
      "dimensions": [
        {"id": "behavior_correctness", "weight": 30, "pass_threshold": 4, "criteria": ["done_behavior is exercised"], "blockers": []},
        {"id": "verification_evidence", "weight": 25, "pass_threshold": 4, "criteria": ["runtime signal and TASKS evidence exist"], "blockers": []},
        {"id": "architecture_boundaries", "weight": 15, "pass_threshold": 4, "criteria": ["boundaries/e2e are respected"], "blockers": []},
        {"id": "observability", "weight": 20, "pass_threshold": 4, "criteria": ["OpenTelemetry trace/span attributes exist"], "blockers": []},
        {"id": "privacy_security", "weight": 10, "pass_threshold": 4, "criteria": ["no secrets/private fixtures in traces"], "blockers": []}
      ]
    }
  ]
}
```

Scoring semantics: each dimension is scored 1-5 by the evaluator; the rubric score is the weight-weighted average of the dimension scores, and `weight` values must sum to 100. A rubric passes only when the weighted average meets the rubric-level `pass_threshold`, every dimension meets its own `pass_threshold`, and no `blockers` condition fires. `scripts/validate_evaluator.py` enforces this shape so the semantics stay computable.

## `OBSERVABILITY.md`

```markdown
# Observability

Runtime verification must leave enough signal for a later agent to understand what actually ran. Prefer `scripts/run_with_signals.py` for task verification commands.

## Required runtime signal fields

- `task_id`
- `kind`
- `command`
- `started_at` and `ended_at` as UTC ISO-8601 timestamps
- `duration_ms`
- `exit_code`
- `trace_id`
- `span_id`

## Storage

Generated runtime signal JSON goes under `.harness/runs/<task-id>/` and is ignored by default. Summarize the successful verification in `TASKS.json`; promote raw run files only when they are intentionally useful review artifacts.

## OpenTelemetry alignment

Use `.harness/otel_attributes.json` to keep local attribute names stable.
```

## `.harness/otel_attributes.json`

```json
{
  "schema_version": 1,
  "attributes": {
    "service.name": "<repo-name>",
    "harness.task_id": "Task id from TASKS.json",
    "harness.run.kind": "verification|test|e2e|benchmark",
    "harness.command": "Wrapped command string",
    "harness.exit_code": "Process exit code from the wrapped command"
  }
}
```

## `.gitignore`

```gitignore
.harness/runs/
```

## Boundary definition template

Create or update `ARCHITECTURE.md` before writing e2e tests for cross-component behavior.

````markdown
# Architecture

## Boundary: <boundary_id>

**Components:** `<component_a>` -> `<component_b>`

**Allowed direction:** `<component_a>` may call `<public_interface>` only.

**Forbidden:** `<component_a>` must not import/call `<forbidden_dependency>`.

**Contract:**

- input shape:
- output shape:
- error shape:
- state/resource lifecycle:

**Executable checks:**

- `make validate-architecture` enforces `<rule>`.
- `tests/e2e/<scenario>.py` proves `<real user/system flow>`.

**Agent-oriented failure text:**

```text
<what failed>: <file/path> violates <boundary_id>.
Why: <short reason>.
Fix: <specific edit>.
Rerun: <command>.
```
````

## Architecture-rule checklist

For every architectural rule, decide whether it can be automated:

- forbidden imports -> static scanner
- forbidden dependency direction -> import graph check
- API contract shape -> schema/contract test
- persistence migration ordering -> integration/e2e migration test
- UI-to-backend flow -> e2e test
- resource lifecycle -> e2e or stress/regression test
- security boundary -> static rule plus runtime/e2e scenario

If a rule cannot be automated yet, record it as manual review debt in `PROGRESS.md` and add a `TASKS.json` item to automate it later.

## Agent-oriented error format

Use this shape for validators, tests, and custom scripts:

```text
<short failure>
why: <architectural or behavioral invariant>
fix: <concrete file/API/change>
rerun: <exact command>
```

Example:

```text
renderer_to_preload_file_ops violation: src/renderer/export.ts imports `fs`.
why: renderer code must not access filesystem APIs directly; file operations must cross the preload bridge.
fix: move filesystem code to src/preload/file-ops.ts, expose it as window.api.exportFile(payload), and call that API from src/renderer/export.ts.
rerun: make validate-architecture && make e2e
```

## E2E prerequisite rule

A task requires e2e/full-pipeline verification when it touches any of these:

- UI plus service/backend
- API plus database/persistence
- migration plus runtime reader
- CLI plus generated artifact
- background job plus scheduler/queue
- auth/permissions across components
- external integration boundary
- resource lifecycle across components
- public contract consumed by another package/service

For those tasks, `verification.command` must include the relevant e2e command before `make check` or as part of `make check`.

## Review feedback promotion process

Use this loop after every review or failed QA pass:

1. Identify whether the issue is a one-off defect or a recurring class.
2. If recurring, write the durable rule in `ARCHITECTURE.md` or `CONSTRAINTS.md`.
3. Add or update an executable check.
4. Make the error message agent-oriented with `fix:` and `rerun:` lines.
5. Add a regression/contract test proving the checker catches the issue.
6. Add or update an e2e test if the issue crossed components.
7. Record the decision in `DECISIONS.md` if it changes project law.

---

# 8. Starter templates

## `AGENTS.md`

````markdown
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
2. Classify the task scope; for cross-component work, define architectural boundaries before writing e2e tests.
3. Activate exactly one task, set `active_task`, recompute VCR, and follow the Work rules below.

### Phase 2 — Clock-out

1. Update `TASKS.json` with task state, verification status, evidence, run timestamp, runtime signal, and VCR.
2. Update `PROGRESS.md`.
3. Run immediate cleanup for temporary artifacts created during the session.
4. Update `QUALITY.md` if module quality, stability, boundaries, or cleanup priority changed.
5. Complete the Session Exit Checklist.
6. Run final `make check` after cleanup/checklist/quality updates.
7. Ensure every completed atomic unit is committed; do not batch unrelated completed work together.

## Session Exit Checklist

Session completion requires both task verification and a clean state check. At the end of every session, confirm:

- [ ] Canonical gate passes: `make check`.
- [ ] Touched-area build/test command passes when the repo defines one separately from `make check` (for example `make test`, `pytest`, `cargo test`, `go test ./...`, or a service-specific smoke test).
- [ ] Feature/task state updated (`TASKS.json`, and `PROGRESS.md` when project state changed).
- [ ] Immediate cleanup completed for temporary artifacts created this session.
- [ ] `QUALITY.md` updated if module quality, stability, boundaries, or cleanup priority changed.
- [ ] No debug code remains (`print`/`console.log`, `debugger`/breakpoints, temporary TODOs, scratch artifacts).
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
- For cross-component changes, define architectural boundaries before writing e2e tests.
- For cross-component changes, passing the declared e2e/full-pipeline test is a prerequisite for completion.
- Turn architectural rules into executable checks whenever possible.
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
5. Read nearest module/service `CONSTRAINTS.md`, if present.
6. Read nearest module/service `ARCHITECTURE.md`, if present.
7. Read nearest module/service `PROGRESS.md`, if present.
8. Inspect nearby tests for executable specifications.

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
- Test policy: `tests/README.md` when present, plus existing test files

## Canonical check command

Use:

```bash
make check
```

## Operating rule

Keep knowledge near the code it governs. Do not duplicate long explanations across files. A change is complete only when code, tests, and relevant nearby docs are updated together.

Do not store active roadmap, detailed architecture, private data, or secrets in this file.
````

## `CLAUDE.md`

```markdown
# Claude Code Instructions

This repository uses `AGENTS.md` as the canonical agent operating contract.
This file is only the Claude Code entrypoint into those repo docs; do not duplicate roadmap, architecture, or active task state here.

Before editing anything:

1. Read `AGENTS.md`.
2. Follow the read order and session lifecycle in `AGENTS.md`.
3. Never read, print, summarize, move, or commit `.env*` files or other secret material.
4. Use `make initialize` for cold-start verification when starting or resuming repo work.
5. Use `make check` as the canonical final consistency gate.

Project status lives in `PROGRESS.md`; module health and cleanup priorities live in `QUALITY.md`.
```

## `CONSTRAINTS.md`

```markdown
# Global Constraints

These constraints apply to all work in this repository. Domain-specific constraints belong closer to the code they govern.

## Knowledge placement

- Keep durable knowledge near the code it describes.
- Keep this root file limited to global constraints.
- Put roadmap/status in `PROGRESS.md`, not `AGENTS.md` or this file.
- Put module design in nearest `ARCHITECTURE.md`.
- Put module status/TODOs in nearest `PROGRESS.md`.
- Put module-specific constraints in nearest `CONSTRAINTS.md` when needed.
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
- Cross-component tasks must define architectural boundaries before e2e tests are written.
- Cross-component tasks must pass the declared e2e/full-pipeline test before completion.
- Architectural rules must become executable checks whenever possible.
- `scripts/validate_tasks.py` and other validators must reject premature victory and print actionable `fix:` guidance for each validation failure.
- Error messages must be designed for agents: include what failed, why it matters, concrete fix steps, and the rerun command.
- Repeated review comments must be promoted into automated checks and regression/e2e tests.
- Session exit must run immediate cleanup, update `QUALITY.md` when module health changes, then run final `make check`; cleanup after final verification invalidates the verification and requires a rerun.
- Cleanup operations must be idempotent; periodic cleanup belongs in explicit cleanup tasks, not hidden side work.
- Every task in the feature list must appear in `TASKS.json` with `done_behavior` and `verification.command`.
- VCR-activated tasks are tasks in `active` or `verified` state; `planned` and `blocked` are excluded from the VCR denominator.
- VCR is verified tasks divided by the sum of active plus verified tasks.
- Do not activate a second active task. If current work cannot proceed, record it as `blocked` with a blocker reason; blocked tasks are suspended records and do not occupy the active lane.
- Run the narrowest useful test first after a behavior change.
- Run the canonical full verification before claiming completion.
- If verification cannot run, record the blocker explicitly.

## Privacy and secrets

- Do not commit API keys, tokens, credentials, private user data, or private customer data.
- Redact secrets as `[REDACTED]` in docs, logs, fixtures, and examples.
- Use synthetic fixtures for tests unless real data is explicitly sanitized and approved.
```

## `DECISIONS.md`

```markdown
# Design Decisions

Durable project decisions that future agents should preserve unless explicitly superseded.
Keep each entry concise: decision, reason, rejected alternative, and active constraint.

## YYYY-MM-DD: Commit after each atomic unit of completed work

- Reason: Commits are free, automatically versioned state snapshots. They make recovery, review, bisection, and cold starts safer.
- Rejected alternative: Batch unrelated completed work into larger commits.
- Constraint: Commit only completed work in the current atomic scope; do not sweep unrelated dirty work into the commit. Commit messages must explain what changed and why.

## YYYY-MM-DD: Use `make check` as the canonical quality gate

- Reason: Agents need one stable command that checks formatting, lint, types, data syntax, task state, and tests before claiming consistency.
- Rejected alternative: Ad hoc test-only verification.
- Constraint: `make check` must run all required repo gates and must include `scripts/validate_tasks.py`.

## YYYY-MM-DD: Treat repo initialization as callable Phase 0

- Reason: Agents and users need one named preflight that establishes live repo truth before choosing or editing an atomic unit.
- Rejected alternative: Ambiguous cold-start prose without a shell target.
- Constraint: `make initialize` (`make init` alias) is read-only: it reports live branch/head state and runs `make check`.

## YYYY-MM-DD: Treat clean session exit as part of completion

- Reason: Future agents inherit artifacts, stale ledgers, and quality drift when cleanup is skipped after behavior verification.
- Rejected alternative: Run tests, claim completion, and leave cleanup/quality updates for an unspecified later pass.
- Constraint: Clock-out order is immediate cleanup, `QUALITY.md` upkeep, Session Exit Checklist, final `make check`, then atomic commit/handoff.

## YYYY-MM-DD: Define completion by verified behavior evidence

- Reason: Agents need a durable, machine-readable task ledger that states what behavior counts as done and what command proved it.
- Rejected alternative: Treat code or docs being written as completion, or keep task state only in prose checklists.
- Constraint: `TASKS.json` is the canonical feature/task state file. Each task must include `done_behavior` and `verification.command`. `make check` must run `scripts/validate_tasks.py`.

## YYYY-MM-DD: Treat blocked tasks as suspended records

- Reason: Blocked work should remain visible without occupying the single active-task lane or distorting Verified Completion Rate.
- Rejected alternative: Count blocked tasks in the VCR denominator, which prevents pivots and makes VCR report suspended records as current work.
- Constraint: VCR denominator includes only `active` and `verified` tasks. `blocked` tasks require a blocker reason/status but are excluded from VCR until reactivated or verified.

## YYYY-MM-DD: Require three-layer termination validation before verified state

- Reason: Agents can declare victory from code-level confidence or prose evidence even when no runtime signal proves the declared verification command succeeded.
- Rejected alternative: Trust `verification.status="passing"` and free-form evidence text without a machine-readable signal from the actual run.
- Constraint: A task may count as verified only when it clears structural status, evidence, and runtime signal `verification.signals.exit_code == 0`.

## YYYY-MM-DD: Require e2e/full-pipeline verification for cross-component changes

- Reason: Unit tests miss interface mismatches, state propagation errors, resource lifecycle issues, and environment dependencies that only appear when components run together.
- Rejected alternative: Allow cross-component tasks to complete after isolated unit tests only.
- Constraint: Cross-component tasks must define boundaries first and include the relevant e2e/full-pipeline command in `verification.command` before they can be marked verified.

## YYYY-MM-DD: Design harness errors for agent self-correction

- Reason: Agents can repair failures faster when validators provide concrete fix steps and rerun commands.
- Rejected alternative: Human-oriented diagnostics that only say what failed.
- Constraint: Custom validators and architecture checks must emit actionable `fix:` guidance, and preferably `rerun:` guidance, for each failure.

## YYYY-MM-DD: Promote recurring review feedback into executable checks

- Reason: Reviewers should not repeatedly catch the same issue by hand.
- Rejected alternative: Keep recurring review comments as tribal knowledge or prose-only guidance.
- Constraint: Repeated review findings must become architecture rules, validator checks, regression tests, or e2e scenarios.
```

## `PROGRESS.md`

````markdown
# Project Progress

Root `PROGRESS.md` is the operational cockpit for this repo: current truth only. Detailed agent lifecycle rules live in `AGENTS.md`; durable decisions live in `DECISIONS.md`; task evidence lives in `TASKS.json`; module health and cleanup priorities live in `QUALITY.md`.

## Current State

- Consistency check: `make check` is the canonical gate.
- Callable initialization phase: `make initialize` (`make init` alias) prints live branch/head state and runs `make check`; canonical Phase 0 steps live in `AGENTS.md`.
- Machine-readable task state: `TASKS.json` records active task, task state, done behavior, verification command, evidence, run timestamp, runtime exit signal, and VCR.
- VCR status: `1.000` or current value; denominator includes only `active` and `verified` tasks.
- Quality register: `QUALITY.md` tracks module scores and repair queue.
- `make check` status: passing/failing/blocked.
- Last recorded `make check` result: summarize real output here.
- Privacy checkpoint: tests use synthetic fixtures; secrets/private data stay out of git.
- Safe checkpoint: no task is intentionally half-edited / or name active task.

Before editing, committing, or delegating, run:

```bash
git status --short
```

Do not trust stale status snapshots in docs; inspect the live working tree.

## Completed

- [x] Add completed durable milestones here.

## In Progress

- [ ] None intentionally active at this checkpoint.

`In Progress` means active WIP right now. Ordered follow-up work belongs in `TASKS.json`, not this prose file.

## Known Issues

- Add known repo-level issues here.

## Next Steps

See `TASKS.json` for canonical planned work and verification commands.

Current planned sequence:

1. `F001` — First planned feature.
2. `F002` — Second planned feature.

## Cold Start

Canonical Phase 0 initialization lives in `AGENTS.md`. Use `make initialize` (`make init` alias) to establish live repo truth, then report branch/status/HEAD, verification result, VCR, active task id, active sprint, evaluator rubric, and the next atomic unit.
````

## `QUALITY.md`

```markdown
# Quality Register

Last assessed: YYYY-MM-DDTHH:MM:SSZ

`QUALITY.md` is the active quality register for modules and cleanup priorities. It is not a one-time audit; update it when verification, understandability, stability, boundaries, conventions, or repair priorities change.

## Quality Dimensions

- Verification passing state: whether the module's declared checks pass now.
- Agent understandability: whether a cold-start agent can locate the source of truth and safe edit points.
- Test stability: whether tests are deterministic, scoped, and representative.
- Architecture-boundary compliance: whether module dependencies and responsibilities follow `ARCHITECTURE.md` and executable boundary checks.
- Code-convention compliance: whether formatting, typing, linting, naming, and repo idioms are followed.
- Known cleanup or repair action: the next concrete action that would improve the module.

## Module Scores

### core

Score: B

- Verification passing state: Passing under the latest recorded `make check`.
- Agent understandability: Mostly clear; main flows documented, edge cases sparse.
- Test stability: Stable.
- Architecture-boundary compliance: Compliant.
- Code-convention compliance: Followed.
- Known cleanup or repair action: Add one e2e test for the highest-risk flow.

### legacy-adapter

Score: C

- Verification passing state: Partial — smoke test only.
- Agent understandability: Difficult — mixed responsibilities.
- Test stability: Unknown.
- Architecture-boundary compliance: Needs review.
- Code-convention compliance: Partially followed.
- Known cleanup or repair action: Isolate adapter boundary and add regression tests.

## Repair Queue

- [ ] Convert the lowest-scoring module's top repair action into a scoped task in `TASKS.json` before starting quality-repair work.
- [ ] Promote recurring review feedback into an executable check or regression test.
```

## `TASKS.json`

```json
{
  "schema_version": 1,
  "active_task": null,
  "vcr": 1.0,
  "policy": "Done means behavior verification passes, not merely that code or docs were written. VCR denominator includes tasks in active or verified state only; planned and blocked are excluded. VCR = verified / (active + verified), where verified requires state='verified', verification.status='passing', and verification.signals.exit_code=0. Do not activate a second active task. Blocked tasks are suspended records that may coexist with a different active task.",
  "tasks": [
    {
      "id": "F001",
      "title": "First feature",
      "state": "planned",
      "done_behavior": "Observable behavior that proves the feature is done.",
      "verification": {
        "command": ".venv/bin/python -m pytest -q tests/test_first_feature.py && make check",
        "status": "not_run",
        "evidence": "",
        "last_run_at": null
      }
    }
  ]
}
```

Verified task shape:

```json
{
  "id": "F001",
  "title": "First feature",
  "state": "verified",
  "done_behavior": "Observable behavior that proves the feature is done.",
  "verification": {
    "command": ".venv/bin/python -m pytest -q tests/test_first_feature.py && make check",
    "status": "passing",
    "evidence": "RED: tests failed because the feature was missing. GREEN: feature tests passed and make check passed with task validation VCR=1.000.",
    "last_run_at": "2026-06-09T21:05:00Z",
    "signals": {
      "exit_code": 0
    }
  }
}
```

## `Makefile`

Generic Makefile starter. Adapt commands to your stack. Keep the target names stable.

```makefile
PYTHON ?= .venv/bin/python
PYTEST ?= $(PYTHON) -m pytest
RUFF ?= $(PYTHON) -m ruff
MYPY ?= $(PYTHON) -m mypy
JSON_VALIDATE ?= $(PYTHON) scripts/validate_json.py
TASKS_VALIDATE ?= $(PYTHON) scripts/validate_tasks.py
SPRINTS_VALIDATE ?= $(PYTHON) scripts/validate_sprints.py
EVALUATOR_VALIDATE ?= $(PYTHON) scripts/validate_evaluator.py
ARCH_VALIDATE ?= $(PYTHON) scripts/validate_architecture.py
RUN_WITH_SIGNALS ?= $(PYTHON) scripts/run_with_signals.py

.PHONY: init initialize check test e2e coverage format format-check lint typecheck validate-json validate-tasks validate-sprints validate-evaluator validate-architecture record-signal

init: initialize

initialize:
	git status --short --branch
	git --no-pager log -1 --decorate --oneline || true
	$(MAKE) check

check: format-check lint typecheck validate-json validate-tasks validate-sprints validate-evaluator validate-architecture coverage

test:
	$(PYTEST) -q

e2e:
	$(PYTEST) -q tests/e2e

coverage:
	$(PYTEST) --cov=<your_package> --cov-report=term-missing -q

format:
	$(RUFF) format .

format-check:
	$(RUFF) format --check .

lint:
	$(RUFF) check .

typecheck:
	$(MYPY) src

validate-json:
	$(JSON_VALIDATE)

validate-tasks:
	$(TASKS_VALIDATE)

validate-sprints:
	$(SPRINTS_VALIDATE)

validate-evaluator:
	$(EVALUATOR_VALIDATE)

record-signal:
	@echo "Usage: $(RUN_WITH_SIGNALS) --task-id FNN --kind verification -- <command>"

validate-architecture:
	@if [ -f scripts/validate_architecture.py ]; then \
		$(ARCH_VALIDATE); \
	else \
		echo "No architecture validator configured."; \
	fi
```

For a non-Python repo, keep the same target names but swap implementations to that stack's native commands. `check` remains the canonical aggregate gate:

```makefile
check: format-check lint typecheck validate-json validate-tasks validate-sprints validate-evaluator validate-architecture test
format-check:
	@echo "run this repo's formatter in check mode"
lint:
	@echo "run this repo's linter"
typecheck:
	@echo "run this repo's type checker"
test:
	@echo "run this repo's test command"
```

---

# 9. Generic harness scripts

Assume Python >=3.11 for these starter scripts. If a repo must support older Python, adapt union-type syntax and timestamp parsing before copying the snippets.

## `scripts/run_with_signals.py`

The runtime signal collector. It runs the wrapped command unchanged, writes a runtime signal JSON under `.harness/runs/<task-id>/`, prints the signal path plus trace/span ids, and exits with the wrapped command's exit code so it can be chained inside `verification.command`.

```python
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


def main(argv: list[str] | None = None) -> int:
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
        print(f"rerun: scripts/run_with_signals.py --task-id {args.task_id} --kind {args.kind} -- <corrected command>", file=sys.stderr)
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
    signal_path.write_text(json.dumps(signal, indent=2) + "\n", encoding="utf-8")

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
```

## `scripts/validate_json.py`

```python
from __future__ import annotations

import json
import sys
from pathlib import Path

DEFAULT_ROOTS = ("TASKS.json", "SPRINTS.json", "EVALUATOR.json", ".harness", "src", "tests")


def iter_json_files(paths: list[Path]) -> list[Path]:
    files: list[Path] = []
    for path in paths:
        if not path.exists():
            continue
        if path.is_file():
            if path.suffix == ".json":
                files.append(path)
            continue
        files.extend(sorted(path.rglob("*.json")))
    return sorted(set(files))


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    roots = [Path(arg) for arg in args] if args else [Path(root) for root in DEFAULT_ROOTS]
    failures: list[str] = []

    files = iter_json_files(roots)
    for path in files:
        try:
            json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            failures.append(f"{path}: line {exc.lineno} column {exc.colno}: {exc.msg}")

    if failures:
        print("Invalid JSON files:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure}", file=sys.stderr)
        print("fix: repair the listed JSON syntax errors or remove stale generated JSON from checked paths", file=sys.stderr)
        print("rerun: make validate-json", file=sys.stderr)
        return 1

    print(f"validated {len(files)} JSON files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```


## `.harness/architecture_rules.json`

Use a small machine-readable rule manifest for architecture checks. Start with import/dependency rules; add richer checks only when the repo needs them.

```json
{
  "rules": [
    {
      "id": "renderer_to_preload_file_ops",
      "type": "forbidden_import",
      "paths": ["src/renderer/**/*.ts", "src/renderer/**/*.tsx"],
      "modules": ["fs", "node:fs", "path", "node:path"],
      "why": "Renderer code must not access filesystem APIs directly; file operations must cross the preload bridge.",
      "fix": "Move filesystem code to src/preload/file-ops.ts, expose it as window.api.exportFile(payload), and call that API from renderer code.",
      "rerun": "make validate-architecture && make e2e"
    }
  ]
}
```

## `scripts/validate_architecture.py`

This is intentionally small and repo-adaptable. It demonstrates the required pattern: executable boundary rule plus agent-oriented error messages.

```python
from __future__ import annotations

import ast
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RULES_FILE = Path(".harness/architecture_rules.json")
DEFAULT_RERUN = "make validate-architecture"


@dataclass(frozen=True)
class Failure:
    rule_id: str
    path: Path
    message: str
    why: str
    fix: str
    rerun: str = DEFAULT_RERUN


def _load_rules(path: Path = RULES_FILE) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    if not isinstance(rules, list):
        raise ValueError(".harness/architecture_rules.json field `rules` must be a list")
    return [rule for rule in rules if isinstance(rule, dict)]


def _iter_rule_files(patterns: list[str]) -> list[Path]:
    files: set[Path] = set()
    for pattern in patterns:
        files.update(Path().glob(pattern))
    return sorted(path for path in files if path.is_file())


def _python_imports(source: str) -> set[str]:
    imports: set[str] = set()
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


def _text_imports(source: str) -> set[str]:
    imports = set(re.findall(r"from\s+['\"]([^'\"]+)['\"]", source))
    imports.update(re.findall(r"import\s+[^'\"]*['\"]([^'\"]+)['\"]", source))
    imports.update(re.findall(r"require\(['\"]([^'\"]+)['\"]\)", source))
    return imports


def _imports_for(path: Path) -> set[str]:
    source = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".py":
        return _python_imports(source)
    return _text_imports(source)


def _check_forbidden_import(rule: dict[str, Any]) -> list[Failure]:
    rule_id = str(rule.get("id") or "unnamed_rule")
    patterns = [str(item) for item in rule.get("paths", [])]
    forbidden = {str(item) for item in rule.get("modules", [])}
    why = str(rule.get("why") or "This dependency violates an architectural boundary.")
    fix = str(rule.get("fix") or "Move the dependency behind the approved boundary/interface.")
    rerun = str(rule.get("rerun") or DEFAULT_RERUN)

    failures: list[Failure] = []
    for path in _iter_rule_files(patterns):
        imports = _imports_for(path)
        bad = sorted(module for module in forbidden if module in imports)
        for module in bad:
            failures.append(
                Failure(
                    rule_id=rule_id,
                    path=path,
                    message=f"{rule_id} violation: {path} imports `{module}`",
                    why=why,
                    fix=fix,
                    rerun=rerun,
                )
            )
    return failures


def validate(rules: list[dict[str, Any]]) -> list[Failure]:
    failures: list[Failure] = []
    for rule in rules:
        rule_type = rule.get("type")
        if rule_type == "forbidden_import":
            failures.extend(_check_forbidden_import(rule))
        else:
            failures.append(
                Failure(
                    rule_id=str(rule.get("id") or "unnamed_rule"),
                    path=RULES_FILE,
                    message=f"unsupported architecture rule type: {rule_type}",
                    why="Unknown rule types are ignored by agents unless the validator fails loudly.",
                    fix="Implement this rule type in scripts/validate_architecture.py or remove it from the manifest.",
                    rerun=DEFAULT_RERUN,
                )
            )
    return failures


def main() -> int:
    try:
        failures = validate(_load_rules())
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Invalid architecture rules: {exc}", file=sys.stderr)
        print("fix: repair .harness/architecture_rules.json or remove invalid rules", file=sys.stderr)
        print(f"rerun: {DEFAULT_RERUN}", file=sys.stderr)
        return 1

    if failures:
        print("Architecture validation failed:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure.message}", file=sys.stderr)
            print(f"    why: {failure.why}", file=sys.stderr)
            print(f"    fix: {failure.fix}", file=sys.stderr)
            print(f"    rerun: {failure.rerun}", file=sys.stderr)
        return 1

    print("architecture validation passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## `scripts/validate_tasks.py`

```python
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

ALLOWED_STATES = {"planned", "active", "blocked", "verified"}
VCR_ACTIVATED_STATES = {"active", "verified"}
ALLOWED_VERIFICATION_STATUSES = {"not_run", "passing", "failing", "blocked"}
VCR_ACTIVATED_STATES = {"active", "verified"}
ALLOWED_CHANGE_SCOPES = {"single_component", "cross_component", "architecture_rule", "docs_only"}
PLANNED_STATE = "planned"
VERIFIED_STATE = "verified"
GENERIC_FIX_HINT = "update this field to match the TASKS.json completion-evidence schema"


@dataclass(frozen=True)
class Failure:
    message: str
    hint: str = GENERIC_FIX_HINT


def _fail(message: str, hint: str = GENERIC_FIX_HINT) -> Failure:
    return Failure(message=message, hint=hint)


def _task_label(task: dict[str, Any], index: int) -> str:
    return str(task.get("id") or f"task[{index}]")


def _has_zero_exit_signal(verification: Any) -> bool:
    if not isinstance(verification, dict):
        return False
    signals = verification.get("signals")
    if not isinstance(signals, dict):
        return False
    exit_code = signals.get("exit_code")
    return isinstance(exit_code, int) and not isinstance(exit_code, bool) and exit_code == 0


def _is_verified(task: dict[str, Any]) -> bool:
    verification = task.get("verification", {})
    return (
        task.get("state") == VERIFIED_STATE
        and isinstance(verification, dict)
        and verification.get("status") == "passing"
        and _has_zero_exit_signal(verification)
    )


def _is_iso8601(value: Any) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    normalized = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        datetime.fromisoformat(normalized)
    except ValueError:
        return False
    return True


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def _command_mentions_e2e(command: str) -> bool:
    markers = ("e2e", "end-to-end", "full-pipeline", "full_pipeline")
    return any(marker in command for marker in markers)


def _task_requires_e2e(task: dict[str, Any]) -> bool:
    return task.get("change_scope") == "cross_component" or task.get("e2e_required") is True


def _validate_termination(task: dict[str, Any], label: str) -> list[Failure]:
    if task.get("state") != VERIFIED_STATE:
        return []

    failures: list[Failure] = []
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


def _validate_task(task: Any, index: int, seen_ids: set[str]) -> list[Failure]:
    failures: list[Failure] = []
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


def validate_ledger(data: Any) -> tuple[list[Failure], str]:
    failures: list[Failure] = []
    if not isinstance(data, dict):
        return [_fail("TASKS ledger must be a JSON object", "replace TASKS.json with a JSON object")], ""

    if data.get("schema_version") != 1:
        failures.append(_fail("schema_version must be 1", "set schema_version to 1"))

    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        failures.append(_fail("tasks must be a non-empty list", "add at least one task object to tasks"))
        return failures, ""

    seen_ids: set[str] = set()
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
    if not isinstance(declared_vcr, int | float) or not math.isclose(float(declared_vcr), computed_vcr, abs_tol=5e-4):
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


def main(argv: list[str] | None = None) -> int:
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
```

## `scripts/validate_sprints.py`

Validates `SPRINTS.json`: schema version, sprint shape, allowed sprint states (`planned`, `active`, `completed`), at most one active sprint, and a top-level `active_sprint` pointer that matches. When sibling `TASKS.json`/`EVALUATOR.json` files exist, it also cross-checks that `task_ids` and `evaluator_rubric_id` reference real entries.

```python
from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

ALLOWED_SPRINT_STATES = {"planned", "active", "completed"}
RERUN_HINT = "make validate-sprints"


@dataclass(frozen=True)
class Failure:
    message: str
    hint: str


def _fail(message: str, hint: str) -> Failure:
    return Failure(message=message, hint=hint)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_non_empty_string_list(value: Any) -> bool:
    return isinstance(value, list) and bool(value) and all(_is_non_empty_string(item) for item in value)


def _sibling_ids(path: Path, list_key: str) -> set[str] | None:
    """Collect ids from a sibling ledger; None skips the cross-check when the ledger is absent or unreadable."""
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    items = data.get(list_key) if isinstance(data, dict) else None
    if not isinstance(items, list):
        return None
    return {item["id"] for item in items if isinstance(item, dict) and _is_non_empty_string(item.get("id"))}


def _validate_sprint(
    sprint: Any,
    index: int,
    seen_ids: set[str],
    task_ids: set[str] | None,
    rubric_ids: set[str] | None,
) -> list[Failure]:
    if not isinstance(sprint, dict):
        return [_fail(f"sprint[{index}] must be an object", "replace this sprint entry with a JSON object")]

    failures: list[Failure] = []
    label = str(sprint.get("id") or f"sprint[{index}]")

    sprint_id = sprint.get("id")
    if not _is_non_empty_string(sprint_id):
        failures.append(_fail(f"{label}: id must be a non-empty string", "give the sprint a stable id like S001"))
    elif sprint_id in seen_ids:
        failures.append(_fail(f"{label}: id must be unique", "rename or remove the duplicate sprint id"))
    else:
        seen_ids.add(sprint_id)

    if not _is_non_empty_string(sprint.get("title")):
        failures.append(_fail(f"{label}: title must be a non-empty string", "add a concise sprint title"))

    if not _is_non_empty_string(sprint.get("goal")):
        failures.append(
            _fail(f"{label}: goal must be a non-empty string", "state the observable outcome this sprint must reach")
        )

    if sprint.get("state") not in ALLOWED_SPRINT_STATES:
        failures.append(
            _fail(
                f"{label}: state must be one of {sorted(ALLOWED_SPRINT_STATES)}",
                "use planned, active, or completed",
            )
        )

    task_ids_field = sprint.get("task_ids")
    if not _is_non_empty_string_list(task_ids_field):
        failures.append(
            _fail(
                f"{label}: task_ids must be a non-empty list of task ids",
                "list the TASKS.json ids that belong to this sprint",
            )
        )
    elif task_ids is not None:
        unknown = sorted(set(task_ids_field) - task_ids)
        if unknown:
            failures.append(
                _fail(
                    f"{label}: task_ids reference unknown tasks: {', '.join(unknown)}",
                    "add these tasks to TASKS.json or remove them from the sprint",
                )
            )

    if not _is_non_empty_string_list(sprint.get("required_gates")):
        failures.append(
            _fail(
                f"{label}: required_gates must be a non-empty list of commands",
                'declare the gates that must pass for this sprint, e.g. ["make check"]',
            )
        )

    rubric_id = sprint.get("evaluator_rubric_id")
    if not _is_non_empty_string(rubric_id):
        failures.append(
            _fail(
                f"{label}: evaluator_rubric_id must be a non-empty string",
                "reference a rubric id defined in EVALUATOR.json",
            )
        )
    elif rubric_ids is not None and rubric_id not in rubric_ids:
        failures.append(
            _fail(
                f"{label}: evaluator_rubric_id '{rubric_id}' is not defined in EVALUATOR.json",
                "add the rubric to EVALUATOR.json or reference an existing rubric id",
            )
        )

    observability = sprint.get("observability")
    if observability is not None and not isinstance(observability, dict):
        failures.append(
            _fail(
                f"{label}: observability must be an object when present",
                'use {"runtime_signal_required": true, "otel_semconv": "OBSERVABILITY.md"}',
            )
        )
    elif isinstance(observability, dict) and "runtime_signal_required" in observability:
        if not isinstance(observability["runtime_signal_required"], bool):
            failures.append(
                _fail(
                    f"{label}: observability.runtime_signal_required must be a boolean",
                    "set runtime_signal_required to true or false",
                )
            )

    return failures


def validate_contract(data: Any, task_ids: set[str] | None, rubric_ids: set[str] | None) -> tuple[list[Failure], str]:
    if not isinstance(data, dict):
        return [_fail("SPRINTS contract must be a JSON object", "replace SPRINTS.json with a JSON object")], ""

    failures: list[Failure] = []
    if data.get("schema_version") != 1:
        failures.append(_fail("schema_version must be 1", "set schema_version to 1"))

    sprints = data.get("sprints")
    if not isinstance(sprints, list) or not sprints:
        failures.append(_fail("sprints must be a non-empty list", "add at least one sprint object to sprints"))
        return failures, ""

    seen_ids: set[str] = set()
    for index, sprint in enumerate(sprints):
        failures.extend(_validate_sprint(sprint, index, seen_ids, task_ids, rubric_ids))

    valid_sprints = [sprint for sprint in sprints if isinstance(sprint, dict)]
    active_sprints = [sprint for sprint in valid_sprints if sprint.get("state") == "active"]
    if len(active_sprints) > 1:
        failures.append(
            _fail(
                "more than one sprint is active",
                "keep at most one sprint in state='active'; complete or re-plan the others",
            )
        )

    expected_active = active_sprints[0].get("id") if len(active_sprints) == 1 else None
    if data.get("active_sprint") != expected_active:
        failures.append(
            _fail(
                "active_sprint must equal the sole active sprint id, or null when no sprint is active",
                "set active_sprint to the one sprint in state='active', or null",
            )
        )

    summary = f"sprints={len(valid_sprints)} active={expected_active or 'none'}"
    return failures, summary


def main(argv: list[str] | None = None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    path = Path(args[0]) if args else Path("SPRINTS.json")

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"{path}: sprint contract not found", file=sys.stderr)
        print("fix: create SPRINTS.json from the starter template", file=sys.stderr)
        print(f"rerun: {RERUN_HINT}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"{path}: line {exc.lineno} column {exc.colno}: {exc.msg}", file=sys.stderr)
        print("fix: repair the JSON syntax error", file=sys.stderr)
        print(f"rerun: {RERUN_HINT}", file=sys.stderr)
        return 1

    task_ids = _sibling_ids(path.parent / "TASKS.json", "tasks")
    rubric_ids = _sibling_ids(path.parent / "EVALUATOR.json", "rubrics")
    failures, summary = validate_contract(data, task_ids, rubric_ids)
    if failures:
        print("Invalid sprint contract:", file=sys.stderr)
        for failure in failures:
            print(f"- {failure.message}", file=sys.stderr)
            print(f"    fix: {failure.hint}", file=sys.stderr)
            print(f"    rerun: {RERUN_HINT}", file=sys.stderr)
        return 1

    print(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

## `scripts/validate_evaluator.py`

Validates `EVALUATOR.json` rubric shape: unique ids, thresholds within the 1-5 scoring range, non-empty criteria, weights summing to 100, and an `active_rubric` pointer that resolves. See the scoring semantics under the evaluator rubric template in section 7.

```python
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

RERUN_HINT = "make validate-evaluator"
SCORE_MIN = 1.0
SCORE_MAX = 5.0
WEIGHT_TOTAL = 100.0


@dataclass(frozen=True)
class Failure:
    message: str
    hint: str


def _fail(message: str, hint: str) -> Failure:
    return Failure(message=message, hint=hint)


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def _is_string_list(value: Any) -> bool:
    return isinstance(value, list) and all(_is_non_empty_string(item) for item in value)


def _validate_dimension(dimension: Any, rubric_label: str, index: int, seen: set[str]) -> list[Failure]:
    if not isinstance(dimension, dict):
        return [
            _fail(
                f"{rubric_label}: dimensions[{index}] must be an object",
                "replace this dimension entry with a JSON object",
            )
        ]

    failures: list[Failure] = []
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


def _validate_rubric(rubric: Any, index: int, seen_ids: set[str]) -> list[Failure]:
    if not isinstance(rubric, dict):
        return [_fail(f"rubrics[{index}] must be an object", "replace this rubric entry with a JSON object")]

    failures: list[Failure] = []
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
        failures.append(_fail(f"{label}: dimensions must be a non-empty list", "add the weighted dimensions this rubric scores"))
        return failures

    seen_dimension_ids: set[str] = set()
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


def validate_rubrics(data: Any) -> tuple[list[Failure], str]:
    if not isinstance(data, dict):
        return [_fail("EVALUATOR rubric file must be a JSON object", "replace EVALUATOR.json with a JSON object")], ""

    failures: list[Failure] = []
    if data.get("schema_version") != 1:
        failures.append(_fail("schema_version must be 1", "set schema_version to 1"))

    rubrics = data.get("rubrics")
    if not isinstance(rubrics, list) or not rubrics:
        failures.append(_fail("rubrics must be a non-empty list", "add at least one rubric object to rubrics"))
        return failures, ""

    seen_ids: set[str] = set()
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


def main(argv: list[str] | None = None) -> int:
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
```

---

# 10. Contract tests

These tests keep the harness honest.

## `tests/test_makefile_contract.py`

```python
from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _make_dry_run(target: str) -> str:
    result = subprocess.run(
        ["make", "--dry-run", "--always-make", target],
        cwd=ROOT,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    return result.stdout


def test_make_check_wires_quality_gates():
    output = _make_dry_run("check")

    assert "format" in output.lower()
    assert "lint" in output.lower() or "ruff check" in output
    assert "typecheck" in output.lower() or "mypy" in output or "tsc" in output
    assert "scripts/validate_json.py" in output
    assert "scripts/validate_tasks.py" in output
    assert "scripts/validate_sprints.py" in output
    assert "scripts/validate_evaluator.py" in output
    assert "validate_architecture" in output or "validate-architecture" in output
    assert "pytest" in output or "coverage" in output or "test" in output.lower()


def test_make_initialize_is_callable_phase_zero():
    output = _make_dry_run("initialize")

    status_index = output.index("git status --short --branch")
    head_index = output.index("git --no-pager log -1 --decorate --oneline || true")
    check_index = output.index("make check")
    assert status_index < head_index < check_index


def test_make_init_aliases_initialize():
    output = _make_dry_run("init")

    assert "git status --short --branch" in output
    assert "git --no-pager log -1 --decorate --oneline || true" in output
    assert "make check" in output
```

## `tests/test_task_completion_evidence.py`

```python
from __future__ import annotations

import json
import math
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TASKS_FILE = ROOT / "TASKS.json"
VALIDATOR = ROOT / "scripts" / "validate_tasks.py"
ALLOWED_STATES = {"planned", "active", "blocked", "verified"}
VCR_ACTIVATED_STATES = {"active", "verified"}


def _run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_task_ledger_records_completion_evidence_and_vcr():
    data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))

    assert data["schema_version"] == 1
    assert "active_task" in data
    assert isinstance(data["tasks"], list)
    assert data["tasks"]

    task_ids: set[str] = set()
    for task in data["tasks"]:
        assert task["id"] not in task_ids
        task_ids.add(task["id"])
        assert task["title"].strip()
        assert task["done_behavior"].strip()
        assert task["state"] in ALLOWED_STATES
        assert task["verification"]["command"].strip()

        if task["state"] == "verified":
            assert task["verification"]["status"] == "passing"
            assert task["verification"]["evidence"].strip()

    active_tasks = [task for task in data["tasks"] if task["state"] == "active"]
    assert len(active_tasks) <= 1
    expected_active = active_tasks[0]["id"] if active_tasks else None
    assert data["active_task"] == expected_active

    activated = [task for task in data["tasks"] if task["state"] in VCR_ACTIVATED_STATES]
    verified = [
        task
        for task in activated
        if task["state"] == "verified"
        and task["verification"]["status"] == "passing"
        and task["verification"].get("signals", {}).get("exit_code") == 0
    ]
    expected_vcr = len(verified) / len(activated) if activated else 1.0
    assert math.isclose(float(data["vcr"]), expected_vcr, abs_tol=5e-4)


def test_task_validator_accepts_canonical_task_ledger():
    result = _run_validator(TASKS_FILE)

    assert result.returncode == 0, result.stderr
    assert "VCR" in result.stdout


def test_task_validator_requires_verification_commands(tmp_path: Path):
    ledger = {
        "schema_version": 1,
        "active_task": None,
        "vcr": 1.0,
        "tasks": [
            {
                "id": "F999",
                "title": "Missing verification command",
                "done_behavior": "The task cannot be completed without an explicit verification command.",
                "state": "planned",
                "verification": {"command": "", "status": "not_run", "evidence": ""},
            }
        ],
    }
    path = tmp_path / "TASKS.json"
    path.write_text(json.dumps(ledger), encoding="utf-8")

    result = _run_validator(path)

    assert result.returncode != 0
    assert "verification.command" in result.stderr


def test_task_validator_requires_e2e_for_cross_component_tasks(tmp_path: Path):
    ledger = {
        "schema_version": 1,
        "active_task": None,
        "vcr": 1.0,
        "tasks": [
            {
                "id": "F998",
                "title": "Cross-component task without e2e",
                "change_scope": "cross_component",
                "components_touched": ["ui", "api"],
                "boundaries_touched": ["ui_to_api"],
                "e2e_required": True,
                "done_behavior": "The UI calls the API and renders the saved result.",
                "state": "planned",
                "verification": {"command": "pytest -q tests/test_api.py && make check", "status": "not_run", "evidence": ""},
            }
        ],
    }
    path = tmp_path / "TASKS.json"
    path.write_text(json.dumps(ledger), encoding="utf-8")

    result = _run_validator(path)

    assert result.returncode != 0
    assert "e2e/full-pipeline" in result.stderr
    assert "fix:" in result.stderr


def test_task_validator_requires_boundary_metadata_for_cross_component_tasks(tmp_path: Path):
    ledger = {
        "schema_version": 1,
        "active_task": None,
        "vcr": 1.0,
        "tasks": [
            {
                "id": "F997",
                "title": "Cross-component task without boundary metadata",
                "change_scope": "cross_component",
                "e2e_required": True,
                "done_behavior": "The UI calls the API and renders the saved result.",
                "state": "planned",
                "verification": {"command": "pytest -q tests/e2e/test_ui_api.py && make check", "status": "not_run", "evidence": ""},
            }
        ],
    }
    path = tmp_path / "TASKS.json"
    path.write_text(json.dumps(ledger), encoding="utf-8")

    result = _run_validator(path)

    assert result.returncode != 0
    assert "components_touched" in result.stderr
    assert "boundaries_touched" in result.stderr
```

## `tests/test_task_termination_signals.py`

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
TASKS_FILE = ROOT / "TASKS.json"
VALIDATOR = ROOT / "scripts" / "validate_tasks.py"


def _run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _write_ledger(tmp_path: Path, task: dict[str, Any], *, active_task: str | None = None) -> Path:
    activated = [task] if task["state"] in {"active", "verified"} else []
    verified = [
        task
        for task in activated
        if task["state"] == "verified"
        and task["verification"].get("status") == "passing"
        and isinstance(task["verification"].get("signals"), dict)
        and task["verification"].get("signals", {}).get("exit_code") == 0
    ]
    ledger = {
        "schema_version": 1,
        "active_task": active_task,
        "vcr": len(verified) / len(activated) if activated else 1.0,
        "tasks": [task],
    }
    path = tmp_path / "TASKS.json"
    path.write_text(json.dumps(ledger), encoding="utf-8")
    return path


def _verified_task(**verification_overrides: Any) -> dict[str, Any]:
    verification: dict[str, Any] = {
        "command": "python -m pytest -q tests/test_example.py",
        "status": "passing",
        "evidence": "pytest returned exit code 0 with the critical path exercised.",
        "last_run_at": "2026-06-09T19:55:15Z",
        "signals": {"exit_code": 0},
    }
    for key, value in verification_overrides.items():
        if value is None:
            verification.pop(key, None)
        else:
            verification[key] = value
    return {
        "id": "F999",
        "title": "Synthetic verified task",
        "done_behavior": "The synthetic task records runtime termination evidence.",
        "state": "verified",
        "verification": verification,
    }


def test_task_ledger_records_runtime_signals_for_verified_tasks():
    data = json.loads(TASKS_FILE.read_text(encoding="utf-8"))

    verified_tasks = [task for task in data["tasks"] if task["state"] == "verified"]
    for task in verified_tasks:
        signals = task["verification"].get("signals")
        assert isinstance(signals, dict), task["id"]
        assert signals.get("exit_code") == 0, task["id"]


def test_validator_accepts_canonical_task_ledger_with_runtime_signals():
    result = _run_validator(TASKS_FILE)

    assert result.returncode == 0, result.stderr
    assert "VCR" in result.stdout


def test_verified_task_requires_runtime_signals(tmp_path: Path):
    task = _verified_task(signals=None)
    path = _write_ledger(tmp_path, task)

    result = _run_validator(path)

    assert result.returncode != 0
    assert "verification.signals" in result.stderr
    assert "runtime" in result.stderr


def test_verified_task_rejects_nonzero_exit_code_as_premature_victory(tmp_path: Path):
    task = _verified_task(signals={"exit_code": 1})
    path = _write_ledger(tmp_path, task)

    result = _run_validator(path)

    assert result.returncode != 0
    assert "premature victory" in result.stderr
    assert "exit_code=1" in result.stderr


def test_verified_task_rejects_boolean_exit_code(tmp_path: Path):
    task = _verified_task(signals={"exit_code": True})
    path = _write_ledger(tmp_path, task)

    result = _run_validator(path)

    assert result.returncode != 0
    assert "signals.exit_code must be an integer" in result.stderr


def test_verified_task_requires_iso8601_last_run_at(tmp_path: Path):
    task = _verified_task(last_run_at="yesterday")
    path = _write_ledger(tmp_path, task)

    result = _run_validator(path)

    assert result.returncode != 0
    assert "last_run_at" in result.stderr
    assert "ISO-8601" in result.stderr


def test_validator_prints_actionable_repair_hint_for_each_failure(tmp_path: Path):
    task = _verified_task(signals={"exit_code": 1}, last_run_at="yesterday")
    path = _write_ledger(tmp_path, task)

    result = _run_validator(path)

    assert result.returncode != 0
    lines = result.stderr.splitlines()
    failure_indexes = [index for index, line in enumerate(lines) if line.startswith("- ")]
    assert failure_indexes
    for index in failure_indexes:
        assert index + 1 < len(lines)
        assert lines[index + 1].startswith("    fix: ")
```

## `tests/test_harness_observability.py`

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WRAPPER = ROOT / "scripts" / "run_with_signals.py"


def _run_wrapper(
    cwd: Path, wrapped: list[str], *, task_id: str = "F900", kind: str = "verification"
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(WRAPPER), "--task-id", task_id, "--kind", kind, "--", *wrapped],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _signal_files(cwd: Path, task_id: str = "F900") -> list[Path]:
    return sorted((cwd / ".harness" / "runs" / task_id).glob("*.json"))


def test_wrapper_records_runtime_signal_with_otel_attributes(tmp_path: Path):
    result = _run_wrapper(tmp_path, [sys.executable, "-c", "print('ok')"])

    assert result.returncode == 0, result.stderr
    assert "runtime signal:" in result.stdout
    assert "exit_code=0" in result.stdout

    files = _signal_files(tmp_path)
    assert len(files) == 1
    signal = json.loads(files[0].read_text(encoding="utf-8"))

    assert signal["task_id"] == "F900"
    assert signal["run_kind"] == "verification"
    assert signal["exit_code"] == 0
    assert isinstance(signal["exit_code"], int) and not isinstance(signal["exit_code"], bool)
    assert isinstance(signal["duration_ms"], int)
    assert signal["started_at"] and signal["ended_at"]
    assert signal["argv"]

    otel = signal["otel"]
    assert len(otel["trace_id"]) == 32
    assert len(otel["span_id"]) == 16
    int(otel["trace_id"], 16)
    int(otel["span_id"], 16)
    assert otel["status_code"] == "OK"

    attributes = signal["attributes"]
    assert attributes["harness.task.id"] == "F900"
    assert attributes["harness.run.kind"] == "verification"
    assert attributes["process.exit_code"] == 0
    assert attributes["test.status"] == "passed"


def test_wrapper_propagates_failure_exit_code_and_prints_repair_hints(tmp_path: Path):
    result = _run_wrapper(tmp_path, [sys.executable, "-c", "raise SystemExit(3)"])

    assert result.returncode == 3
    assert "exit_code=3" in result.stdout
    assert "fix:" in result.stderr
    assert "rerun:" in result.stderr

    files = _signal_files(tmp_path)
    assert len(files) == 1
    signal = json.loads(files[0].read_text(encoding="utf-8"))
    assert signal["exit_code"] == 3
    assert signal["otel"]["status_code"] == "ERROR"
    assert signal["attributes"]["test.status"] == "failed"
```

## `tests/test_sprint_contracts.py`

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_sprints.py"


def _run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _sprint(**overrides: Any) -> dict[str, Any]:
    sprint: dict[str, Any] = {
        "id": "S900",
        "title": "Synthetic sprint",
        "state": "active",
        "goal": "Prove the sprint validator enforces the contract.",
        "task_ids": ["F900"],
        "required_gates": ["make check"],
        "evaluator_rubric_id": "default_harness_rubric",
        "observability": {"runtime_signal_required": True, "otel_semconv": "OBSERVABILITY.md"},
    }
    for key, value in overrides.items():
        if value is None:
            sprint.pop(key, None)
        else:
            sprint[key] = value
    return sprint


def _write_contract(tmp_path: Path, sprints: list[dict[str, Any]], *, active_sprint: str | None = "S900") -> Path:
    contract = {"schema_version": 1, "active_sprint": active_sprint, "sprints": sprints}
    path = tmp_path / "SPRINTS.json"
    path.write_text(json.dumps(contract), encoding="utf-8")
    return path


def test_sprint_validator_accepts_canonical_sprint_contract():
    result = _run_validator(ROOT / "SPRINTS.json")

    assert result.returncode == 0, result.stderr
    assert "sprints=" in result.stdout


def test_sprint_validator_requires_required_gates(tmp_path: Path):
    path = _write_contract(tmp_path, [_sprint(required_gates=None)])

    result = _run_validator(path)

    assert result.returncode != 0
    assert "required_gates" in result.stderr
    assert "fix:" in result.stderr
    assert "rerun:" in result.stderr


def test_sprint_validator_rejects_task_ids_missing_from_task_ledger(tmp_path: Path):
    tasks = {
        "schema_version": 1,
        "active_task": None,
        "vcr": 1.0,
        "tasks": [
            {
                "id": "F900",
                "title": "Synthetic task",
                "state": "planned",
                "done_behavior": "Synthetic behavior.",
                "verification": {"command": "make check", "status": "not_run", "evidence": "", "last_run_at": None},
            }
        ],
    }
    (tmp_path / "TASKS.json").write_text(json.dumps(tasks), encoding="utf-8")
    path = _write_contract(tmp_path, [_sprint(task_ids=["F900", "F999"])])

    result = _run_validator(path)

    assert result.returncode != 0
    assert "unknown tasks" in result.stderr
    assert "F999" in result.stderr


def test_sprint_validator_enforces_single_active_sprint(tmp_path: Path):
    second = _sprint(id="S901", title="Second active sprint")
    path = _write_contract(tmp_path, [_sprint(), second])

    result = _run_validator(path)

    assert result.returncode != 0
    assert "more than one sprint is active" in result.stderr


def test_sprint_validator_requires_active_sprint_pointer_to_match(tmp_path: Path):
    path = _write_contract(tmp_path, [_sprint(state="completed")], active_sprint="S900")

    result = _run_validator(path)

    assert result.returncode != 0
    assert "active_sprint" in result.stderr
```

## `tests/test_architecture_rules.py`

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_architecture.py"

FORBIDDEN_FS_RULE: dict[str, Any] = {
    "id": "renderer_to_preload_file_ops",
    "type": "forbidden_import",
    "paths": ["src/renderer/**/*.ts"],
    "modules": ["fs", "node:fs"],
    "why": "Renderer code must not access filesystem APIs directly.",
    "fix": "Move filesystem code behind the preload bridge.",
    "rerun": "make validate-architecture && make e2e",
}


def _run_validator(cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR)],
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _write_rules(cwd: Path, rules: list[dict[str, Any]]) -> None:
    harness_dir = cwd / ".harness"
    harness_dir.mkdir(parents=True, exist_ok=True)
    (harness_dir / "architecture_rules.json").write_text(json.dumps({"rules": rules}), encoding="utf-8")


def test_validator_passes_when_no_rules_manifest_exists(tmp_path: Path):
    result = _run_validator(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "architecture validation passed" in result.stdout


def test_validator_rejects_forbidden_import_with_agent_oriented_error(tmp_path: Path):
    _write_rules(tmp_path, [FORBIDDEN_FS_RULE])
    renderer_dir = tmp_path / "src" / "renderer"
    renderer_dir.mkdir(parents=True)
    (renderer_dir / "export.ts").write_text("import fs from 'fs';\n", encoding="utf-8")

    result = _run_validator(tmp_path)

    assert result.returncode != 0
    assert "renderer_to_preload_file_ops violation" in result.stderr
    assert "export.ts" in result.stderr
    assert "why:" in result.stderr
    assert "fix:" in result.stderr
    assert "rerun:" in result.stderr


def test_validator_accepts_compliant_code(tmp_path: Path):
    _write_rules(tmp_path, [FORBIDDEN_FS_RULE])
    renderer_dir = tmp_path / "src" / "renderer"
    renderer_dir.mkdir(parents=True)
    (renderer_dir / "export.ts").write_text(
        "import { api } from './bridge';\nexport const run = () => api.exportFile();\n", encoding="utf-8"
    )

    result = _run_validator(tmp_path)

    assert result.returncode == 0, result.stderr
    assert "architecture validation passed" in result.stdout


def test_validator_fails_loudly_on_unsupported_rule_type(tmp_path: Path):
    _write_rules(tmp_path, [{"id": "exotic_rule", "type": "telepathy"}])

    result = _run_validator(tmp_path)

    assert result.returncode != 0
    assert "unsupported architecture rule type" in result.stderr
    assert "fix:" in result.stderr
```


## `tests/test_blocked_vcr_semantics.py`

```python
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "scripts" / "validate_tasks.py"


def _run_validator(path: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VALIDATOR), str(path)],
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def _task(task_id: str, state: str, *, status: str | None = None, signals: dict[str, Any] | None = None) -> dict[str, Any]:
    verification: dict[str, Any] = {
        "command": "python -m pytest -q tests/test_example.py",
        "status": status or ("passing" if state == "verified" else "not_run"),
        "evidence": "pytest returned exit code 0." if state == "verified" else "",
        "last_run_at": "2026-06-10T00:00:00Z" if state == "verified" else "",
    }
    if signals is not None:
        verification["signals"] = signals
    elif state == "verified":
        verification["signals"] = {"exit_code": 0}
    return {
        "id": task_id,
        "title": f"Synthetic {task_id}",
        "done_behavior": "Synthetic task for VCR semantics.",
        "state": state,
        "verification": verification,
    }


def _write_ledger(tmp_path: Path, tasks: list[dict[str, Any]], *, active_task: str | None, vcr: float) -> Path:
    path = tmp_path / "TASKS.json"
    path.write_text(
        json.dumps({"schema_version": 1, "active_task": active_task, "vcr": vcr, "tasks": tasks}),
        encoding="utf-8",
    )
    return path


def test_blocked_tasks_are_suspended_records_excluded_from_vcr_and_active_lane(tmp_path: Path):
    path = _write_ledger(
        tmp_path,
        [
            _task("F001", "verified"),
            _task("F002", "blocked", status="blocked"),
            _task("F003", "active"),
        ],
        active_task="F003",
        vcr=0.5,
    )

    result = _run_validator(path)

    assert result.returncode == 0, result.stderr
    assert "activated=2" in result.stdout
    assert "verified=1" in result.stdout
    assert "VCR=0.500" in result.stdout


def test_only_blocked_tasks_leave_vcr_at_one_and_no_active_lane(tmp_path: Path):
    path = _write_ledger(tmp_path, [_task("F002", "blocked", status="blocked")], active_task=None, vcr=1.0)

    result = _run_validator(path)

    assert result.returncode == 0, result.stderr
    assert "activated=0" in result.stdout
    assert "verified=0" in result.stdout
    assert "VCR=1.000" in result.stdout


def test_two_active_tasks_are_rejected(tmp_path: Path):
    path = _write_ledger(tmp_path, [_task("F001", "active"), _task("F002", "active")], active_task=None, vcr=0.0)

    result = _run_validator(path)

    assert result.returncode != 0
    assert "more than one active task" in result.stderr or "cannot activate more than one" in result.stderr


def test_validator_declares_the_vcr_denominator_states_explicitly():
    text = VALIDATOR.read_text(encoding="utf-8")

    assert "VCR_ACTIVATED_STATES" in text
    assert '{"active", "verified"}' in text or "{'active', 'verified'}" in text
    assert "state') != PLANNED_STATE" not in text
```

## `tests/test_quality_and_claude_contracts.py`

```python
from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_quality_register_is_first_class_and_linked_from_harness_router_and_cockpit():
    quality = _read("QUALITY.md")
    agents = _read("AGENTS.md")
    progress = _read("PROGRESS.md")

    assert "# Quality Register" in quality
    assert "## Quality Dimensions" in quality
    assert "## Module Scores" in quality
    assert "## Repair Queue" in quality

    for required in [
        "Verification passing state",
        "Agent understandability",
        "Test stability",
        "Architecture-boundary compliance",
        "Code-convention compliance",
        "Known cleanup or repair action",
    ]:
        assert required in quality

    assert "QUALITY.md" in agents
    assert "QUALITY.md" in progress


def test_claude_md_is_a_thin_router_to_agents_md():
    claude = _read("CLAUDE.md")

    assert "AGENTS.md" in claude
    assert "canonical" in claude.lower()
    assert len([line for line in claude.splitlines() if line.strip()]) <= 30
    assert "## Work rules" not in claude
    assert "## Session lifecycle" not in claude
    assert "## Source-of-truth map" not in claude


def test_phase_zero_details_are_centralized_in_agents_not_progress():
    agents = _read("AGENTS.md")
    progress = _read("PROGRESS.md")

    assert "### Phase 0" in agents
    assert "make initialize" in agents
    assert "## Phase 0" not in progress
    assert "AGENTS.md" in progress
    assert "make initialize" in progress


def test_session_exit_uses_repo_canonical_gate_without_npm_as_canonical():
    agents = _read("AGENTS.md")
    session_exit = agents.split("## Session Exit Checklist", maxsplit=1)[1].split("### Cleanup modes", maxsplit=1)[0]

    assert "make check" in session_exit
    assert ("npm " + "run") not in session_exit
    assert ("npm " + "test") not in session_exit
```


---

# 11. Activation and verification snippets

## Activate a task manually

Edit `TASKS.json`. The fragment below shows only the fields that change; the surrounding ledger in this example also contains one already-verified task, so activated=2 and verified=1 yield `vcr: 0.5` after activation (a full task entry also carries `title`, `done_behavior`, and scope metadata):

```json
{
  "active_task": "F002",
  "vcr": 0.5,
  "tasks": [
    {
      "id": "F002",
      "state": "active",
      "verification": {
        "command": ".venv/bin/python -m pytest -q tests/test_feature.py && make check",
        "status": "not_run",
        "evidence": "",
        "last_run_at": null
      }
    }
  ]
}
```

Then run:

```bash
make validate-tasks
```

## Mark a task blocked

Use `blocked` when work cannot proceed due to an external blocker and should be suspended without occupying the active lane.

```json
{
  "id": "F002",
  "state": "blocked",
  "verification": {
    "command": ".venv/bin/python -m pytest -q tests/test_feature.py && make check",
    "status": "blocked",
    "evidence": "Blocked because required dependency X is unavailable. No verified behavior claimed.",
    "last_run_at": null
  }
}
```

A blocked task is excluded from the VCR denominator and does not occupy the single active lane. Keep its blocker reason visible in evidence; reactivate it by moving it to `active`, or re-plan it back to `planned` with `verification.status` `not_run` if the work is no longer in scope.

## Capture verification evidence

Preferred: wrap the declared command so the runtime signal JSON is recorded for you:

```bash
python scripts/run_with_signals.py --task-id F002 --kind verification -- <declared verification command>
```

Manual fallback (`pipefail` protects declared commands that contain pipes):

```bash
set -o pipefail
(<declared verification command>)
code=$?
stamp=$(date -Iseconds)
echo "last_run_at=$stamp"
echo "exit_code=$code"
exit "$code"
```

If exit code is 0, update the task:

```json
{
  "state": "verified",
  "verification": {
    "command": "<declared verification command>",
    "status": "passing",
    "evidence": "RED: narrow tests failed for expected missing behavior. GREEN: narrow tests passed; make check passed with task validation VCR=1.000.",
    "last_run_at": "<stamp>",
    "signals": {
      "exit_code": 0
    }
  }
}
```

---

# 12. Adaptation checklist for a new repo

1. Add root files:
   - `AGENTS.md`
   - `CONSTRAINTS.md`
   - `DECISIONS.md`
   - `PROGRESS.md`
   - `QUALITY.md`
   - `TASKS.json`
   - `SPRINTS.json`
   - `EVALUATOR.json`
   - `OBSERVABILITY.md`
   - `.gitignore`
   - `.harness/otel_attributes.json`
   - `.harness/architecture_rules.json` when architecture checks are used
   - `.harness/runs/` as a generated runtime-signal directory
   - `ARCHITECTURE.md` when the repo has cross-component boundaries
2. Add scripts:
   - `scripts/run_with_signals.py`
   - `scripts/validate_json.py`
   - `scripts/validate_tasks.py`
   - `scripts/validate_sprints.py`
   - `scripts/validate_evaluator.py`
   - `scripts/validate_architecture.py` when architecture rules can be automated
3. Add or adapt `Makefile`:
   - `init`
   - `initialize`
   - `check`
   - `test`
   - `coverage` when `check` depends on coverage
   - `format`
   - `format-check`
   - `lint`
   - `typecheck`
   - `validate-json`
   - `validate-tasks`
   - `validate-sprints`
   - `validate-evaluator`
   - `validate-architecture`
   - `record-signal`
   - `e2e`
4. Add contract tests:
   - `tests/test_makefile_contract.py`
   - `tests/test_task_completion_evidence.py`
   - `tests/test_task_termination_signals.py`
   - `tests/test_harness_observability.py`
   - `tests/test_sprint_contracts.py`
   - `tests/test_architecture_rules.py` when architecture checks exist
   - `tests/e2e/...` for cross-component flows
5. Replace placeholders:
   - package name in coverage target
   - formatter/linter/typechecker commands
   - initial task list
   - privacy constraints relevant to repo
6. Run:

```bash
make initialize
```

7. Add `.gitignore` entries for generated runtime artifacts while keeping static harness config committed:

```gitignore
.harness/runs/
```

8. Fix gates until `make check` passes.
9. Commit the harness as one atomic unit:

```bash
git add AGENTS.md CONSTRAINTS.md DECISIONS.md PROGRESS.md QUALITY.md TASKS.json SPRINTS.json EVALUATOR.json OBSERVABILITY.md .harness/otel_attributes.json .harness/architecture_rules.json .gitignore Makefile scripts tests
git commit -m "chore: add agent harness and verified task ledger"
```

---

# 13. Anti-patterns this harness blocks

## Premature victory

Bad:

```text
Implemented feature. Looks good.
```

Harness response:

```text
Invalid task ledger:
- F002: verified tasks must include verification.signals (runtime exit signal)
    fix: add "signals": {"exit_code": 0} captured from the actual verification command run
```

## Status-only completion

Bad:

```json
"state": "verified",
"verification": {
  "status": "passing",
  "evidence": "tests pass"
}
```

Invalid because there is no timestamp or runtime exit signal.

## Multiple loose threads

Bad:

```json
"tasks": [
  {"id": "F001", "state": "active"},
  {"id": "F002", "state": "active"}
]
```

Invalid because VCR is below 1.0 and more than one unverified activated task exists.

## Unit-only completion for cross-component work

Bad:

```text
Renderer tests pass. Service tests pass. Mark export flow done.
```

Invalid because the real boundary was never exercised.

Correct:

```bash
make validate-architecture && make e2e && make check
```

Then record the runtime signal in `TASKS.json`.

## Human-only error messages

Bad:

```text
Architecture violation.
```

Correct:

```text
renderer_to_preload violation: src/renderer/export.ts imports fs.
why: renderer must not access filesystem APIs directly.
fix: move filesystem calls to src/preload/file-ops.ts and expose window.api.exportFile.
rerun: make validate-architecture && make e2e
```

## Unpromoted review feedback

Bad:

```text
Reviewer repeatedly comments: "Don't import database models in UI code."
```

Correct:

```text
Add a boundary rule, add a static check, add an agent-oriented fix message, and add a regression test proving the check fails on that import.
```

## Roadmap in agent router

Bad:

```text
AGENTS.md contains a 100-line roadmap and stale implementation notes.
```

Correct placement:

- active roadmap -> `PROGRESS.md` or `TASKS.json`
- stable architecture -> local `ARCHITECTURE.md`
- global law -> `CONSTRAINTS.md`
- decisions -> `DECISIONS.md`

## Observability outside the harness

Bad:

```text
Agent says: "tests passed earlier" but no runtime signal file, trace/span id, command, or exit code exists.
```

Correct:

```bash
python scripts/run_with_signals.py --task-id F001 --kind verification -- make check
```

Then summarize the durable result in `TASKS.json`.

## Skipping session cleanup

Bad:

```text
Feature works, but temp files remain, feature state is stale, startup path is unknown, and module quality was not updated.
```

Correct:

```text
Session Exit Checklist is complete; immediate cleanup ran; QUALITY.md reflects changed module state; periodic cleanup handles accumulated drift weekly.
```

## Implicit sprint/evaluator criteria

Bad:

```text
Sprint goal and review criteria live only in chat.
```

Correct:

```text
SPRINTS.json names task ids/gates/evaluator; EVALUATOR.json names weighted dimensions and blockers; make check validates both.
```

## Ad hoc verification

Bad:

```bash
pytest -q
```

Then claiming complete.

Correct:

```bash
<narrow declared test> && make check
```

Then record evidence, timestamp, and exit code.

---

# 14. Minimal operating loop

Use this loop for every feature:

```text
initialize
  -> inspect TASKS.json
  -> classify next task scope
  -> define architecture boundaries first if cross-component
  -> activate one planned task
  -> write failing tests from done_behavior
  -> turn architecture rules into executable checks
  -> run RED
  -> implement minimally
  -> run GREEN
  -> run e2e/full-pipeline verification if cross-component
  -> run declared verification command through run_with_signals.py when runtime observability is required
  -> capture last_run_at + exit_code + trace/span/duration when available
  -> mark verified only if exit_code == 0
  -> promote repeated review feedback into checks
  -> update PROGRESS.md
  -> update QUALITY.md if module quality/cleanup priority changed
  -> complete Session Exit Checklist and immediate cleanup
  -> make check
  -> commit atomic unit
```

The harness is working when a future agent can enter cold, run `make initialize`, read the ledgers, and know exactly:

- what repo state is true
- what work is active
- what work is planned
- what command proves each task done
- whether completion claims are backed by runtime evidence
- what to do next without trusting chat memory
