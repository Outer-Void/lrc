PYTHON ?= python3

.PHONY: install fmt lint types test wheel examples ci

install:
	$(PYTHON) -m pip install -e '.[dev]'

fmt:
	ruff format .

lint:
	ruff format --check .
	ruff check .

types:
	mypy

test:
	$(PYTHON) -m pytest

wheel:
	PYTHON=$(PYTHON) bash scripts/verify_wheel.sh

# Every shipped example must compile.
examples:
	for f in examples/*.lrc; do $(PYTHON) -m lrc compile "$$f" >/dev/null || exit 1; done

ci: lint types test wheel examples
