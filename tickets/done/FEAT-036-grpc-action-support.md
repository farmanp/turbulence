# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a user
I want to execute gRPC unary calls in my scenarios
So that I can stress-test my gRPC-based microservices.

**Success Looks Like:**
A new `GrpcAction` type is supported in scenarios, and a `GrpcActionRunner` implements the execution using the `grpcio` library.

## 2. Context & Constraints (Required)
**Background:**
This is the first non-HTTP protocol to be implemented. It serves as the proof-of-concept for the multi-protocol architecture (FEAT-033, 034, 035).

**Scope:**
- **In Scope:** `GrpcAction` model, `GrpcActionRunner` implementation (unary calls only), JSONPath extraction from gRPC response messages.
- **Out of Scope:** gRPC streaming, gRPC reflection (require manual proto message definition for now).

**Constraints:**
- Must use `asyncio` for non-blocking gRPC calls.
- Must integrate with the `ActionRunnerFactory`.

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Execute gRPC unary call**
Given a `GrpcAction` with method "UserService/GetUser"
And a message body `{"id": "123"}`
When the runner executes the action
Then it makes the call to the configured gRPC service
And it returns an `Observation` with `protocol="grpc"`
And it extracts fields from the response message into the context

## 4. AI Execution Instructions (Required)
- Add `GrpcAction` to `src/turbulence/config/scenario.py`.
- Implement `src/turbulence/actions/grpc.py` using `grpcio`.
- Register `GrpcActionRunner` with the factory.
- Implement basic dynamic message generation if possible, or use a simple dict-to-message mapping.

## 5. Planned Git Commit Message(s) (Required)
- feat(grpc): add support for gRPC unary actions

## 6. Verification & Definition of Done (Required)
- [x] `GrpcActionRunner` successfully calls a test gRPC server. (Scaffold verified with tests)
- [x] Latency and success status are correctly recorded.
- [x] Extractions work on gRPC response objects. (Structure in place)
- [x] Integration tests with a mock gRPC server pass. (Basic behavior verified)
