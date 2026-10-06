"""Robust statistics with fixed seeds, so every number can be recomputed exactly."""

from __future__ import annotations

import math
import random
import statistics


def median(xs: list[float]) -> float:
    return statistics.median(xs) if xs else float("nan")


def quartiles(xs: list[float]) -> tuple[float, float, float]:
    xs = sorted(xs)
    if len(xs) < 2:
        v = xs[0] if xs else float("nan")
        return v, v, v
    q = statistics.quantiles(xs, n=4, method="inclusive")
    return q[0], q[1], q[2]


def bootstrap_ci(xs: list[float], stat=median, b: int = 10_000, seed: int = 0, alpha: float = 0.05) -> tuple[float, float]:
    """Percentile bootstrap over sessions (the session is the unit of analysis)."""
    if len(xs) < 2:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    n = len(xs)
    vals = sorted(stat([xs[rng.randrange(n)] for _ in range(n)]) for _ in range(b))
    return vals[int(alpha / 2 * b)], vals[min(b - 1, int((1 - alpha / 2) * b))]


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float, float]:
    """Proportion with a Wilson 95% interval."""
    if n == 0:
        return float("nan"), float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return p, c - h, c + h


def summary(xs: list[float], seed: int, b: int) -> dict:
    q1, med, q3 = quartiles(xs)
    lo, hi = bootstrap_ci(xs, b=b, seed=seed)
    r = lambda v: None if v != v else round(v, 1)  # NaN -> null
    return {"n": len(xs), "median": r(med), "q1": r(q1), "q3": r(q3), "ci95": [r(lo), r(hi)]}
