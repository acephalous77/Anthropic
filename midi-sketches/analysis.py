"""Lightweight, dependency-free approximations of two research-backed
"well-formedness" metrics, used as QC signals in generator.py:

- Zipf rank-frequency slope (Manaris et al. 2005, Computer Music Journal
  29(1)): aesthetically-typical music's pitch/duration/interval distributions
  plot close to a straight line of slope ~-1 on log-log rank-frequency axes.
  Too flat (~0) reads as too-even/random; too steep (more negative) reads as
  monotone/repetitive.
- Melodic interval entropy, a rough analogue of IDyOM's "entropy" concept
  (Pearce 2005) -- not a trained information-content model (that needs a
  corpus we don't have), just Shannon entropy over the interval histogram,
  used as a cheap proxy for "is this melody varied or is it stuck in a rut."
"""

import math
from collections import Counter


def zipf_slope(values):
    """Log-log rank-frequency slope + R^2 for a sequence of discrete values.
    Returns (None, None) if there aren't enough distinct values to fit."""
    counts = Counter(values)
    ranked = sorted(counts.values(), reverse=True)
    if len(ranked) < 3:
        return None, None

    xs = [math.log(r) for r in range(1, len(ranked) + 1)]
    ys = [math.log(c) for c in ranked]
    n = len(xs)
    mean_x, mean_y = sum(xs) / n, sum(ys) / n
    ss_xy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    ss_xx = sum((x - mean_x) ** 2 for x in xs)
    ss_yy = sum((y - mean_y) ** 2 for y in ys)
    if ss_xx == 0 or ss_yy == 0:
        return None, None
    slope = ss_xy / ss_xx
    r2 = (ss_xy ** 2) / (ss_xx * ss_yy)
    return slope, r2


def shannon_entropy(values):
    """Shannon entropy (bits) of a sequence's empirical distribution."""
    counts = Counter(values)
    n = len(values)
    if n == 0:
        return 0.0
    return -sum((c / n) * math.log2(c / n) for c in counts.values())


def melodic_intervals(pitches):
    return [pitches[i] - pitches[i - 1] for i in range(1, len(pitches))]
