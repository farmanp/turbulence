"""Tests for gRPC action runner (FEAT-036)."""

import pytest

from turbulence.actions.grpc import GrpcActionRunner
from turbulence.config.scenario import GrpcAction
from turbulence.config.sut import SUTConfig
from turbulence.models.observation import Observation


@pytest.fixture
def grpc_sut_config():
    return SUTConfig.model_validate({
        "name": "grpc-test-system",
        "services": {
            "user-service": {
                "protocol": "grpc",
                "grpc": {
                    "host": "localhost",
                    "port": 50051,
                    "timeout_seconds": 5.0
                }
            }
        }
    })


@pytest.mark.asyncio
async def test_grpc_runner_initialization(grpc_sut_config):
    action = GrpcAction(
        name="get-user",
        service="user-service",
        method="UserService/GetUser",
        message={"id": "123"}
    )
    runner = GrpcActionRunner(action, grpc_sut_config)
    assert runner.action.name == "get-user"
    assert runner.sut_config.name == "grpc-test-system"


@pytest.mark.asyncio
async def test_grpc_runner_fails_gracefully_when_no_server(grpc_sut_config):
    """Ensure the runner returns a failure observation when it can't connect/resolve."""
    action = GrpcAction(
        name="get-user",
        service="user-service",
        method="UserService/GetUser",
        message={"id": "123"}
    )
    runner = GrpcActionRunner(action, grpc_sut_config)

    # This will fail because no server is running and resolution isn't implemented
    observation, context = await runner.execute({})

    assert isinstance(observation, Observation)
    assert observation.ok is False
    assert observation.protocol == "grpc"
    assert "Failed to resolve gRPC service" in observation.errors[0]
    assert observation.metadata["method"] == "UserService/GetUser"


@pytest.mark.asyncio
async def test_grpc_runner_requires_grpc_service():
    sut_config = SUTConfig.model_validate({
        "name": "mixed-system",
        "services": {
            "api": {"base_url": "https://api.com"} # Default HTTP
        }
    })
    action = GrpcAction(
        name="get-user",
        service="api",
        method="UserService/GetUser"
    )
    runner = GrpcActionRunner(action, sut_config)

    with pytest.raises(ValueError, match="not configured for gRPC"):
        await runner.execute({})
