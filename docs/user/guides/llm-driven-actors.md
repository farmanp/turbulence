# LLM-Driven Actors

This guide explains how to use LLM-powered personas to create realistic, varied user behavior in your load tests. Instead of hand-coding every decision path, you describe personas in natural language and let an LLM generate behavior policies.

## The Problem

Traditional load tests execute the same deterministic flow for every virtual user. Real users behave differently:

- **Impatient shoppers** add items directly to cart without reading details
- **Careful researchers** view product details, read reviews, compare options
- **Window shoppers** browse extensively but rarely purchase

Modeling this variety by hand requires complex branching logic and probability tuning. LLM-Driven Actors solve this by:

1. **Generating** behavior policies from natural language personas (pre-test)
2. **Executing** weighted random decisions without LLM calls (during test)
3. **Analyzing** results with AI insights (post-test)

## Architecture

```
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│   GENERATE          │     │   EXECUTE           │     │   ANALYZE           │
│                     │     │                     │     │                     │
│ turbulence generate │ ──▶ │ turbulence run      │ ──▶ │ turbulence analyze  │
│                     │     │ --policies ...      │     │                     │
│ Personas → Policies │     │ No LLM calls        │     │ Results → Insights  │
│ (~$0.50 per gen)    │     │ Fast, deterministic │     │ (~$0.25 per run)    │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
```

**Key insight:** LLM calls happen *before* and *after* the test, never during execution. This keeps tests fast, reproducible, and cost-effective.

## Quick Start

### 1. Define Personas

Create a `personas.yaml` file describing your user types:

```yaml
personas:
  - id: impatient_shopper
    description: |
      A busy professional who values speed over thoroughness.
      - Adds items to cart immediately without viewing details
      - Abandons checkout if anything takes too long
      - Prefers one-click purchase options
      - Rarely browses, knows what they want

  - id: careful_researcher
    description: |
      A methodical buyer who researches before purchasing.
      - Always views product details before adding to cart
      - Reads reviews and compares specifications
      - Completes purchase after careful consideration
      - Takes time between actions

  - id: window_shopper
    description: |
      A casual browser with no intent to buy.
      - Browses extensively, views many products
      - Rarely adds items to cart
      - Almost never completes checkout
      - Often returns to browse more
```

### 2. Generate Policies

Use the `generate` command to create behavior policies:

```bash
# Requires ANTHROPIC_API_KEY environment variable
turbulence generate --personas personas.yaml --output policies.yaml
```

This produces a `policies.yaml` with weighted decision rules:

```yaml
policies:
  - persona_id: impatient_shopper
    decisions:
      product_browse:
        options:
          add_to_cart: 0.70    # 70% add directly
          view_details: 0.20   # 20% view first
          skip: 0.10           # 10% skip
      checkout_behavior:
        options:
          complete_purchase: 0.60
          abandon: 0.30
          continue_browsing: 0.10

  - persona_id: careful_researcher
    decisions:
      product_browse:
        options:
          view_details: 0.80   # 80% view details
          add_to_cart: 0.15
          skip: 0.05
      checkout_behavior:
        options:
          complete_purchase: 0.70
          continue_browsing: 0.25
          abandon: 0.05
```

### 3. Create Scenarios with Decide Actions

Use the `decide` action type to make policy-based decisions:

```yaml
id: shopping-flow
description: LLM-driven shopping behavior

flow:
  - type: http
    name: list_products
    service: api
    method: GET
    path: /api/products
    extract:
      first_product_id: "$.products[0].id"

  # Decision point: what does this user do after seeing products?
  - type: decide
    name: browse_decision
    decision: product_browse      # Matches key in policy
    output_var: browse_action     # Result stored here

  # Branch based on the decision
  - type: branch
    name: handle_browse
    condition: "context.get('browse_action') == 'view_details'"
    if_true:
      - type: http
        name: view_product
        service: api
        method: GET
        path: "/api/products/{{first_product_id}}"
    if_false:
      - type: branch
        name: check_add_cart
        condition: "context.get('browse_action') == 'add_to_cart'"
        if_true:
          - type: http
            name: add_to_cart
            service: api
            method: POST
            path: /api/cart
            body:
              product_id: "{{first_product_id}}"
        if_false:
          # skip action - just browse more
          - type: http
            name: browse_more
            service: api
            method: GET
            path: /api/products
            query:
              page: "2"

  # Another decision point
  - type: decide
    name: checkout_decision
    decision: checkout_behavior
    output_var: checkout_action

  - type: branch
    name: handle_checkout
    condition: "context.get('checkout_action') == 'complete_purchase'"
    if_true:
      - type: http
        name: checkout
        service: api
        method: POST
        path: /api/checkout
    if_false:
      - type: http
        name: final_browse
        service: api
        method: GET
        path: /api/products
        condition: "context.get('checkout_action') == 'continue_browsing'"

stop_when:
  any_action_fails: false
```

### 4. Run with Policies

Pass the policies file to the run command:

```bash
turbulence run \
  --sut sut.yaml \
  --scenarios scenarios/ \
  --policies policies.yaml \
  -n 100 -p 10
```

Each instance uses weighted random selection based on the policy, with results like:

```
Turbulence Run
  Run ID: run_20260127_143052
  Policies: 3 personas (impatient_shopper, careful_researcher, window_shopper)
  Instances: 100
  Parallelism: 10

Execution Summary
  Total instances: 100
  Passed: 100
  Pass rate: 100.0%
```

### 5. Analyze Results (Optional)

Get AI-powered insights about your test run:

```bash
# Requires ANTHROPIC_API_KEY environment variable
turbulence analyze --run-id run_20260127_143052
```

Output:
```
Performance Analysis for run_20260127_143052
============================================

Observations:
- /api/products: p99 latency increased 3x under load (150ms → 450ms)
  Pattern: Slowdown correlates with concurrent cart additions
  Recommendation: Add database connection pooling

- Cart endpoints: 2% error rate in careful_researcher instances
  Pattern: All failures have product_id from page 2+ results
  Likely cause: Race condition when products sell out

- Checkout flow: impatient_shopper instances show 15% abandon rate
  Matches expected policy behavior (configured 30% abandon)

Summary: System handles varied user behavior well. Focus on
product listing performance under concurrent load.
```

## Decide Action Reference

### Schema

```yaml
- type: decide
  name: <string>           # Required: unique action name
  decision: <string>       # Required: decision point (matches policy key)
  output_var: <string>     # Optional: context variable for result (default: decision_result)
  policy_ref: <string>     # Optional: specific persona policy to use
```

### How It Works

1. The `decide` action looks up the `decision` key in the loaded policy
2. Performs weighted random selection using a seeded RNG
3. Stores the selected option in `output_var` in the context
4. Subsequent `branch` actions can check `context.get('output_var')`

### Reproducibility

Decisions are seeded per-instance (`seed + instance_index`), ensuring:
- Same seed produces same decisions across runs
- Each instance gets unique but deterministic behavior
- Failures can be reproduced exactly with replay

## Manual Policies (No API Key)

If you don't have an API key, create policies manually:

```yaml
# policies.yaml
policies:
  - persona_id: default_user
    decisions:
      product_browse:
        options:
          view_details: 0.50
          add_to_cart: 0.30
          skip: 0.20
      checkout_behavior:
        options:
          complete_purchase: 0.40
          abandon: 0.35
          continue_browsing: 0.25
```

Run with `--policies policies.yaml` as usual.

## Best Practices

### 1. Start with 2-3 Personas

Don't overcomplicate. Three well-defined personas cover most user behavior variety.

### 2. Name Decision Points Clearly

Use descriptive names that match your domain:
- `product_browse`, `checkout_behavior`, `payment_method`
- Not `decision_1`, `step_3_choice`

### 3. Keep Weights Realistic

Base weights on real analytics if available:
- If 70% of users abandon checkout, configure `abandon: 0.70`
- If 5% use guest checkout, configure `guest_checkout: 0.05`

### 4. Use Conditional Actions

Combine `decide` with `condition` on actions:

```yaml
- type: http
  name: apply_coupon
  service: api
  method: POST
  path: /api/cart/coupon
  condition: "context.get('browse_action') == 'add_to_cart'"
```

### 5. Verify with Small Runs

Test policy distribution with 30-50 instances before scaling:

```bash
turbulence run --sut sut.yaml --scenarios scenarios/ --policies policies.yaml -n 30
```

## Troubleshooting

### "Unknown action type for rendering: DecideAction"

Ensure you're using a version with the decide action wired up. Update to latest.

### Policy not applied

Check that:
1. `--policies` flag points to valid YAML
2. `decision` in scenario matches a key in `policies[].decisions`
3. `persona_id` exists in the policies file

### All instances take same path

Verify seed is different per instance. The runner uses `seed + instance_index` to ensure variety.

### "Policy not found" warning

The `policy_ref` in your decide action doesn't match any `persona_id` in policies. Check spelling.

## Cost Estimation

| Command | Claude API Cost |
|---------|-----------------|
| `generate` (3 personas) | ~$0.50 |
| `analyze` (1000 instances) | ~$0.25 |
| `run` (any size) | $0.00 |

Tests themselves are free - LLM costs only apply to optional pre/post processing.

## Next Steps

- [Scenario Authoring](../scenario-authoring.md) - Full action reference
- [Branching and Conditions](../scenario-authoring.md#branching) - Advanced flow control
- [RFC-002: LLM Actor Policies](../../rfcs/RFC-002-llm-actor-policies.md) - Design rationale
