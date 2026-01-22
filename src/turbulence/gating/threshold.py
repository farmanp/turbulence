"""Threshold parsing and evaluation for CI gating."""

import re
from dataclasses import dataclass
from typing import Literal

from turbulence.models.manifest import RunSummary

# Operator type alias
Operator = Literal["<", ">", "<=", ">="]

# Regex to parse threshold string: metric operator value
# e.g., "pass_rate<0.99", "p95_latency_ms>=1000"
THRESHOLD_PATTERN = re.compile(
    r"^(?P<metric>[a-zA-Z0-9_]+)\s*(?P<operator><=|>=|<|>)\s*(?P<value>[0-9.]+)\s*$"
)

# Supported metrics mapping (name -> attribute in RunSummary)
# Note: pass_rate in summary is 0-100, but users might provide 0.0-1.0.
# We will check value range. If value <= 1.0 for pass_rate, we assume ratio and multiply by 100.
SUPPORTED_METRICS = {
    "pass_rate": "pass_rate",
    "error_count": "error_count",
    "p50_latency_ms": "p50_latency_ms",
    "p95_latency_ms": "p95_latency_ms",
    "p99_latency_ms": "p99_latency_ms",
    "fail_count": "fail_count",
}


class ThresholdError(Exception):
    """Raised when threshold string is invalid."""
    pass


@dataclass
class Threshold:
    """A single gating threshold."""

    metric: str
    operator: Operator
    value: float
    raw_string: str

    @classmethod
    def parse(cls, threshold_str: str) -> "Threshold":
        """Parse a threshold string into a Threshold object.

        Args:
            threshold_str: String like "pass_rate>95"

        Returns:
            Threshold object.

        Raises:
            ThresholdError: If syntax is invalid or metric unknown.
        """
        match = THRESHOLD_PATTERN.match(threshold_str.strip())
        if not match:
            raise ThresholdError(
                f"Invalid threshold syntax: '{threshold_str}'. "
                "Expected format: metric<op>value (e.g., pass_rate>=99.5)"
            )

        metric = match.group("metric")
        operator = match.group("operator")
        value_str = match.group("value")

        if metric not in SUPPORTED_METRICS:
            valid = ", ".join(sorted(SUPPORTED_METRICS.keys()))
            raise ThresholdError(
                f"Unknown metric '{metric}'. Available metrics: {valid}"
            )

        try:
            value = float(value_str)
        except ValueError:
            raise ThresholdError(f"Invalid numeric value: '{value_str}'")

        return cls(
            metric=metric,
            operator=operator, # type: ignore
            value=value,
            raw_string=threshold_str
        )

    def evaluate(self, summary: RunSummary) -> tuple[bool, float, str]:
        """Evaluate the threshold against a run summary.

        Args:
            summary: The run summary to check.

        Returns:
            Tuple of (passed: bool, actual_value: float, message: str)
        """
        attr_name = SUPPORTED_METRICS[self.metric]
        actual = getattr(summary, attr_name)
        
        # Special handling for pass_rate if threshold is <= 1.0 (assume ratio)
        threshold_val = self.value
        if self.metric == "pass_rate" and threshold_val <= 1.0 and actual > 1.0:
            # User likely meant ratio (e.g. 0.99) but actual is percentage (e.g. 99.0)
            threshold_val *= 100.0

        passed = False
        if self.operator == "<":
            passed = actual < threshold_val
        elif self.operator == ">":
            passed = actual > threshold_val
        elif self.operator == "<=":
            passed = actual <= threshold_val
        elif self.operator == ">=":
            passed = actual >= threshold_val

        status = "PASSED" if passed else "FAILED"
        message = (
            f"Threshold {status}: {self.metric} ({actual:.2f}) {self.operator} {threshold_val}"
        )
        
        return passed, actual, message
