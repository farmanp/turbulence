# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a Turbulence developer
I want a protocol-agnostic Observation model
So that I can store results from diverse protocols like gRPC, Kafka, and SQL in a consistent format.

**Success Looks Like:**
The `Observation` model includes `protocol` and `metadata` fields, while keeping legacy HTTP fields for backward compatibility.

## 2. Context & Constraints (Required)
**Background:**
The current `Observation` model is highly focused on HTTP (status_code, headers). To support multi-protocol transport, we need a more flexible structure that can hold protocol-specific metadata without bloating the top-level schema.

**Scope:**
- **In Scope:** Updating `Observation` Pydantic model, adding `protocol` discriminator, adding `metadata` dict.
- **Out of Scope:** Changing the JSONL storage format (it's already untyped/flexible).

**Constraints:**
- Must keep `status_code` and `headers` fields for backward compatibility.
- Must ensure `latency_ms` and `ok` remain the core metrics for all protocols.

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: gRPC Observation**
Given a gRPC action execution
When the observation is created
Then `protocol` is set to "grpc"
And `metadata` contains gRPC-specific info (trailers, status code)
And `body` contains the response message

## 4. AI Execution Instructions (Required)
- Update `src/turbulence/models/observation.py`.
- Add `protocol: str = "http"` field.
- Add `metadata: dict[str, Any]` field.
- Ensure all existing fields are preserved.

## 5. Planned Git Commit Message(s) (Required)
- feat(models): evolve Observation model for multi-protocol support

## 6. Verification & Definition of Done (Required)
- [x] Pydantic model validation passes for both HTTP and non-HTTP observations.
- [x] Existing reporting logic (which uses `status_code`) continues to work.
- [x] Tests for `Observation` model pass.
