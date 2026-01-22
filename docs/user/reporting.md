# Reports and Artifacts

Every run creates a directory under `runs/<run_id>/` with JSONL artifacts and
metadata. These are used to generate HTML reports and replay instances.

## Artifact Layout

- `manifest.json`: Run metadata, seed, and configuration.
- `instances.jsonl`: One line per instance with status and timings.
- `steps.jsonl`: One line per executed step with observations.
- `assertions.jsonl`: Assertion results and messages.
- `summary.json`: Aggregated statistics.
- `artifacts/`: Optional per-instance raw data.

## HTML Reports

Generate a report from a run:

```bash
turbulence report --run-id <run_id>
```

The HTML file defaults to `runs/<run_id>/report.html`.
