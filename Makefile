# Canonical executable truth for this repository.
# Requirements: GNU make + python3 (stdlib only). Keep target names stable when
# adapting to your stack; swap recipe bodies for your real tools.

PYTHON ?= python3

# Keep gates clean-state friendly: no bytecode caches from checks/tests.
export PYTHONDONTWRITEBYTECODE = 1

JSON_VALIDATE      = $(PYTHON) scripts/validate_json.py
TASKS_VALIDATE     = $(PYTHON) scripts/validate_tasks.py
SPRINTS_VALIDATE   = $(PYTHON) scripts/validate_sprints.py
EVALUATOR_VALIDATE = $(PYTHON) scripts/validate_evaluator.py
ARCH_VALIDATE      = $(PYTHON) scripts/validate_architecture.py
RUN_WITH_SIGNALS   = $(PYTHON) scripts/run_with_signals.py

.PHONY: init initialize check test e2e format format-check lint typecheck \
        validate validate-json validate-tasks validate-sprints \
        validate-evaluator validate-architecture record-signal

init: initialize

# Phase 0 cold start: read-only. Prints live repo truth, then runs the gate.
initialize:
	git status --short --branch
	git --no-pager log -1 --decorate --oneline || true
	$(MAKE) check

# Canonical aggregate quality gate.
check: format-check lint typecheck validate test

# All harness ledger/config validators.
validate: validate-json validate-tasks validate-sprints validate-evaluator validate-architecture

test:
	$(PYTHON) -m unittest discover -s tests -p "test_*.py"

e2e:
	$(PYTHON) -m unittest discover -s tests/e2e -p "test_*.py"

# Stdlib placeholder: replace with your formatter (e.g. `ruff format .`).
format:
	@echo "format: no formatter wired; replace this recipe with your stack's formatter"

# Stdlib placeholder: replace with your formatter's check mode (e.g. `ruff format --check .`).
format-check:
	@echo "format-check: no formatter wired; replace this recipe with your stack's formatter check"

# Stdlib syntax lint over harness code; replace/extend with your real linter.
lint:
	@$(PYTHON) -c "import ast, pathlib; files = sorted([*pathlib.Path('scripts').rglob('*.py'), *pathlib.Path('tests').rglob('*.py')]); [ast.parse(f.read_text(encoding='utf-8'), filename=str(f)) for f in files]; print('lint: parsed', len(files), 'python files (stdlib syntax check)')"

# Stdlib placeholder: replace with your type checker (e.g. `mypy src`).
typecheck:
	@echo "typecheck: no type checker wired; replace this recipe with your stack's type checker"

validate-json:
	$(JSON_VALIDATE)

validate-tasks:
	$(TASKS_VALIDATE)

validate-sprints:
	$(SPRINTS_VALIDATE)

validate-evaluator:
	$(EVALUATOR_VALIDATE)

validate-architecture:
	$(ARCH_VALIDATE)

record-signal:
	@echo "usage: $(RUN_WITH_SIGNALS) --task-id F001 --kind verification -- <command>"
