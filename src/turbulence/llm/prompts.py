"""Prompt templates for LLM-powered features."""

# ruff: noqa: E501
# Prompt templates contain prose that should not be line-wrapped

POLICY_GENERATION_SYSTEM = """You are an expert at generating realistic user behavior policies for load testing.
Your policies help simulate diverse user personas in e-commerce and API testing scenarios."""

POLICY_GENERATION_PROMPT = """Generate behavior policies for the following persona:

**Persona ID:** {persona_id}
**Description:** {description}
{hints_section}
{api_schema_section}

Generate a YAML policy with:
1. Decision weights for key behavioral decision points (values should sum to 1.0 per decision)
2. Realistic test data arrays for the persona

Output only valid YAML matching this structure:
```yaml
persona_id: {persona_id}
decisions:
  # Example decision points - adapt to the persona
  product_browse:
    options:
      view_details: 0.3
      add_to_cart: 0.5
      skip: 0.2
  checkout_behavior:
    options:
      complete: 0.7
      abandon: 0.3
data:
  search_queries:
    - "example query 1"
    - "example query 2"
  # Add other relevant test data
```"""

ANALYSIS_SYSTEM = """You are an expert performance analyst reviewing load test results.
Provide actionable insights about performance issues, error patterns, and optimization opportunities."""

ANALYSIS_PROMPT = """Analyze these load test results:

**Run ID:** {run_id}
**Total Instances:** {total_instances}
**Duration:** {duration_seconds:.1f}s

**Endpoint Statistics:**
{endpoint_stats}

**Error Summary:**
{error_summary}

**Latency Distribution:**
{latency_distribution}

Provide:
1. Key observations about performance patterns
2. Likely causes for any issues found
3. Specific recommendations for improvement
4. Summary assessment

Format your response with clear sections and bullet points."""
