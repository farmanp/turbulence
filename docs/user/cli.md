# CLI Reference

Windtunnel exposes four primary commands.

## `windtunnel run`

Execute workflow simulations against a SUT.

```bash
windtunnel run --sut sut.yaml --scenarios scenarios/ --n 100 --parallel 25
```

Options:

- `--sut, -s` (required): Path to the SUT YAML file.
- `--scenarios, -c` (required): Directory of scenario YAML files.
- `--n, -n`: Number of workflow instances to run (default: 100).
- `--parallel, -p`: Max concurrent instances (default: engine default).
- `--seed`: Random seed for reproducible runs.
- `--output, -o`: Output directory for artifacts (default: `runs`).

## `windtunnel report`

Generate an HTML report from run artifacts.

```bash
windtunnel report --run-id run_20240115_001
```

Options:

- `--run-id, -r` (required): Run ID to report on.
- `--runs-dir, -d`: Directory containing run artifacts (default: `runs`).
- `--output, -o`: Output path (default: `runs/<run_id>/report.html`).

## `windtunnel replay`

Replay a specific instance for debugging.

```bash
windtunnel replay --run-id run_20240115_001 --instance-id inst_042
```

Options:

- `--run-id, -r` (required): Run ID that contains the instance.
- `--instance-id, -i` (required): Instance ID to replay.
- `--runs-dir, -d`: Directory containing run artifacts (default: `runs`).
- `--scenarios, -c`: Directory of scenario definitions (optional).
- `--sut, -s`: SUT config path (optional).
- `--verbose, -v`: Print per-step details.

## `windtunnel serve`

Serve the Web UI and API server.

```bash
windtunnel serve --runs-dir runs/ --port 8000
```

`windtunnel serve` requires `uvicorn` to be installed.

Options:

- `--runs-dir, -d`: Directory containing run artifacts (default: `runs`).
- `--port, -p`: Port to bind (default: 8000).
- `--host, -h`: Host to bind (default: 127.0.0.1).
- `--static-dir`: Directory containing built frontend assets.
