# Architecture Overview

Windtunnel is organized around a few core subsystems:

- **Config** (`src/windtunnel/config/`): Pydantic models for SUT and scenarios.
- **Engine** (`src/windtunnel/engine/`): Async execution, context, templating,
  and replay mechanics.
- **Actions** (`src/windtunnel/actions/`): HTTP, wait, and assertion runners.
- **Storage** (`src/windtunnel/storage/`): JSONL artifact persistence and
  summaries under `runs/<run_id>/`.
- **Report** (`src/windtunnel/report/`): HTML report generation from artifacts.
- **API** (`src/windtunnel/api/`): API service used by the web UI.
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
