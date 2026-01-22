"""Base classes and protocols for storage backends."""

from pathlib import Path
from typing import Protocol, runtime_checkable

from turbulence.models.manifest import (
    AssertionRecord,
    InstanceRecord,
    RunManifest,
    StepRecord,
)


@runtime_checkable
class StorageWriter(Protocol):
    """Protocol for storage backend implementations.

    Defines the interface for writing run artifacts (instances, steps, assertions)
    to a persistent storage medium.
    """

    def initialize(self, run_path: Path, manifest: RunManifest) -> None:
        """Initialize the storage with run metadata.

        Args:
            run_path: Base directory for the run.
            manifest: Run manifest containing configuration and metadata.
        """
        ...

    def write_instance(self, record: InstanceRecord) -> None:
        """Write a single instance record.

        Args:
            record: The instance record to write.
        """
        ...

    def write_step(self, record: StepRecord) -> None:
        """Write a single step record.

        Args:
            record: The step record to write.
        """
        ...

    def write_assertion(self, record: AssertionRecord) -> None:
        """Write a single assertion record.

        Args:
            record: The assertion record to write.
        """
        ...

    def close(self) -> None:
        """Close any open resources (files, database connections)."""
        ...
