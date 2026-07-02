"""Deterministic (seeded) micro-timing and velocity variation, plus practitioner-
grade swing math (Roger Linn / MPC-style swing percentage).

Everything here is reproducible: same input + seed always yields the same output.
Timing amounts are usually derived from milliseconds via `ms_to_ticks` rather than
picked as raw tick counts, so they stay meaningful across tempos.

Timing *deviation* uses 1/f (pink) noise, not independent white-noise jitter --
controlled studies (Frühauf/Kopiez/Platz 2013; Davies/Madison/Silva/Gouyon 2013)
found random microtiming does not reliably increase perceived "groove" and often
reduces it, while listeners prefer long-range-correlated (1/f) timing fluctuations
over uncorrelated ones (Hennig, Fleischmann & Geisel 2011, PLOS ONE 6(10):e26457).
`velocity` variation is left as independent jitter -- that specific finding was
about *timing*, not dynamics.
"""

import math
import random


def ms_to_ticks(ms, bpm, ppq):
    """Convert a millisecond offset to ticks at the given tempo/resolution."""
    return round(ms / 1000 * bpm / 60 * ppq)


def jitter(events, timing_ticks=0, vel_amount=0, seed=0):
    """Nudge each event's start time and velocity by a small *independent* random
    amount. Kept for velocity; prefer `pink_jitter` for timing (see module docstring)."""
    rng = random.Random(seed)
    out = []
    for ev in events:
        dt = rng.randint(-timing_ticks, timing_ticks) if timing_ticks else 0
        dv = rng.randint(-vel_amount, vel_amount) if vel_amount else 0
        out.append(ev._replace(start=max(0, ev.start + dt), vel=max(1, min(127, ev.vel + dv))))
    return out


def voss_mccartney(rng, n, octaves=8):
    """A standard discrete approximation of 1/f (pink) noise: `octaves` running
    random generators, each updated half as often as the last (so lower
    "frequencies" persist longer), summed. Returns `n` unnormalized samples."""
    generators = [rng.uniform(-1, 1) for _ in range(octaves)]
    total = sum(generators)
    out = []
    for i in range(1, n + 1):
        changed = i ^ (i - 1)  # bits that flipped going from i-1 to i
        for j in range(octaves):
            if changed & (1 << j):
                total -= generators[j]
                generators[j] = rng.uniform(-1, 1)
                total += generators[j]
        out.append(total)
    return out


def pink_jitter(events, bpm, ppq, sd_ms=15, seed=0):
    """Apply 1/f-correlated timing deviation (see module docstring) with the
    given target standard deviation in milliseconds, converted to ticks at
    this tempo/resolution. Deviations are assigned in start-time order, so
    nearby notes get correlated (not independent) nudges."""
    if not events:
        return events
    order = sorted(range(len(events)), key=lambda i: events[i].start)
    rng = random.Random(seed)
    noise = voss_mccartney(rng, len(events))
    mean = sum(noise) / len(noise)
    variance = sum((x - mean) ** 2 for x in noise) / len(noise)
    std = math.sqrt(variance) or 1.0
    target_ticks = ms_to_ticks(sd_ms, bpm, ppq)

    out = list(events)
    for rank, idx in enumerate(order):
        offset = round((noise[rank] - mean) / std * target_ticks)
        out[idx] = events[idx]._replace(start=max(0, events[idx].start + offset))
    return out




def sixteenth_swing_pct(bpm, slow=62.0, fast=50.0, slow_bpm=80, fast_bpm=140):
    """Tempo-dependent swing percentage for the *sixteenth*-note grid that
    `swing()` operates on. CAUTION (a bug we actually hit): jazz BUR research
    quotes EIGHTH-note beat-upbeat ratios (up to ~78%); feeding those into a 16th-note
    swing overstates the shuffle by a whole metric level (a 3:1 eighth ratio is
    an extreme, past-triplet 16th shuffle), so this stays in the practitioner
    16th-swing band: gentle at slow tempos, straightening toward 50% as tempo
    rises. Defaults span Logic's 16C-ish (~58-62%) down to straight."""
    if bpm <= slow_bpm:
        return slow
    if bpm >= fast_bpm:
        return fast
    frac = (bpm - slow_bpm) / (fast_bpm - slow_bpm)
    return slow + frac * (fast - slow)


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
