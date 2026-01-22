# Turbulence (Fault Injection)

Scenarios can include optional `turbulence` settings to inject latency, timeouts,
or retries. This is useful for resilience testing.

## Example

```yaml
id: checkout-with-latency

turbulence:
  global:
    latency_ms:
      min: 50
      max: 200

  services:
    payments:
      timeout_after_ms: 1500

  actions:
    process_payment:
      retry_count: 2
```

## Policy Resolution

When a request executes, Windtunnel resolves turbulence policies in this order:

1. Global policy
2. Service-specific policy
3. Action-specific policy

Later policies override earlier ones for the same field.
