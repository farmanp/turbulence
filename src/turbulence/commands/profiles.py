"""Command to list available environment profiles."""

from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

from turbulence.config.loader import load_sut

console = Console()


def profiles(
    sut: Path = typer.Option(
        ...,
        "--sut",
        "-s",
        help="Path to the SUT configuration file",
        exists=True,
        file_okay=True,
        dir_okay=False,
        resolve_path=True,
    ),
) -> None:
    """List available environment profiles in a SUT configuration."""
    try:
        # Load raw config to see all profiles, ignoring profile resolution errors
        config = load_sut(sut)
    except Exception as e:
        console.print(f"[bold red]Error loading SUT config:[/bold red] {e}")
        raise typer.Exit(code=1)

    console.print(f"[bold]Available profiles for '{config.name}':[/bold]")

    if not config.profiles:
        console.print("  [yellow]No profiles defined.[/yellow]")
        return

    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Profile", style="cyan")
    table.add_column("Default", justify="center")
    table.add_column("Overrides")

    for name, profile in sorted(config.profiles.items()):
        is_default = name == config.default_profile
        overrides = []
        if profile.default_headers:
            overrides.append(f"headers ({len(profile.default_headers)})")
        if profile.services:
            services = []
            for svc_name, svc_conf in profile.services.items():
                changes = []
                if svc_conf.base_url: changes.append("url")
                if svc_conf.timeout_seconds: changes.append("timeout")
                if svc_conf.headers: changes.append("headers")
                services.append(f"{svc_name}: [{', '.join(changes)}]")
            overrides.append(f"services ({'; '.join(services)})")

        table.add_row(
            name,
            "✓" if is_default else "",
            ", ".join(overrides) if overrides else "None",
        )

    console.print(table)
