# Scenario Authoring

Scenarios describe a workflow as a sequence of actions and assertions. Each
scenario is a YAML file in your scenarios directory.

## Structure

```yaml
id: checkout-happy-path
description: Complete checkout flow with payment

entry:
  seed_data:
    customer_id: "cust_001"
    cart_items:
      - sku: "WIDGET-001"
        quantity: 2
        price: 29.99

flow:
  - name: create_cart
    type: http
    service: api
    method: POST
    path: /carts
    json:
      customer_id: "{{entry.seed_data.customer_id}}"
      items: "{{entry.seed_data.cart_items}}"
    extract:
      cart_id: "$.id"

  - name: wait_for_confirmation
    type: wait
    service: api
    method: GET
    path: /orders/{{cart_id}}
    interval_seconds: 1
    timeout_seconds: 30
    expect:
      jsonpath: "$.status"
      equals: "confirmed"

assertions:
  - name: cart_confirmed
    expect:
      status_code: 200
      jsonpath: "$.status"
      equals: "confirmed"

stop_when:
  any_action_fails: true
  any_assertion_fails: true

max_steps: 50
```

## Actions

Turbulence supports three action types:

### HTTP Action

```yaml
- name: create_cart
  type: http
  service: api
  method: POST
  path: /carts
  headers:
    X-Trace: "{{correlation_id}}"
  query:
    verbose: "true"
  json:
    customer_id: "{{entry.seed_data.customer_id}}"
  extract:
    cart_id: "$.id"
  retry:
    max_attempts: 3
    on_status: [500, 502, 503]
    on_timeout: true
    backoff: exponential
    base_delay_ms: 100
```

- `extract` values use JSONPath. Extracted values become top-level context
  variables for later actions.
- `retry` (optional) configures automatic retries on failure.

### Retry Configuration

HTTP actions support configurable retry policies:

- `max_attempts` (default: 3): Total attempts including the first one.
- `on_status` (default: []): List of status codes to retry (e.g., `[500, 503]`).
- `on_timeout` (default: false): Retry on request timeout.
- `on_connection_error` (default: false): Retry on connection refused/error.
- `backoff` (default: "exponential"): "fixed" or "exponential".
- `delay_ms` (default: 1000): Delay for fixed backoff.
- `base_delay_ms` (default: 100): Initial delay for exponential backoff.
- `max_delay_ms` (default: 10000): Max delay for exponential backoff.

### Wait Action

Use `wait` to poll until a condition is met or timeout occurs.

```yaml
- name: wait_for_confirmation
  type: wait
  service: api
  method: GET
  path: /orders/{{cart_id}}
  interval_seconds: 1
  timeout_seconds: 30
  expect:
    jsonpath: "$.status"
    equals: "confirmed"
```

### Assert Action

Inline assertions validate expectations against the last response.

```yaml
- name: status_ok
  type: assert
  expect:
    status_code: 200
```

## Final Assertions

Assertions can also run at the end of the workflow:

```yaml
assertions:
  - name: cart_not_empty
    expect:
      jsonpath: "$.items"
      contains: "WIDGET-001"
```

## Stop Conditions

`stop_when` controls when a workflow should stop early:

- `any_action_fails`: stop if any action fails.
- `any_assertion_fails`: stop if any assertion fails.

## Limits

- `max_steps` caps the total number of steps executed per instance.
