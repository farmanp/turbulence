"""Turbulence CLI module."""

import typer

from turbulence import __version__
from turbulence.commands import replay, report, run, serve

app = typer.Typer(
    name="turbulence",
    help="Workflow simulation and testing framework",
    add_completion=False,
    no_args_is_help=True,
)

# Register commands
app.command(name="run", help="Execute workflow simulations")(run)
app.command(name="report", help="Generate HTML report from run artifacts")(report)
app.command(name="replay", help="Replay a specific workflow instance")(replay)
app.command(name="serve", help="Serve the Web UI dashboard")(serve)


@app.callback(invoke_without_command=True)
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-V",
        help="Show version and exit",
        is_eager=True,
    ),
) -> None:
    """Turbulence - Workflow simulation and testing framework."""
    if version:
        typer.echo(f"turbulence {__version__}")
        raise typer.Exit()


if __name__ == "__main__":
    app()
