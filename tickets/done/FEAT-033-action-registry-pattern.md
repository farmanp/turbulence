# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a Turbulence developer
I want a central registry for action runners
So that I can easily add support for new protocols (gRPC, Kafka, etc.) without modifying the core execution engine.

**Success Looks Like:**
The `ScenarioRunner` uses an `ActionRunnerFactory` to create action runners based on the `type` field in the scenario action, replacing the existing `isinstance` check chains.

## 2. Context & Constraints (Required)
**Background:**
Currently, `ScenarioRunner` has hardcoded logic to decide which runner to use for each action type. This makes the engine brittle and hard to extend for non-HTTP protocols. A registry pattern decouples action definitions from their execution logic.

**Scope:**
- **In Scope:** `ActionRunnerFactory` class, `register` method for runners, integration into `ScenarioRunner`.
- **Out of Scope:** Implementation of new protocol runners (separate tickets).

**Constraints:**
- Must maintain backward compatibility with existing HTTP, Wait, and Assert actions.
- Must support dynamic registration of runners at package initialization.

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Action dispatch via factory**
Given a scenario with an "http" action
When the scenario runner executes the step
Then it requests a runner from the `ActionRunnerFactory`
And the factory returns an instance of `HttpActionRunner`

**Scenario: Registering a new action type**
Given a new custom action runner class
When I register it with `ActionRunnerFactory.register("custom", CustomRunner)`
Then I can execute scenarios containing actions with `type: custom`

## 4. AI Execution Instructions (Required)
- Create `src/turbulence/actions/factory.py`.
- Implement `ActionRunnerFactory` with `register` and `create` methods.
- Update `src/turbulence/engine/scenario_runner.py` to use the factory for action dispatch.
- Register existing runners in `src/turbulence/actions/__init__.py`.

## 5. Planned Git Commit Message(s) (Required)
- feat(engine): implement ActionRunnerFactory for dynamic action dispatch

## 6. Verification & Definition of Done (Required)
- [x] Factory correctly dispatches existing action types.
- [x] Unit tests for `ActionRunnerFactory` pass.
- [x] Integration tests for `ScenarioRunner` pass.
- [x] No regressions in existing simulation runs.
