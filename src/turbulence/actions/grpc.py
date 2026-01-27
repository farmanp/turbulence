"""gRPC action runner for executing gRPC unary calls."""

import time
from typing import Any

import grpc
from google.protobuf import json_format

from turbulence.actions.base import BaseActionRunner
from turbulence.config.scenario import GrpcAction
from turbulence.config.sut import SUTConfig
from turbulence.models.observation import Observation
from turbulence.utils.extractor import extract_values


class GrpcActionRunner(BaseActionRunner):
    """Executes gRPC unary calls and extracts values from response messages.

    This runner handles gRPC unary requests. It currently requires that the
    service supports reflection OR that the necessary proto definitions are
    somehow accessible (implementation planned for dynamic proto loading).
    """

    def __init__(
        self,
        action: GrpcAction,
        sut_config: SUTConfig,
        channel: grpc.aio.Channel | None = None,
    ) -> None:
        """Initialize the gRPC action runner.

        Args:
            action: The gRPC action configuration to execute.
            sut_config: The system under test configuration.
            channel: Optional gRPC channel. If not provided, one will be created.
        """
        self.action = action
        self.sut_config = sut_config
        self.channel = channel

    async def execute(
        self,
        context: dict[str, Any],
    ) -> tuple[Observation, dict[str, Any]]:
        """Execute the gRPC action and return observation with updated context."""
        from turbulence.actions.grpc_utils import GrpcReflectionClient

        service = self.sut_config.get_service(self.action.service)

        if service.protocol != "grpc" or not service.grpc:
            raise ValueError(f"Service '{self.action.service}' is not configured for gRPC")

        host = service.grpc.host
        port = service.grpc.port
        target = f"{host}:{port}"

        start_time = time.perf_counter()

        try:
            # Use pooled channel if available, otherwise create temporary
            channel_context: Any
            if self.channel:
                from contextlib import asynccontextmanager
                @asynccontextmanager
                async def noop_context(c): yield c
                channel_context = noop_context(self.channel)
            else:
                channel_context = grpc.aio.insecure_channel(target)

            async with channel_context as channel:
                # Resolve method
                if "/" not in self.action.method:
                    raise ValueError(f"Invalid gRPC method format: {self.action.method}. Expected 'Package.Service/Method'")

                full_service_name, method_name = self.action.method.split("/", 1)

                # Use reflection to get message classes
                refl = GrpcReflectionClient(channel)
                resolved = await refl.resolve_service(full_service_name)

                if not resolved:
                    error_msg = f"Failed to resolve gRPC service '{full_service_name}' via reflection. Ensure reflection is enabled on the server."
                    return self._error_obs(error_msg, start_time, host, port), context

                message_classes = refl.get_message_classes(full_service_name, method_name)
                if not message_classes:
                    error_msg = f"Method '{method_name}' not found in service '{full_service_name}'"
                    return self._error_obs(error_msg, start_time, host, port), context

                request_class, response_class = message_classes

                # Parse request
                request_msg = json_format.ParseDict(self.action.body or {}, request_class())

                # Execute call
                method_path = f"/{full_service_name}/{method_name}"

                metadata = []
                if self.action.metadata:
                    for k, v in self.action.metadata.items():
                        metadata.append((k.lower(), str(v)))

                # Add correlation ID if present
                if "X-Correlation-ID" in self.sut_config.default_headers:
                    metadata.append(("x-correlation-id", self.sut_config.default_headers["X-Correlation-ID"]))

                response_msg = await channel.unary_unary(
                    method_path,
                    request_serializer=request_class.SerializeToString,
                    response_deserializer=response_class.FromString,
                )(request_msg, metadata=metadata, timeout=service.grpc.timeout_seconds)

                # Convert response to dict
                response_dict = json_format.MessageToDict(response_msg)

                observation = Observation(
                    ok=True,
                    protocol="grpc",
                    status_code=0,
                    latency_ms=(time.perf_counter() - start_time) * 1000,
                    headers={},
                    body=response_dict,
                    action_name=self.action.name,
                    service=self.action.service,
                    metadata={
                        "host": host,
                        "port": port,
                        "method": self.action.method,
                    },
                )

                # Extract values if specified
                if self.action.extract:
                    extracted = extract_values(self.action.extract, response_dict)
                    context.update(extracted)

                return observation, context

        except Exception as e:
            return self._error_obs(str(e), start_time, host, port), context

    def _error_obs(self, error: str, start_time: float, host: str, port: int) -> Observation:
        """Helper to create an error observation."""
        return Observation(
            ok=False,
            protocol="grpc",
            status_code=grpc.StatusCode.UNKNOWN.value[0],
            latency_ms=(time.perf_counter() - start_time) * 1000,
            headers={},
            body=None,
            errors=[error],
            action_name=self.action.name,
            service=self.action.service,
            metadata={
                "host": host,
                "port": port,
                "method": self.action.method,
            },
        )
