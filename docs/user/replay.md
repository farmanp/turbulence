# Replay

Replay executes a single workflow instance again using the stored artifacts.
This is useful for debugging failures or verifying fixes.

## Usage

```bash
turbulence replay --run-id run_20240115_001 --instance-id inst_042
```

Optional flags:

- `--scenarios, -c` to provide scenario YAMLs if you want to override or inspect
  updated scenario definitions.
- `--sut, -s` to point at a specific SUT config.
- `--verbose, -v` for step-by-step output and latency details.

## What Gets Replayed

Replay uses the stored run context (correlation ID, extracted data, and the
original scenario flow) to reproduce the instance as closely as possible.
