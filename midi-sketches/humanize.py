"""Deterministic (seeded) micro-timing and velocity variation, plus 16th-note swing.

Everything here is reproducible: same input + seed always yields the same output.
"""

import random


def jitter(events, timing_ticks=0, vel_amount=0, seed=0):
    """Nudge each event's start time and velocity by a small random amount."""
    rng = random.Random(seed)
    out = []
    for ev in events:
        dt = rng.randint(-timing_ticks, timing_ticks) if timing_ticks else 0
        dv = rng.randint(-vel_amount, vel_amount) if vel_amount else 0
        out.append(ev._replace(start=max(0, ev.start + dt), vel=max(1, min(127, ev.vel + dv))))
    return out


def swing(events, step_ticks, amount_ticks):
    """Delay every other step (the off-16ths) by `amount_ticks` -- classic MPC-style swing.

    A note exactly on an even step (0, 2, 4, ...) is untouched; a note on an odd
    step (1, 3, 5, ...) is pushed later, turning straight 16ths into a shuffled feel.
    """
    out = []
    for ev in events:
        step_idx = ev.start // step_ticks
        out.append(ev._replace(start=ev.start + amount_ticks) if step_idx % 2 == 1 else ev)
    return out
