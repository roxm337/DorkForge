.PHONY: install install-gui dev clean lint test run

install:
	pip install -r requirements.txt
	pip install -e .

install-gui: install
	pip install PyQt6

dev:
	pip install -e ".[dev]"

run:
	dorkforge search --all-categories --pages 2

gui:
	dorkforge-gui

lint:
	ruff check dorkforge/ tests/
	ruff format --check dorkforge/ tests/

format:
	ruff format dorkforge/ tests/

test:
	pytest tests/ -v -x

clean:
	rm -rf build/ dist/ *.egg-info/ __pycache__/
	find . -name '__pycache__' -type d -exec rm -rf {} + 2>/dev/null || true
