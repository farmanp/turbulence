# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a user
I want to define diverse service types (HTTP, gRPC, Kafka) in my SUT config
So that I can test complex microservices architectures within a single configuration.

**Success Looks Like:**
The `Service` model in `SUTConfig` supports multiple protocols through a discriminated union or polymorphic configuration blocks.

## 2. Context & Constraints (Required)
**Background:**
Currently, `Service.base_url` is typed as `HttpUrl`, which strictly blocks any non-HTTP protocol. We need to allow services to define protocol-specific connection details (host/port for gRPC, bootstrap servers for Kafka).

**Scope:**
- **In Scope:** `HttpServiceConfig`, `GrpcServiceConfig`, `KafkaServiceConfig` models. Updating `Service` to be polymorphic.
- **Out of Scope:** Editing SUT configs in the Web UI.

**Constraints:**
- Must maintain backward compatibility for existing SUT configs using the top-level `base_url`.
- Use Pydantic's `model_validator(mode="after")` to automatically migrate legacy HTTP fields to the new structured format.

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Load legacy HTTP config**
Given an old SUT config with `base_url: "http://api.com"`
When the config is loaded
Then it is automatically migrated to the `http` config block internally
And `protocol` is set to "http"

**Scenario: Load gRPC config**
Given a SUT config with `protocol: grpc` and a `grpc` block
When the config is loaded
Then it validates the `host` and `port` fields
And it correctly populates the `GrpcServiceConfig` model

## 4. AI Execution Instructions (Required)
- Update `src/turbulence/config/sut.py`.
- Define `HttpServiceConfig`, `GrpcServiceConfig`, and `KafkaServiceConfig`.
- Update `Service` to include `protocol` and optional protocol-specific config blocks.
- Implement migration logic in a model validator.
- Update `ProfileService` to support these new fields for environment overrides.

## 5. Planned Git Commit Message(s) (Required)
- feat(config): implement polymorphic Service model for multi-protocol support

## 6. Verification & Definition of Done (Required)
- [x] Legacy SUT configs load and validate correctly.
- [x] gRPC and Kafka service definitions validate correctly.
- [x] Profile overrides work for new protocol blocks.
- [x] Tests in `tests/test_sut_config.py` and `tests/test_sut_profiles.py` pass.
