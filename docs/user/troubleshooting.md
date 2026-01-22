# Troubleshooting

## Config Load Errors

- **Symptom:** `ConfigLoadError: Service 'payment' not found`
- **Cause:** You referenced `service: payment` in your scenario, but your `sut.yaml` only defines other services (e.g., `api`).
- **Solution:** Verify the `service` name in your scenario matches a key in the `services` dictionary of your SUT config.

- **Symptom:** `ValidationError` parsing YAML
- **Cause:** Missing required fields or invalid types (e.g., `port` is a string instead of an int).
- **Solution:** Check your YAML against the schema definitions in the documentation.

## Template Errors

- **Symptom:** `TemplateError: 'user_id' is undefined`
- **Cause:** You used `{{user_id}}` in a template, but that variable does not exist in the current context.
- **Solution:** Ensure the variable was added to the context via `seed_data` or an `extract` block in a previous step.

## JSONPath Errors

- **Symptom:** `JSONPathError` or empty extraction results.
- **Cause:** The path expression does not match the structure of the response.
- **Solution:** 
    1. Check `steps.jsonl` to see the actual response body received.
    2. Test your JSONPath against that body using an online evaluator.
    3. Remember `extract` values are typically under `$.key`.

## Timeouts

- **Symptom:** `TimeoutError` in logs or report.
- **Cause:** 
    - `wait` actions: The condition wasn't met within `timeout_seconds`.
    - `http` actions: The server took longer than the configured timeout to respond.
- **Solution:** Increase `timeout_seconds` or investigate why the SUT is slow/unresponsive.

## Replay Differences

- If replay shows differences, compare scenario definitions and SUT config
  between the original run and the replay.
