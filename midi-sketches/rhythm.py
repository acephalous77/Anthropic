"""Step-grid authoring helpers, plus a Euclidean (Bjorklund) rhythm generator."""

from midiwriter import Event


def bjorklund(pulses, steps):
    """Return a list[bool] of length `steps` with `pulses` as evenly spaced as possible.

    Standard Euclidean-rhythm construction (Bjorklund's algorithm), e.g.
    bjorklund(3, 8) -> the classic tresillo [x..x..x.].
    """
    if pulses <= 0:
        return [False] * steps
    if pulses >= steps:
        return [True] * steps

    counts = []
    remainders = [pulses]
    divisor = steps - pulses
    level = 0
    while True:
        counts.append(divisor // remainders[level])
        remainders.append(divisor % remainders[level])
        divisor = remainders[level]
        level += 1
        if remainders[level] <= 1:
            break
    counts.append(divisor)

    pattern = []

    def build(level):
        if level == -1:
            pattern.append(False)
        elif level == -2:
            pattern.append(True)
        else:
            for _ in range(counts[level]):
                build(level - 1)
            if remainders[level] != 0:
                build(level - 2)

    build(level)
    i = pattern.index(True)
    return pattern[i:] + pattern[:i]


def euclid_grid(pulses, steps, rotate=0):
    """Return a grid string ('x' hit / '.' rest) of length `steps`, rotated by `rotate` steps."""
    pattern = bjorklund(pulses, steps)
    if rotate:
        rotate %= steps
        pattern = pattern[rotate:] + pattern[:rotate]
    return "".join("x" if v else "." for v in pattern)


# Named (pulses, steps) presets documented by Toussaint (2005, "The Euclidean
# Algorithm Generates Traditional Musical Rhythms") as real-world rhythms --
# useful ostinato starting points rather than an arbitrary pulse count.
EUCLIDEAN_PRESETS = {
    "tresillo": (3, 8),      # Cuban tresillo / Habanera, also bluegrass banjo
    "cinquillo": (5, 8),     # Cuban cinquillo / West African bell pattern
    "bossa": (5, 16),        # Brazilian bossa nova bass pattern
    "fume_fume": (5, 12),    # Ghanaian fume-fume / soukous
    "west_african_12": (7, 12),
    "samba": (7, 16),
    "reich": (8, 12),        # a Steve Reich signature rhythm
    "central_african_5": (2, 5),
}


def euclidean_preset(name, rotate=0):
    """A named Euclidean pattern (see EUCLIDEAN_PRESETS) as a grid string."""
    pulses, steps = EUCLIDEAN_PRESETS[name]
    return euclid_grid(pulses, steps, rotate)


def euclidean_preset_tiled(name, target_steps, rotate=0):
    """A named preset repeated (and truncated) to exactly fill `target_steps` --
    e.g. the 8-step tresillo tiled twice to fit a 16-step bar."""
    grid = euclidean_preset(name, rotate)
    reps = -(-target_steps // len(grid))  # ceil division
    return (grid * reps)[:target_steps]


def grid_from_hits(length, hits, accents=None):
    """Build a grid string from step indices, e.g. grid_from_hits(16, {0, 7, 11}, accents={0})."""
    accents = accents or set()
    return "".join("X" if i in accents else ("x" if i in hits else ".") for i in range(length))


def grid_to_events(grid, note, step_ticks, start_tick=0, vel=100, accent_vel=None,
                    accent_steps=None, dur_ticks=None, humanize=None, channel=0):
    """Convert a step-grid string into a list of Event.

    grid: string of 'x'/'X' (hit), '.' (rest) per step. 'X' is always accented.
    accent_steps: optional set of step indices to accent at accent_vel.
    humanize: optional list/tuple of per-step tick offsets (same length as grid), for swing/drift.
    """
    accent_steps = accent_steps or set()
    dur_ticks = dur_ticks if dur_ticks is not None else step_ticks
    events = []
    for i, ch in enumerate(grid):
        if ch not in ("x", "X"):
            continue
        v = vel
        if ch == "X" or i in accent_steps:
            v = accent_vel if accent_vel is not None else min(127, vel + 20)
        t = start_tick + i * step_ticks
        if humanize:
            t += humanize[i]
        events.append(Event(t, dur_ticks, note, v, channel))
    return events
