# Turbulence

**High-Performance Workflow Simulation & Testing Framework**

Turbulence is a developer-centric framework designed to stress-test, validate, and analyze complex distributed systems. It combines the ease of writing scenarios in YAML/Python with the raw power of an asynchronous execution engine to simulate thousands of concurrent users.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![GitHub](https://img.shields.io/github/stars/farmanp/turbulence?style=social)](https://github.com/farmanp/turbulence)

---

## 🚀 Key Features

*   **⚡ Async Performance:** Built on Python's `asyncio` to simulate thousands of concurrent workflows on a single node.
*   **📝 Declarative Scenarios:** Define complex user journeys (HTTP requests, delays, assertions) in simple YAML files.
*   **🔍 Deep Observability:** Automatically correlates traces with `run_id`, `instance_id`, and `correlation_id`.
*   **📊 Rich Reporting:** Generates beautiful HTML reports with pass/fail metrics, latency distributions, and error analysis.
*   **💾 Crash-Safe Storage:** Persists every step, request, and assertion to efficient JSONL files for post-run analysis.
*   **🔧 Pressure Engine:** Inject fault patterns (latency, errors, timeouts) to test system resilience.
*   **🖥️ Web Dashboard:** Real-time monitoring UI with run history, instance timelines, and deep investigation views.

---

## 🛠️ Installation

```bash
# Recommended: create a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install from source
pip install -e .
```

---

## 🚦 Quick Start

### 1. Define your System Under Test (SUT)
Create a `sut.yaml` file to define your target environment:
```yaml
name: "My E-Commerce App"
default_headers:
  X-Correlation-ID: "{{correlation_id}}"
services:
  api:
    base_url: "http://localhost:8080"
    timeout_seconds: 30
```

### 2. Write a Scenario
Create a `scenarios/checkout.yaml` file to describe a user journey:
```yaml
id: "checkout_flow"
description: "User adds item to cart and checks out"

flow:
  - type: "http"
    name: "get_products"
    service: "catalog"
    method: "GET"
    path: "/api/products"
    extract:
      product_id: "$.items[0].id"

  - type: "wait"
    name: "think_time"
    service: "frontend"
    path: "/"
    expect:
      status_code: 200

  - type: "http"
    name: "add_to_cart"
    service: "cart"
    method: "POST"
    path: "/api/cart"
    json:
      item_id: "{{ product_id }}"
      qty: 1
    
assertions:
  - type: "assert"
    name: "cart_not_empty"
    expect:
      status_code: 201
```

### 3. Run the Simulation
Execute the scenario with 50 concurrent users:

```bash
turbulence run \
  --sut sut.yaml \
  --scenarios scenarios/ \
  --parallel 50 \
  --count 500
```

### 4. View the Report
Generate and open the HTML report:

```bash
turbulence report --run-id <run_id_from_step_3>
open runs/<run_id>/report.html
```

---

## 📂 Project Structure

*   `src/turbulence/`: Core framework code.
    *   `actions/`: Action runners (HTTP, Wait, Assert).
    *   `engine/`: Async execution engine, templating, and replay.
    *   `storage/`: JSONL persistence layer.
    *   `pressure/`: Fault injection engine.
    *   `validation/`: JSON Schema validation.
    *   `evaluation/`: Safe expression evaluator.
    *   `api/`: FastAPI backend for web dashboard.
    *   `report/`: HTML report generation.
*   `ui/`: React web dashboard (Vite + Tailwind).
*   `docs/`: Docusaurus documentation site.
*   `runs/`: Output directory for test artifacts and reports.
*   `tickets/`: Development roadmap and ticket tracking.

---

## 🖥️ Web Dashboard

Start the web UI for real-time monitoring:

```bash
# Start the API server
turbulence serve --port 8000

# In another terminal, start the UI dev server
cd ui && npm run dev
```

The dashboard provides:
- **Run History:** Overview of all test runs with pass/fail metrics
- **Run Detail:** Deep dive into individual runs with error analysis
- **Instance Timeline:** Step-by-step trace of workflow execution
- **Real-time Updates:** WebSocket streaming for live run monitoring

---

## 🤝 Contributing

We welcome contributions! Please check `tickets/TICKET-GRAPH.md` to see the roadmap and currently active tasks.

1.  Clone the repository:
    ```bash
    git clone https://github.com/farmanp/turbulence.git
    cd turbulence
    ```
2.  Install dev dependencies: `pip install -e ".[dev]"`
3.  Run tests: `pytest`
4.  Submit a Pull Request.

---

## 📄 License

MIT © 2026 Turbulence Contributors