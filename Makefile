.PHONY: install test mypy lint format check coverage ci \
        build check-dist release-notes preview-release tag release-test release

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

# ── Release workflow ────────────────────────────────────────────────────────
#
#  1. Update `version` in pyproject.toml.
#  2. Update CHANGES.md: replace "(unreleased)" with today's date.
#  3. make preview-release   → builds, validates metadata + README, prints release notes.
#  4. make release-test      → uploads to TestPyPI; inspect the page before going live.
#  5. Commit and tag:
#       git commit -am "Release v$(VERSION)"
#       make tag
#       git push && git push origin v$(VERSION)
#  6. make release           → publishes to PyPI.
#
# TestPyPI credentials go in ~/.pypirc or TWINE_* env vars.
# PyPI credentials: uv publish uses UV_PUBLISH_TOKEN or ~/.pypirc.
# ───────────────────────────────────────────────────────────────────────────

VERSION := $(shell grep '^version = ' pyproject.toml | sed 's/version = "\(.*\)"/\1/')
PACKAGE := $(shell grep '^name = ' pyproject.toml | sed 's/name = "\(.*\)"/\1/')

build:
	rm -rf dist/
	uv build

check-dist: build
	uv run twine check --strict dist/*

release-notes:
	@awk '/^## $(VERSION)/{p=1;next} p&&/^## /{exit} p' CHANGES.md

preview-release: check-dist
	@echo "━━━ $(PACKAGE) v$(VERSION) ━━━"
	@echo ""
	@echo "Built artifacts:"
	@ls -lh dist/
	@echo ""
	@echo "Release notes (from CHANGES.md):"
	@echo "──────────────────────────────────"
	@$(MAKE) --no-print-directory release-notes

tag:
	git tag -a "v$(VERSION)" -m "Release $(VERSION)"
	@echo "Created tag v$(VERSION). Push with: git push origin v$(VERSION)"

release-test: check-dist
	uv publish --publish-url https://test.pypi.org/legacy/
	@echo ""
	@echo "Inspect at: https://test.pypi.org/project/$(PACKAGE)/"

release: check-dist
	uv publish
	@echo ""
	@echo "Published: https://pypi.org/project/$(PACKAGE)/$(VERSION)/"
