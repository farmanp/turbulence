# AI-Ready Story Template (Core)

## 1. Intent (Required)
**User Story:**
As a user testing across multiple environments (dev, staging, prod)
I want to easily switch between environment configurations
So that I can run the same scenarios against different targets without editing files

**Success Looks Like:**
Users can define environment profiles and switch between them with a CLI flag, enabling the same scenarios to run against development, staging, or production with appropriate URLs, credentials, and settings.

## 2. Context & Constraints (Required)
**Background:**
Teams test against multiple environments—local development, CI staging, production smoke tests. Currently, users must:
- Maintain separate SUT config files per environment
- Manually swap files or edit URLs before runs
- Risk accidentally testing against wrong environment

Environment profiles solve this by centralizing environment differences and making switching explicit and safe.

**Scope:**
- **In Scope:** Profile definition in SUT config, CLI flag to select profile, profile inheritance/overrides, default profile
- **Out of Scope:** Remote profile storage, dynamic profile switching mid-run, profile-specific scenarios

**Constraints:**
- Must be backward compatible (existing SUT configs work unchanged)
- Profile selection must be explicit (no silent defaults to production)
- Profiles only affect SUT config, not scenario logic
- Works with environment variables (FEAT-031)

## 3. Acceptance Criteria (Required)
*Format: Gherkin (Given/When/Then)*

**Scenario: Define and use profiles**
Given a SUT config with profiles for "staging" and "production"
When I run with `--profile staging`
Then the staging base_url and headers are used

**Scenario: Profile overrides base config**
Given a SUT config with base `timeout_seconds: 30`
And staging profile with `timeout_seconds: 60`
When I run with `--profile staging`
Then timeout is 60 seconds

**Scenario: Profile inherits from base**
Given a SUT config with base `default_headers: {Accept: application/json}`
And staging profile with only `base_url` override
When I run with `--profile staging`
Then Accept header is still "application/json"

**Scenario: Missing profile error**
Given a SUT config without a "production" profile
When I run with `--profile production`
Then an error is raised
And available profiles are listed

**Scenario: Default profile**
Given a SUT config with `default_profile: staging`
When I run without `--profile` flag
Then staging profile is used

**Scenario: No default profile**
Given a SUT config with profiles but no default
When I run without `--profile` flag
Then the base config (no profile) is used

**Scenario: List available profiles**
Given a SUT config with staging, production, and local profiles
When I run `turbulence profiles --sut sut.yaml`
Then it lists: staging, production, local

**Scenario: Profile with environment variables**
Given staging profile with `base_url: "{{env.STAGING_URL}}"`
And STAGING_URL is set to "https://staging.api.com"
When I run with `--profile staging`
Then base_url is "https://staging.api.com"

**Scenario: Backward compatibility**
Given a SUT config without any profiles section
When I run without `--profile` flag
Then it works exactly as before

## 4. AI Execution Instructions (Required)
**Allowed to Change:**
- `src/turbulence/config/sut.py` - Add profiles model
- `src/turbulence/config/loader.py` - Profile resolution logic
- `src/turbulence/commands/run.py` - Add --profile CLI option
- `src/turbulence/cli.py` - Add profiles list command

**Must NOT Change:**
- Scenario file format
- Observation/artifact format
- Existing SUT configs without profiles must work unchanged

**Ambiguity Rule:**
If unclear, acceptance criteria override all other sections.

## 5. Planned Git Commit Message(s) (Required)
- feat(config): add environment profiles for multi-target testing

## 6. Verification & Definition of Done (Required)
- [ ] Acceptance criteria pass
- [ ] Backward compatible with existing SUT configs
- [ ] CLI --profile flag works
- [ ] Profile inheritance/override works correctly
- [ ] Clear error messages for missing profiles
- [ ] `turbulence profiles` command works
- [ ] Documentation updated
- [ ] Code reviewed

## 7. Resources
- [Spring Profiles](https://docs.spring.io/spring-boot/docs/current/reference/html/features.html#features.profiles) - Inspiration
- [AWS CLI Profiles](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-profiles.html) - Similar pattern

## 8. Example Configuration

```yaml
# sut.yaml
name: My E-commerce API

# Base configuration (shared across all profiles)
default_headers:
  Accept: application/json
  X-Correlation-ID: "{{correlation_id}}"

services:
  api:
    base_url: "http://localhost:8080"
    timeout_seconds: 30
  payments:
    base_url: "http://localhost:8081"
    timeout_seconds: 60

# Environment profiles
profiles:
  local:
    # Uses base config as-is

  staging:
    services:
      api:
        base_url: "https://staging-api.mystore.com"
      payments:
        base_url: "https://staging-payments.mystore.com"
    default_headers:
      Authorization: "Bearer {{env.STAGING_API_TOKEN}}"

  production:
    services:
      api:
        base_url: "https://api.mystore.com"
        timeout_seconds: 10  # Stricter timeout in prod
      payments:
        base_url: "https://payments.mystore.com"
        timeout_seconds: 30
    default_headers:
      Authorization: "Bearer {{env.PROD_API_TOKEN}}"

# Optional: set default profile
default_profile: local
```

```bash
# Usage examples
turbulence run --sut sut.yaml --scenarios scenarios/ -n 10 --profile staging

turbulence run --sut sut.yaml --scenarios scenarios/ -n 5 --profile production

# List available profiles
turbulence profiles --sut sut.yaml
# Output:
# Available profiles for "My E-commerce API":
#   - local (default)
#   - staging
#   - production
```
