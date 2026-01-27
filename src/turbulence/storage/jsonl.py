"""JSONL (JSON Lines) writer utilities for streaming artifact storage."""

import json
from pathlib import Path
from typing import IO, Any

from pydantic import BaseModel

from turbulence.models.manifest import (
    AssertionRecord,
    InstanceRecord,
    RunManifest,
    StepRecord,
)


class JSONLWriter:
    """Writer for JSONL (JSON Lines) format files.

    Provides streaming writes with immediate flush for durability.
    Each call to write() appends a single JSON line to the file.
    """

    def __init__(self, path: Path) -> None:
        """Initialize the JSONL writer.

        Args:
            path: Path to the JSONL file to write to.
        """
        self._path = path
        self._file: IO[str] | None = None

    @property
    def path(self) -> Path:
        """Return the path to the JSONL file."""
        return self._path

    def open(self) -> "JSONLWriter":
        """Open the file for appending.

        Returns:
            Self for method chaining.
        """
        self._file = self._path.open("a", encoding="utf-8")
        return self

    def close(self) -> None:
        """Close the file handle."""
        if self._file is not None:
            self._file.close()
            self._file = None

    def write(self, record: dict[str, Any] | BaseModel) -> None:
        """Write a single record as a JSON line.

        The record is serialized to JSON, written as a single line,
        and the file is flushed immediately for durability.

        Args:
            record: Dictionary or Pydantic model to write.

        Raises:
            RuntimeError: If the writer has not been opened.
        """
        if self._file is None:
            raise RuntimeError("JSONLWriter must be opened before writing")

        if isinstance(record, BaseModel):
            line = record.model_dump_json()
        else:
            line = json.dumps(record, default=str)

        self._file.write(line + "\n")
        self._file.flush()

    def __enter__(self) -> "JSONLWriter":
        """Context manager entry."""
        return self.open()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> None:
        """Context manager exit."""
        self.close()


class JSONLStorageWriter:
    """Storage backend implementing the JSONL format.

    Maintains the legacy Turbulence format with separate instances.jsonl,
    steps.jsonl, and assertions.jsonl files.
    """

    def __init__(self) -> None:
        """Initialize JSONL storage backend."""
        self._instances_writer: JSONLWriter | None = None
        self._steps_writer: JSONLWriter | None = None
        self._assertions_writer: JSONLWriter | None = None

    def initialize(self, run_path: Path, manifest: RunManifest) -> None:
        """Initialize the run directory and write the manifest.

        Args:
            run_path: Base directory for the run.
            manifest: Run manifest containing configuration and metadata.
        """
        manifest_path = run_path / "manifest.json"
        with manifest_path.open("w", encoding="utf-8") as f:
            f.write(manifest.model_dump_json(indent=2))

        self._instances_writer = JSONLWriter(run_path / "instances.jsonl").open()
        self._steps_writer = JSONLWriter(run_path / "steps.jsonl").open()
        self._assertions_writer = JSONLWriter(run_path / "assertions.jsonl").open()

    def write_instance(self, record: InstanceRecord) -> None:
        """Write an instance record."""
        if self._instances_writer:
            self._instances_writer.write(record)

    def write_step(self, record: StepRecord) -> None:
        """Write a step record."""
        if self._steps_writer:
            self._steps_writer.write(record)

    def write_assertion(self, record: AssertionRecord) -> None:
        """Write an assertion record."""
        if self._assertions_writer:
            self._assertions_writer.write(record)

    def close(self) -> None:
        """Close all open file handles."""
        if self._instances_writer:
            self._instances_writer.close()
        if self._steps_writer:
            self._steps_writer.close()
        if self._assertions_writer:
            self._assertions_writer.close()


def write_jsonl_record(path: Path, record: dict[str, Any] | BaseModel) -> None:
    """Write a single record to a JSONL file (append mode).

    This is a convenience function for one-off writes.
    For multiple writes, use JSONLWriter for better performance.

    Args:
        path: Path to the JSONL file.
        record: Dictionary or Pydantic model to write.
    """
    if isinstance(record, BaseModel):
        line = record.model_dump_json()
    else:
        line = json.dumps(record, default=str)

    with path.open("a", encoding="utf-8") as f:
        f.write(line + "\n")
        f.flush()


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    """Read all records from a JSONL file.

    Args:
        path: Path to the JSONL file.

    Returns:
        List of dictionaries, one per line.
    """
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
