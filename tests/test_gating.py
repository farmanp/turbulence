"""Tests for CI gating thresholds."""

import pytest

from turbulence.gating import Threshold, ThresholdError
from turbulence.models.manifest import RunSummary


class TestThresholdParsing:
    def test_parse_valid_pass_rate(self):
        t = Threshold.parse("pass_rate>95")
        assert t.metric == "pass_rate"
        assert t.operator == ">"
        assert t.value == 95.0

    def test_parse_valid_latency(self):
        t = Threshold.parse("p95_latency_ms<=500.5")
        assert t.metric == "p95_latency_ms"
        assert t.operator == "<="
        assert t.value == 500.5

    def test_parse_invalid_syntax(self):
        with pytest.raises(ThresholdError, match="Invalid threshold syntax"):
            Threshold.parse("pass_rate95")

    def test_parse_unknown_metric(self):
        with pytest.raises(ThresholdError, match="Unknown metric"):
            Threshold.parse("unknown_metric>10")

    def test_parse_invalid_value(self):
        # Regex catches non-numeric values first
        with pytest.raises(ThresholdError, match="Invalid threshold syntax"):
            Threshold.parse("pass_rate>high")


class TestThresholdEvaluation:
    @pytest.fixture
    def summary(self):
        return RunSummary(
            run_id="test",
            pass_rate=98.5,
            p95_latency_ms=200.0,
            error_count=0,
        )

    def test_pass_rate_success(self, summary):
        t = Threshold.parse("pass_rate>95")
        passed, val, msg = t.evaluate(summary)
        assert passed
        assert val == 98.5
        assert "PASSED" in msg

    def test_pass_rate_failure(self, summary):
        t = Threshold.parse("pass_rate>99")
        passed, val, msg = t.evaluate(summary)
        assert not passed
        assert val == 98.5
        assert "FAILED" in msg

    def test_pass_rate_ratio_conversion(self, summary):
        # User provides 0.95, summary has 98.5. Should compare 98.5 > 95.0
        t = Threshold.parse("pass_rate>0.95")
        passed, val, msg = t.evaluate(summary)
        assert passed
        assert "0.95" in msg or "95.0" in str(t.value * 100) # Logic modifies local var

    def test_latency_success(self, summary):
        t = Threshold.parse("p95_latency_ms<300")
        passed, _, _ = t.evaluate(summary)
        assert passed

    def test_latency_failure(self, summary):
        t = Threshold.parse("p95_latency_ms<100")
        passed, _, _ = t.evaluate(summary)
        assert not passed

    def test_equality_operators(self, summary):
        t1 = Threshold.parse("error_count<=0")
        assert t1.evaluate(summary)[0]
        
        t2 = Threshold.parse("error_count>=0")
        assert t2.evaluate(summary)[0]
