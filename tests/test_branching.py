"""Tests for branching flows and conditional execution."""

import pytest
import httpx
from unittest.mock import AsyncMock, MagicMock

from turbulence.config.scenario import (
    Scenario,
    HttpAction,
    WaitAction,
    AssertAction,
    BranchAction,
    StopCondition,
)
from turbulence.config.sut import SUTConfig
from turbulence.engine.scenario_runner import ScenarioRunner
from turbulence.engine.template import TemplateEngine
from turbulence.models.observation import Observation

@pytest.fixture
def template_engine():
    return TemplateEngine()

from turbulence.config.sut import SUTConfig, Service

@pytest.fixture
def sut_config():
    return SUTConfig(
        name="test-sut", 
        services={"api": Service(base_url="http://localhost:8080")}
    )

@pytest.fixture
def scenario_runner(template_engine, sut_config):
    return ScenarioRunner(template_engine, sut_config)

@pytest.mark.asyncio
async def test_conditional_skip(scenario_runner):
    """Test skipping a step based on a condition."""
    scenario = Scenario(
        id="test-skip",
        flow=[
            HttpAction(name="step1", service="api", method="GET", path="/", condition="1 == 2"),
            HttpAction(name="step2", service="api", method="GET", path="/", condition="1 == 1"),
        ],
        stop_when=StopCondition()
    )
    
    context = {}
    client = MagicMock()
    
    # We need to mock _execute_action because we don't want to actually hit the network
    # But since we're testing skipping, step1 should NOT call _execute_action
    scenario_runner._execute_action = AsyncMock(return_value=(Observation(ok=True, action_name="step2", latency_ms=0.0), context))
    
    results = []
    async for r in scenario_runner.execute_flow(scenario, context, client):
        results.append(r)
    
    assert len(results) == 2
    # Step 1 should be skipped
    assert results[0][2].condition_skipped is True
    assert results[0][2].action_name == "step1"
    
    # Step 2 should be executed
    assert results[1][2].action_name == "step2"
    assert results[1][2].condition_skipped is False
    scenario_runner._execute_action.assert_called_once()

@pytest.mark.asyncio
async def test_branching_if_true(scenario_runner):
    """Test taking the if_true branch."""
    scenario = Scenario(
        id="test-branch",
        flow=[
            BranchAction(
                name="branch1",
                condition="true",
                if_true=[
                    HttpAction(name="true_step", service="api", method="GET", path="/")
                ],
                if_false=[
                    HttpAction(name="false_step", service="api", method="GET", path="/")
                ]
            )
        ],
        stop_when=StopCondition()
    )
    
    context = {}
    client = MagicMock()
    scenario_runner._execute_action = AsyncMock(return_value=(Observation(ok=True, action_name="true_step", latency_ms=0.0), context))
    
    results = []
    async for r in scenario_runner.execute_flow(scenario, context, client):
        results.append(r)
    
    assert len(results) == 2
    # Result 0 is the branch decision
    assert results[0][2].branch_taken == "if_true"
    assert results[0][2].branch_result is True
    
    # Result 1 is the action in the branch
    assert results[1][2].action_name == "true_step"
    scenario_runner._execute_action.assert_called_once()

@pytest.mark.asyncio
async def test_branching_if_false(scenario_runner):
    """Test taking the if_false branch."""
    scenario = Scenario(
        id="test-branch",
        flow=[
            BranchAction(
                name="branch1",
                condition="false",
                if_true=[
                    HttpAction(name="true_step", service="api", method="GET", path="/")
                ],
                if_false=[
                    HttpAction(name="false_step", service="api", method="GET", path="/")
                ]
            )
        ],
        stop_when=StopCondition()
    )
    
    context = {}
    client = MagicMock()
    scenario_runner._execute_action = AsyncMock(return_value=(Observation(ok=True, action_name="false_step", latency_ms=0.0), context))
    
    results = []
    async for r in scenario_runner.execute_flow(scenario, context, client):
        results.append(r)
    
    assert len(results) == 2
    # Result 0 is the branch decision
    assert results[0][2].branch_taken == "if_false"
    assert results[0][2].branch_result is False
    
    # Result 1 is the action in the branch
    assert results[1][2].action_name == "false_step"
    scenario_runner._execute_action.assert_called_once()

@pytest.mark.asyncio
async def test_branching_with_context(scenario_runner):
    """Test branching based on context variables."""
    scenario = Scenario(
        id="test-branch-context",
        flow=[
            BranchAction(
                name="branch1",
                condition="{{last_response.status_code}} == 200",
                if_true=[
                    HttpAction(name="success_step", service="api", method="GET", path="/")
                ],
                if_false=[
                    HttpAction(name="fail_step", service="api", method="GET", path="/")
                ]
            )
        ],
        stop_when=StopCondition()
    )
    
    context = {"last_response": {"status_code": 200}}
    client = MagicMock()
    scenario_runner._execute_action = AsyncMock(return_value=(Observation(ok=True, action_name="success_step", latency_ms=0.0), context))
    
    results = []
    async for r in scenario_runner.execute_flow(scenario, context, client):
        results.append(r)
    
    assert len(results) == 2
    assert results[0][2].branch_taken == "if_true"
    assert results[1][2].action_name == "success_step"
