# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a user testing APIs over unreliable networks
I want automatic retry on transient failures
So that flaky infrastructure doesn't cause false test failures

**Success Looks Like:**
HTTP actions can be configured with retry policies that automatically retry on configurable conditions (5xx errors, timeouts, connection errors) with backoff strategies, without manual retry logic in scenarios.

## 2. Context & Constraints (Required)
**Background:**
Real-world APIs experience transient failures—network blips, momentary overloads, cold starts. Without retry logic, these cause test failures that don't reflect actual application bugs. Users currently have no way to handle this except manually duplicating steps or accepting false failures.

**Scope:**
- **In Scope:** Retry configuration on HTTP actions, configurable retry conditions (status codes, exceptions), backoff strategies (fixed, exponential), max attempts, retry logging in observations
- **Out of Scope:** Circuit breaker patterns, retry budgets across instances, retry on assertion failures

**Constraints:**
- Retries must be transparent in observations (show all attempts)
- Must not change behavior of existing scenarios (opt-in only)
- Backoff delays count toward action timeout
- Must work with parallel execution without blocking other instances

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Retry on 5xx status code**
Given an HTTP action configured with `retry: {on_status: [500, 502, 503], max_attempts: 3}`
When the first request returns 503
And the second request returns 200
Then the action succeeds
And the observation shows 2 attempts

**Scenario: Retry on timeout**
Given an HTTP action configured with `retry: {on_timeout: true, max_attempts: 3}`
When the first request times out
And the second request succeeds
Then the action succeeds
And the observation records the timeout attempt

**Scenario: Exponential backoff**
Given an HTTP action configured with `retry: {backoff: exponential, base_delay_ms: 100, max_attempts: 3}`
When retries occur
Then delay between attempt 1 and 2 is ~100ms
And delay between attempt 2 and 3 is ~200ms

**Scenario: Fixed backoff**
Given an HTTP action configured with `retry: {backoff: fixed, delay_ms: 500, max_attempts: 3}`
When retries occur
Then delay between each attempt is ~500ms

**Scenario: Max attempts exhausted**
Given an HTTP action configured with `retry: {max_attempts: 3}`
When all 3 attempts fail with 503
Then the action fails
And the observation shows all 3 attempts
And the final error is from the last attempt

**Scenario: No retry on 4xx**
Given an HTTP action configured with `retry: {on_status: [500, 502, 503]}`
When the request returns 400
Then no retry occurs
And the action fails immediately

**Scenario: Retry on connection error**
Given an HTTP action configured with `retry: {on_connection_error: true, max_attempts: 2}`
When the first request fails with connection refused
And the second request succeeds
Then the action succeeds

**Scenario: Default behavior unchanged**
Given an HTTP action with no retry configuration
When the request returns 503
Then no retry occurs
And the action fails as before

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- `src/turbulence/config/scenario.py` - Add RetryConfig model to HttpAction
- `src/turbulence/actions/http.py` - Implement retry logic
- `src/turbulence/models/observation.py` - Add retry attempt tracking

**Must NOT Change:**
- Default behavior of existing scenarios
- Wait action (has its own polling logic)
- Assert action (no HTTP to retry)

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(http): add configurable retry policies with backoff strategies

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Existing tests still pass (no breaking changes)
- [ ] Retry attempts visible in observations
- [ ] Backoff timing verified in tests
- [ ] Documentation updated
- [ ] Code reviewed

## 7. Resources
- [Exponential Backoff](https://en.wikipedia.org/wiki/Exponential_backoff)
- [httpx Retry Patterns](https://www.python-httpx.org/advanced/#custom-transports)
- [tenacity library](https://github.com/jd/tenacity) - Python retry library for reference

## 8. Example Configuration

```yaml
flow:
  - type: http
    name: call_flaky_api
    service: api
    method: GET
    path: /api/v1/orders
    retry:
      max_attempts: 3
      on_status: [500, 502, 503, 504]
      on_timeout: true
      on_connection_error: true
      backoff: exponential
      base_delay_ms: 100
      max_delay_ms: 5000
```
