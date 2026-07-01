"""Deterministic (seeded) micro-timing and velocity variation, plus practitioner-
grade swing math (Roger Linn / MPC-style swing percentage).

Everything here is reproducible: same input + seed always yields the same output.
Timing amounts are usually derived from milliseconds via `ms_to_ticks` rather than
picked as raw tick counts, so they stay meaningful across tempos.
"""

import random


def ms_to_ticks(ms, bpm, ppq):
    """Convert a millisecond offset to ticks at the given tempo/resolution."""
    return round(ms / 1000 * bpm / 60 * ppq)


def jitter(events, timing_ticks=0, vel_amount=0, seed=0):
    """Nudge each event's start time and velocity by a small random amount."""
    rng = random.Random(seed)
    out = []
    for ev in events:
        dt = rng.randint(-timing_ticks, timing_ticks) if timing_ticks else 0
        dv = rng.randint(-vel_amount, vel_amount) if vel_amount else 0
        out.append(ev._replace(start=max(0, ev.start + dt), vel=max(1, min(127, ev.vel + dv))))
    return out


def split_by(events, predicate):
    """Partition events into (matching, rest) -- e.g. to jitter kicks and ghost
    notes by different amounts: `kicks, rest = split_by(events, lambda e: e.note == KICK)`."""
    matching, rest = [], []
    for e in events:
        (matching if predicate(e) else rest).append(e)
    return matching, rest


def swing_ticks(swing_pct, eighth_ticks):
    """Roger Linn / MPC-style swing: `swing_pct` is the fraction (0-100) of an
    8th note given to its first 16th. 50 = straight, 66 = perfect triplet swing,
    75 = maximum (dotted-16th + 32nd). Returns the tick offset to delay the
    second (off-beat) 16th of each pair -- feed straight into `swing()`.
    """
    return round((swing_pct / 100 - 0.5) * eighth_ticks)


def swing(events, step_ticks, amount_ticks=None, swing_pct=None, eighth_ticks=None):
    """Delay every other step (the off-16ths) -- classic MPC-style swing.

    A note exactly on an even step (0, 2, 4, ...) is untouched; a note on an odd
    step (1, 3, 5, ...) is pushed later, turning straight 16ths into a shuffled feel.
    Pass either `amount_ticks` directly, or `swing_pct` (+ `eighth_ticks`, default
    2 * step_ticks) to compute it via the practitioner formula.
    """
    if amount_ticks is None:
        amount_ticks = swing_ticks(swing_pct, eighth_ticks or step_ticks * 2)
    out = []
    for ev in events:
        step_idx = ev.start // step_ticks
        out.append(ev._replace(start=ev.start + amount_ticks) if step_idx % 2 == 1 else ev)
    return out
