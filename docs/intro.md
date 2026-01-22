---
sidebar_position: 1
slug: /
---

# Turbulence Docs

Turbulence is a workflow simulation and testing framework for distributed
systems. You model user journeys in YAML, run them concurrently with the async
engine, and get JSONL artifacts plus a rich HTML report for analysis.

Use the **User Guide** to get running quickly and author scenarios. The
**Developer Guide** covers internals, local development, and testing.

## Core Workflow

1. Define a System Under Test (SUT) in YAML.
2. Create one or more scenario YAML files describing the workflow steps.
3. Run `turbulence run` to execute instances and store artifacts under `runs/`.
4. Generate reports with `turbulence report` or replay a single instance with
   `turbulence replay`.

If you are new, start with **User Guide → Getting Started**.

## Next Steps

- **I want to write tests:** Go to [Scenario Authoring](/user/scenario-authoring) to learn how to define workflows.
- **I want to understand the code:** Check out the [Architecture Decomposition](/architecture/decomposition) to see how the system is built.
- **I want to contribute:** Read the [Contributing Guide](/developer/contributing) for setup instructions.
