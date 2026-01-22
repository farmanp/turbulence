# Architecture Overview

Turbulence is organized around a few core subsystems:

- **Config** (`src/turbulence/config/`): Pydantic models for SUT and scenarios.
- **Engine** (`src/turbulence/engine/`): Async execution, context, templating,
  and replay mechanics.
- **Actions** (`src/turbulence/actions/`): HTTP, wait, and assertion runners.
- **Storage** (`src/turbulence/storage/`): JSONL artifact persistence and
  summaries under `runs/<run_id>/`.
- **Report** (`src/turbulence/report/`): HTML report generation from artifacts.
- **API** (`src/turbulence/api/`): API service used by the web UI.
- **UI** (`ui/`): React + Vite dashboard.

## Execution Flow

1. The CLI loads SUT + scenario YAMLs.
2. `ParallelExecutor` schedules workflow instances.
3. Each instance runs a scenario flow, writing step + assertion artifacts.
4. Summary data is written at the end of the run.
5. Reports and replay consume the artifacts.

## Context and Templating

`WorkflowContext` stores run metadata, entry data, and extracted values. The
`TemplateEngine` renders action fields using this context, supporting both
simple substitutions and type-preserving single-variable templates.
