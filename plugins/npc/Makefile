.DEFAULT_GOAL := help
PYTHON        := python3
PYTEST        := $(PYTHON) -m pytest

.PHONY: help test coverage lint fmt check

help:
	@printf "%-12s %s\n" "test"     "Run the test suite"
	@printf "%-12s %s\n" "coverage" "Run tests with coverage (requires pytest-cov)"
	@printf "%-12s %s\n" "lint"     "Check code style (requires ruff)"
	@printf "%-12s %s\n" "fmt"      "Auto-format code (requires ruff)"
	@printf "%-12s %s\n" "check"    "lint + test"

test:
	$(PYTEST)

coverage:
	@$(PYTHON) -c "import pytest_cov" 2>/dev/null || \
		{ echo "Install pytest-cov first: pip install pytest-cov"; exit 1; }
	$(PYTEST) --cov=npc --cov-report=term-missing

lint:
	@$(PYTHON) -m ruff check hooks/ tests/ 2>/dev/null || \
		{ echo "(ruff not installed — run: pip install ruff)"; exit 0; }

fmt:
	@$(PYTHON) -m ruff format hooks/ tests/ 2>/dev/null || \
		{ echo "(ruff not installed — run: pip install ruff)"; exit 0; }

check: lint test
