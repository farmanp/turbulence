"""Persona models for user behavior simulation.

Personas define the characteristics and behavioral tendencies of simulated users.
They are used as input to LLM policy generation to create realistic test scenarios.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Persona(BaseModel):
    """A user persona for behavior simulation.

    Personas describe user archetypes with natural language descriptions that
    guide how the simulated user should behave during workflow execution.

    Attributes:
        id: Unique identifier for this persona.
        description: Natural language description of the persona's behavior.
        hints: Optional structured hints for policy generation.

    Example:
        >>> persona = Persona(
        ...     id="impatient_shopper",
        ...     description="A busy user who abandons cart if checkout takes too long",
        ...     hints={"timeout_tolerance": "low", "retry_behavior": "none"}
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    id: str = Field(..., description="Unique identifier for this persona")
    description: str = Field(
        ..., description="Natural language description of the persona's behavior"
    )
    hints: dict[str, Any] | None = Field(
        default=None,
        description="Optional structured hints for policy generation",
    )


class PersonaConfig(BaseModel):
    """Configuration file containing multiple personas.

    This model represents a YAML configuration file that defines a collection
    of personas for use in behavior simulation scenarios.

    Attributes:
        personas: List of personas to generate policies for.

    Example:
        >>> config = PersonaConfig(
        ...     personas=[
        ...         Persona(id="power_user", description="Experienced user"),
        ...         Persona(id="novice", description="First-time user"),
        ...     ]
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    personas: list[Persona] = Field(
        ...,
        description="List of personas to generate policies for",
        min_length=1,
    )
