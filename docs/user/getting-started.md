# Getting Started

## Prerequisites

- Python 3.10+
- A virtual environment manager (recommended)

## Install

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
```

If you want developer tooling, use:

```bash
pip install -e ".[dev]"
```

## Try it now

Don't have an API handy? Run this against [httpbin.org](https://httpbin.org) to see Turbulence in action immediately.

1. Create a simple SUT config (`httpbin-sut.yaml`):

```yaml
name: httpbin-demo
services:
  api:
    base_url: "https://httpbin.org"
```

2. Create a scenario (`scenarios/echo.yaml`):

```yaml
id: echo-flow
description: Simple echo test against httpbin
flow:
  - name: send_data
    type: http
    service: api
    method: POST
    path: /post
    json:
      message: "Hello Turbulence"
    extract:
      returned_data: "$.json.message"

assertions:
  - name: verify_echo
    expect:
      jsonpath: "$.json.message"
      equals: "Hello Turbulence"
```

3. Run the simulation:

```bash
turbulence run --sut httpbin-sut.yaml --scenarios scenarios/ --n 10
```

## Quick Start

1. Create a SUT config (`sut.yaml`):

```yaml
name: ecommerce-checkout
default_headers:
  X-Run-ID: "{{run_id}}"
  X-Correlation-ID: "{{correlation_id}}"
  Content-Type: "application/json"

services:
  api:
    base_url: "https://api.example.com"
  payments:
    base_url: "https://payments.example.com"
    headers:
      X-API-Key: "your-api-key"
```

2. Create a scenario (`scenarios/checkout.yaml`):

```yaml
id: checkout-happy-path
description: Complete checkout flow with payment

entry:
  seed_data:
    cart_items:
      - sku: "WIDGET-001"
        quantity: 2
        price: 29.99
    customer_id: "cust_001"

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
      total: "$.total"

  - name: process_payment
    type: http
    service: payments
    method: POST
    path: /charges
    json:
      amount: "{{total}}"
      cart_id: "{{cart_id}}"
    extract:
      payment_id: "$.id"
      status: "$.status"

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
  - name: payment_completed
    expect:
      status_code: 200
      jsonpath: "$.payment_status"
      equals: "captured"

stop_when:
  any_assertion_fails: true

max_steps: 50
```

3. Run the simulation:

```bash
turbulence run --sut sut.yaml --scenarios scenarios/ --n 200 --parallel 25
```

4. Generate a report:

```bash
turbulence report --run-id <run_id>
```

Artifacts are stored under `runs/<run_id>/` by default.
