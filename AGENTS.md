# Repository Guidelines

## Project Structure & Module Organization

- `src/turbulence/` contains the library and CLI implementation. Key modules include `actions/`, `commands/`, `config/`, `engine/`, `models/`, `report/`, and `storage/`.
- `ui/` hosts the React frontend (Vite + Tailwind) with `components/`, `pages/`, and `api/` clients.
- `docs/` houses the Docusaurus documentation site and user guides.
- `tests/` contains pytest suites and fixtures. Scenario samples live under `tests/fixtures/scenarios/`.
- `tickets/` holds planning and design notes for features and infra work.
- `use-cases/` contains validated scenario + SUT examples for common flows.
- Module-level `CLAUDE.md` files document local conventions; skim the nearest one before making changes in that area.

## Build, Test, and Development Commands

- `pip install -e ".[dev]"` installs the package in editable mode with dev tooling.
- `turbulence --help` verifies CLI wiring and lists available commands.
- `pytest tests/` runs the test suite.
- `ruff check src/ tests/` runs linting.
- `ruff format src/ tests/` formats code.
- `mypy src/` runs strict type checking.
- `npm run docs:start` runs the docs dev server.

## Coding Style & Naming Conventions

- Python 3.10+, 4-space indentation, line length 88.
- Prefer double quotes (Ruff formatter configuration).
- Type annotations are expected everywhere (`mypy` is strict and disallows untyped defs).
- Use snake_case for functions/modules, PascalCase for classes, and descriptive CLI command names.
- Prefer UTC-aware datetimes (`datetime.now(UTC)`).

## Testing Guidelines

- Framework: `pytest` with `pytest-asyncio` enabled (`asyncio_mode=auto`).
- Test files use `test_*.py` naming; fixtures live in `tests/fixtures/`.
- Add coverage for new actions, engine behavior, and CLI commands; include both success and error paths.

## Commit & Pull Request Guidelines

- Commit messages follow Conventional Commits patterns seen in history, e.g. `feat: ...` or `feat(engine): ...`.
- PRs should include: a short summary, testing notes (commands run), and any relevant `tickets/` references.
- Include screenshots for report/HTML changes (see `src/turbulence/report/templates/`).

## Configuration & Security Notes

- Scenario/SUT configs are YAML-based (see `tests/fixtures/` for examples).
- The lint rules include security checks (`ruff`’s `S` rules); resolve warnings before merging.
