# Contributing

Thanks for helping improve Turbulence.

## Workflow

1. Check `tickets/` for active work and context.
2. Create a feature branch.
3. Keep changes scoped and tested.

## Code Style

- Python 3.10+ and type annotations everywhere.
- 4-space indentation, line length 88.
- Prefer double quotes.

## Tests and Checks

```bash
pytest tests/
ruff check src/ tests/
mypy src/
```

## Pull Requests

- Use Conventional Commits for commit messages.
- Include a summary and tests run.
- Add screenshots for report/HTML changes.
