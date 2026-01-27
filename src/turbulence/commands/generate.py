"""Generate command for creating LLM-powered behavior policies."""

import asyncio
from pathlib import Path
from typing import Annotated

import typer
import yaml
from rich.console import Console

console = Console()


def generate(
    personas: Annotated[
        Path,
        typer.Option(
            "--personas",
            "-p",
            help="Path to personas.yaml file",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ],
    output: Annotated[
        Path,
        typer.Option(
            "--output",
            "-o",
            help="Output path for generated policies.yaml",
        ),
    ] = Path("policies.yaml"),
    api_schema: Annotated[
        Path | None,
        typer.Option(
            "--api-schema",
            help="Optional OpenAPI schema for context",
            exists=True,
            file_okay=True,
            dir_okay=False,
        ),
    ] = None,
    model: Annotated[
        str,
        typer.Option(
            "--model",
            "-m",
            help="Claude model to use",
        ),
    ] = "claude-sonnet-4-20250514",
) -> None:
    """Generate behavior policies from persona definitions using Claude.

    Reads persona definitions from a YAML file and generates weighted
    decision policies for each persona using Claude AI.

    Example:
        turbulence generate --personas personas.yaml --output policies.yaml
    """
    asyncio.run(_generate_async(personas, output, api_schema, model))


async def _generate_async(
    personas_path: Path,
    output_path: Path,
    api_schema_path: Path | None,
    model: str,
) -> None:
    """Async implementation of policy generation.

    Args:
        personas_path: Path to the personas YAML configuration file.
        output_path: Path where the generated policies will be written.
        api_schema_path: Optional path to OpenAPI schema for context.
        model: Claude model identifier to use for generation.
    """
    import os

    from turbulence.actors.persona import PersonaConfig
    from turbulence.actors.policy import DecisionWeights, Policy, PolicyConfig
    from turbulence.llm.prompts import POLICY_GENERATION_PROMPT, POLICY_GENERATION_SYSTEM

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print(
            "[red]Error:[/red] ANTHROPIC_API_KEY environment variable not set"
        )
        raise typer.Exit(1)

    # Import provider (may fail if anthropic not installed)
    try:
        from turbulence.llm.anthropic import AnthropicProvider
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("Install with: pip install -e '.[llm]'")
        raise typer.Exit(1)

    # Load personas
    console.print(f"Loading personas from [cyan]{personas_path}[/cyan]...")
    with open(personas_path) as f:
        raw_config = yaml.safe_load(f)

    try:
        persona_config = PersonaConfig(**raw_config)
    except Exception as e:
        console.print(f"[red]Error parsing personas:[/red] {e}")
        raise typer.Exit(1)

    # Load API schema if provided
    api_schema_summary = ""
    if api_schema_path:
        console.print(f"Loading API schema from [cyan]{api_schema_path}[/cyan]...")
        with open(api_schema_path) as f:
            schema = yaml.safe_load(f)
        # Extract just paths for summary
        if "paths" in schema:
            endpoints = list(schema["paths"].keys())[:20]
            api_schema_summary = "Available endpoints:\n" + "\n".join(
                f"  - {ep}" for ep in endpoints
            )

    # Initialize provider
    provider = AnthropicProvider(api_key=api_key, model=model)

    # Generate policies for each persona
    policies: list[Policy] = []

    for persona in persona_config.personas:
        console.print(f"Generating policy for [green]{persona.id}[/green]...")

        # Build prompt
        hints_section = ""
        if persona.hints:
            hints_section = f"\n**Hints:** {yaml.dump(persona.hints, default_flow_style=True)}"

        api_section = ""
        if api_schema_summary:
            api_section = f"\n**API Context:**\n{api_schema_summary}"

        prompt = POLICY_GENERATION_PROMPT.format(
            persona_id=persona.id,
            description=persona.description,
            hints_section=hints_section,
            api_schema_section=api_section,
        )

        try:
            response = await provider.complete(prompt, system=POLICY_GENERATION_SYSTEM)

            # Extract YAML from response (handle markdown code blocks)
            yaml_content = response
            if "```yaml" in response:
                yaml_content = response.split("```yaml")[1].split("```")[0]
            elif "```" in response:
                yaml_content = response.split("```")[1].split("```")[0]

            policy_data = yaml.safe_load(yaml_content)

            # Convert to Policy model
            decisions = {}
            if "decisions" in policy_data:
                for name, opts in policy_data["decisions"].items():
                    if isinstance(opts, dict) and "options" in opts:
                        decisions[name] = DecisionWeights(options=opts["options"])
                    elif isinstance(opts, dict):
                        decisions[name] = DecisionWeights(options=opts)

            policy = Policy(
                persona_id=persona.id,
                decisions=decisions,
                data=policy_data.get("data"),
            )
            policies.append(policy)
            console.print(f"  Generated {len(decisions)} decision points")

        except Exception as e:
            console.print(
                f"[yellow]Warning:[/yellow] Failed to generate policy for "
                f"{persona.id}: {e}"
            )
            # Create empty policy
            policies.append(Policy(persona_id=persona.id))

    # Save policies
    policy_config = PolicyConfig(policies=policies)
    output_data = {
        "policies": [p.model_dump(exclude_none=True) for p in policy_config.policies]
    }

    with open(output_path, "w") as f:
        yaml.dump(output_data, f, default_flow_style=False, sort_keys=False)

    console.print(
        f"\n[green]Success![/green] Generated {len(policies)} policies to "
        f"[cyan]{output_path}[/cyan]"
    )
