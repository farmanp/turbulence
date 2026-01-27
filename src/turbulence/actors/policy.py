"""Policy models for LLM-generated behavior rules.

Policies define the concrete decision weights and test data that control
how a simulated user behaves at each decision point in a workflow.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class DecisionWeights(BaseModel):
    """Weighted options for a decision point.

    Represents a probability distribution over possible actions at a single
    decision point in the workflow. Weights should approximately sum to 1.0
    but this is not strictly enforced to allow for flexibility.

    Attributes:
        options: Map of option names to weights (should sum to ~1.0).

    Example:
        >>> weights = DecisionWeights(
        ...     options={"add_to_cart": 0.7, "continue_browsing": 0.2, "abandon": 0.1}
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    options: dict[str, float] = Field(
        ...,
        description="Map of option names to weights (should sum to ~1.0)",
    )

    @field_validator("options")
    @classmethod
    def validate_weights(cls, v: dict[str, float]) -> dict[str, float]:
        """Ensure all weights are non-negative.

        Args:
            v: The options dictionary to validate.

        Returns:
            The validated options dictionary.

        Raises:
            ValueError: If any weight is negative.
        """
        for name, weight in v.items():
            if weight < 0:
                raise ValueError(
                    f"Weight for '{name}' must be non-negative, got {weight}"
                )
        return v


class Policy(BaseModel):
    """Generated behavior policy for a persona.

    A policy contains the concrete rules that govern how a simulated user
    behaves during workflow execution. It includes weighted decision options
    and optional generated test data.

    Attributes:
        persona_id: ID of the persona this policy is for.
        decisions: Map of decision point names to weighted options.
        data: Generated test data arrays keyed by category.

    Example:
        >>> policy = Policy(
        ...     persona_id="impatient_shopper",
        ...     decisions={
        ...         "checkout_delay": DecisionWeights(
        ...             options={"abandon": 0.8, "wait": 0.2}
        ...         )
        ...     },
        ...     data={"product_ids": ["SKU001", "SKU002"]}
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    persona_id: str = Field(..., description="ID of the persona this policy is for")
    decisions: dict[str, DecisionWeights] = Field(
        default_factory=dict,
        description="Map of decision point names to weighted options",
    )
    data: dict[str, list[Any]] | None = Field(
        default=None,
        description="Generated test data arrays keyed by category",
    )


class PolicyConfig(BaseModel):
    """Configuration file containing multiple policies.

    This model represents a YAML configuration file that contains generated
    policies for one or more personas.

    Attributes:
        policies: List of generated policies.

    Example:
        >>> config = PolicyConfig(
        ...     policies=[
        ...         Policy(persona_id="power_user", decisions={}),
        ...         Policy(persona_id="novice", decisions={}),
        ...     ]
        ... )
    """

    model_config = ConfigDict(extra="forbid")

    policies: list[Policy] = Field(
        ...,
        description="List of generated policies",
    )
