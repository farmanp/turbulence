"""SUT (System Under Test) configuration models."""

from typing import Any, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


class HttpServiceConfig(BaseModel):
    """Configuration for HTTP specific service settings."""

    model_config = ConfigDict(extra="forbid")

    base_url: HttpUrl = Field(
        ...,
        description="Base URL for the service (e.g., https://api.example.com)",
    )
    headers: dict[str, str] = Field(
        default_factory=dict,
        description="Service-specific headers",
    )
    timeout_seconds: float = Field(
        default=30.0,
        description="Request timeout in seconds",
        gt=0,
    )

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_base_url(cls, v: Any) -> Any:
        """Ensure base_url doesn't have trailing slash."""
        if isinstance(v, str):
            return v.rstrip("/")
        if hasattr(v, "unicode_string"):
            return v.unicode_string().rstrip("/")
        return v


class GrpcServiceConfig(BaseModel):
    """Configuration for gRPC specific service settings."""

    model_config = ConfigDict(extra="forbid")

    host: str = Field(..., description="Service host")
    port: int = Field(..., description="Service port", gt=0, lt=65536)
    use_tls: bool = Field(default=False, description="Whether to use TLS/SSL")
    proto_path: str | None = Field(
        default=None,
        description="Path to .proto file or directory containing protos",
    )
    timeout_seconds: float = Field(
        default=30.0, description="Request timeout", gt=0
    )


class KafkaServiceConfig(BaseModel):
    """Configuration for Kafka specific service settings."""

    model_config = ConfigDict(extra="forbid")

    bootstrap_servers: list[str] = Field(
        ..., description="List of bootstrap server addresses"
    )
    timeout_seconds: float = Field(
        default=30.0, description="Connection timeout", gt=0
    )


class ProfileHttpServiceConfig(BaseModel):
    """Configuration overrides for HTTP specific service settings."""

    model_config = ConfigDict(extra="forbid")

    base_url: HttpUrl | None = Field(
        default=None,
        description="Override base URL",
    )
    headers: dict[str, str] | None = Field(
        default=None,
        description="Override headers",
    )
    timeout_seconds: float | None = Field(
        default=None,
        description="Override timeout in seconds",
        gt=0,
    )

    @field_validator("base_url", mode="before")
    @classmethod
    def validate_base_url(cls, v: Any) -> Any:
        """Ensure base_url doesn't have trailing slash."""
        if v is None:
            return v
        if isinstance(v, str):
            return v.rstrip("/")
        if hasattr(v, "unicode_string"):
            return v.unicode_string().rstrip("/")
        return v


class ProfileGrpcServiceConfig(BaseModel):
    """Configuration overrides for gRPC specific service settings."""

    model_config = ConfigDict(extra="forbid")

    host: str | None = Field(default=None, description="Override host")
    port: int | None = Field(default=None, description="Override port", gt=0, lt=65536)
    use_tls: bool | None = Field(default=None, description="Override TLS usage")
    proto_path: str | None = Field(default=None, description="Override proto path")
    timeout_seconds: float | None = Field(
        default=None, description="Override timeout", gt=0
    )


class ProfileKafkaServiceConfig(BaseModel):
    """Configuration overrides for Kafka specific service settings."""

    model_config = ConfigDict(extra="forbid")

    bootstrap_servers: list[str] | None = Field(
        default=None, description="Override bootstrap servers"
    )
    timeout_seconds: float | None = Field(
        default=None, description="Override timeout", gt=0
    )


class Service(BaseModel):
    """Configuration for a single service in the system under test."""

    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    protocol: Literal["http", "grpc", "kafka"] = Field(
        default="http",
        description="Protocol used by the service",
    )
    http: HttpServiceConfig | None = Field(
        default=None,
        description="HTTP-specific configuration",
    )
    grpc: GrpcServiceConfig | None = Field(
        default=None,
        description="gRPC-specific configuration",
    )
    kafka: KafkaServiceConfig | None = Field(
        default=None,
        description="Kafka-specific configuration",
    )

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy(cls, data: Any) -> Any:
        """Migrate legacy top-level fields to explicit protocol blocks."""
        if not isinstance(data, dict):
            return data

        legacy_fields = ["base_url", "headers", "timeout_seconds"]
        has_legacy = any(k in data for k in legacy_fields)

        # If has legacy fields and no protocol, default to http
        if has_legacy and "protocol" not in data:
            data["protocol"] = "http"

        # If data is purely legacy (has base_url) and no protocol, default to http
        # (Already handled by has_legacy above, but keeping logic clear)

        # If protocol is http and we have legacy fields, move them to 'http' block
        if data.get("protocol", "http") == "http" and "http" not in data:
            http_data = {k: data.pop(k) for k in legacy_fields if k in data}
            if http_data:
                data["http"] = http_data

        return data

    @model_validator(mode="after")
    def validate_protocol_config(self) -> "Service":
        """Ensure the chosen protocol has its corresponding config block."""
        if self.protocol == "http" and not self.http:
            raise ValueError(
                "HTTP service configuration ('http' block or legacy fields) "
                "is required for protocol 'http'"
            )
        if self.protocol == "grpc" and not self.grpc:
            raise ValueError(
                "gRPC service configuration ('grpc' block) is required for protocol 'grpc'"
            )
        if self.protocol == "kafka" and not self.kafka:
            raise ValueError(
                "Kafka service configuration ('kafka' block) is required for protocol 'kafka'"
            )
        return self

    @property
    def base_url(self) -> HttpUrl:
        """Helper for HTTP actions (backward compatibility)."""
        if self.http:
            return self.http.base_url
        raise AttributeError(f"Service '{self.protocol}' doesn't have a base_url")

    @property
    def headers(self) -> dict[str, str]:
        """Helper for HTTP actions (backward compatibility)."""
        if self.http:
            return self.http.headers
        return {}

    @property
    def timeout_seconds(self) -> float:
        """Helper for backward compatibility."""
        if self.http:
            return self.http.timeout_seconds
        if self.grpc:
            return self.grpc.timeout_seconds
        if self.kafka:
            return self.kafka.timeout_seconds
        return 30.0


class ProfileService(BaseModel):
    """Service configuration overrides for a profile."""

    model_config = ConfigDict(extra="forbid")

    protocol: Literal["http", "grpc", "kafka"] | None = Field(
        default=None,
        description="Override protocol",
    )
    http: ProfileHttpServiceConfig | None = Field(
        default=None,
        description="Override HTTP config",
    )
    grpc: ProfileGrpcServiceConfig | None = Field(
        default=None,
        description="Override gRPC config",
    )
    kafka: ProfileKafkaServiceConfig | None = Field(
        default=None,
        description="Override Kafka config",
    )

    @model_validator(mode="before")
    @classmethod
    def migrate_legacy(cls, data: Any) -> Any:
        """Migrate legacy top-level fields in profile overrides."""
        if not isinstance(data, dict):
            return data

        legacy_fields = ["base_url", "headers", "timeout_seconds"]
        has_legacy = any(k in data for k in legacy_fields)

        # If has legacy fields and no protocol/http, assume http override
        if has_legacy and "http" not in data:
            http_data = {k: data.pop(k) for k in legacy_fields if k in data}
            if http_data:
                data["http"] = http_data
                if "protocol" not in data:
                    data["protocol"] = "http"

        return data

    @property
    def base_url(self) -> HttpUrl | None:
        """Helper for HTTP actions (backward compatibility)."""
        if self.http:
            return self.http.base_url
        return None

    @property
    def headers(self) -> dict[str, str] | None:
        """Helper for HTTP actions (backward compatibility)."""
        if self.http:
            return self.http.headers
        return None

    @property
    def timeout_seconds(self) -> float | None:
        """Helper for backward compatibility."""
        if self.http and self.http.timeout_seconds:
            return self.http.timeout_seconds
        if self.grpc and self.grpc.timeout_seconds:
            return self.grpc.timeout_seconds
        if self.kafka and self.kafka.timeout_seconds:
            return self.kafka.timeout_seconds
        return None


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
        service_headers = {}
        if service.protocol == "http" and service.http:
            service_headers = service.http.headers
        return {**self.default_headers, **service_headers}
