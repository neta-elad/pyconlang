.PHONY: all
all: format lint type test

.PHONY: lint
lint: 
	isort . -q
	autoflake . --recursive \
				--exclude .env \
				--remove-unused-variables \
				--remove-all-unused-imports \
				--expand-star-imports \
				--in-place

.PHONY: format
format:
	black .

.PHONY: type
type:
	mypy --strict pyconlang


.PHONY: test
test:
	pytest -q


.PHONY: env
env:
	! [ -d .env ] && python3 -m venv .env || true

.PHONY: install
install:
	yes | pip uninstall pyconlang
	pip install -e .[test]

diagrams.html: pyconlang/lexicon/parser.py
	python -m pyconlang.lexicon.parser

.PHONY: clean
clean:
	rm -r .env
	rm diagrams.html
