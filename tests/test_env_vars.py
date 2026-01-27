"""Tests for environment variable resolution in configuration."""

import os
from unittest.mock import patch

import pytest
import yaml

from turbulence.config.env import EnvVarError, resolve_env_vars
from turbulence.config.loader import ConfigLoadError, load_scenario, load_sut


def test_resolve_env_vars_simple():
    """Test simple environment variable resolution."""
    with patch.dict(os.environ, {"API_KEY": "secret123"}):
        data = {"auth": "Bearer {{env.API_KEY}}"}
        resolved = resolve_env_vars(data)
        assert resolved == {"auth": "Bearer secret123"}


def test_resolve_env_vars_multiple():
    """Test multiple environment variables in one string."""
    with patch.dict(os.environ, {"HOST": "api.example.com", "VER": "v1"}):
        data = {"url": "https://{{env.HOST}}/{{env.VER}}/users"}
        resolved = resolve_env_vars(data)
        assert resolved == {"url": "https://api.example.com/v1/users"}


def test_resolve_env_vars_default_value():
    """Test environment variable with default value."""
    # Variable not set, use default
    with patch.dict(os.environ, {}, clear=True):
        data = {"port": "{{env.PORT | default:8080}}"}
        resolved = resolve_env_vars(data)
        assert resolved == {"port": "8080"}

    # Variable set, ignore default
    with patch.dict(os.environ, {"PORT": "9000"}):
        data = {"port": "{{env.PORT | default:8080}}"}
        resolved = resolve_env_vars(data)
        assert resolved == {"port": "9000"}


def test_resolve_env_vars_missing_required():
    """Test missing required environment variable raises error."""
    with patch.dict(os.environ, {}, clear=True):
        data = {"key": "{{env.MISSING_VAR}}"}
        with pytest.raises(EnvVarError) as excinfo:
            resolve_env_vars(data)
        assert "Required environment variable 'MISSING_VAR'" in str(excinfo.value)


def test_resolve_env_vars_recursive():
    """Test recursive resolution in dicts and lists."""
    with patch.dict(os.environ, {"VAR1": "val1", "VAR2": "val2"}):
        data = {
            "top": "{{env.VAR1}}",
            "nested_dict": {"inner": "{{env.VAR2}}"},
            "nested_list": ["{{env.VAR1}}", {"item": "{{env.VAR2}}"}],
        }
        resolved = resolve_env_vars(data)
        assert resolved == {
            "top": "val1",
            "nested_dict": {"inner": "val2"},
            "nested_list": ["val1", {"item": "val2"}],
        }


def test_load_sut_with_env_vars(tmp_path):
    """Test loading SUT config with environment variables."""
    sut_path = tmp_path / "sut.yaml"
    sut_content = {
        "name": "Test SUT",
        "default_headers": {"Authorization": "Bearer {{env.API_TOKEN}}"},
        "services": {
            "api": {
                "base_url": "{{env.BASE_URL}}",
                "timeout_seconds": "{{env.TIMEOUT | default:45}}",
            }
        },
    }
    sut_path.write_text(yaml.dump(sut_content))

    with patch.dict(os.environ, {"API_TOKEN": "token123", "BASE_URL": "http://api.test"}):
        sut = load_sut(sut_path)
        assert sut.default_headers["Authorization"] == "Bearer token123"
        assert str(sut.services["api"].base_url).rstrip("/") == "http://api.test"
        assert sut.services["api"].timeout_seconds == 45.0


def test_load_scenario_with_env_vars(tmp_path):
    """Test loading scenario with environment variables."""
    scenario_path = tmp_path / "scenario.yaml"
    scenario_content = {
        "id": "test-scenario",
        "flow": [
            {
                "type": "http",
                "name": "get-info",
                "service": "api",
                "method": "GET",
                "path": "/info/{{env.USER_ID}}",
                "json": {"key": "{{env.API_KEY}}"},
            }
        ],
    }
    scenario_path.write_text(yaml.dump(scenario_content))

    with patch.dict(os.environ, {"USER_ID": "user123", "API_KEY": "secret"}):
        scenario = load_scenario(scenario_path)
        action = scenario.flow[0]
        assert action.path == "/info/user123"
        assert action.body == {"key": "secret"}


def test_load_sut_missing_env_var_error(tmp_path):
    """Test error when loading SUT with missing env var."""
    sut_path = tmp_path / "sut.yaml"
    sut_content = {
        "name": "Test SUT",
        "services": {"api": {"base_url": "http://api.test/{{env.MISSING}}"}},
    }
    sut_path.write_text(yaml.dump(sut_content))

    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ConfigLoadError) as excinfo:
            load_sut(sut_path)
        assert "Environment variable resolution failed" in str(excinfo.value)
        assert "MISSING" in str(excinfo.value)
