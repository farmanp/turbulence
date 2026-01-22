"""Storage backends for Turbulence artifacts."""

from pathlib import Path
from typing import Any

from turbulence.models.manifest import RunManifest
from turbulence.storage.base import StorageWriter
from turbulence.storage.jsonl import JSONLStorageWriter


def create_storage_writer(storage_type: str = "jsonl") -> StorageWriter:
    """Factory function to create a storage writer.

    Args:
        storage_type: Type of storage backend ('jsonl' or 'sqlite').

    Returns:
        Implementation of StorageWriter.

    Raises:
        ValueError: If storage_type is unknown.
    """
    if storage_type == "jsonl":
        return JSONLStorageWriter()
    elif storage_type == "sqlite":
        # Deferred import to avoid circular dependencies or unnecessary imports
        from turbulence.storage.sqlite import SQLiteStorageWriter

        return SQLiteStorageWriter()
    else:
        raise ValueError(f"Unknown storage type: {storage_type}")
