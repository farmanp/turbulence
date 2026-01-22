"""Tests for HTTP action retry policies."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from turbulence.actions.http import HttpActionRunner
from turbulence.config.scenario import HttpAction, RetryConfig
from turbulence.config.sut import Service, SUTConfig


@pytest.fixture
def sut_config():
    return SUTConfig(
        name="Test SUT",
        services={
            "api": Service(base_url="http://test.com", timeout_seconds=1.0)
        }
    )


@pytest.fixture
def mock_client():
    client = AsyncMock(spec=httpx.AsyncClient)
    client.request = AsyncMock()
    return client


@pytest.mark.asyncio
async def test_retry_on_status_success_eventually(sut_config, mock_client):
    """Test retrying on configured status codes until success."""
    action = HttpAction(
        name="test_retry",
        service="api",
        method="GET",
        path="/flaky",
        retry=RetryConfig(
            max_attempts=3,
            on_status=[503]
        )
    )
    
    # Mock responses: 503, then 200
    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_503.reason_phrase = "Service Unavailable"
    mock_503.headers = {}
    mock_503.text = "Error"
    
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.headers = {}
    mock_200.json.return_value = {"status": "ok"}
    
    mock_client.request.side_effect = [mock_503, mock_200]
    
    runner = HttpActionRunner(action, sut_config, client=mock_client)
    observation, _ = await runner.execute({})
    
    assert observation.ok
    assert observation.status_code == 200
    assert len(observation.attempts) == 2
    assert observation.attempts[0]["status_code"] == 503
    assert observation.attempts[1]["status_code"] == 200


@pytest.mark.asyncio
async def test_retry_exhausted(sut_config, mock_client):
    """Test that action fails when retry attempts are exhausted."""
    action = HttpAction(
        name="test_fail",
        service="api",
        method="GET",
        path="/fail",
        retry=RetryConfig(
            max_attempts=3,
            on_status=[503]
        )
    )
    
    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_503.reason_phrase = "Service Unavailable"
    mock_503.headers = {}
    
    mock_client.request.return_value = mock_503
    
    runner = HttpActionRunner(action, sut_config, client=mock_client)
    observation, _ = await runner.execute({})
    
    assert not observation.ok
    assert observation.status_code == 503
    assert len(observation.attempts) == 3
    assert mock_client.request.call_count == 3


@pytest.mark.asyncio
async def test_retry_on_timeout(sut_config, mock_client):
    """Test retrying on request timeouts."""
    action = HttpAction(
        name="test_timeout",
        service="api",
        method="GET",
        path="/timeout",
        retry=RetryConfig(
            max_attempts=2,
            on_timeout=True,
            backoff="fixed",
            delay_ms=10
        )
    )
    
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.headers = {}
    mock_200.json.return_value = {}

    # First raise timeout, then success
    mock_client.request.side_effect = [
        httpx.TimeoutException("Timeout"),
        mock_200
    ]
    
    runner = HttpActionRunner(action, sut_config, client=mock_client)
    observation, _ = await runner.execute({})
    
    assert observation.ok
    assert len(observation.attempts) == 2
    assert "Timeout" in str(observation.attempts[0]["error"])


@pytest.mark.asyncio
async def test_retry_on_connection_error(sut_config, mock_client):
    """Test retrying on connection errors."""
    action = HttpAction(
        name="test_conn_err",
        service="api",
        method="GET",
        path="/conn",
        retry=RetryConfig(
            max_attempts=2,
            on_connection_error=True,
            backoff="fixed",
            delay_ms=10
        )
    )
    
    mock_200 = MagicMock()
    mock_200.status_code = 200
    mock_200.headers = {}
    mock_200.json.return_value = {}

    # First raise ConnectError, then success
    mock_client.request.side_effect = [
        httpx.ConnectError("Refused"),
        mock_200
    ]
    
    runner = HttpActionRunner(action, sut_config, client=mock_client)
    observation, _ = await runner.execute({})
    
    assert observation.ok
    assert len(observation.attempts) == 2
    assert "Refused" in str(observation.attempts[0]["error"])


@pytest.mark.asyncio
async def test_no_retry_on_unconfigured_error(sut_config, mock_client):
    """Test that retry doesn't happen for unconfigured error types."""
    action = HttpAction(
        name="test_no_retry",
        service="api",
        method="GET",
        path="/fail",
        retry=RetryConfig(
            max_attempts=3,
            on_status=[500]
        )
    )
    
    # 404 is not in on_status
    mock_404 = MagicMock()
    mock_404.status_code = 404
    mock_404.reason_phrase = "Not Found"
    mock_404.headers = {}
    
    mock_client.request.return_value = mock_404
    
    runner = HttpActionRunner(action, sut_config, client=mock_client)
    observation, _ = await runner.execute({})
    
    assert not observation.ok
    assert observation.status_code == 404
    assert len(observation.attempts) == 1  # Only 1 attempt


@pytest.mark.asyncio
async def test_fixed_backoff_timing(sut_config, mock_client):
    """Test fixed backoff timing."""
    action = HttpAction(
        name="test_backoff",
        service="api",
        method="GET",
        path="/backoff",
        retry=RetryConfig(
            max_attempts=2,
            on_status=[503],
            backoff="fixed",
            delay_ms=50
        )
    )
    
    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_503.headers = {}
    
    mock_client.request.return_value = mock_503
    
    runner = HttpActionRunner(action, sut_config, client=mock_client)
    
    with patch("asyncio.sleep") as mock_sleep:
        await runner.execute({})
        
        # Should sleep once for 0.05s
        mock_sleep.assert_called_once_with(0.05)


@pytest.mark.asyncio
async def test_exponential_backoff_timing(sut_config, mock_client):
    """Test exponential backoff timing."""
    action = HttpAction(
        name="test_exp_backoff",
        service="api",
        method="GET",
        path="/exp",
        retry=RetryConfig(
            max_attempts=3,
            on_status=[503],
            backoff="exponential",
            base_delay_ms=100
        )
    )
    
    mock_503 = MagicMock()
    mock_503.status_code = 503
    mock_503.headers = {}
    
    mock_client.request.return_value = mock_503
    
    runner = HttpActionRunner(action, sut_config, client=mock_client)
    
    with patch("asyncio.sleep") as mock_sleep:
        await runner.execute({})
        
        # Attempt 1 -> Fail. Retry count = 1. Delay = 100 * 2^0 = 100ms = 0.1s
        # Attempt 2 -> Fail. Retry count = 2. Delay = 100 * 2^1 = 200ms = 0.2s
        assert mock_sleep.call_count == 2
        mock_sleep.assert_any_call(0.1)
        mock_sleep.assert_any_call(0.2)
