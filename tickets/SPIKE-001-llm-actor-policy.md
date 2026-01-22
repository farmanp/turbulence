# AI-Ready Spike Template

## 1. Research Question (Required)
**Question:**
Can we use LLMs to generate realistic user behavior policies for workflow variation, and what are the tradeoffs?

**Context:**
Current variation and branching flows require manual rule definition. LLMs could potentially generate more realistic, diverse user behaviors automatically—deciding when to abandon cart, what products to add, how to respond to errors—based on persona descriptions rather than explicit rules.

## 2. Scope & Timebox
**Timebox:** 2-3 days

**In Scope:**
- Evaluate LLM integration patterns for behavior generation
- Prototype simple policy generation from persona description
- Measure latency and cost impact on run execution
- Assess reproducibility challenges (LLM non-determinism)
- Explore caching strategies for policy decisions

**Out of Scope:**
- Full production implementation
- Fine-tuning models
- Multi-modal inputs (screenshots, etc.)
- Real-time LLM calls during high-parallelism runs

## 3. Success Criteria (Required)
**Deliverables:**
- [ ] Written summary of findings with pros/cons
- [ ] Prototype demonstrating basic policy generation
- [ ] Latency measurements for policy calls
- [ ] Cost analysis per 1000 instances
- [ ] Reproducibility analysis
- [ ] Recommendation with clear go/no-go criteria

## 4. Research Plan
1. **Literature Review** (2 hours)
   - Survey existing LLM-driven testing tools
   - Review chaos engineering + AI papers
   - Identify common patterns and pitfalls

2. **Architecture Exploration** (4 hours)
   - Design integration points in Turbulence
   - Evaluate: pre-generation vs. real-time vs. hybrid
   - Consider caching and batching strategies

3. **Prototype Implementation** (8 hours)
   - Create simple LLM policy generator
   - Test with Claude/GPT-4 APIs
   - Implement basic caching layer

4. **Benchmarking** (4 hours)
   - Measure latency per policy decision
   - Calculate cost at various scales
   - Test reproducibility with temperature=0

5. **Documentation** (4 hours)
   - Write findings document
   - Create recommendation with tradeoffs
   - Define v2 requirements if proceeding

## 5. Findings
*[To be filled after research]*

**Options Considered:**
| Option | Pros | Cons |
|--------|------|------|
| A: Pre-generate all policies | Fast execution, reproducible, lower cost | Less dynamic, requires upfront generation |
| B: Real-time LLM calls | Most realistic behavior, adapts to responses | Slow, expensive, non-reproducible |
| C: Hybrid (pre-gen + fallback) | Balance of speed and realism | Complex implementation, partial reproducibility |
| D: No LLM integration | Simple, fast, reproducible | Manual policy writing, less realistic |

**Recommendation:**
*[To be filled after research]*

## 6. Next Steps
*[To be filled after research]*
- [ ] Action item 1
- [ ] Action item 2

## 7. Resources
- [Claude API Documentation](https://docs.anthropic.com/)
- [OpenAI API Documentation](https://platform.openai.com/docs/)
- [LLM Testing Papers](https://arxiv.org/search/?query=llm+testing)

## Research Questions to Answer

### Feasibility
1. Can LLMs generate consistent, valid workflow decisions?
2. What prompt engineering is needed for reliable output?
3. How do we handle invalid/unparseable LLM responses?

### Performance
4. What's the latency overhead per decision?
5. Can we batch decisions effectively?
6. What caching hit rates are achievable?

### Cost
7. What's the cost per 1000 workflow instances?
8. How does cost scale with workflow complexity?
9. Can smaller/cheaper models work adequately?

### Reproducibility
10. Can we achieve deterministic behavior with temperature=0?
11. How do we handle model version changes?
12. What's the seed strategy for LLM-influenced runs?

### Quality
13. Do LLM-generated behaviors find more bugs than rules?
14. Are the behaviors realistic compared to production traffic?
15. Can we validate LLM decisions against ground truth?

## Example Persona-to-Policy Concept
```yaml
# Input: High-level persona description
persona:
  name: "Impatient Shopper"
  description: |
    A busy professional who shops during lunch breaks.
    Abandons cart if checkout takes too long.
    Prefers express shipping.
    Gets frustrated with payment failures and may try once then leave.

# Output: Generated policy rules (from LLM)
generated_policy:
  cart_behavior:
    max_items: 3
    abandon_after_seconds: 30
    add_to_cart_delay_ms: {min: 100, max: 500}

  checkout_behavior:
    shipping_preference: "express"
    retry_payment_on_failure: 1
    abandon_on_second_failure: true

  timing:
    max_step_wait_seconds: 10
    impatience_threshold_seconds: 20
```
