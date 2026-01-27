# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a Turbulence developer
I want a centralized way to manage connection lifecycles for different protocols
So that I can efficiently reuse clients (HTTP, gRPC, Kafka) across concurrent workflow instances.

**Success Looks Like:**
An internal `ClientPool` or `ConnectionManager` service that provides pre-configured clients based on service definitions, handling initialization and cleanup.

## 2. Context & Constraints (Required)
**Background:**
Currently, `ScenarioRunner` creates a new `httpx.AsyncClient` for each run. As we add gRPC and Kafka, managing many persistent connections becomes critical for performance and resource usage.

**Scope:**
- **In Scope:** `ClientPool` class, per-service client caching, graceful shutdown of connections.
- **Out of Scope:** Global pooling across different simulation runs (keep it scoped to a single `run` command execution).

**Constraints:**
- Must handle the lifecycle of `httpx.AsyncClient`, gRPC channels, and Kafka producers.
- Must be thread-safe (though primarily used in an async context).

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Reuse HTTP client**
Given two workflow instances hitting the same "api" service
When they request a client from the pool
Then they receive the same `httpx.AsyncClient` instance
And the client remains open until the simulation completes

## 4. AI Execution Instructions (Required)
- Implement `src/turbulence/engine/client_pool.py`.
- Refactor `ScenarioRunner` to use the pool instead of creating clients inline.
- Ensure all clients are closed when the simulation finishes.

## 5. Planned Git Commit Message(s) (Required)
- feat(engine): add ClientPool for unified connection management

## 6. Verification & Definition of Done (Required)
- [x] Clients are correctly reused across instances.
- [x] No connection leaks are detected.
- [x] Cleanup logic is verified to run on simulation completion.
