# Templating and Context

Windtunnel uses a Jinja2-based template engine for action fields like `path`,
`headers`, `query`, and `json`. Templates are rendered at execution time using
the current workflow context.

## Supported Context Values

Top-level variables available in templates:

- `run_id`
- `instance_id`
- `correlation_id`
- `entry` (the scenario entry block)
- Extracted values (from `extract`) stored at the top level

Example:

```yaml
path: /orders/{{cart_id}}
json:
  customer_id: "{{entry.seed_data.customer_id}}"
```

## Type Preservation

If a value is **only** a template variable (e.g., `"{{amount}}"`), the rendered
value keeps its original type instead of becoming a string.

## Last Response Helpers

After an HTTP or wait action, `last_response` is added to the context and is
usable by assertions and expressions:

- `last_response.status_code`
- `last_response.headers`
- `last_response.body`

## JSONPath

JSONPath is used in `extract` and assertions:

```yaml
extract:
  order_id: "$.id"

expect:
  jsonpath: "$.status"
  equals: "confirmed"
```

## Common Errors

- Missing variables cause a template error.
- Invalid JSONPath expressions are reported in the run artifacts and console.
