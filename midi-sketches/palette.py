"""Reusable *generative* building blocks: constrained-random rhythm, bassline,
and melody generators shared by the archetypes in generator.py.

Everything here takes an explicit `random.Random` instance (never the global
`random` module) so a whole clip is reproducible from one seed. The randomness
is always constrained -- duration partitions that sum exactly to the bar,
scale walks that mostly move by step with a post-leap reversal rule, motifs
scored against a Narmour-style interval table and consonance-checked against
the bassline -- so output is "smart" (musically plausible) rather than
uniform noise. Parameter defaults follow practitioner/analytical guidance:
~65-80% stepwise motion, leaps resolved by a reversing step, dissonance
avoided on strong beats.
"""

import math

from rhythm import euclid_grid, grid_from_hits
from theory import SCALES, scale_degree


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


def min_safe_chunk_steps(bpm, min_ioi_ms=100, steps_per_beat=4):
    """The smallest chunk length (in 16th-note steps) whose onset spacing stays
    above `min_ioi_ms` at this tempo -- polyrhythms/cells finer than ~100ms IOI
    (>=600 BPM implied pulse) cross the documented cognitive grouping limit and
    read as texture/noise rather than a groove."""
    step_ms = 60000 / bpm / steps_per_beat
    return max(1, math.ceil(min_ioi_ms / step_ms))



# Vos & Troost (1989, Music Perception 6(4)): analyzing melodic-interval corpora,
# small intervals (steps) tended to descend and large intervals (leaps) tended to
# ascend. Encoded here as a directional bias rather than the coin-flip symmetry
# an unweighted choice would give.
_STEP_SIZES, _STEP_WEIGHTS = [-2, -1, 1, 2], [0.15, 0.40, 0.30, 0.15]
_LEAP_DIRECTIONS, _LEAP_DIR_WEIGHTS = [-1, 1], [0.35, 0.65]


def scale_walk(rng, start_degree, n, leap_prob=0.15, root_pull=0.2, max_leap=5):
    """A random walk over scale degrees: mostly stepwise motion (biased to
    descend, per Vos & Troost), occasional leaps (biased to ascend) that are
    then resolved by a step in the opposite direction (Narmour-style
    post-leap reversal), with an occasional pull back to the starting degree
    (usually the root) for coherence. Roughly 65-80% of moves end up stepwise."""
    degrees = [start_degree]
    force_reversal = None  # direction (+-1) the *next* move must take, after a leap
    for _ in range(1, n):
        if force_reversal is not None:
            nd = degrees[-1] + force_reversal * rng.choice([1, 2])
            degrees.append(nd)
            force_reversal = None
            continue
        if rng.random() < root_pull:
            degrees.append(start_degree)
            continue
        if rng.random() < leap_prob:
            direction = rng.choices(_LEAP_DIRECTIONS, weights=_LEAP_DIR_WEIGHTS)[0]
            size = max_leap if max_leap < 3 else rng.randint(3, max_leap)
            degrees.append(degrees[-1] + direction * size)
            force_reversal = -direction
        else:
            degrees.append(degrees[-1] + rng.choices(_STEP_SIZES, weights=_STEP_WEIGHTS)[0])
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


def motif(rng, n_notes, dur_choices=(1, 2, 3, 4), leap_prob=0.25, root_pull=0.15, max_leap=5):
    """A short melodic idea as (relative scale-degree offset, duration) pairs,
    independent of any particular root/register -- render with `render_motif`.
    Tune `leap_prob`/`max_leap` down for a narrow, chant-like character or up
    for wide, dramatic leaps."""
    offsets = scale_walk(rng, 0, n_notes, leap_prob=leap_prob, root_pull=root_pull, max_leap=max_leap)
    durs = [rng.choice(dur_choices) for _ in range(n_notes)]
    return list(zip(offsets, durs))


# A repeated note (0) must NOT outscore genuine motion, or best-of-N motif
# selection degenerates into "the whole motif is one frozen pitch."
_INTERVAL_SCORE = {0: 0, 1: 2, 2: 2, 3: 2, 4: 2, 5: 1, 6: -2, 7: 0, 8: -1, 9: -1, 10: -10, 11: -10, 12: -5}


def interval_score(semitones):
    """A Narmour-flavoured melodic-smoothness score for one interval: small
    consonant steps/3rds score positively, 7ths and wide leaps are penalized."""
    n = abs(semitones)
    if n > 12:
        return -10
    return _INTERVAL_SCORE.get(n, -3)


def score_motif(m, root, scale):
    """Sum of interval_score() across a motif's rendered pitches -- higher is smoother."""
    pitches = [scale_degree(root, scale, offset) for offset, _ in m]
    return sum(interval_score(pitches[i] - pitches[i - 1]) for i in range(1, len(pitches)))


def motif_scored(rng, n_notes, root, scale, attempts=5, **kwargs):
    """Generate `attempts` candidate motifs and keep the best one: prefer having
    at least 2 distinct pitches (never settle on a frozen single-note motif),
    then the smoothest interval_score."""
    best, best_key = None, None
    for _ in range(attempts):
        m = motif(rng, n_notes, **kwargs)
        pitches = [scale_degree(root, scale, offset) for offset, _ in m]
        key = (len(set(pitches)) >= 2, score_motif(m, root, scale))
        if best_key is None or key > best_key:
            best, best_key = m, key
    return best


def motif_invert(m):
    """Flip each interval's direction around the first note -- classic thematic development."""
    if len(m) < 2:
        return list(m)
    out = [m[0]]
    for i in range(1, len(m)):
        interval = m[i][0] - m[i - 1][0]
        out.append((out[-1][0] - interval, m[i][1]))
    return out


def motif_retrograde(m):
    """Play the motif backwards."""
    return list(reversed(m))


def motif_augment(m, factor=2):
    """Stretch every note's duration by `factor`."""
    return [(offset, dur * factor) for offset, dur in m]


def motif_diminish(m, factor=2):
    """Compress every note's duration by `factor` (minimum 1 step)."""
    return [(offset, max(1, dur // factor)) for offset, dur in m]


def motif_fragment(m, start=0, length=None):
    """A sub-slice of the motif -- development by fragmentation."""
    length = length or max(1, len(m) // 2)
    return m[start:start + length]


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


def harmonize(notes, interval, vel_scale=0.75):
    """Return a parallel voice of `notes` shifted by `interval` semitones -- e.g.
    -12 for an octave-below 'shadow', +12 for an octave-above 'high character'
    (the Fever Ray doubled/pitch-shifted voice), +7 for a fifth. The caller
    concatenates it with the original to thicken/stack. Out-of-range notes drop."""
    out = []
    for (s, d, n, v) in notes:
        nn = n + interval
        if 0 <= nn <= 127:
            out.append((s, d, nn, max(1, int(v * vel_scale))))
    return out


def antiphon(rng, call_motif, response_motif, root, scale, n_bars, bar_steps,
             call_reg, resp_reg, vel_base=88, degree_shift=0):
    """Two-voice call-and-response: odd bars answer the even bars' call, in a
    different register -- a dialogue between two 'characters' rather than one
    line. Returns a list of per-bar note lists."""
    bars = []
    for i in range(n_bars):
        if i % 2 == 0:
            notes = render_motif(rng, call_motif, root, scale, rng.choice([0, 2]),
                                 degree_shift=degree_shift, register=call_reg, vel_base=vel_base)
        else:
            notes = render_motif(rng, response_motif, root, scale, rng.choice([1, 3]),
                                 degree_shift=degree_shift + 2, register=resp_reg, vel_base=vel_base - 4)
        bars.append([(s, d, n, v) for (s, d, n, v) in notes if s < bar_steps])
    return bars


# --- hook engine: catchy, singable melodic phrases (not wandering walks) -----
# Syncopated onset templates over a 16-step bar, each ending on a held "landing"
# note. Real hooks have a memorable *rhythm*, not even eighths.
HOOK_RHYTHMS = [
    [0, 4, 6, 8, 12],
    [0, 2, 4, 8, 12],
    [2, 4, 6, 8, 12],       # pickup / anacrusis feel
    [0, 3, 6, 8, 11],
    [0, 4, 7, 8, 12],
    [0, 2, 6, 8, 10, 12],
    [0, 6, 8, 10, 12],
]
_HOOK_TONES = [0, 2, 4, 5, 7, 9, 11]   # chord/stable scale-degree steps (root,3rd,5th,6th,oct,...)


def _arch(n, start, peak, land):
    """A contour that rises to a peak then falls to a landing, snapped to stable
    (chord) tones -- the memorable shape ear-worms are built on."""
    if n == 1:
        return [land]
    up = max(n // 2, 1)
    degs = []
    for i in range(n):
        if i <= up:
            d = start + (peak - start) * (i / up)
        else:
            d = peak + (land - peak) * ((i - up) / max(n - 1 - up, 1))
        degs.append(min(_HOOK_TONES, key=lambda c: abs(c - d)))
    degs[-1] = land
    return degs


def hook_phrase(rng, root, scale, register, vel_base=94):
    """A catchy antecedent/consequent hook (two 16-step bars sharing one rhythm):
    the antecedent poses a question (lands on the 5th/octave, unresolved), the
    consequent answers it (same rhythm, resolves to the root). The peak note is
    accented. Repeat this across a section and it becomes the earworm."""
    onsets = sorted(set(o for o in rng.choice(HOOK_RHYTHMS) if o < 16))
    durs = [onsets[i + 1] - onsets[i] for i in range(len(onsets) - 1)] + [16 - onsets[-1]]
    start_deg = rng.choice([0, 2])
    peak = rng.choice([4, 5, 7, 7, 9])          # bias to 5th / octave / higher for a clear peak

    def make(land):
        degs = _arch(len(onsets), start_deg, peak, land)
        out = []
        for o, dr, dg in zip(onsets, durs, degs):
            pitch = clamp_register(scale_degree(root, scale, dg), *register)
            vel = vel_base + (10 if dg == peak else 0) + rng.randint(-4, 4)
            out.append((o, dr, pitch, max(1, min(127, vel))))
        return out

    return make(rng.choice([4, 7])), make(0)   # (antecedent question, consequent answer)


def ostinato_cell(rng, root, scale, register, vel_base=88):
    """A short fixed riff (Fairlight/Reich-style) -- a rhythmic, chord-tone-heavy
    one-bar cell meant to repeat *identically* as an instrumental hook."""
    onsets = sorted(set(o for o in rng.choice(HOOK_RHYTHMS) if o < 16))
    durs = [onsets[i + 1] - onsets[i] for i in range(len(onsets) - 1)] + [16 - onsets[-1]]
    degs = [rng.choice([0, 2, 4, 0, 4, 5, 7]) for _ in onsets]   # chord-tone-weighted, memorable
    cell = []
    for o, dr, dg in zip(onsets, durs, degs):
        pitch = clamp_register(scale_degree(root, scale, dg), *register)
        cell.append((o, dr, pitch, vel_base + rng.randint(-4, 4)))
    return cell


def spread_chord(root, scale, degrees=(0, 2, 4, 6, 7)):
    """A chord voiced upward as scale tones (default root/3rd/5th/7th/octave) --
    the material an arpeggiator runs through."""
    return [scale_degree(root, scale, d) for d in degrees]


def arpeggiate(rng, chord, steps, rate=1, direction="up", register=None,
               vel_base=84, vel_spread=6, gate=0.9, accent_every=4):
    """Run `chord` as an arpeggio filling `steps`, one note every `rate` steps.
    direction: up / down / updown / random. `gate` (<1) shortens each note for a
    plucky feel. CLEVER USE: give the chord a coprime number of tones (e.g. 5)
    and rate=1 over a 16-step bar and the pattern re-phases against the beat --
    the hypnotic Weird Fishes / Idioteque arp drift (grouping dissonance)."""
    order = list(chord)
    if direction == "down":
        order = order[::-1]
    elif direction == "updown" and len(order) > 2:
        order = order + order[-2:0:-1]
    dur = max(1, round(rate * gate))
    notes, idx = [], 0
    for k, pos in enumerate(range(0, steps, rate)):
        pitch = rng.choice(chord) if direction == "random" else order[idx % len(order)]
        idx += 1
        if register:
            pitch = clamp_register(pitch, *register)
        vel = vel_base + (10 if k % accent_every == 0 else 0) + rng.randint(-vel_spread, vel_spread)
        notes.append((pos, dur, pitch, max(1, min(127, vel))))
    return notes


def euclid_cross(rng, steps, specs):
    """Coprime Euclidean layers for polyrhythmic hand percussion: `specs` is a
    list of (voice, pulses, rotate). Returns {voice: grid_string}. Using
    different pulse counts over the same step-grid produces real cross-rhythm
    (e.g. 3-against-5-against-7 congas), not aligned hits."""
    from rhythm import euclid_grid
    return {voice: euclid_grid(pulses, steps, rotate) for voice, pulses, rotate in specs}


def _is_consonant(semitones):
    return abs(semitones) % 12 in (0, 3, 4, 5, 7, 8, 9)


def resolve_consonance(bass_notes, melody_notes, root, scale, strong_steps):
    """Where a melody note lands on a strong beat against a sounding bass note,
    nudge it (by up to a few semitones, staying in-scale) to the nearest
    consonant interval if the raw pitch clashes -- a lightweight two-voice
    counterpoint filter (avoid dissonant downbeats, prefer 3rd/5th/6th/8ve)."""
    scale_pcs = {(root + iv) % 12 for iv in SCALES[scale]}
    out = []
    for start, dur, note_num, vel in melody_notes:
        if start in strong_steps:
            under = [b for b in bass_notes if b[0] <= start < b[0] + b[1]]
            if under and not _is_consonant(note_num - under[0][2]):
                bass_note = under[0][2]
                for delta in (1, -1, 2, -2, 3, -3, 4, -4):
                    cand = note_num + delta
                    if cand % 12 in scale_pcs and _is_consonant(cand - bass_note):
                        note_num = cand
                        break
        out.append((start, dur, note_num, vel))
    return out


def phase_melody(rng, root, scale, n_bars, bar_steps=16, cell_len=None, vel_base=90, bpm=None):
    """Tile a short cell (length `cell_len`, default a random 3/5/7) continuously
    across `n_bars` of `bar_steps` -- when `bar_steps % cell_len != 0` the cell
    drifts out of phase with the bar line every repeat (an n-against-`bar_steps`
    polymeter), splitting notes at bar boundaries so each bar stays self-contained.
    If `bpm` is given, the cell's chunk sizes are kept coarse enough that the
    fastest onset spacing stays above the ~100ms cognitive grouping limit.
    """
    cell_len = cell_len or rng.choice([3, 5, 7])
    chunk_choices = (1, 2)
    if bpm:
        min_chunk = min_safe_chunk_steps(bpm)
        chunk_choices = tuple(c for c in (1, 2, 3) if c >= min_chunk) or (cell_len,)
    cell_partition = duration_partition(rng, cell_len, chunk_choices=chunk_choices)
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


def additive_phase_melody(rng, root, scale, n_bars, bar_steps=16, start_len=2, vel_base=90):
    """A Glass/Reich-style additive process: the melodic cell grows by one note
    each repeat (2 notes, then 3, then 4, ...) instead of tiling a fixed cell --
    a second way to generalize 'a melodic idea against the bar' beyond a static
    n-against-4 polymeter."""
    bars_out = [[] for _ in range(n_bars)]
    total_steps = n_bars * bar_steps
    pos, cell_notes = 0, start_len
    degrees_pool = scale_walk(rng, 0, start_len + n_bars, leap_prob=0.12, root_pull=0.25)
    while pos < total_steps:
        length = min(cell_notes, len(degrees_pool))
        # lay out `length` equal-ish steps summing to a short cell (2-3 steps each)
        step_each = rng.choice([2, 3])
        for i in range(length):
            dur = min(step_each, total_steps - pos)
            if dur <= 0:
                break
            note_num = scale_degree(root, scale, degrees_pool[i % len(degrees_pool)])
            vel = vel_base + rng.randint(-8, 10)
            remaining, cur = dur, pos
            while remaining > 0:
                bar_idx, local = divmod(cur, bar_steps)
                take = min(remaining, bar_steps - local)
                bars_out[bar_idx].append((local, take, note_num, vel))
                cur += take
                remaining -= take
            pos += dur
        cell_notes += 1
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
