# Architecture

Root-level boundary map. Define boundaries here **before** writing e2e tests for cross-component behavior, then turn each durable rule into an executable check in `.harness/architecture_rules.json` (validated by `make validate-architecture`).

## Components of this template

- **Ledgers** (`TASKS.json`, `SPRINTS.json`, `EVALUATOR.json`): machine-readable state; never edited by scripts, only validated.
- **Validators** (`scripts/validate_*.py`): read-only executable checks with agent-oriented `fix:`/`rerun:` errors.
- **Runtime signal wrapper** (`scripts/run_with_signals.py`): the only component that writes runtime artifacts, under `.harness/runs/` only.
- **Installer** (`scripts/install_harness.py`): copies the harness contract into another repo; never deletes, never touches `.git` or `.harness/runs/`.
- **Makefile**: the only public entrypoint humans/agents/CI should call; targets fan out to the scripts above.
- **Contract tests** (`tests/`): prove the harness stays wired; e2e tests under `tests/e2e/` exercise the installer→Makefile→validator pipeline.

## Boundary: stdlib_only_harness_gates

**Components:** `scripts/`, `tests/` -> Python standard library only

**Allowed direction:** harness code may import stdlib modules; repos adopting the template wire third-party tools into Makefile recipe bodies instead.

**Forbidden:** `scripts/**` and `tests/**` must not import third-party packages (e.g. `pytest`, `ruff`, `mypy`, `requests`).

**Contract:** a fresh clone passes `make initialize` / `make check` with only GNU make and `python3` installed.

**Executable checks:**

- `make validate-architecture` enforces the forbidden-import rule from `.harness/architecture_rules.json`.
- `tests/test_architecture_rules.py` proves the checker rejects violations.
- `tests/e2e/test_harness_pipeline.py` proves an installed copy still validates end to end.

**Agent-oriented failure text:**

```text
stdlib_only_harness_gates violation: <file> imports `<module>`.
why: harness gates must run with GNU make and the Python standard library only.
fix: use stdlib equivalents in scripts/ and tests/; wire third-party tooling into the format/lint/typecheck targets instead.
rerun: make validate-architecture && make test
```

## Boundary template for your repo

```markdown
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
```

If a rule cannot be automated yet, record it as manual review debt in `PROGRESS.md` and add a `TASKS.json` item to automate it later.
