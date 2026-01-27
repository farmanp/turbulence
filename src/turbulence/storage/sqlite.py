"""SQLite storage backend for high-performance querying."""

import json
import sqlite3
from pathlib import Path

from turbulence.models.manifest import (
    AssertionRecord,
    InstanceRecord,
    RunManifest,
    StepRecord,
)


class SQLiteStorageWriter:
    """Storage backend implementing SQLite storage.

    Stores all run data (manifest, instances, steps, assertions) in a single
    indexed SQLite database file (turbulence.db).
    """

    def __init__(self) -> None:
        """Initialize SQLite storage backend."""
        self._conn: sqlite3.Connection | None = None
        self._run_path: Path | None = None

    def initialize(self, run_path: Path, manifest: RunManifest) -> None:
        """Initialize the database and create schema.

        Args:
            run_path: Base directory for the run.
            manifest: Run manifest containing configuration and metadata.
        """
        self._run_path = run_path
        db_path = run_path / "turbulence.db"
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._create_schema()

        # Write manifest to runs table
        with self._conn:
            self._conn.execute(
                """
                INSERT INTO runs (id, started_at, sut_name, scenario_ids, seed, config)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    manifest.run_id,
                    manifest.timestamp.isoformat() if manifest.timestamp else None,
                    manifest.sut_name,
                    json.dumps(manifest.scenario_ids),
                    manifest.seed,
                    manifest.config.model_dump_json() if manifest.config else None,
                ),
            )

    def _create_schema(self) -> None:
        """Create the SQLite database schema."""
        if not self._conn:
            return

        with self._conn:
            # Runs table
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS runs (
                    id TEXT PRIMARY KEY,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    sut_name TEXT,
                    scenario_ids TEXT,
                    seed INTEGER,
                    config TEXT
                )
                """
            )

            # Instances table
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS instances (
                    id TEXT PRIMARY KEY,
                    run_id TEXT REFERENCES runs(id),
                    scenario_id TEXT,
                    correlation_id TEXT,
                    status TEXT,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    entry_data TEXT,
                    error TEXT
                )
                """
            )

            # Steps table
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS steps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instance_id TEXT REFERENCES instances(id),
                    run_id TEXT,
                    correlation_id TEXT,
                    step_index INTEGER,
                    step_name TEXT,
                    step_type TEXT,
                    timestamp TIMESTAMP,
                    observation TEXT
                )
                """
            )

            # Assertions table
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS assertions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    instance_id TEXT REFERENCES instances(id),
                    run_id TEXT,
                    correlation_id TEXT,
                    step_index INTEGER,
                    assertion_name TEXT,
                    passed BOOLEAN,
                    expected TEXT,
                    actual TEXT,
                    message TEXT,
                    timestamp TIMESTAMP
                )
                """
            )

            # Indexes for performance
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_instances_status ON instances(status)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_instances_scenario ON instances(scenario_id)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_steps_instance ON steps(instance_id)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_steps_type ON steps(step_type)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_assertions_instance ON assertions(instance_id)")
            self._conn.execute("CREATE INDEX IF NOT EXISTS idx_assertions_passed ON assertions(passed)")

    def write_instance(self, record: InstanceRecord) -> None:
        """Write an instance record."""
        if not self._conn:
            return

        status = "pass" if record.passed else "fail"
        with self._conn:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO instances 
                (id, run_id, scenario_id, correlation_id, status, started_at, completed_at, entry_data, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.instance_id,
                    record.run_id,
                    record.scenario_id,
                    record.correlation_id,
                    status,
                    record.started_at.isoformat() if record.started_at else None,
                    record.completed_at.isoformat() if record.completed_at else None,
                    json.dumps(record.entry_data),
                    record.error,
                ),
            )

    def write_step(self, record: StepRecord) -> None:
        """Write a step record."""
        if not self._conn:
            return

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO steps 
                (instance_id, run_id, correlation_id, step_index, step_name, step_type, timestamp, observation)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.instance_id,
                    record.run_id,
                    record.correlation_id,
                    record.step_index,
                    record.step_name,
                    record.step_type,
                    record.timestamp.isoformat() if record.timestamp else None,
                    json.dumps(record.observation),
                ),
            )

    def write_assertion(self, record: AssertionRecord) -> None:
        """Write an assertion record."""
        if not self._conn:
            return

        with self._conn:
            self._conn.execute(
                """
                INSERT INTO assertions 
                (instance_id, run_id, correlation_id, step_index, assertion_name, passed, expected, actual, message, timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.instance_id,
                    record.run_id,
                    record.correlation_id,
                    record.step_index,
                    record.assertion_name,
                    record.passed,
                    json.dumps(record.expected) if record.expected is not None else None,
                    json.dumps(record.actual) if record.actual is not None else None,
                    record.message,
                    record.timestamp.isoformat() if record.timestamp else None,
                ),
            )

    def close(self) -> None:
        """Close the database connection."""
        if self._conn:
            # We don't have a direct finalized RunManifest in initialize,
            # but we can update completed_at in finalize if we had access to it.
            # For now, just close.
            self._conn.close()
            self._conn = None
