.PHONY: install test mypy lint format check coverage ci

install:
	uv sync --group dev

test:
	uv run pytest

mypy:
	uv run mypy py3votecore/

lint:
	uv run ruff check py3votecore/ test_functionality/ test_performance/

format:
	uv run ruff format py3votecore/ test_functionality/ test_performance/
	uv run ruff check --fix py3votecore/ test_functionality/ test_performance/

check: lint mypy

coverage:
	uv run coverage run
	uv run coverage report

ci: check test
