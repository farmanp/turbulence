"""SUT (System Under Test) configuration models."""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, field_validator


class Service(BaseModel):
    """Configuration for a single service in the system under test."""

    model_config = ConfigDict(extra="forbid")

    base_url: HttpUrl = Field(
        ...,
        description="Base URL for the service (e.g., https://api.example.com)",
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Service-specific headers (override default_headers)",
    )
    timeout_seconds: float = Field(
        default=30.0,
        description="Default timeout for requests to this service",
        gt=0,
    )

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_base_url(cls, v: Any) -> Any:
        """Ensure base_url doesn't have trailing slash."""
        if isinstance(v, str):
            return v.rstrip("/")
        return v


class ProfileService(BaseModel):
    """Service configuration overrides for a profile."""

    model_config = ConfigDict(extra="forbid")

    base_url: HttpUrl | None = Field(
        default=None,
        description="Override base URL",
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="Override/merge headers",
    )
    timeout_seconds: float | None = Field(
        default=None,
        description="Override timeout",
        gt=0,
    )

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_base_url(cls, v: Any) -> Any:
        """Ensure base_url doesn't have trailing slash."""
        if isinstance(v, str):
            return v.rstrip("/")
        return v


class Profile(BaseModel):
    """Configuration overrides for a specific environment profile."""

    model_config = ConfigDict(extra="forbid")

    default_headers: dict[str, str] | None = Field(
        default=None,
        description="Override default headers",
    )
    services: dict[str, ProfileService] | None = Field(
        default=None,
        description="Override service configurations",
    )


class SUTConfig(BaseModel):
    """System Under Test configuration.

    Defines the services that Turbulence will interact with during simulations,
    including base URLs, default headers, and service-specific settings.
    """

    model_config = ConfigDict(extra="forbid")

    name: str = Field(
        ...,
        description="Name of the system under test",
        min_length=1,
    )
    default_headers: dict[str, str] = Field(
        default_factory=dict,
        description="Default headers applied to all requests (can use {{templates}})",
    )
    services: dict[str, Service] = Field(
        ...,
        description="Map of service names to their configurations",
        min_length=1,
    )
    profiles: dict[str, Profile] = Field(
        default_factory=dict,
        description="Environment-specific configuration overrides",
    )
    default_profile: str | None = Field(
        default=None,
        description="Name of the profile to use if none specified via CLI",
    )

    def get_service(self, name: str) -> Service:
        """Get a service by name.

        Args:
            name: The service name

        Returns:
            The service configuration

        Raises:
            KeyError: If the service doesn't exist
        """
        if name not in self.services:
            available = ", ".join(sorted(self.services.keys()))
            raise KeyError(f"Service '{name}' not found. Available: {available}")
        return self.services[name]

    def get_headers_for_service(self, service_name: str) -> dict[str, str]:
        """Get merged headers for a service (default + service-specific).

        Args:
            service_name: The service name

        Returns:
            Merged headers dictionary
        """
        service = self.get_service(service_name)
        return {**self.default_headers, **service.headers}
