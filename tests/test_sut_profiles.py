"""Tests for SUT configuration profiles."""

from pathlib import Path

import pytest
import yaml

from turbulence.config.loader import ConfigLoadError, load_sut
from turbulence.config.sut import SUTConfig


@pytest.fixture
def sut_with_profiles(tmp_path):
    """Create a SUT config file with profiles."""
    sut_path = tmp_path / "sut.yaml"
    sut_content = {
        "name": "Profiled SUT",
        "default_headers": {"X-Common": "common"},
        "services": {
            "api": {"base_url": "http://base.api", "timeout_seconds": 30},
            "db": {"base_url": "http://base.db"},
        },
        "default_profile": "dev",
        "profiles": {
            "dev": {
                "services": {
                    "api": {"base_url": "http://dev.api"},
                }
            },
            "prod": {
                "default_headers": {"X-Env": "prod"},
                "services": {
                    "api": {"base_url": "http://prod.api", "timeout_seconds": 10},
                    "db": {"headers": {"X-Secret": "123"}},
                },
            },
        },
    }
    sut_path.write_text(yaml.dump(sut_content))
    return sut_path


def test_load_base_config_explicitly(sut_with_profiles):
    """Test loading base config ignoring default profile when explicitly None?
    
    Actually, load_sut(profile=None) uses default_profile if set.
    There is currently no way to FORCE base config if default_profile is set
    without modifying the file. This is acceptable per requirements.
    """
    # Create one WITHOUT default_profile to test base loading
    base_sut_path = sut_with_profiles.parent / "base_sut.yaml"
    with sut_with_profiles.open() as f:
        data = yaml.safe_load(f)
    del data["default_profile"]
    base_sut_path.write_text(yaml.dump(data))

    config = load_sut(base_sut_path)
    assert str(config.services["api"].base_url).rstrip("/") == "http://base.api"


def test_load_default_profile(sut_with_profiles):
    """Test that default profile is loaded when no profile specified."""
    config = load_sut(sut_with_profiles)
    assert str(config.services["api"].base_url).rstrip("/") == "http://dev.api"
    # Inheritance
    assert str(config.services["db"].base_url).rstrip("/") == "http://base.db"


def test_load_specific_profile(sut_with_profiles):
    """Test loading a specific profile by name."""
    config = load_sut(sut_with_profiles, profile="prod")
    
    # Check overrides
    assert str(config.services["api"].base_url).rstrip("/") == "http://prod.api"
    assert config.services["api"].timeout_seconds == 10.0
    
    # Check header merging
    assert config.default_headers["X-Common"] == "common"
    assert config.default_headers["X-Env"] == "prod"
    
    # Check service specific header merge
    assert config.services["db"].headers["X-Secret"] == "123"


def test_load_missing_profile_raises_error(sut_with_profiles):
    """Test that requesting a missing profile raises ConfigLoadError."""
    with pytest.raises(ConfigLoadError) as excinfo:
        load_sut(sut_with_profiles, profile="missing")
    assert "Profile 'missing' not found" in str(excinfo.value)
    assert "Available profiles: dev, prod" in str(excinfo.value)


def test_backward_compatibility(tmp_path):
    """Test that SUT configs without profiles work unchanged."""
    sut_path = tmp_path / "old_sut.yaml"
    sut_content = {
        "name": "Old SUT",
        "services": {"api": {"base_url": "http://api.com"}}
    }
    sut_path.write_text(yaml.dump(sut_content))
    
    config = load_sut(sut_path)
    assert config.name == "Old SUT"
    assert config.profiles == {}
