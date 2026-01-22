"""Pytest fixtures for Windtunnel tests."""

import pytest
from typer.testing import CliRunner


@pytest.fixture
def cli_runner() -> CliRunner:
    """Provide a Typer CLI runner for testing commands."""
    return CliRunner()
