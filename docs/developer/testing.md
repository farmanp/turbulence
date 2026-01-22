# Testing and Quality

## Tests

```bash
pytest tests/
```

## Linting

```bash
ruff check src/ tests/
```

## Type Checking

```bash
mypy src/
```

## Notes

- `pytest-asyncio` is enabled with `asyncio_mode=auto`.
- Keep new code fully typed (`mypy` is strict).
- Add tests for new actions, engine behavior, and CLI commands.
