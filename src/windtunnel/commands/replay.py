"""Replay command for re-executing specific workflow instances."""

from pathlib import Path

import typer
from rich.console import Console

console = Console()


def replay(
    run_id: str = typer.Option(
        ...,
        "--run-id",
        "-r",
        help="The run ID containing the instance to replay",
    ),
    instance_id: str = typer.Option(
        ...,
        "--instance-id",
        "-i",
        help="The specific instance ID to replay",
    ),
    runs_dir: Path = typer.Option(
        Path("runs"),
        "--runs-dir",
        "-d",
        help="Directory containing run artifacts",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Show detailed step-by-step output",
    ),
) -> None:
    """Replay a specific workflow instance for debugging.

    Loads the instance from stored artifacts and re-executes it with the same
    seed, context, and correlation ID. Useful for debugging failures by
    reproducing the exact conditions of the original run.

    Example:
        windtunnel replay --run-id run_20240115_001 --instance-id inst_042
    """
    run_path = runs_dir / run_id
    if not run_path.exists():
        console.print(f"[red]Error: Run '{run_id}' not found in {runs_dir}[/red]")
        raise typer.Exit(code=1)

    console.print("[bold blue]Windtunnel Replay[/bold blue]")
    console.print(f"  Run ID: {run_id}")
    console.print(f"  Instance ID: {instance_id}")
    console.print(f"  Run path: {run_path}")
    console.print(f"  Verbose: {verbose}")
    console.print()
    console.print(
        "[yellow]Replay execution not yet implemented (see FEAT-010)[/yellow]"
    )
    raise typer.Exit(code=0)
