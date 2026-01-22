# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a user with secrets and environment-specific values
I want to reference environment variables and secrets in my configs
So that I don't hardcode sensitive data in YAML files

**Success Looks Like:**
SUT configs and scenarios can use `{{env.VAR_NAME}}` syntax to read environment variables at runtime, keeping secrets out of version control and enabling environment-specific configuration.

## 2. Context & Constraints (Required)
**Background:**
Testing against real APIs requires authentication tokens, API keys, and environment-specific URLs. Currently, these must be hardcoded in YAML files, which is:
- A security risk (secrets in version control)
- Inflexible (can't switch environments without editing files)
- Non-standard (most tools support env var substitution)

**Scope:**
- **In Scope:** `{{env.VAR}}` syntax in SUT config and scenarios, error on missing required vars, optional default values, documentation
- **Out of Scope:** External secret managers (Vault, AWS Secrets Manager), encrypted config files, secret rotation

**Constraints:**
- Must work in both SUT config and scenario files
- Must fail clearly if required env var is missing
- Must not break existing `{{variable}}` template syntax
- Env vars resolved at config load time, not runtime

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Read environment variable in SUT config**
Given environment variable `API_KEY` is set to "secret123"
And SUT config contains `Authorization: "Bearer {{env.API_KEY}}"`
When the config is loaded
Then the header value is "Bearer secret123"

**Scenario: Read environment variable in scenario**
Given environment variable `TEST_USER_ID` is set to "user_456"
And scenario contains `customer_id: "{{env.TEST_USER_ID}}"`
When the scenario is loaded
Then the body contains `customer_id: "user_456"`

**Scenario: Missing required environment variable**
Given environment variable `API_KEY` is not set
And SUT config contains `Authorization: "Bearer {{env.API_KEY}}"`
When the config is loaded
Then an error is raised
And the error message includes "API_KEY"

**Scenario: Default value for missing variable**
Given environment variable `LOG_LEVEL` is not set
And config contains `level: "{{env.LOG_LEVEL | default:info}}"`
When the config is loaded
Then the value is "info"

**Scenario: Environment variable in base_url**
Given environment variable `API_HOST` is set to "https://staging.api.com"
And SUT config contains `base_url: "{{env.API_HOST}}"`
When the config is loaded
Then the service base_url is "https://staging.api.com"

**Scenario: Multiple environment variables**
Given `API_HOST` is "https://api.com" and `API_VERSION` is "v2"
And config contains `base_url: "{{env.API_HOST}}/{{env.API_VERSION}}"`
When the config is loaded
Then the value is "https://api.com/v2"

**Scenario: Coexistence with runtime templates**
Given SUT config contains `X-Correlation-ID: "{{correlation_id}}"`
And scenario contains `user: "{{env.TEST_USER}}"`
When configs are loaded and scenario runs
Then env vars are resolved at load time
And runtime templates are resolved at execution time

**Scenario: Environment variable in extract path**
Given environment variable `RESPONSE_PATH` is set to "$.data.id"
And scenario contains `extract: { order_id: "{{env.RESPONSE_PATH}}" }`
When the scenario is loaded
Then the extract path is "$.data.id"

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- `src/turbulence/config/loader.py` - Add env var resolution
- `src/turbulence/engine/template.py` - May need updates for two-phase resolution
- Add new `src/turbulence/config/env.py` for env resolution logic

**Must NOT Change:**
- Runtime template resolution (correlation_id, instance_id, etc.)
- Pydantic model definitions (resolve before validation)

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(config): add environment variable support with {{env.VAR}} syntax

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Works in SUT config (headers, base_url)
- [ ] Works in scenarios (body, path, headers)
- [ ] Clear error messages for missing vars
- [ ] Default value syntax works
- [ ] Documentation updated
- [ ] Code reviewed

## 7. Resources
- [12-Factor App Config](https://12factor.net/config)
- [envsubst](https://www.gnu.org/software/gettext/manual/html_node/envsubst-Invocation.html) - Inspiration for syntax

## 8. Example Configuration

```yaml
# sut.yaml
name: My API

services:
  api:
    base_url: "{{env.API_BASE_URL}}"
    timeout_seconds: 30

default_headers:
  Authorization: "Bearer {{env.API_TOKEN}}"
  X-Api-Key: "{{env.API_KEY | default:development-key}}"
```

```yaml
# scenarios/checkout.yaml
id: checkout
flow:
  - type: http
    name: login
    service: api
    method: POST
    path: /auth/login
    body:
      email: "{{env.TEST_USER_EMAIL}}"
      password: "{{env.TEST_USER_PASSWORD}}"
```

```bash
# Running with env vars
API_BASE_URL=https://staging.api.com \
API_TOKEN=secret_token_123 \
TEST_USER_EMAIL=test@example.com \
TEST_USER_PASSWORD=testpass \
turbulence run --sut sut.yaml --scenarios scenarios/ -n 10
```
