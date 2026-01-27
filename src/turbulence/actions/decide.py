"""Decide action runner for policy-based weighted random selection."""

import random
import time
from typing import Any

from turbulence.actions.base import BaseActionRunner
from turbulence.actors.policy import Policy
from turbulence.config.scenario import DecideAction
from turbulence.models.observation import Observation


class DecideActionRunner(BaseActionRunner):
    """Runner for decide actions that perform weighted random selection.

    Uses a seeded random number generator for reproducibility across runs.
    The decision is based on weights from the provided policy.
    """

    def __init__(
        self,
        action: DecideAction,
        policy: Policy | None = None,
        seed: int | None = None,
    ) -> None:
        """Initialize the decide action runner.

        Args:
            action: The decide action configuration.
            policy: Optional policy containing decision weights.
            seed: Optional seed for reproducible random selection.
        """
        self.action = action
        self.policy = policy
        self.rng = random.Random(seed)  # noqa: S311

    def _weighted_choice(self, options: dict[str, float]) -> str:
        """Select an option based on weights.

        Args:
            options: Map of option names to weights.

        Returns:
            The selected option name.
        """
        if not options:
            raise ValueError("No options provided for weighted choice")

        # Normalize weights to sum to 1.0
        total = sum(options.values())
        if total <= 0:
            # Fall back to uniform distribution
            return self.rng.choice(list(options.keys()))

        normalized = {k: v / total for k, v in options.items()}

        # Weighted random selection
        r = self.rng.random()
        cumulative = 0.0
        for option, weight in normalized.items():
            cumulative += weight
            if r <= cumulative:
                return option

        # Fallback to last option (shouldn't happen with proper normalization)
        return list(options.keys())[-1]

    async def execute(
        self,
        context: dict[str, Any],
    ) -> tuple[Observation, dict[str, Any]]:
        """Execute the decide action.

        Args:
            context: Current execution context.

        Returns:
            Tuple of (Observation, updated_context) with decision result.
        """
        start_time = time.perf_counter()

        decision_name = self.action.decision
        output_var = self.action.output_var

        # Get decision weights from policy
        if self.policy and decision_name in self.policy.decisions:
            weights = self.policy.decisions[decision_name]
            options = weights.options
        else:
            # No policy or decision not found - return error observation
            elapsed = (time.perf_counter() - start_time) * 1000
            return (
                Observation(
                    ok=False,
                    protocol="decide",
                    latency_ms=elapsed,
                    action_name=self.action.name,
                    errors=[
                        f"Decision '{decision_name}' not found in policy"
                        if self.policy
                        else "No policy provided for decide action"
                    ],
                    body={"decision": decision_name, "result": None},
                ),
                context,
            )

        # Make the weighted random selection
        choice = self._weighted_choice(options)

        # Update context with the decision result
        updated_context = {**context, output_var: choice}

        elapsed = (time.perf_counter() - start_time) * 1000

        return (
            Observation(
                ok=True,
                protocol="decide",
                latency_ms=elapsed,
                action_name=self.action.name,
                body={
                    "decision": decision_name,
                    "result": choice,
                    "options": options,
                },
            ),
            updated_context,
        )
