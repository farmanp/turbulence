"""Integration tests for branching flows."""

import pytest
from unittest.mock import AsyncMock, MagicMock

import httpx

from turbulence.config.scenario import (
    Action,
    AssertAction,
    BranchAction,
    Expectation,
    HttpAction,
    Scenario,
    StopCondition,
)
from turbulence.config.sut import SUTConfig, Service
from turbulence.engine.scenario_runner import ScenarioRunner
from turbulence.engine.template import TemplateEngine
from turbulence.models.observation import Observation


@pytest.fixture
def sut_config() -> SUTConfig:
    """Create a test SUT config."""
    return SUTConfig(
        name="test-api",
        services={
            "api": Service(base_url="http://localhost:8080"),
            "payments": Service(base_url="http://localhost:8081"),
        },
    )


@pytest.fixture
def template_engine() -> TemplateEngine:
    """Create a template engine."""
    return TemplateEngine()


@pytest.fixture
def mock_client() -> AsyncMock:
    """Create a mock HTTP client."""
    client = AsyncMock(spec=httpx.AsyncClient)
    return client


class TestBranchActionParsing:
    """Test BranchAction model parsing."""

    def test_branch_action_with_nested_http_actions(self) -> None:
        """Test parsing BranchAction with nested HTTP actions."""
        branch = BranchAction(
            name="handle_payment",
            condition='{{payment_status}} == "declined"',
            if_true=[
                {
                    "type": "http",
                    "name": "retry_payment",
                    "service": "payments",
                    "method": "POST",
                    "path": "/retry",
                }
            ],
            if_false=[
                {
                    "type": "http",
                    "name": "confirm_order",
                    "service": "api",
                    "method": "POST",
                    "path": "/confirm",
                }
            ],
        )

        assert branch.name == "handle_payment"
        assert branch.condition == '{{payment_status}} == "declined"'
        assert len(branch.if_true) == 1
        assert len(branch.if_false) == 1
        assert isinstance(branch.if_true[0], HttpAction)
        assert isinstance(branch.if_false[0], HttpAction)

    def test_branch_action_with_empty_branches(self) -> None:
        """Test BranchAction with empty branch lists."""
        branch = BranchAction(
            name="skip_if_cached",
            condition="{{is_cached}}",
            if_true=[],  # Skip if cached
            if_false=[
                {
                    "type": "http",
                    "name": "fetch_data",
                    "service": "api",
                    "method": "GET",
                    "path": "/data",
                }
            ],
        )

        assert len(branch.if_true) == 0
        assert len(branch.if_false) == 1

    def test_nested_branch_actions(self) -> None:
        """Test BranchAction with nested branch."""
        outer_branch = BranchAction(
            name="outer_branch",
            condition="{{is_premium}}",
            if_true=[
                {
                    "type": "branch",
                    "name": "premium_path",
                    "condition": '{{tier}} == "gold"',
                    "if_true": [
                        {
                            "type": "http",
                            "name": "gold_discount",
                            "service": "api",
                            "method": "POST",
                            "path": "/discount/gold",
                        }
                    ],
                    "if_false": [
                        {
                            "type": "http",
                            "name": "standard_discount",
                            "service": "api",
                            "method": "POST",
                            "path": "/discount/standard",
                        }
                    ],
                }
            ],
            if_false=[],
        )

        assert len(outer_branch.if_true) == 1
        nested = outer_branch.if_true[0]
        assert isinstance(nested, BranchAction)
        assert nested.name == "premium_path"


class TestSimpleConditionalSkip:
    """Test simple conditional skip on actions."""

    def test_http_action_with_condition_field(self) -> None:
        """Test HTTP action with optional condition field."""
        action = HttpAction(
            name="optional_step",
            service="api",
            method="GET",
            path="/optional",
            condition='{{is_enabled}} == True',
        )
        assert action.condition == '{{is_enabled}} == True'

    def test_assert_action_with_condition_field(self) -> None:
        """Test assert action with optional condition field."""
        action = AssertAction(
            name="conditional_assert",
            expect=Expectation(status_code=200),
            condition="{{should_validate}}",
        )
        assert action.condition == "{{should_validate}}"


class TestScenarioRunnerBranching:
    """Test ScenarioRunner with branching flows."""

    @pytest.mark.asyncio
    async def test_branch_takes_if_true_path(
        self,
        sut_config: SUTConfig,
        template_engine: TemplateEngine,
        mock_client: AsyncMock,
    ) -> None:
        """Test that branch takes if_true path when condition is true."""
        # Mock HTTP response
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        mock_response.elapsed = MagicMock()
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_client.request.return_value = mock_response

        scenario = Scenario(
            id="test_branch_true",
            flow=[
                BranchAction(
                    name="check_status",
                    condition='"{{status}}" == "declined"',
                    if_true=[
                        HttpAction(
                            name="retry_action",
                            service="api",
                            method="POST",
                            path="/retry",
                        ),
                    ],
                    if_false=[
                        HttpAction(
                            name="confirm_action",
                            service="api",
                            method="POST",
                            path="/confirm",
                        ),
                    ],
                ),
            ],
        )

        runner = ScenarioRunner(template_engine, sut_config)
        context = {"status": "declined"}

        results = []
        async for result in runner.execute_flow(scenario, context, mock_client):
            results.append(result)

        # Should have branch decision + one action from if_true
        assert len(results) == 2

        # First result is branch decision
        _, action, obs, _ = results[0]
        assert isinstance(action, BranchAction)
        assert obs.branch_result is True
        assert obs.branch_taken == "if_true"

        # Second result is the retry action
        _, action, _, _ = results[1]
        assert isinstance(action, HttpAction)
        assert action.name == "retry_action"

    @pytest.mark.asyncio
    async def test_branch_takes_if_false_path(
        self,
        sut_config: SUTConfig,
        template_engine: TemplateEngine,
        mock_client: AsyncMock,
    ) -> None:
        """Test that branch takes if_false path when condition is false."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        mock_response.elapsed = MagicMock()
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_client.request.return_value = mock_response

        scenario = Scenario(
            id="test_branch_false",
            flow=[
                BranchAction(
                    name="check_status",
                    condition='"{{status}}" == "declined"',
                    if_true=[
                        HttpAction(
                            name="retry_action",
                            service="api",
                            method="POST",
                            path="/retry",
                        ),
                    ],
                    if_false=[
                        HttpAction(
                            name="confirm_action",
                            service="api",
                            method="POST",
                            path="/confirm",
                        ),
                    ],
                ),
            ],
        )

        runner = ScenarioRunner(template_engine, sut_config)
        context = {"status": "approved"}  # Not declined

        results = []
        async for result in runner.execute_flow(scenario, context, mock_client):
            results.append(result)

        # Should have branch decision + one action from if_false
        assert len(results) == 2

        # First result is branch decision
        _, action, obs, _ = results[0]
        assert isinstance(action, BranchAction)
        assert obs.branch_result is False
        assert obs.branch_taken == "if_false"

        # Second result is the confirm action
        _, action, _, _ = results[1]
        assert isinstance(action, HttpAction)
        assert action.name == "confirm_action"

    @pytest.mark.asyncio
    async def test_action_skipped_with_condition(
        self,
        sut_config: SUTConfig,
        template_engine: TemplateEngine,
        mock_client: AsyncMock,
    ) -> None:
        """Test that action is skipped when condition is false."""
        mock_response = MagicMock(spec=httpx.Response)
        mock_response.status_code = 200
        mock_response.headers = {"content-type": "application/json"}
        mock_response.json.return_value = {"success": True}
        mock_response.text = '{"success": true}'
        mock_response.elapsed = MagicMock()
        mock_response.elapsed.total_seconds.return_value = 0.1
        mock_client.request.return_value = mock_response

        scenario = Scenario(
            id="test_conditional_skip",
            flow=[
                HttpAction(
                    name="always_run",
                    service="api",
                    method="GET",
                    path="/always",
                ),
                HttpAction(
                    name="conditional_step",
                    service="api",
                    method="GET",
                    path="/conditional",
                    condition="{{should_run}}",
                ),
                HttpAction(
                    name="after_conditional",
                    service="api",
                    method="GET",
                    path="/after",
                ),
            ],
        )

        runner = ScenarioRunner(template_engine, sut_config)
        context = {"should_run": False}

        results = []
        async for result in runner.execute_flow(scenario, context, mock_client):
            results.append(result)

        # Should have 3 results
        assert len(results) == 3

        # First action executed
        _, action1, obs1, _ = results[0]
        assert action1.name == "always_run"
        assert obs1.condition_skipped is False

        # Second action skipped
        _, action2, obs2, _ = results[1]
        assert action2.name == "conditional_step"
        assert obs2.condition_skipped is True

        # Third action executed
        _, action3, obs3, _ = results[2]
        assert action3.name == "after_conditional"
        assert obs3.condition_skipped is False

        # HTTP client should only be called twice (skipped action doesn't make request)
        assert mock_client.request.call_count == 2

    @pytest.mark.asyncio
    async def test_context_propagates_through_branches(
        self,
        sut_config: SUTConfig,
        template_engine: TemplateEngine,
        mock_client: AsyncMock,
    ) -> None:
        """Test that context updates propagate through branch execution."""
        # First response returns user_id
        mock_response1 = MagicMock(spec=httpx.Response)
        mock_response1.status_code = 200
        mock_response1.headers = {"content-type": "application/json"}
        mock_response1.json.return_value = {"user_id": "user_123"}
        mock_response1.text = '{"user_id": "user_123"}'
        mock_response1.elapsed = MagicMock()
        mock_response1.elapsed.total_seconds.return_value = 0.1

        # Second response uses user_id
        mock_response2 = MagicMock(spec=httpx.Response)
        mock_response2.status_code = 200
        mock_response2.headers = {"content-type": "application/json"}
        mock_response2.json.return_value = {"success": True}
        mock_response2.text = '{"success": true}'
        mock_response2.elapsed = MagicMock()
        mock_response2.elapsed.total_seconds.return_value = 0.1

        mock_client.request.side_effect = [mock_response1, mock_response2]

        scenario = Scenario(
            id="test_context_propagation",
            flow=[
                HttpAction(
                    name="get_user",
                    service="api",
                    method="GET",
                    path="/user",
                    extract={"user_id": "$.user_id"},
                ),
                BranchAction(
                    name="check_user",
                    condition='"{{user_id}}" == "user_123"',
                    if_true=[
                        HttpAction(
                            name="update_user",
                            service="api",
                            method="POST",
                            path="/user/{{user_id}}/update",
                        ),
                    ],
                    if_false=[],
                ),
            ],
        )

        runner = ScenarioRunner(template_engine, sut_config)
        context: dict = {}

        results = []
        async for result in runner.execute_flow(scenario, context, mock_client):
            results.append(result)

        # get_user + branch decision + update_user
        assert len(results) == 3

        # Verify extraction worked and was available in branch
        _, _, _, final_context = results[2]
        assert final_context.get("user_id") == "user_123"

        # Verify the update_user path was called with user_id
        calls = mock_client.request.call_args_list
        assert "/user/user_123/update" in str(calls[1])


class TestBranchObservationFields:
    """Test observation fields for branch decisions."""

    def test_branch_observation_fields(self) -> None:
        """Test that branch observation has correct fields."""
        obs = Observation(
            ok=True,
            latency_ms=0.0,
            action_name="test_branch",
            branch_condition='{{status}} == "active"',
            branch_result=True,
            branch_taken="if_true",
        )

        assert obs.branch_condition == '{{status}} == "active"'
        assert obs.branch_result is True
        assert obs.branch_taken == "if_true"
        assert obs.condition_skipped is False

    def test_skipped_observation_fields(self) -> None:
        """Test that skipped observation has correct fields."""
        obs = Observation(
            ok=True,
            latency_ms=0.0,
            action_name="skipped_action",
            branch_condition="{{should_run}}",
            branch_result=False,
            condition_skipped=True,
        )

        assert obs.condition_skipped is True
        assert obs.branch_result is False


class TestScenarioYamlParsing:
    """Test parsing scenarios from YAML-like dicts."""

    def test_scenario_with_branch_action(self) -> None:
        """Test parsing a complete scenario with branch action."""
        scenario_dict = {
            "id": "payment_flow",
            "description": "Handle payment with retry logic",
            "flow": [
                {
                    "type": "http",
                    "name": "attempt_payment",
                    "service": "payments",
                    "method": "POST",
                    "path": "/charge",
                    "extract": {"payment_status": "$.status"},
                },
                {
                    "type": "branch",
                    "name": "handle_result",
                    "condition": '{{payment_status}} == "declined"',
                    "if_true": [
                        {
                            "type": "http",
                            "name": "retry_with_backup",
                            "service": "payments",
                            "method": "POST",
                            "path": "/charge",
                            "json": {"payment_method": "backup_card"},
                        }
                    ],
                    "if_false": [
                        {
                            "type": "http",
                            "name": "confirm_order",
                            "service": "api",
                            "method": "POST",
                            "path": "/orders/confirm",
                        }
                    ],
                },
            ],
        }

        scenario = Scenario(**scenario_dict)

        assert scenario.id == "payment_flow"
        assert len(scenario.flow) == 2

        # First action is HTTP
        assert isinstance(scenario.flow[0], HttpAction)
        assert scenario.flow[0].name == "attempt_payment"

        # Second action is Branch
        branch = scenario.flow[1]
        assert isinstance(branch, BranchAction)
        assert branch.name == "handle_result"
        assert len(branch.if_true) == 1
        assert len(branch.if_false) == 1
