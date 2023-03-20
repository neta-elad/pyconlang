.PHONY: all
all: format lint type test

.PHONY: lint
lint: 
	isort . -q
	autoflake .

.PHONY: format
format:
	black .

.PHONY: type
type:
	mypy --strict pyconlang


.PHONY: test
test:
	pytest


.PHONY: env
env:
	! [ -d .venv ] && python3 -m venv .venv || true

.PHONY: install
install:
	yes | pip uninstall pyconlang
	pip install -e .[test]

diagrams.html: pyconlang/parser.py pyconlang/lexicon/parser.py
	python -m pyconlang.lexicon.parser

.PHONY: clean
clean:
	rm -r .venv
	rm diagrams.html
