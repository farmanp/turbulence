# RFC-002: LLM-Driven Actor Policies

## 1. Objective
Enable users to define complex, realistic simulation behaviors using high-level natural language personas, leveraging LLMs to translate these descriptions into executable `VariationConfig` rules.

## 2. Proposed Design: Static Expansion at Load-Time

To maintain Turbulence's performance and reproducibility, we will avoid making real-time LLM calls during simulation execution. Instead, we propose a "Static Expansion" pattern.

### 2.1 The Persona Model
Users define personas in their scenario YAML:

```yaml
personas:
  - name: "Impatient Shopper"
    count: 100
    description: |
      A busy professional who abandons their cart if any step takes longer than 5 seconds.
      They prefer buying only 1-2 high-value items.
      They never retry a failed payment.
```

### 2.2 The Expansion Process
When `turbulence run` starts:
1.  The engine identifies scenarios with `personas`.
2.  If an API key is provided (`TURBULENCE_LLM_KEY`), the engine sends the persona description + the scenario's parameter schema to an LLM (e.g., Claude 3.5 Sonnet).
3.  The LLM returns a structured `VariationConfig` object.
4.  The engine caches this expanded config in the run directory for reproducibility.

### 2.3 Example LLM Output
The LLM translates "never retry failed payment" and "1-2 high-value items" into:

```json
{
  "parameters": {
    "cart_quantity": { "type": "range", "min": 1, "max": 2 }
  },
  "toggles": [
    { "name": "retry_payment", "probability": 0.0 }
  ],
  "timing": {
    "jitter_ms": { "min": 100, "max": 500 }
  }
}
```

## 3. Advantages
-   **Zero Runtime Latency:** Simulations run at full speed without waiting for LLM responses.
-   **Cost Predictability:** One LLM call per persona per run (or even cached across runs).
-   **Reproducibility:** The expanded JSON config is stored in artifacts, allowing exact replay.
-   **Developer Experience:** Users describe *intent* ("Impatient Shopper") rather than *implementation* (ranges and probabilities).

## 4. Implementation Phases

1.  **Phase 1: Manual Personas:** Support the `personas` schema but allow users to provide the JSON expansion manually (no LLM yet).
2.  **Phase 2: LLM Integration:** Implement the `PersonaExpander` using Anthropic/OpenAI SDKs.
3.  **Phase 3: Web UI Integration:** Allow users to "Preview Persona" in the Scenario Visualizer, seeing the generated rules before running.

## 5. Security & Safety
-   LLM calls will be opt-in via environment variables.
-   Prompts will be strictly structured to return only JSON.
-   Generated configs will be validated against Pydantic models before application.
