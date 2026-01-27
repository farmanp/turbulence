"""Analyze command for LLM-powered test result analysis."""

import asyncio
import json
from collections import defaultdict
from pathlib import Path
from statistics import mean, median
from typing import Annotated

import typer
from rich.console import Console
from rich.markdown import Markdown

console = Console()


def analyze(
    run_id: Annotated[
        str,
        typer.Option(
            "--run-id",
            "-r",
            help="Run ID to analyze (e.g., run_20260127_062808)",
        ),
    ],
    runs_dir: Annotated[
        Path,
        typer.Option(
            "--runs-dir",
            help="Directory containing run artifacts",
        ),
    ] = Path("runs"),
    model: Annotated[
        str,
        typer.Option(
            "--model",
            "-m",
            help="Claude model to use",
        ),
    ] = "claude-sonnet-4-20250514",
) -> None:
    """Analyze test run results using Claude AI.

    Reads run artifacts and generates human-readable insights about
    performance patterns, errors, and optimization opportunities.

    Example:
        turbulence analyze --run-id run_20260127_062808
    """
    asyncio.run(_analyze_async(run_id, runs_dir, model))


async def _analyze_async(
    run_id: str,
    runs_dir: Path,
    model: str,
) -> None:
    """Async implementation of run analysis.

    Args:
        run_id: The unique identifier of the run to analyze.
        runs_dir: Directory containing run artifact directories.
        model: Claude model identifier to use for analysis.
    """
    import os

    from turbulence.llm.prompts import ANALYSIS_PROMPT, ANALYSIS_SYSTEM

    # Check for API key
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        console.print(
            "[red]Error:[/red] ANTHROPIC_API_KEY environment variable not set"
        )
        raise typer.Exit(1)

    # Import provider
    try:
        from turbulence.llm.anthropic import AnthropicProvider
    except ImportError as e:
        console.print(f"[red]Error:[/red] {e}")
        console.print("Install with: pip install -e '.[llm]'")
        raise typer.Exit(1)

    # Find run directory
    run_path = runs_dir / run_id
    if not run_path.exists():
        console.print(f"[red]Error:[/red] Run not found: {run_path}")
        raise typer.Exit(1)

    # Load manifest
    manifest_path = run_path / "manifest.json"
    if not manifest_path.exists():
        console.print(f"[red]Error:[/red] Manifest not found: {manifest_path}")
        raise typer.Exit(1)

    with open(manifest_path) as f:
        manifest = json.load(f)

    console.print(f"Analyzing run [cyan]{run_id}[/cyan]...")

    # Load and aggregate steps
    steps_path = run_path / "steps.jsonl"
    if not steps_path.exists():
        console.print(f"[red]Error:[/red] Steps file not found: {steps_path}")
        raise typer.Exit(1)

    # Aggregate statistics
    endpoint_stats: dict[str, dict] = defaultdict(
        lambda: {
            "count": 0,
            "errors": 0,
            "latencies": [],
            "status_codes": defaultdict(int),
        }
    )

    error_messages: list[str] = []
    total_steps = 0

    with open(steps_path) as f:
        for line in f:
            if not line.strip():
                continue
            step = json.loads(line)
            total_steps += 1

            # Extract endpoint key
            action_name = step.get("action_name", "unknown")
            endpoint = action_name

            stats = endpoint_stats[endpoint]
            stats["count"] += 1

            if step.get("latency_ms"):
                stats["latencies"].append(step["latency_ms"])

            if step.get("status_code"):
                stats["status_codes"][step["status_code"]] += 1

            if not step.get("ok", True):
                stats["errors"] += 1
                if step.get("errors"):
                    error_messages.extend(step["errors"][:3])  # Limit per step

    # Format endpoint statistics
    endpoint_lines = []
    for endpoint, stats in sorted(endpoint_stats.items()):
        latencies = stats["latencies"]
        if latencies:
            p50 = median(latencies)
            p99_idx = int(len(latencies) * 0.99)
            p99 = sorted(latencies)[p99_idx] if len(latencies) > 1 else latencies[0]
            avg = mean(latencies)
            error_rate = 100 * stats["errors"] / max(stats["count"], 1)
            endpoint_lines.append(
                f"- {endpoint}: {stats['count']} calls, "
                f"avg={avg:.1f}ms, p50={p50:.1f}ms, p99={p99:.1f}ms, "
                f"errors={stats['errors']} ({error_rate:.1f}%)"
            )
        else:
            endpoint_lines.append(
                f"- {endpoint}: {stats['count']} calls, errors={stats['errors']}"
            )

    # Format error summary
    error_summary = "No errors recorded"
    if error_messages:
        unique_errors = list(set(error_messages))[:10]
        error_summary = "\n".join(f"- {err}" for err in unique_errors)

    # Format latency distribution
    all_latencies: list[float] = []
    for stats in endpoint_stats.values():
        all_latencies.extend(stats["latencies"])

    latency_dist = "No latency data"
    if all_latencies:
        sorted_lat = sorted(all_latencies)
        latency_dist = (
            f"- Min: {min(all_latencies):.1f}ms\n"
            f"- p50: {sorted_lat[len(sorted_lat) // 2]:.1f}ms\n"
            f"- p90: {sorted_lat[int(len(sorted_lat) * 0.9)]:.1f}ms\n"
            f"- p99: {sorted_lat[int(len(sorted_lat) * 0.99)]:.1f}ms\n"
            f"- Max: {max(all_latencies):.1f}ms"
        )

    # Calculate duration
    duration = manifest.get("duration_seconds", 0)
    total_instances = manifest.get("instances", {}).get("total", 0)

    # Build analysis prompt
    prompt = ANALYSIS_PROMPT.format(
        run_id=run_id,
        total_instances=total_instances,
        duration_seconds=duration,
        endpoint_stats="\n".join(endpoint_lines) or "No endpoint data",
        error_summary=error_summary,
        latency_distribution=latency_dist,
    )

    # Get analysis from Claude
    console.print("Generating analysis...")
    provider = AnthropicProvider(api_key=api_key, model=model)

    try:
        analysis = await provider.complete(prompt, system=ANALYSIS_SYSTEM)

        # Display results
        console.print("\n")
        console.print(Markdown(f"# Performance Analysis: {run_id}\n\n{analysis}"))

    except Exception as e:
        console.print(f"[red]Error during analysis:[/red] {e}")
        raise typer.Exit(1)
