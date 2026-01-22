"""Environment variable resolution for configuration files."""

import os
import re
from typing import Any


class EnvVarError(Exception):
    """Raised when environment variable resolution fails."""

    pass


# Pattern for {{env.VAR}} or {{env.VAR | default:VALUE}}
# Group 1: Variable name
# Group 2: Optional default value part (e.g., " | default:value")
# Group 3: Optional default value itself
ENV_VAR_PATTERN = re.compile(
    r"\{\{\s*env\.([a-zA-Z_][a-zA-Z0-9_]*)\s*(\|\s*default:([^}]+))?\s*\}\}"
)


def resolve_env_vars(data: Any) -> Any:
    """Recursively resolve environment variables in a data structure.

    Args:
        data: Dictionary, list, or string to resolve env vars in.

    Returns:
        Data with env vars resolved.

    Raises:
        EnvVarError: If a required environment variable is missing.
    """
    if isinstance(data, dict):
        return {k: resolve_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [resolve_env_vars(i) for i in data]
    elif isinstance(data, str):
        return _resolve_string(data)
    else:
        return data


def _resolve_string(value: str) -> str:
    """Resolve environment variables in a single string.

    If the entire string is a single {{env.VAR}} expression, we could
    potentially preserve types (e.g. env var is an int), but the requirements
    show it being used mostly in strings (base_url, headers).
    For now, we'll return strings.
    """

    def replacer(match: re.Match) -> str:
        var_name = match.group(1)
        has_default = match.group(2) is not None
        default_value = match.group(3).strip() if has_default else None

        val = os.environ.get(var_name)
        if val is not None:
            return val

        if has_default:
            return default_value  # type: ignore

        raise EnvVarError(
            f"Required environment variable '{var_name}' is not set and no default provided."
        )

    try:
        return ENV_VAR_PATTERN.sub(replacer, value)
    except EnvVarError:
        raise
