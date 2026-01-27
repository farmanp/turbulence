"""Scenario execution engine.

Consolidates step-by-step scenario execution logic used by both
the run command and replay engine.
"""

import asyncio
import logging
from collections.abc import AsyncIterator
from typing import Any

from turbulence.actions import ActionRunnerFactory
from turbulence.actors.policy import Policy
from turbulence.config.scenario import (
    Action,
    AssertAction,
    BranchAction,
    DecideAction,
    HttpAction,
    Scenario,
    WaitAction,
)
from turbulence.config.sut import SUTConfig
from turbulence.engine.client_pool import ClientPool
from turbulence.engine.conditions import ConditionEvaluator
from turbulence.engine.template import TemplateEngine
from turbulence.models.observation import Observation
from turbulence.pressure.engine import TurbulenceEngine

logger = logging.getLogger(__name__)


class ScenarioRunner:
    """Executes scenario flows with context management and action execution.

    Handles template rendering, action execution, and context updates for
    scenario steps. Used by both run command and replay engine to ensure
    consistent execution behavior.
    """

    def __init__(
        self,
        template_engine: TemplateEngine,
        sut_config: SUTConfig,
        client_pool: ClientPool,
        turbulence_engine: TurbulenceEngine | None = None,
        policies: dict[str, Policy] | None = None,
        seed: int | None = None,
    ) -> None:
        """Initialize the scenario runner.

        Args:
            template_engine: Engine for rendering template variables
            sut_config: System under test configuration
            client_pool: Pool for managing connection lifecycles
            turbulence_engine: Optional engine for fault injection
            policies: Optional dict mapping persona_id to Policy for decide actions
            seed: Optional seed for reproducible decide action randomness
        """
        self.template_engine = template_engine
        self.sut_config = sut_config
        self.client_pool = client_pool
        self.turbulence_engine = turbulence_engine
        self.policies = policies or {}
        self.seed = seed
        self.condition_evaluator = ConditionEvaluator(template_engine)

    async def execute_flow(
        self,
        scenario: Scenario,
        context: dict[str, Any],
    ) -> AsyncIterator[tuple[int, Action, Observation, dict[str, Any]]]:
        """Execute scenario flow steps, yielding results for each step.

        Args:
            scenario: Scenario definition with flow steps
            context: Execution context dictionary
            client: HTTP client for requests

        Yields:
            Tuple of (step_index, action, observation, updated_context)
            for each executed step
        """
        # Extract timing config from context if present (injected by VariationEngine)
        variation_data = context.get("entry", {}).get("seed_data", {}).get("variation", {})
        step_delay_ms = variation_data.get("_step_delay_ms", 0)
        jitter_ms = variation_data.get("_timing_jitter_ms", 0)

        # Handle max_steps to prevent infinite loops (mostly relevant for future looping features,
        # but good for branching too)
        max_steps = getattr(scenario.stop_when, "max_steps", 100)
        steps_executed = 0

        # We use a helper to implement recursive execution for BranchAction
        async for result in self._execute_actions_recursive(
            actions=scenario.flow,
            context=context,
            start_index=0,
            step_delay_ms=step_delay_ms,
            jitter_ms=jitter_ms,
        ):
            yield result
            steps_executed += 1

            # Stop if global max reached
            if steps_executed >= max_steps:
                logger.warning(f"Scenario {scenario.id} reached max_steps ({max_steps})")
                break

            # Stop if last action failed and scenario is configured to halt
            _, _, observation, _ = result
            if not observation.ok and scenario.stop_when.any_action_fails:
                break

    async def _execute_actions_recursive(
        self,
        actions: list[Action],
        context: dict[str, Any],
        start_index: int,
        step_delay_ms: int,
        jitter_ms: int,
    ) -> AsyncIterator[tuple[int, Action, Observation, dict[str, Any]]]:
        """Recursively execute a list of actions (to support nested branches)."""
        idx = start_index
        for action in actions:
            # Check condition if present (for simple conditional skip)
            if hasattr(action, "condition") and action.condition and not isinstance(action, BranchAction):
                result, rendered = self.condition_evaluator.evaluate_safe(
                    action.condition, context, default=True
                )
                if not result:
                    # Yield a "Skipped" observation
                    skip_obs = Observation(
                        ok=True,
                        status_code=None,
                        latency_ms=0.0,
                        headers={},
                        body=None,
                        action_name=action.name,
                        service=None,
                        branch_condition=action.condition,
                        branch_result=False,
                        condition_skipped=True,
                    )
                    logger.debug(
                        f"Skipped action '{action.name}' due to false condition: "
                        f"{action.condition} → {rendered}"
                    )
                    yield idx, action, skip_obs, context
                    idx += 1
                    continue

            # Apply delays/jitter (only between top-level actions or first in branch?)
            # For simplicity, we apply before every non-skipped action
            total_delay_ms = 0
            if idx > 0:
                total_delay_ms += step_delay_ms
            total_delay_ms += jitter_ms

            if total_delay_ms > 0:
                await asyncio.sleep(total_delay_ms / 1000.0)

            if isinstance(action, BranchAction):
                # Execute BranchAction logic
                obs, context, branch_results = await self._execute_branch(action, context, step_delay_ms, jitter_ms)

                # Yield the branch decision observation
                yield idx, action, obs, context
                idx += 1

                # Then yield each individual step observation from the branch
                for b_idx, b_action, b_obs, b_context in branch_results:
                    # Update the global context with the nested execution's result
                    context = b_context
                    yield b_idx, b_action, b_obs, context
            else:
                # Normal action execution
                observation, context = await self._execute_action(
                    action=action,
                    context=context,
                )

                # Update last_response context for HTTP and Wait actions
                if isinstance(action, (HttpAction, WaitAction)):
                    self._update_last_response(context, observation)

                yield idx, action, observation, context
                idx += 1

    async def _execute_branch(
        self,
        action: BranchAction,
        context: dict[str, Any],
        step_delay_ms: int,
        jitter_ms: int,
    ) -> tuple[Observation, dict[str, Any], list[tuple[int, Action, Observation, dict[str, Any]]]]:
        """Evaluate a branch condition and prepare execution results."""
        # Evaluate the branch condition
        decision, rendered = self.condition_evaluator.evaluate_safe(
            action.condition, context, default=False
        )
        branch_name = "if_true" if decision else "if_false"
        branch_actions = action.if_true if decision else action.if_false

        logger.debug(
            f"Branch '{action.name}': {action.condition} → {rendered} = {decision}, "
            f"taking {branch_name} ({len(branch_actions)} actions)"
        )

        obs = Observation(
            ok=True,
            status_code=None,
            latency_ms=0.0,
            headers={},
            body=None,
            action_name=action.name,
            service=None,
            branch_condition=action.condition,
            branch_result=decision,
            branch_taken=branch_name,
        )

        results: list[tuple[int, Action, Observation, dict[str, Any]]] = []
        # Execute nested actions
        async for r in self._execute_actions_recursive(
            actions=branch_actions,
            context=context,
            start_index=0,
            step_delay_ms=step_delay_ms,
            jitter_ms=jitter_ms,
        ):
            results.append(r)
            context = r[3]  # Update context for next step in branch

        return obs, context, results

    async def _execute_action(
        self,
        action: Action,
        context: dict[str, Any],
    ) -> tuple[Observation, dict[str, Any]]:
        """Execute a single action with template rendering.

        Args:
            action: Action to execute
            context: Current execution context
            client: HTTP client for requests

        Returns:
            Tuple of (observation, updated_context)
        """
        # Render templates in action
        rendered_action = self._render_action(action, context)

        # Resolve appropriate client from pool
        client = None
        channel = None

        if hasattr(rendered_action, "service"):
            service_name = rendered_action.service
            service = self.sut_config.get_service(service_name)

            if service.protocol == "http":
                client = await self.client_pool.get_http_client(service_name)
            elif service.protocol == "grpc":
                channel = await self.client_pool.get_grpc_channel(service_name)

        # Execute based on action type via Factory
        try:
            # For decide actions, resolve policy and pass seed
            extra_kwargs: dict[str, Any] = {}
            if isinstance(rendered_action, DecideAction):
                # Look up policy by policy_ref or use first available
                policy_ref = rendered_action.policy_ref
                if policy_ref and policy_ref in self.policies:
                    extra_kwargs["policy"] = self.policies[policy_ref]
                elif self.policies:
                    # Use first policy if no specific ref
                    extra_kwargs["policy"] = next(iter(self.policies.values()))
                extra_kwargs["seed"] = self.seed

            runner = ActionRunnerFactory.create(
                action=rendered_action,
                sut_config=self.sut_config,
                client=client,
                channel=channel,
                **extra_kwargs,
            )
        except ValueError as e:
            raise ValueError(f"Unknown action type: {type(action)}. {e}")

        # Apply turbulence if configured (currently only for HTTP)
        if isinstance(rendered_action, HttpAction) and self.turbulence_engine is not None:
            policy = self.turbulence_engine.resolve_policy(
                service=rendered_action.service,
                action=rendered_action.name,
            )
            if policy is not None:
                return await self.turbulence_engine.apply(
                    policy=policy,
                    action_name=rendered_action.name,
                    service_name=rendered_action.service,
                    instance_id=str(context.get("instance_id", "")),
                    context=context,
                    execute=lambda: runner.execute(context),
                )

        return await runner.execute(context)

    def _render_action(
        self,
        action: Action,
        context: dict[str, Any],
    ) -> Action:
        """Render template variables in an action.

        Args:
            action: Action with potential template variables
            context: Context for template rendering

        Returns:
            Action with templates rendered
        """
        action_dict = action.model_dump()
        rendered_dict = self.template_engine.render_dict(action_dict, context)

        if isinstance(action, HttpAction):
            return HttpAction(**rendered_dict)
        if isinstance(action, WaitAction):
            return WaitAction(**rendered_dict)
        if isinstance(action, AssertAction):
            return AssertAction(**rendered_dict)
        if isinstance(action, BranchAction):
            return BranchAction(**rendered_dict)
        if isinstance(action, DecideAction):
            return DecideAction(**rendered_dict)

        raise ValueError(f"Unknown action type for rendering: {type(action)}")

    def _update_last_response(
        self,
        context: dict[str, Any],
        observation: Observation,
    ) -> None:
        """Update context with last response data.

        Args:
            context: Context to update
            observation: Observation from action execution
        """
        context["last_response"] = {
            "status_code": getattr(observation, "status_code", None),
            "headers": getattr(observation, "headers", {}),
            "body": getattr(observation, "body", None),
        }
