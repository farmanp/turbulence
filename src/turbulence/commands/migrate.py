"""Migration command for converting JSONL artifacts to SQLite."""

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.progress import Progress

from turbulence.models.manifest import (
    AssertionRecord,
    InstanceRecord,
    RunManifest,
    StepRecord,
)
from turbulence.storage.sqlite import SQLiteStorageWriter

console = Console()


def migrate(
    run_path: Path = typer.Argument(
        ...,
        help="Path to the run directory containing JSONL artifacts",
        exists=True,
        file_okay=False,
        dir_okay=True,
        resolve_path=True,
    ),
) -> None:
    """Migrate a JSONL run to SQLite backend.
    
    Reads instances.jsonl, steps.jsonl, and assertions.jsonl from the run
    directory and populates a turbulence.db file.
    """
    manifest_path = run_path / "manifest.json"
    if not manifest_path.exists():
        console.print(f"[red]Error:[/red] Manifest not found at {manifest_path}")
        raise typer.Exit(1)

    db_path = run_path / "turbulence.db"
    if db_path.exists():
        if not typer.confirm("SQLite database already exists. Overwrite?"):
            raise typer.Exit()
        db_path.unlink()

    console.print(f"[bold blue]Migrating Run:[/bold blue] {run_path.name}")

    # Load manifest
    try:
        manifest_data = json.loads(manifest_path.read_text())
        manifest = RunManifest.model_validate(manifest_data)
    except Exception as e:
        console.print(f"[red]Error loading manifest:[/red] {e}")
        raise typer.Exit(1)

    storage = SQLiteStorageWriter()
    storage.initialize(run_path, manifest)

    def migrate_file(filename: str, record_model: type, write_func: callable, label: str):
        file_path = run_path / filename
        if not file_path.exists():
            console.print(f"[yellow]Skipping {filename}:[/yellow] File not found")
            return

        with file_path.open("r", encoding="utf-8") as f:
            lines = f.readlines()
            if not lines:
                return

            with Progress() as progress:
                task = progress.add_task(label, total=len(lines))
                for line in lines:
                    line = line.strip()
                    if not line:
                        progress.advance(task)
                        continue
                    try:
                        record = record_model.model_validate(json.loads(line))
                        write_func(record)
                    except Exception as e:
                        console.print(f"[yellow]Warning:[/yellow] Failed to migrate line in {filename}: {e}")
                    progress.advance(task)

    # Migrate instances
    migrate_file("instances.jsonl", InstanceRecord, storage.write_instance, "[green]Migrating instances")

    # Migrate steps
    migrate_file("steps.jsonl", StepRecord, storage.write_step, "[cyan]Migrating steps")

    # Migrate assertions
    migrate_file("assertions.jsonl", AssertionRecord, storage.write_assertion, "[magenta]Migrating assertions")

    storage.close()
    console.print("\n[bold green]Migration complete![/bold green]")
    console.print(f"SQLite database created at {db_path}")
