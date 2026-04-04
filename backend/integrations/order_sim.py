"""
Simulated order volume proxy.
Correlated with mobility: order_volume = mobility_index * 0.85 + noise
"""

import random


def simulate_order_volume(mobility_index: float, baseline: float = 100) -> dict:
    """Simulate order volume based on mobility index."""

    # Orders correlate with mobility at ~0.85
    noise = random.gauss(0, 5)
    order_volume = max(0, mobility_index * 0.85 + noise)
    pct_of_baseline = (order_volume / max(baseline, 1)) * 100

    return {
        "order_volume": round(order_volume, 1),
        "baseline": baseline,
        "pct_of_baseline": round(pct_of_baseline, 1),
        "source": "simulated_order_proxy",
    }
