# Troubleshooting

## Config Load Errors

- Invalid YAML or missing required fields surface as `ConfigLoadError`.
- If you see a service-not-found error, verify `service` names match the SUT.

## Template Errors

- Missing variables cause a template error at runtime.
- Verify you are using valid context variables (see Templating page).

## JSONPath Errors

- Invalid JSONPath expressions are reported in `steps.jsonl` and console output.
- Start by validating the JSONPath against the response body.

## Timeouts

- `wait` actions can time out if `timeout_seconds` is too low.
- HTTP timeouts use the service `timeout_seconds` value.

## Replay Differences

- If replay shows differences, compare scenario definitions and SUT config
  between the original run and the replay.
