"""Abstract base class for LLM providers."""

from __future__ import annotations

from abc import ABC, abstractmethod


class LLMProvider(ABC):
    """Abstract base class for LLM provider implementations.

    All LLM providers must implement the async complete() method to generate
    text completions from prompts.

    Example:
        >>> class MyProvider(LLMProvider):
        ...     async def complete(self, prompt: str, system: str | None = None) -> str:
        ...         # Implementation here
        ...         return "response"
    """

    @abstractmethod
    async def complete(self, prompt: str, system: str | None = None) -> str:
        """Generate a completion for the given prompt.

        Args:
            prompt: The user prompt to complete.
            system: Optional system prompt to guide the model's behavior.

        Returns:
            The generated text completion.

        Raises:
            Exception: If the completion request fails.
        """
        ...
