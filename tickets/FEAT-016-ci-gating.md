# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a developer
I want CI to fail when metrics exceed thresholds
So that I can gate deployments on simulation quality

**Success Looks Like:**
CLI supports --fail-on conditions that evaluate against run metrics, returning exit code 2 when thresholds are violated.

## 2. Context & Constraints (Required)
**Background:**
Turbulence runs in CI pipelines to validate changes before deployment. Teams need configurable quality gates—minimum pass rates, maximum latencies—that fail the build when violated. This prevents regressions from reaching production.

**Scope:**
- **In Scope:** --fail-on flag parsing, metric evaluation, multiple conditions (AND logic), exit code 2 on violation
- **Out of Scope:** Complex condition expressions, OR logic, webhook notifications

**Constraints:**
- Exit code must be 2 (not 1) for threshold violations to distinguish from execution failures
- Multiple --fail-on flags combine with AND logic
- Must support pass_rate and latency metrics
- Must output which threshold(s) were violated

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Pass rate threshold**
Given --fail-on "pass_rate<0.98"
And the run achieves 97% pass rate
When the run completes
Then exit code is 2
And output indicates "pass_rate (0.97) < 0.98"

**Scenario: Latency threshold**
Given --fail-on "p95_latency_ms>1500"
And the run p95 latency is 1800ms
When the run completes
Then exit code is 2
And output indicates "p95_latency_ms (1800) > 1500"

**Scenario: Multiple thresholds (all pass)**
Given --fail-on "pass_rate<0.95" --fail-on "p99_latency_ms>3000"
And the run achieves 98% pass rate and 2500ms p99
When the run completes
Then exit code is 0

**Scenario: Multiple thresholds (one fails)**
Given --fail-on "pass_rate<0.95" --fail-on "p99_latency_ms>2000"
And the run achieves 98% pass rate and 2500ms p99
When the run completes
Then exit code is 2
And output indicates which threshold was violated

**Scenario: Threshold syntax validation**
Given --fail-on "invalid_syntax"
When the command parses arguments
Then an error indicates invalid threshold syntax
And valid syntax examples are shown

**Scenario: Available metrics documented**
Given --fail-on with --help
When I view the help text
Then available metrics are listed (pass_rate, p50_latency_ms, p95_latency_ms, p99_latency_ms, error_count)

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- Update src/turbulence/commands/run.py to add --fail-on
- Create src/turbulence/gating/__init__.py
- Create src/turbulence/gating/threshold.py for parsing and evaluation

**Must NOT Change:**
- Core run execution
- Report generation
- Artifact storage

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(cli): add --fail-on threshold gating for CI pipelines

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Tests verify threshold parsing and evaluation
- [ ] Code reviewed
- [ ] No breaking changes
- [ ] Exit codes are correct for all scenarios

## 7. Resources
- [CLI Exit Codes](https://tldp.org/LDP/abs/html/exitcodes.html)

## Example CI Usage
```yaml
# GitHub Actions example
- name: Run Turbulence simulation
  run: |
    turbulence run \
      --sut sut.yaml \
      --scenarios scenarios/ \
      --n 1000 \
      --parallel 50 \
      --fail-on "pass_rate<0.99" \
      --fail-on "p95_latency_ms>1000"

# Exit codes:
# 0 - All thresholds passed
# 1 - Execution error (config invalid, service unreachable, etc.)
# 2 - Threshold violation (quality gate failed)
```
