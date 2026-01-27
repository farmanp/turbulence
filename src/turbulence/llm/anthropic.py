"""Anthropic/Claude LLM provider implementation."""

from __future__ import annotations

from turbulence.llm.provider import LLMProvider

try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    anthropic = None  # type: ignore[assignment]


class AnthropicProvider(LLMProvider):
    """LLM provider implementation using Anthropic's Claude models.

    This provider uses the Anthropic API to generate text completions
    with Claude models.

    Attributes:
        api_key: The Anthropic API key for authentication.
        model: The Claude model to use for completions.
        max_tokens: Maximum tokens in the completion response.

    Example:
        >>> provider = AnthropicProvider(api_key="sk-ant-...")
        >>> response = await provider.complete(
        ...     prompt="Explain async/await in Python",
        ...     system="You are a helpful programming tutor."
        ... )
    """

    def __init__(
        self,
        api_key: str,
        model: str = "claude-sonnet-4-20250514",
        max_tokens: int = 4096,
    ) -> None:
        """Initialize the Anthropic provider.

        Args:
            api_key: The Anthropic API key for authentication.
            model: The Claude model to use. Defaults to claude-sonnet-4-20250514.
            max_tokens: Maximum tokens in the response. Defaults to 4096.

        Raises:
            ImportError: If the anthropic package is not installed.
        """
        if not ANTHROPIC_AVAILABLE:
            raise ImportError(
                "The anthropic package is required for AnthropicProvider. "
                "Install it with: pip install anthropic"
            )

        self.api_key = api_key
        self.model = model
        self.max_tokens = max_tokens
        self._client = anthropic.AsyncAnthropic(api_key=api_key)

    async def complete(self, prompt: str, system: str | None = None) -> str:
        """Generate a completion using Claude.

        Args:
            prompt: The user prompt to complete.
            system: Optional system prompt to guide Claude's behavior.

        Returns:
            The generated text completion from Claude.

        Raises:
            anthropic.APIError: If the API request fails.
        """
        messages = [{"role": "user", "content": prompt}]

        kwargs: dict[str, object] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages,
        }

        if system is not None:
            kwargs["system"] = system

        response = await self._client.messages.create(**kwargs)  # type: ignore[arg-type]

        # Extract text from the response content blocks
        text_blocks = [
            block.text for block in response.content if hasattr(block, "text")
        ]
        return "".join(text_blocks)
