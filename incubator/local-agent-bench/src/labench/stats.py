"""Statistical utilities for pass-rate estimation.

Pass rates from a few dozen binary trials carry real uncertainty; reporting
a bare percentage invites over-interpretation. We report Wilson score
intervals (better coverage than normal approximation at small n and
extreme rates) and provide a seeded bootstrap for comparing two runs.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass(frozen=True)
class Interval:
    point: float
    low: float
    high: float


def wilson_interval(successes: int, n: int, z: float = 1.96) -> Interval:
    """Wilson score interval for a binomial proportion."""
    if n <= 0:
        raise ValueError("n must be positive")
    if not 0 <= successes <= n:
        raise ValueError("successes must be within [0, n]")
    p = successes / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    margin = (z / denom) * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))
    return Interval(point=p, low=max(0.0, center - margin), high=min(1.0, center + margin))


def bootstrap_diff_ci(
    a: list[bool],
    b: list[bool],
    iterations: int = 5000,
    alpha: float = 0.05,
    seed: int = 42,
) -> Interval:
    """Percentile bootstrap CI for pass-rate difference (a minus b).

    If the interval excludes zero, the difference is unlikely to be noise
    at the given alpha. Not a substitute for a paired design, but honest
    for independent runs.
    """
    if not a or not b:
        raise ValueError("both samples must be non-empty")
    rng = random.Random(seed)
    point = _mean(a) - _mean(b)
    diffs = sorted(
        _mean(rng.choices(a, k=len(a))) - _mean(rng.choices(b, k=len(b)))
        for _ in range(iterations)
    )
    lo_idx = int((alpha / 2) * iterations)
    hi_idx = min(iterations - 1, int((1 - alpha / 2) * iterations))
    return Interval(point=point, low=diffs[lo_idx], high=diffs[hi_idx])


def _mean(values: list[bool]) -> float:
    return sum(values) / len(values)
