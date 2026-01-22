"""Configuration loaders for SUT and scenario files."""

from pathlib import Path

import yaml
from pydantic import ValidationError

from turbulence.config.env import EnvVarError, resolve_env_vars
from turbulence.config.scenario import Scenario
from turbulence.config.sut import SUTConfig


class ConfigLoadError(Exception):
    """Raised when configuration loading fails."""

    def __init__(self, message: str, path: Path, details: str | None = None) -> None:
        self.path = path
        self.details = details
        full_message = f"{message}: {path}"
        if details:
            full_message += f"\n{details}"
        super().__init__(full_message)


def load_sut(path: Path, profile: str | None = None) -> SUTConfig:
    """Load and validate a SUT configuration from a YAML file.

    Args:
        path: Path to the sut.yaml file
        profile: Optional environment profile to activate

    Returns:
        Validated SUTConfig object (with profile applied if specified)

    Raises:
        ConfigLoadError: If the file cannot be read, validation fails, or profile invalid
    """
    if not path.exists():
        raise ConfigLoadError("SUT config file not found", path)

    if not path.is_file():
        raise ConfigLoadError("SUT config path is not a file", path)

    try:
        with path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigLoadError("Invalid YAML syntax", path, str(e)) from e

    if data is None:
        raise ConfigLoadError("SUT config file is empty", path)

    try:
        data = resolve_env_vars(data)
    except EnvVarError as e:
        raise ConfigLoadError("Environment variable resolution failed", path, str(e)) from e

    try:
        config = SUTConfig.model_validate(data)
    except ValidationError as e:
        # Format validation errors nicely
        errors = []
        for error in e.errors():
            loc = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"  - {loc}: {msg}")
        raise ConfigLoadError(
            "SUT config validation failed",
            path,
            "\n".join(errors),
        ) from e

    # Determine which profile to use
    target_profile = profile or config.default_profile

    if not target_profile:
        return config

    if target_profile not in config.profiles:
        available = ", ".join(sorted(config.profiles.keys()))
        raise ConfigLoadError(
            f"Profile '{target_profile}' not found",
            path,
            f"Available profiles: {available}" if available else "No profiles defined",
        )

    return _apply_profile(config, target_profile)


def _apply_profile(config: SUTConfig, profile_name: str) -> SUTConfig:
    """Apply a profile's overrides to the base configuration."""
    profile = config.profiles[profile_name]

    # Merge default headers
    if profile.default_headers:
        config.default_headers.update(profile.default_headers)

    # Merge services
    if profile.services:
        for name, override in profile.services.items():
            if name not in config.services:
                # Skip services not in base config to avoid incomplete definitions
                # (Service requires base_url which might be missing in override)
                continue

            base_service = config.services[name]

            if override.base_url:
                base_service.base_url = override.base_url

            if override.timeout_seconds:
                base_service.timeout_seconds = override.timeout_seconds

            if override.headers:
                base_service.headers.update(override.headers)

    return config


def load_scenario(path: Path) -> Scenario:
    """Load and validate a single scenario from a YAML file.

    Args:
        path: Path to the scenario YAML file

    Returns:
        Validated Scenario object

    Raises:
        ConfigLoadError: If the file cannot be read or validation fails
    """
    if not path.exists():
        raise ConfigLoadError("Scenario file not found", path)

    if not path.is_file():
        raise ConfigLoadError("Scenario path is not a file", path)

    try:
        with path.open() as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigLoadError("Invalid YAML syntax", path, str(e)) from e

    if data is None:
        raise ConfigLoadError("Scenario file is empty", path)

    try:
        data = resolve_env_vars(data)
    except EnvVarError as e:
        raise ConfigLoadError("Environment variable resolution failed", path, str(e)) from e

    try:
        scenario = Scenario.model_validate(data)
        scenario._source_path = path
        return scenario
    except ValidationError as e:
        errors = []
        for error in e.errors():
            loc = ".".join(str(x) for x in error["loc"])
            msg = error["msg"]
            errors.append(f"  - {loc}: {msg}")
        raise ConfigLoadError(
            "Scenario validation failed",
            path,
            "\n".join(errors),
        ) from e


def load_scenarios(directory: Path) -> list[Scenario]:
    """Load all scenarios from a directory.

    Args:
        directory: Path to the scenarios directory

    Returns:
        List of validated Scenario objects

    Raises:
        ConfigLoadError: If the directory doesn't exist or any scenario is invalid
    """
    if not directory.exists():
        raise ConfigLoadError("Scenarios directory not found", directory)

    if not directory.is_dir():
        raise ConfigLoadError("Scenarios path is not a directory", directory)

    scenario_files = sorted(directory.glob("*.yaml")) + sorted(directory.glob("*.yml"))

    if not scenario_files:
        raise ConfigLoadError("No scenario files found", directory)

    scenarios = []
    errors = []

    for path in scenario_files:
        try:
            scenario = load_scenario(path)
            scenarios.append(scenario)
        except ConfigLoadError as e:
            errors.append(str(e))

    if errors:
        raise ConfigLoadError(
            f"Failed to load {len(errors)} scenario(s)",
            directory,
            "\n\n".join(errors),
        )

    # Check for duplicate scenario IDs
    seen_ids: dict[str, Path] = {}
    for scenario, path in zip(scenarios, scenario_files, strict=True):
        if scenario.id in seen_ids:
            raise ConfigLoadError(
                f"Duplicate scenario ID '{scenario.id}'",
                path,
                f"Also defined in: {seen_ids[scenario.id]}",
            )
        seen_ids[scenario.id] = path

    return scenarios
