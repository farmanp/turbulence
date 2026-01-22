"""Unit tests for condition evaluation."""

import pytest

from turbulence.engine.conditions import (
    ConditionEvaluationError,
    ConditionEvaluator,
)


class TestConditionEvaluator:
    """Test suite for ConditionEvaluator."""

    @pytest.fixture
    def evaluator(self) -> ConditionEvaluator:
        """Create a ConditionEvaluator instance."""
        return ConditionEvaluator()

    # Basic template rendering tests
    def test_simple_equality_true(self, evaluator: ConditionEvaluator) -> None:
        """Test simple equality that evaluates to true."""
        context = {"status": "declined"}
        result, rendered = evaluator.evaluate('"{{status}}" == "declined"', context)
        assert result is True
        assert rendered == '"declined" == "declined"'

    def test_simple_equality_false(self, evaluator: ConditionEvaluator) -> None:
        """Test simple equality that evaluates to false."""
        context = {"status": "approved"}
        result, rendered = evaluator.evaluate('"{{status}}" == "declined"', context)
        assert result is False
        assert rendered == '"approved" == "declined"'

    def test_numeric_comparison_greater(self, evaluator: ConditionEvaluator) -> None:
        """Test numeric comparison with greater than."""
        context = {"amount": 150}
        result, rendered = evaluator.evaluate("{{amount}} > 100", context)
        assert result is True
        assert rendered == "150 > 100"

    def test_numeric_comparison_less_or_equal(self, evaluator: ConditionEvaluator) -> None:
        """Test numeric comparison with less than or equal."""
        context = {"amount": 50}
        result, rendered = evaluator.evaluate("{{amount}} <= 100", context)
        assert result is True
        assert rendered == "50 <= 100"

    def test_boolean_literal_true(self, evaluator: ConditionEvaluator) -> None:
        """Test boolean literal true from context."""
        context = {"is_premium": True}
        result, rendered = evaluator.evaluate("{{is_premium}}", context)
        assert result is True
        assert rendered == "True"

    def test_boolean_literal_false(self, evaluator: ConditionEvaluator) -> None:
        """Test boolean literal false from context."""
        context = {"is_premium": False}
        result, rendered = evaluator.evaluate("{{is_premium}}", context)
        assert result is False
        assert rendered == "False"

    def test_string_literal_true(self, evaluator: ConditionEvaluator) -> None:
        """Test string literal 'true' evaluates to True."""
        context: dict = {}
        result, rendered = evaluator.evaluate("true", context)
        assert result is True

    def test_string_literal_false(self, evaluator: ConditionEvaluator) -> None:
        """Test string literal 'false' evaluates to False."""
        context: dict = {}
        result, rendered = evaluator.evaluate("false", context)
        assert result is False

    def test_empty_condition(self, evaluator: ConditionEvaluator) -> None:
        """Test empty condition returns True."""
        context = {"status": "active"}
        result, rendered = evaluator.evaluate("", context)
        assert result is True
        assert rendered == ""

    # Boolean operators
    def test_and_operator_true(self, evaluator: ConditionEvaluator) -> None:
        """Test AND operator with both conditions true."""
        context = {"a": 10, "b": 20}
        result, rendered = evaluator.evaluate("{{a}} > 5 and {{b}} > 15", context)
        assert result is True

    def test_and_operator_false(self, evaluator: ConditionEvaluator) -> None:
        """Test AND operator with one condition false."""
        context = {"a": 3, "b": 20}
        result, rendered = evaluator.evaluate("{{a}} > 5 and {{b}} > 15", context)
        assert result is False

    def test_or_operator_true(self, evaluator: ConditionEvaluator) -> None:
        """Test OR operator with one condition true."""
        context = {"a": 3, "b": 20}
        result, rendered = evaluator.evaluate("{{a}} > 5 or {{b}} > 15", context)
        assert result is True

    def test_or_operator_false(self, evaluator: ConditionEvaluator) -> None:
        """Test OR operator with both conditions false."""
        context = {"a": 3, "b": 10}
        result, rendered = evaluator.evaluate("{{a}} > 5 or {{b}} > 15", context)
        assert result is False

    def test_not_operator(self, evaluator: ConditionEvaluator) -> None:
        """Test NOT operator."""
        context = {"is_active": False}
        result, rendered = evaluator.evaluate("not {{is_active}}", context)
        assert result is True

    # Complex expressions
    def test_nested_context_access(self, evaluator: ConditionEvaluator) -> None:
        """Test accessing nested context values."""
        context = {"user": {"role": "admin"}}
        result, rendered = evaluator.evaluate('"{{user.role}}" == "admin"', context)
        assert result is True

    def test_in_operator(self, evaluator: ConditionEvaluator) -> None:
        """Test 'in' operator for membership."""
        context = {"status": "pending"}
        # Note: we need to use body/headers/context for list membership
        # Since we're using SafeExpressionEvaluator, we can access context
        result, rendered = evaluator.evaluate(
            'context.get("status") in ["pending", "processing"]',
            context,
        )
        assert result is True

    def test_not_in_operator(self, evaluator: ConditionEvaluator) -> None:
        """Test 'not in' operator for non-membership."""
        context = {"status": "completed"}
        result, rendered = evaluator.evaluate(
            'context.get("status") not in ["pending", "processing"]',
            context,
        )
        assert result is True

    # last_response access
    def test_body_access(self, evaluator: ConditionEvaluator) -> None:
        """Test accessing body from last_response."""
        context = {
            "last_response": {
                "body": {"status": "success", "code": 200},
                "headers": {},
            }
        }
        result, rendered = evaluator.evaluate(
            'body.get("status") == "success"',
            context,
        )
        assert result is True

    def test_headers_access(self, evaluator: ConditionEvaluator) -> None:
        """Test accessing headers from last_response."""
        context = {
            "last_response": {
                "body": None,
                "headers": {"content-type": "application/json"},
            }
        }
        result, rendered = evaluator.evaluate(
            'headers.get("content-type") == "application/json"',
            context,
        )
        assert result is True

    # Error handling
    def test_missing_variable_raises_error(self, evaluator: ConditionEvaluator) -> None:
        """Test that missing variable raises ConditionEvaluationError."""
        context = {"foo": "bar"}
        with pytest.raises(ConditionEvaluationError) as exc_info:
            evaluator.evaluate("{{missing_var}} == 'test'", context)
        assert "Template rendering failed" in str(exc_info.value)
        assert exc_info.value.condition == "{{missing_var}} == 'test'"

    def test_invalid_expression_raises_error(self, evaluator: ConditionEvaluator) -> None:
        """Test that invalid expression syntax raises error."""
        context = {"value": 10}
        with pytest.raises(ConditionEvaluationError) as exc_info:
            evaluator.evaluate("{{value}} ** __import__('os')", context)
        assert exc_info.value.condition == "{{value}} ** __import__('os')"

    # evaluate_safe tests
    def test_evaluate_safe_returns_default_on_error(
        self, evaluator: ConditionEvaluator
    ) -> None:
        """Test evaluate_safe returns default on error."""
        context = {"foo": "bar"}
        result, rendered = evaluator.evaluate_safe(
            "{{missing_var}} == 'test'",
            context,
            default=True,
        )
        assert result is True

    def test_evaluate_safe_success(self, evaluator: ConditionEvaluator) -> None:
        """Test evaluate_safe works for valid conditions."""
        context = {"status": "active"}
        result, rendered = evaluator.evaluate_safe(
            '"{{status}}" == "active"',
            context,
            default=False,
        )
        assert result is True
        assert rendered == '"active" == "active"'


class TestConditionEvaluatorEdgeCases:
    """Edge case tests for ConditionEvaluator."""

    @pytest.fixture
    def evaluator(self) -> ConditionEvaluator:
        return ConditionEvaluator()

    def test_numeric_zero_is_falsy(self, evaluator: ConditionEvaluator) -> None:
        """Test that numeric zero is treated as falsy in boolean context."""
        context = {"count": 0}
        # "0" as string is not in ("true", "1"), so it goes to expression eval
        result, rendered = evaluator.evaluate("{{count}}", context)
        assert result is False
        assert rendered == "0"

    def test_none_value_handling(self, evaluator: ConditionEvaluator) -> None:
        """Test handling of None values."""
        context = {"value": None}
        result, rendered = evaluator.evaluate("{{value}} is None", context)
        assert result is True

    def test_string_comparison_with_quotes(self, evaluator: ConditionEvaluator) -> None:
        """Test string comparison requires proper quoting."""
        context = {"name": "Alice"}
        # Without quotes around template, the rendered expression would be:
        # Alice == "Alice" which fails because Alice is not a valid identifier
        # We need: "Alice" == "Alice"
        result, rendered = evaluator.evaluate('"{{name}}" == "Alice"', context)
        assert result is True

    def test_integer_preservation(self, evaluator: ConditionEvaluator) -> None:
        """Test that integers are preserved through template rendering."""
        context = {"count": 42}
        result, rendered = evaluator.evaluate("{{count}} == 42", context)
        assert result is True
        assert rendered == "42 == 42"

    def test_float_comparison(self, evaluator: ConditionEvaluator) -> None:
        """Test floating point comparisons."""
        context = {"price": 19.99}
        result, rendered = evaluator.evaluate("{{price}} < 20.0", context)
        assert result is True

    def test_complex_boolean_expression(self, evaluator: ConditionEvaluator) -> None:
        """Test complex boolean expression with multiple operators."""
        context = {
            "status": "active",
            "balance": 100,
            "is_verified": True,
        }
        result, rendered = evaluator.evaluate(
            '("{{status}}" == "active" or {{balance}} > 50) and {{is_verified}}',
            context,
        )
        assert result is True
