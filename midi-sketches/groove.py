"""The feel engine: what separates a pattern from a pocket.

Three measured weaknesses in the library, three fixes:

1. FLAT DYNAMICS -> a meter-aware accent hierarchy (downbeat > mid-bar >
   backbeats > 8ths > 16ths) applied as per-step velocity weights, plus a
   ghost-note generator that tucks quiet snare/hat ticks (vel 20-40) into the
   gaps around the backbeat -- where a real drummer's left hand lives.

2. SMEARED TIMING -> role-based microtiming FEELS instead of uniform jitter:
   systematic per-voice offsets (snare lays back, hats push, bass sits just
   behind the kick), plus a tiny per-hit spread. The pocket comes from the
   *relationship* between voices, not from randomness. Beat 1 stays anchored.

3. NOTHING EVER REPEATS -> repetition architecture: phrase plans (AAAB, AABA')
   built from one cell and a vary() operator that keeps most of the bar
   identical and mutates the tail -- state it, state it again, THEN develop.
   That's what makes a part hookable.
"""

import random

from midiwriter import Event

# ---------------------------------------------------------------- accent hierarchy
# velocity weight per 16th-step position in a 4/4 bar: beat 1 strongest, then
# beat 3, then 2 & 4, then the 8th offbeats, then the 16th "e"/"a" positions.
METRIC_W16 = [1.00, 0.72, 0.80, 0.70,
              0.88, 0.70, 0.80, 0.72,
              0.94, 0.70, 0.80, 0.70,
              0.88, 0.72, 0.82, 0.74]


def metric_weight(step, bar_steps=16):
    if bar_steps == 16:
        return METRIC_W16[step % 16]
    # odd meters: strong on 1, medium on each beat (every 2 steps), weak between
    if step == 0:
        return 1.0
    return 0.85 if step % 2 == 0 else 0.72


def apply_accents(events, step_ticks, bar_steps=16, floor=0.65, depth=1.0):
    """Scale each event's velocity by its metric position. `depth` < 1 softens
    the hierarchy (drones); > 1 exaggerates it (funk)."""
    out = []
    for e in events:
        step = (e.start // step_ticks) % bar_steps
        w = metric_weight(step, bar_steps)
        w = 1.0 - (1.0 - w) * depth
        out.append(e._replace(vel=max(1, min(127, round(e.vel * max(floor, w))))))
    return out


def apply_accents_metered(events, step_ticks, time_sig_changes, ppq,
                          floor=0.65, depth=1.0):
    """apply_accents for pieces whose meter changes: each event's bar position
    is computed from the time signature in effect at its tick (render_piece
    emits time-sig changes exactly on bar starts, so bars tile cleanly from
    each change)."""
    if not events:
        return events
    changes = sorted(time_sig_changes)
    out = []
    for e in events:
        t0, (num, den) = changes[0]
        for tick, sig in changes:
            if tick <= e.start:
                t0, (num, den) = tick, sig
            else:
                break
        bar_ticks = ppq * 4 * num // den
        pos = ((e.start - t0) % bar_ticks) // step_ticks
        w = metric_weight(pos, bar_ticks // step_ticks)
        w = 1.0 - (1.0 - w) * depth
        out.append(e._replace(vel=max(1, min(127, round(e.vel * max(floor, w))))))
    return out


# ---------------------------------------------------------------- ghost notes
SNARE_NOTES = {38, 40}
HAT_NOTES = {42, 44}

# 16th positions a drummer's ghost hand favours (around/leading into backbeats)
GHOST_SPOTS = [3, 6, 7, 10, 14, 15]


def add_ghosts(rng, cell_events, step_ticks, bar_steps=16, density=0.5,
               ghost_note=38, vel_range=(22, 38)):
    """Insert low-velocity snare ghosts into empty 16th slots of a ONE-BAR drum
    cell. Enrich the cell first, then tile it, so the ghost pattern is part of
    the loop's identity (a real drummer's ghosts are consistent, not random)."""
    occupied = {(e.start // step_ticks) % bar_steps for e in cell_events}
    spots = [s for s in GHOST_SPOTS if s < bar_steps and s not in occupied]
    rng.shuffle(spots)
    take = max(1, round(len(spots) * density)) if spots else 0
    out = list(cell_events)
    for s in sorted(spots[:take]):
        out.append(Event(s * step_ticks, step_ticks // 2, ghost_note,
                         rng.randint(*vel_range), 9))
    return out


# ---------------------------------------------------------------- role-based feel
def _role(e):
    if e.channel == 9:
        if e.note in (35, 36):
            return "kick"
        if e.note in SNARE_NOTES or e.note == 39:
            return "snare"
        if e.note in (42, 44, 46):
            return "hats"
        return "perc"
    return "bass" if e.channel == 0 else "lead"


# per-role timing offsets in ms (+ = behind the beat, - = pushing) and a tiny
# per-hit human spread (sd ms). These relationships are the feel.
FEELS = {
    # deep head-nod: snare drags hard, bass sits behind the kick (Dilla/Purdie)
    "laidback": dict(kick=(0, 1.5), snare=(16, 3), hats=(5, 4), perc=(8, 4),
                     bass=(9, 3), lead=(12, 5)),
    # motorik/four-floor: hats drive ahead, everything else tight
    "pushing":  dict(kick=(0, 1), snare=(-2, 2), hats=(-7, 2.5), perc=(-4, 3),
                     bass=(0, 2), lead=(-3, 4)),
    # ceremonial/tribal: kick anchored, toms breathe wide, lead floats free
    "ritual":   dict(kick=(0, 2), snare=(8, 4), hats=(3, 5), perc=(12, 7),
                     bass=(6, 4), lead=(18, 9)),
    # machine: everything dead on the grid (contrast / electro)
    "machine":  dict(kick=(0, 0), snare=(0, 0), hats=(0, 0), perc=(0, 0),
                     bass=(0, 0), lead=(0, 0)),
}


def apply_feel(events, feel, bpm, ppq, rng, anchor_ticks=None):
    """Shift each event by its role's systematic offset + a small per-hit spread.
    Notes on the very first downbeat stay anchored at 0 (no dead space)."""
    spec = FEELS[feel]
    tick_ms = 60000.0 / (bpm * ppq)
    half_step = ppq // 8
    out = []
    for e in events:
        off_ms, sd_ms = spec[_role(e)]
        off = (off_ms + rng.gauss(0, sd_ms)) / tick_ms
        start = max(0, round(e.start + off))
        if e.start == 0:
            start = 0                      # beat 1 of the loop never moves
        elif anchor_ticks and e.start % anchor_ticks == 0 and _role(e) == "kick":
            start = e.start                # kicks on downbeats stay planted
        out.append(e._replace(start=start))
    return out


# ---------------------------------------------------------------- repetition + variation
def vary_cell(rng, cell, bar_steps=16, keep=0.7):
    """A varied restatement of a (onset, dur, pitch, vel) cell: everything before
    `keep` of the bar is IDENTICAL; the tail gets 1-2 small mutations. This is
    the B in AAAB -- recognisably the same thing, freshly said."""
    cut = bar_steps * keep
    head = [n for n in cell if n[0] < cut]
    tail = [list(n) for n in cell if n[0] >= cut]
    if not tail:                            # nothing after the cut: echo the last note up an octave
        if head:
            o, d, p, v = head[-1]
            tail = [[min(bar_steps - 1, o + d), max(1, d // 2), p + 12, max(1, v - 8)]]
        return head + [tuple(t) for t in tail]
    for _ in range(rng.randint(1, 2)):
        mut = rng.choice(("octave", "swap", "nudge", "split"))
        if mut == "octave":
            t = rng.choice(tail)
            t[2] += rng.choice((-12, 12))
            t[2] = min(120, max(24, t[2]))
        elif mut == "swap" and len(tail) >= 2:
            tail[-1][2], tail[-2][2] = tail[-2][2], tail[-1][2]
        elif mut == "nudge":
            t = tail[-1]
            if t[0] + 1 < bar_steps:
                t[0] += 1
                t[1] = max(1, min(t[1], bar_steps - t[0]))
        elif mut == "split" and tail[-1][1] >= 2:
            o, d, p, v = tail[-1]
            tail[-1] = [o, d // 2, p, v]
            tail.append([o + d // 2, d - d // 2, p, max(1, v - 10)])
    return head + [tuple(t) for t in sorted(tail)]


def vary_grids(rng, grids, bar_steps=16):
    """Drum-cell variation: flip 1-2 slots in the last quarter of the bar into
    hits (a small turnaround/fill) on a tom/snare-ish voice."""
    out = dict(grids)
    candidates = [v for v in grids if v not in ("chh", "ohh")] or list(grids)
    for _ in range(rng.randint(1, 2)):
        voice = rng.choice(candidates)
        g = list(out[voice])
        empt = [i for i in range(bar_steps * 3 // 4, bar_steps) if g[i] == "."]
        if empt:
            g[rng.choice(empt)] = "x"
            out[voice] = "".join(g)
    return out


def phrase_cells(rng, cell, plan="AAAB", bar_steps=16, keep=0.7):
    """Tile one cell into a phrase: A bars are IDENTICAL (that's the hook),
    B bars are vary_cell restatements, and a lower-case plan letter rests
    (silence -- the breath)."""
    b = None
    out = []
    for ch in plan:
        if ch == "A":
            out.append(list(cell))
        elif ch == "B":
            if b is None:
                b = vary_cell(rng, cell, bar_steps, keep)
            out.append(list(b))
        else:                               # '.' or lowercase: a breath bar
            out.append([])
    return out


def breathe(cell, bar_steps=16, gap=3, gate=0.85):
    """Give a melodic cell a breath: nothing sounds in the last `gap` steps of
    the bar, and every note's gate is shortened slightly so notes detach."""
    limit = bar_steps - gap
    out = []
    for (o, d, p, v) in cell:
        if o >= limit:
            continue
        d = min(d, limit - o)
        d = max(1, round(d * gate))
        out.append((o, d, p, v))
    return out


def cells_to_events(cells, step_ticks, bar_steps=16, channel=1):
    ev = []
    for bar_i, cell in enumerate(cells):
        base = bar_i * bar_steps * step_ticks
        for (o, d, p, v) in cell:
            ev.append(Event(base + o * step_ticks, d * step_ticks, p,
                            max(1, min(127, v)), channel))
    return ev
