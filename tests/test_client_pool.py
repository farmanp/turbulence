"""Tests for ClientPool (FEAT-037)."""

import pytest

from turbulence.config.sut import SUTConfig
from turbulence.engine.client_pool import ClientPool


@pytest.fixture
def sut_config():
    return SUTConfig.model_validate({
        "name": "test-system",
        "services": {
            "api": {"base_url": "https://api.example.com"},
            "auth": {"base_url": "https://auth.example.com"},
            "grpc-svc": {
                "protocol": "grpc",
                "grpc": {"host": "localhost", "port": 50051}
            }
        }
    })


@pytest.mark.asyncio
async def test_client_pool_reuses_http_clients(sut_config):
    pool = ClientPool(sut_config)

    client1 = await pool.get_http_client("api")
    client2 = await pool.get_http_client("api")
    client3 = await pool.get_http_client("auth")

    assert client1 is client2
    assert client1 is not client3
    assert client1.base_url == "https://api.example.com/"
    assert client3.base_url == "https://auth.example.com/"

    await pool.close_all()


@pytest.mark.asyncio
async def test_client_pool_reuses_grpc_channels(sut_config):
    pool = ClientPool(sut_config)

    channel1 = await pool.get_grpc_channel("grpc-svc")
    channel2 = await pool.get_grpc_channel("grpc-svc")

    assert channel1 is channel2

    await pool.close_all()


@pytest.mark.asyncio
async def test_client_pool_close_all(sut_config):
    pool = ClientPool(sut_config)
    client = await pool.get_http_client("api")

    # Mocking close to verify it's called
    original_aclose = client.aclose
    closed = False
    async def mock_aclose():
        nonlocal closed
        closed = True
        await original_aclose()

    client.aclose = mock_aclose

    await pool.close_all()
    assert closed
    assert len(pool._http_clients) == 0
