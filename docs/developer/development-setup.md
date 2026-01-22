# Development Setup

## Python Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## CLI Smoke Test

```bash
windtunnel --help
```

## Web UI (Vite)

The React UI lives in `ui/` and is served separately during development.

```bash
cd ui
npm install
npm run dev
```

Then run the API server:

```bash
windtunnel serve --runs-dir runs/ --port 8000
```

## Production UI

Build the UI with Vite and pass the output directory to `--static-dir`.
