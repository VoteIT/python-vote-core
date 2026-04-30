# Changelog

## 2.0.0 (2026-04-30)

- Renamed and forked project to avoid version trouble. (Old version used date, not semantic versioning)
- Migrated to `uv` for package and dependency management.
- Added support for Python 3.13 and 3.14.
- Added `Makefile` with developer targets: `install`, `test`, `mypy`, `lint`, `format`, `check`, `coverage`, `ci`.
- Added `ruff` for formatting and linting.
- Added full static type annotations throughout the source code (`mypy` clean).
- **Fix**: STV quota was not updated after a ballot reset, causing winner determination and surplus redistribution to use the original (lower) quota instead of the recalculated one. This could produce incorrect winners in multi-seat elections where ballots exhaust before all seats are filled.
- **Fix**: Schulze/Condorcet methods mutated the caller's ballot data in-place when converting from grouping or ranking notation to rating format. Input ballots are now deep-copied so reuse is safe.

## Older versions (py-vote-core / python-vote-core)

### 20110509.1

- Fixing PyPi release

### 20110509.0

- Initial PyPi release
