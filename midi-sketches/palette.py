"""Reusable *generative* building blocks: constrained-random rhythm, bassline,
and melody generators shared by the archetypes in generator.py.

Everything here takes an explicit `random.Random` instance (never the global
`random` module) so a whole clip is reproducible from one seed. The randomness
is always constrained -- duration partitions that sum exactly to the bar,
scale walks that mostly move by step, motifs rendered from scale degrees --
so output is "smart" (musically plausible) rather than uniform noise.
"""

from rhythm import euclid_grid, grid_from_hits
from theory import scale_degree


def duration_partition(rng, steps, chunk_choices=(2, 3, 4, 6)):
    """Split `steps` into a lopsided sequence of chunk lengths that sums exactly to `steps`."""
    parts = []
    remaining = steps
    while remaining > 0:
        choices = [c for c in chunk_choices if c <= remaining] or [remaining]
        c = rng.choice(choices)
        parts.append(c)
        remaining -= c
    return parts


def scale_walk(rng, start_degree, n, leap_prob=0.18, root_pull=0.22):
    """A random walk over scale degrees: mostly stepwise motion, occasional leaps,
    with a pull back toward the starting degree (usually the root) for coherence."""
    degrees = [start_degree]
    for _ in range(1, n):
        if rng.random() < root_pull:
            nd = start_degree
        elif rng.random() < leap_prob:
            nd = degrees[-1] + rng.choice([-5, -4, -3, 3, 4, 5])
        else:
            nd = degrees[-1] + rng.choice([-2, -1, -1, 1, 1, 2])
        degrees.append(nd)
    return degrees


def clamp_register(n, lo, hi):
    """Shift a MIDI note by octaves until it sits in [lo, hi]."""
    while n < lo:
        n += 12
    while n > hi:
        n -= 12
    return n


def bass_phrase(rng, root, scale, steps, register, vel_range=(82, 100)):
    """A duration-partitioned, scale-stepping bassline for one bar: strong on
    the downbeat, mostly stepwise, occasionally leaping -- Radiohead-angular
    when the partition is lopsided, Fever-Ray-drone-ish when it isn't."""
    partition = duration_partition(rng, steps)
    degrees = scale_walk(rng, 0, len(partition))
    notes = []
    pos = 0
    for i, dur in enumerate(partition):
        pitch = clamp_register(scale_degree(root, scale, degrees[i]), *register)
        vel = rng.randint(*vel_range) + (10 if pos == 0 else 0)
        notes.append((pos, dur, pitch, min(127, vel)))
        pos += dur
    return notes


def motif(rng, n_notes, dur_choices=(1, 2, 3, 4)):
    """A short melodic idea as (relative scale-degree offset, duration) pairs,
    independent of any particular root/register -- render with `render_motif`."""
    offsets = scale_walk(rng, 0, n_notes, leap_prob=0.25, root_pull=0.15)
    durs = [rng.choice(dur_choices) for _ in range(n_notes)]
    return list(zip(offsets, durs))


def render_motif(rng, m, root, scale, start_step, degree_shift=0, register=None, vel_base=90, vel_spread=10):
    """Turn a motif (from `motif()`) into (start_step, dur, note, vel) tuples starting at `start_step`."""
    notes = []
    pos = start_step
    for offset, dur in m:
        pitch = scale_degree(root, scale, offset + degree_shift)
        if register:
            pitch = clamp_register(pitch, *register)
        vel = vel_base + rng.randint(-vel_spread, vel_spread)
        notes.append((pos, dur, pitch, max(1, min(127, vel))))
        pos += dur
    return notes


def phase_melody(rng, root, scale, n_bars, bar_steps=16, cell_len=None, vel_base=90):
    """Tile a short cell (length `cell_len`, default a random 3/5/7) continuously
    across `n_bars` of `bar_steps` -- when `bar_steps % cell_len != 0` the cell
    drifts out of phase with the bar line every repeat (an n-against-`bar_steps`
    polymeter), splitting notes at bar boundaries so each bar stays self-contained.
    """
    cell_len = cell_len or rng.choice([3, 5, 7])
    cell_partition = duration_partition(rng, cell_len, chunk_choices=(1, 2))
    cell_degrees = scale_walk(rng, 0, len(cell_partition), leap_prob=0.1, root_pull=0.2)
    cell = [(dur, deg, vel_base + rng.randint(-8, 10)) for dur, deg in zip(cell_partition, cell_degrees)]

    total_steps = n_bars * bar_steps
    bars_out = [[] for _ in range(n_bars)]
    pos, ci = 0, 0
    while pos < total_steps:
        dur, degree, vel = cell[ci % len(cell)]
        dur = min(dur, total_steps - pos)
        if dur <= 0:
            break
        note_num = scale_degree(root, scale, degree)
        remaining, cur = dur, pos
        while remaining > 0:
            bar_idx, local = divmod(cur, bar_steps)
            take = min(remaining, bar_steps - local)
            bars_out[bar_idx].append((local, take, note_num, vel))
            cur += take
            remaining -= take
        pos += dur
        ci += 1
    return bars_out


def kick_pattern(rng, steps, pulse_choices=(2, 3, 3, 4, 4, 5), downbeat_bias=0.55):
    """A Euclidean kick pattern, usually (but not always) rotated to land on the downbeat."""
    pulses = rng.choice(pulse_choices)
    rotate = 0 if rng.random() < downbeat_bias else rng.randint(1, steps - 1)
    return euclid_grid(pulses, steps, rotate)


def hats_pattern(rng, steps, density="med", glitch_prob=0.35):
    """Even hi-hat subdivision (sparse/med/busy) with an occasional glitchy dropout."""
    sub = {"sparse": 4, "med": 2, "busy": 1}.get(density, 2)
    hits = set(range(0, steps, sub))
    if rng.random() < glitch_prob and len(hits) > 4:
        drop_n = rng.randint(1, max(1, len(hits) // 4))
        hits -= set(rng.sample(sorted(hits), drop_n))
    accents = {0}
    if steps >= 8:
        accents.add(steps // 2)
    return grid_from_hits(steps, hits, accents=accents)
