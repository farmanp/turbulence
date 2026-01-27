"""Factory for creating action runners based on action type."""

import inspect
from typing import Any

import httpx

from turbulence.actions.base import ActionRunner
from turbulence.config.scenario import Action
from turbulence.config.sut import SUTConfig


class ActionRunnerFactory:
    """Central registry and factory for action runners.
    
    Allows dynamic registration of runners for different protocols and 
    action types, decoupling the engine from specific implementations.
    """

    _runners: dict[str, type[ActionRunner]] = {}

    @classmethod
    def register(cls, action_type: str, runner_class: type[ActionRunner]) -> None:
        """Register a runner class for a specific action type.
        
        Args:
            action_type: The type string (e.g., "http", "wait").
            runner_class: The class to instantiate for this type.
        """
        cls._runners[action_type] = runner_class

    @classmethod
    def create(
        cls,
        action: Action,
        sut_config: SUTConfig | None = None,
        client: httpx.AsyncClient | None = None,
        channel: Any = None,
        **kwargs: Any,
    ) -> ActionRunner:
        """Create a runner instance for the given action and dependencies.
        
        Args:
            action: The action configuration model.
            sut_config: Optional SUT configuration.
            client: Optional HTTP client.
            **kwargs: Additional dependencies to pass to the runner constructor.
            
        Returns:
            An instance of a class implementing the ActionRunner protocol.
            
        Raises:
            ValueError: If no runner is registered for the action type.
        """
        action_type = action.type
        if action_type not in cls._runners:
            raise ValueError(f"No runner registered for action type: {action_type}")

        runner_class = cls._runners[action_type]

        # Use inspection to determine which arguments the runner requires
        sig = inspect.signature(runner_class.__init__)
        params = sig.parameters

        init_args: dict[str, Any] = {}

        # Always prioritize 'action'
        if "action" in params:
            init_args["action"] = action

        # Add shared dependencies if requested by constructor
        if "sut_config" in params:
            init_args["sut_config"] = sut_config
        if "client" in params:
            init_args["client"] = client
        if "channel" in params:
            init_args["channel"] = channel

        # Add any extra explicitly passed kwargs
        for key, value in kwargs.items():
            if key in params:
                init_args[key] = value

        return runner_class(**init_args)  # type: ignore
