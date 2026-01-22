# SUT Configuration

The System Under Test (SUT) config describes the services Turbulence will call.
It is required for every run.

## Schema Overview

```yaml
name: ecommerce-checkout

default_headers:
  X-Run-ID: "{{run_id}}"
  X-Correlation-ID: "{{correlation_id}}"
  Content-Type: "application/json"
  Authorization: "Bearer {{env.API_TOKEN}}"

services:
  api:
    base_url: "{{env.API_BASE_URL}}"
    timeout_seconds: 30
  payments:
    base_url: "{{env.PAYMENTS_BASE_URL}}"
    headers:
      X-API-Key: "{{env.PAYMENTS_API_KEY | default:dev-key}}"
    timeout_seconds: 10
```

## Fields

- `name` (required): Display name for the system under test.
- `default_headers` (optional): Headers merged into every request. Templates are
  rendered at runtime using the workflow context.
- `services` (required): Map of service names to service configs.

### Service Config

- `base_url` (required): Base URL for the service. A trailing slash is stripped.
- `headers` (optional): Service-specific headers that override defaults.
- `timeout_seconds` (optional): Per-service request timeout (default: 30.0).

## Header Merge Order

When a request executes, headers are merged in this order:

1. `default_headers`
2. `services.<service>.headers`
3. Action-level `headers`

Later values override earlier values.

## Environment Profiles

Profiles allow you to define environment-specific overrides in a single config file.
Use the `--profile <name>` CLI flag to activate a profile.

```yaml
name: ecommerce-checkout

default_headers:
  Accept: application/json

services:
  api:
    base_url: "http://localhost:8080"
    timeout_seconds: 30

# Optional default profile
default_profile: local

profiles:
  local:
    # Inherits everything from base
    services: {}

  staging:
    services:
      api:
        base_url: "https://staging-api.example.com"
        # Inherits timeout_seconds: 30

  production:
    default_headers:
      Authorization: "Bearer {{env.PROD_TOKEN}}"
    services:
      api:
        base_url: "https://api.example.com"
        timeout_seconds: 10
```

### Profile Inheritance
- Profiles inherit all settings from the base configuration.
- **Service fields** (`base_url`, `timeout_seconds`) overwrite the base value if specified in the profile.
- **Headers** are merged: profile headers overwrite base headers with the same key, but keep others.

### Usage
```bash
# Use default profile (or base config if no default)
turbulence run -s sut.yaml -c scenarios/

# Use staging profile
turbulence run -s sut.yaml -c scenarios/ --profile staging

# List available profiles
turbulence profiles --sut sut.yaml
```
