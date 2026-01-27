"""Statistical utility functions."""

import math


def calculate_percentile(data: list[float], percentile: float) -> float:
    """Calculate the Nth percentile of a list of values.

    Args:
        data: List of numerical values.
        percentile: Percentile to calculate (0-100).

    Returns:
        The calculated percentile value, or 0.0 if data is empty.
    """
    if not data:
        return 0.0

    # Sort data (copy to avoid modifying original if passed by reference)
    sorted_data = sorted(data)

    # Logic matches Wikipedia "Nearest-rank method" or similar simple interpolation
    k = (len(sorted_data) - 1) * (percentile / 100.0)
    f = math.floor(k)
    c = math.ceil(k)

    if f == c:
        return sorted_data[int(k)]

    d0 = sorted_data[int(f)]
    d1 = sorted_data[int(c)]

    return d0 + (d1 - d0) * (k - f)
