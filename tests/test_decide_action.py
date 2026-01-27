"""Tests for the decide action runner."""

import pytest

from turbulence.actions.decide import DecideActionRunner
from turbulence.actors.policy import DecisionWeights, Policy
from turbulence.config.scenario import DecideAction


class TestDecideActionRunner:
    """Tests for DecideActionRunner."""

    def test_weighted_choice_selects_from_options(self) -> None:
        """Test that weighted choice selects valid options."""
        action = DecideAction(name="test", decision="browse")
        policy = Policy(
            persona_id="tester",
            decisions={
                "browse": DecisionWeights(
                    options={"view": 0.5, "skip": 0.3, "add": 0.2}
                )
            },
        )
        runner = DecideActionRunner(action=action, policy=policy, seed=42)

        # Run many selections to verify distribution
        results: dict[str, int] = {"view": 0, "skip": 0, "add": 0}
        for _ in range(1000):
            runner.rng.seed(runner.rng.randint(0, 1000000))
            choice = runner._weighted_choice(policy.decisions["browse"].options)
            results[choice] += 1

        # All options should be selected at least once
        assert results["view"] > 0
        assert results["skip"] > 0
        assert results["add"] > 0

    def test_weighted_choice_deterministic_with_seed(self) -> None:
        """Test that the same seed produces the same choice."""
        action = DecideAction(name="test", decision="browse")
        policy = Policy(
            persona_id="tester",
            decisions={
                "browse": DecisionWeights(
                    options={"a": 0.5, "b": 0.3, "c": 0.2}
                )
            },
        )

        # Same seed should produce same sequence
        runner1 = DecideActionRunner(action=action, policy=policy, seed=12345)
        runner2 = DecideActionRunner(action=action, policy=policy, seed=12345)

        choices1 = [
            runner1._weighted_choice(policy.decisions["browse"].options)
            for _ in range(10)
        ]
        choices2 = [
            runner2._weighted_choice(policy.decisions["browse"].options)
            for _ in range(10)
        ]

        assert choices1 == choices2

    def test_weighted_choice_handles_zero_weights(self) -> None:
        """Test that zero-weight options are not selected."""
        action = DecideAction(name="test", decision="browse")
        policy = Policy(
            persona_id="tester",
            decisions={
                "browse": DecisionWeights(
                    options={"always": 1.0, "never": 0.0}
                )
            },
        )
        runner = DecideActionRunner(action=action, policy=policy, seed=42)

        # Run many selections - should never select "never"
        for _ in range(100):
            choice = runner._weighted_choice(policy.decisions["browse"].options)
            assert choice == "always"

    @pytest.mark.asyncio
    async def test_execute_returns_observation_with_choice(self) -> None:
        """Test that execute returns an observation with the decision result."""
        action = DecideAction(
            name="what_next",
            decision="product_browse",
            output_var="next_action",
        )
        policy = Policy(
            persona_id="shopper",
            decisions={
                "product_browse": DecisionWeights(
                    options={"view_details": 0.7, "add_to_cart": 0.3}
                )
            },
        )
        runner = DecideActionRunner(action=action, policy=policy, seed=42)

        observation, updated_context = await runner.execute({})

        assert observation.ok is True
        assert observation.protocol == "decide"
        assert observation.action_name == "what_next"
        assert observation.body["decision"] == "product_browse"
        assert observation.body["result"] in ["view_details", "add_to_cart"]
        assert "next_action" in updated_context
        assert updated_context["next_action"] == observation.body["result"]

    @pytest.mark.asyncio
    async def test_execute_preserves_existing_context(self) -> None:
        """Test that execute preserves existing context values."""
        action = DecideAction(name="test", decision="browse", output_var="result")
        policy = Policy(
            persona_id="tester",
            decisions={
                "browse": DecisionWeights(options={"a": 1.0})
            },
        )
        runner = DecideActionRunner(action=action, policy=policy, seed=42)

        existing_context = {"product_id": "123", "user_id": "456"}
        _, updated_context = await runner.execute(existing_context)

        assert updated_context["product_id"] == "123"
        assert updated_context["user_id"] == "456"
        assert updated_context["result"] == "a"

    @pytest.mark.asyncio
    async def test_execute_without_policy_returns_error(self) -> None:
        """Test that execute without a policy returns an error observation."""
        action = DecideAction(name="test", decision="browse")
        runner = DecideActionRunner(action=action, policy=None, seed=42)

        observation, _ = await runner.execute({})

        assert observation.ok is False
        assert "No policy provided" in observation.errors[0]

    @pytest.mark.asyncio
    async def test_execute_with_missing_decision_returns_error(self) -> None:
        """Test that execute with a missing decision returns an error observation."""
        action = DecideAction(name="test", decision="nonexistent")
        policy = Policy(
            persona_id="tester",
            decisions={
                "browse": DecisionWeights(options={"a": 1.0})
            },
        )
        runner = DecideActionRunner(action=action, policy=policy, seed=42)

        observation, _ = await runner.execute({})

        assert observation.ok is False
        assert "not found in policy" in observation.errors[0]


class TestDecideAction:
    """Tests for DecideAction model."""

    def test_decide_action_default_output_var(self) -> None:
        """Test that DecideAction has correct default output_var."""
        action = DecideAction(name="test", decision="browse")

        assert action.output_var == "decision_result"
        assert action.type == "decide"

    def test_decide_action_custom_output_var(self) -> None:
        """Test that DecideAction accepts custom output_var."""
        action = DecideAction(
            name="test",
            decision="browse",
            output_var="my_decision",
        )

        assert action.output_var == "my_decision"

    def test_decide_action_with_policy_ref(self) -> None:
        """Test that DecideAction accepts policy_ref."""
        action = DecideAction(
            name="test",
            decision="browse",
            policy_ref="power_user",
        )

        assert action.policy_ref == "power_user"

    def test_decide_action_with_condition(self) -> None:
        """Test that DecideAction accepts condition."""
        action = DecideAction(
            name="test",
            decision="browse",
            condition="context.get('has_items') == True",
        )

        assert action.condition == "context.get('has_items') == True"


class TestPolicy:
    """Tests for Policy models."""

    def test_decision_weights_validates_non_negative(self) -> None:
        """Test that DecisionWeights rejects negative weights."""
        with pytest.raises(ValueError, match="non-negative"):
            DecisionWeights(options={"a": 0.5, "b": -0.1})

    def test_decision_weights_allows_zero(self) -> None:
        """Test that DecisionWeights allows zero weights."""
        weights = DecisionWeights(options={"a": 0.5, "b": 0.0})

        assert weights.options["b"] == 0.0

    def test_policy_with_data(self) -> None:
        """Test that Policy accepts test data."""
        policy = Policy(
            persona_id="tester",
            decisions={},
            data={
                "search_queries": ["laptop", "phone"],
                "product_ids": ["SKU001", "SKU002"],
            },
        )

        assert policy.data is not None
        assert "search_queries" in policy.data
        assert len(policy.data["search_queries"]) == 2
