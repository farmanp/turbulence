"""Unified client pool for managing connection lifecycles across protocols."""

import asyncio
import logging

import grpc.aio
import httpx

from turbulence.config.sut import SUTConfig

logger = logging.getLogger(__name__)


class ClientPool:
    """Manages a pool of clients (HTTP, gRPC, Kafka) for a simulation run.

    This pool ensures that connections are reused across multiple workflow
    instances and properly cleaned up when the simulation completes.
    """

    def __init__(self, sut_config: SUTConfig) -> None:
        """Initialize the client pool.

        Args:
            sut_config: The system under test configuration.
        """
        self.sut_config = sut_config
        self._http_clients: dict[str, httpx.AsyncClient] = {}
        self._grpc_channels: dict[str, grpc.aio.Channel] = {}
        # Kafka producers will be added in a future ticket
        self._lock = asyncio.Lock()

    async def get_http_client(self, service_name: str) -> httpx.AsyncClient:
        """Get or create an HTTP client for a specific service.

        Args:
            service_name: Name of the service.

        Returns:
            An httpx.AsyncClient instance.
        """
        async with self._lock:
            if service_name not in self._http_clients:
                service = self.sut_config.get_service(service_name)

                # We create one client per service to allow for service-specific
                # configuration like base_url and default headers.
                # Note: httpx.AsyncClient can handle multiple hosts, but
                # pinning it to a service makes header management easier.

                # Determine base_url
                base_url = ""
                if service.protocol == "http" and service.http:
                    base_url = str(service.http.base_url)
                else:
                    try:
                        base_url = str(service.base_url)
                    except AttributeError:
                        pass

                self._http_clients[service_name] = httpx.AsyncClient(
                    base_url=base_url,
                    timeout=service.timeout_seconds,
                )
                logger.debug(f"Created new HTTP client for service '{service_name}'")

            return self._http_clients[service_name]

    async def get_grpc_channel(self, service_name: str) -> grpc.aio.Channel:
        """Get or create a gRPC channel for a specific service.

        Args:
            service_name: Name of the service.

        Returns:
            A grpc.aio.Channel instance.
        """
        async with self._lock:
            if service_name not in self._grpc_channels:
                service = self.sut_config.get_service(service_name)
                if service.protocol != "grpc" or not service.grpc:
                    raise ValueError(f"Service '{service_name}' is not a gRPC service")

                target = f"{service.grpc.host}:{service.grpc.port}"

                if service.grpc.use_tls:
                    # TODO: Support credentials
                    channel = grpc.aio.secure_channel(target, grpc.ssl_channel_credentials())
                else:
                    channel = grpc.aio.insecure_channel(target)

                self._grpc_channels[service_name] = channel
                logger.debug(f"Created new gRPC channel for service '{service_name}'")

            return self._grpc_channels[service_name]

    async def close_all(self) -> None:
        """Close all pooled clients and channels."""
        async with self._lock:
            # Close HTTP clients
            for name, client in self._http_clients.items():
                await client.aclose()
                logger.debug(f"Closed HTTP client for service '{name}'")
            self._http_clients.clear()

            # Close gRPC channels
            for name, channel in self._grpc_channels.items():
                await channel.close()
                logger.debug(f"Closed gRPC channel for service '{name}'")
            self._grpc_channels.clear()
