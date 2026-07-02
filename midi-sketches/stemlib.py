#!/usr/bin/env python3
"""STEMLIB -- the whole building-block library: beats, percussion toppers,
basses, melodies, arps, and chord pads, as individual groove-engined loops.

Organization is BY TYPE (grab a bass, grab a beat), with compatibility built
in: every pitched stem lives in one of six KEY+TEMPO SLOTS -- the same six as
loopkit's families -- so anything from the same slot (and anything in loopkit's
matching family) stacks in key, in tempo, and in feel. Beats and percussion
are key-agnostic: match the BPM and go.

    stemlib/
      beats/       <feel>_<bpm>.mid              (707 pads 36-51, 4 bars ABAB')
      percussion/  <style>_<bpm>.mid             (toppers: layer over any beat)
      basses/      <style>_<Key>_<bpm>.mid
      melodies/    <style>_<Key>_<bpm>.mid
      arps/        <style>_<Key>_<bpm>.mid
      chords/      <cycle>_<Key>_<bpm>.mid
      INDEX.csv    sortable: type, style, key, scale, bpm, feel, file

Loop forms: cell-based material runs A B A B' (statement x2, varied turn);
process-based material (phase, additive, isorhythm, change-ringing, grounds)
runs its full 4-bar cycle -- the process IS the form. Everything: 16th-grid,
hit on beat 1, metric accents, role feel, seeded.

    python stemlib.py    ->  output/stemlib/   (~230 loops)
"""

import csv
import os
import random
import shutil
import zlib

import codex
import groove as G
import humanize
import loopkit as LK
import midiwriter
import palette as P
from midiwriter import Event
from rhythm import euclid_grid, euclidean_preset_tiled, grid_from_hits
from sophia import lead_voicing, voice_into
from theory import CHORDS, scale_degree

HERE = os.path.dirname(__file__)
DEST = os.path.join(HERE, "output", "stemlib")
PPQ = midiwriter.PPQ
STEP = PPQ // 4

REG_BASS, REG_MEL, REG_ARP, REG_CHORD = (33, 50), (60, 84), (72, 96), (46, 64)

# the six slots -- identical keys/tempos/feels to loopkit's families
SLOTS = [
    dict(key="Dm",    bpm=62,  root=50, scale="aeolian",  feel="laidback", mel_prog=5),
    dict(key="Fsphr", bpm=72,  root=54, scale="phrygian", feel="ritual",   mel_prog=89),
    dict(key="Edor",  bpm=84,  root=52, scale="dorian",   feel="laidback", mel_prog=4),
    dict(key="Am",    bpm=96,  root=45, scale="aeolian",  feel="laidback", mel_prog=11),
    dict(key="Cphr",  bpm=110, root=48, scale="phrygian", feel="pushing",  mel_prog=80),
    dict(key="Gm",    bpm=124, root=43, scale="aeolian",  feel="pushing",  mel_prog=81),
]

TEMPO_FEEL = {62: "laidback", 72: "ritual", 84: "laidback", 96: "laidback",
              110: "pushing", 124: "pushing", 54: "laidback", 66: "laidback",
              90: "ritual", 108: "ritual", 140: "pushing"}


# ---------------------------------------------------------------- pipelines
def _anchor(evs):
    half = STEP // 2
    return [e._replace(start=0) if 0 <= e.start < half else e for e in evs]


def loop2(events, bpm, bar_steps, feel, rng, kind, swung=False, breathe=False):
    """2-bar cell material -> 4-bar A B A B' with ghosts/accents/feel."""
    bar_t = bar_steps * STEP
    b1 = sorted(((e.start) // STEP, max(1, e.dur // STEP), e.note, e.vel)
                for e in events if e.start < bar_t)
    b2 = sorted(((e.start - bar_t) // STEP, max(1, e.dur // STEP), e.note, e.vel)
                for e in events if e.start >= bar_t) or b1
    ch = events[0].channel
    if kind == "drums":
        def cev(cell):
            return [Event(o * STEP, d * STEP, p, v, 9) for (o, d, p, v) in cell]
        c1 = G.apply_accents(G.add_ghosts(rng, cev(b1), STEP, bar_steps, density=0.4),
                             STEP, bar_steps)
        c2 = G.apply_accents(G.add_ghosts(rng, cev(b2), STEP, bar_steps, density=0.4),
                             STEP, bar_steps)
        occupied = {e.start // STEP for e in c2}
        c4 = list(c2)
        empt = [s for s in range(bar_steps * 3 // 4, bar_steps) if s not in occupied]
        rng.shuffle(empt)
        pool = [e.note for e in c2 if e.note not in (42, 44, 46)] or [38]
        for s in sorted(empt[: rng.randint(1, 2)]):
            c4.append(Event(s * STEP, STEP // 2, rng.choice(pool), rng.randint(70, 95), 9))
        bars = [c1, c2, c1, c4]
        out = [e._replace(start=e.start + i * bar_t) for i, cell in enumerate(bars) for e in cell]
        if swung:
            out = humanize.swing(out, STEP, swing_pct=humanize.sixteenth_swing_pct(bpm))
        return _anchor(G.apply_feel(out, feel, bpm, PPQ, rng, anchor_ticks=bar_t))
    if breathe:
        b1, b2 = G.breathe(b1, bar_steps), G.breathe(b2, bar_steps)
    # fold vary_cell's octave mutations back into the source cell's own range
    pitches = [p for cell in (b1, b2) for (_, _, p, _) in cell]
    lo, hi = min(pitches), max(pitches)
    def fold(p):
        while p > hi: p -= 12
        while p < lo: p += 12
        return p
    b4 = [(o, d, fold(p), v) for (o, d, p, v) in G.vary_cell(rng, b2, bar_steps)]
    cells = [b1, b2, b1, b4]
    out = G.cells_to_events(cells, STEP, bar_steps, channel=ch)
    out = G.apply_accents(out, STEP, bar_steps, depth=0.6)
    return _anchor(G.apply_feel(out, feel, bpm, PPQ, rng))


def flat(events, bpm, bar_steps, feel, rng, depth=0.5):
    """Process material already spanning its full form: accents + feel only."""
    out = G.apply_accents(events, STEP, bar_steps, depth=depth)
    return _anchor(G.apply_feel(out, feel, bpm, PPQ, rng))


def cell_ev(cell, channel, offset_steps=0):
    return [Event((o + offset_steps) * STEP, d * STEP, p, max(1, min(127, v)), channel)
            for (o, d, p, v) in cell]


# ---------------------------------------------------------------- beats
def _dg(spec, steps=16):
    return {int(k): grid_from_hits(steps, set(v)) for k, v in spec.items()}


def _dgev(grids, steps=16, bar=0):
    out = []
    VEL = {36: 106, 38: 96, 40: 90, 42: 74, 44: 62, 46: 84, 45: 92, 48: 88,
           41: 94, 37: 70, 51: 76, 39: 96, 43: 92, 47: 90, 50: 88}
    for note, grid in grids.items():
        for i, c in enumerate(grid):
            if c in "xX":
                out.append(Event((bar * steps + i) * STEP, STEP, note, VEL.get(note, 84), 9))
    return out


def two_bars(a, b=None, steps=16):
    return _dgev(a, steps, 0) + _dgev(b or a, steps, 1)


BEAT_DEFS = {
    # style: (tempos, bar_steps, swung, builder)
    "halftime":  ([62, 72, 84], 16, True,  lambda r: LK.beat_halftime(r)),
    "fourfloor": ([96, 110, 124], 16, False, lambda r: LK.beat_fourfloor(r)),
    "broken":    ([84, 96, 110], 16, False, lambda r: LK.beat_broken(r)),
    "tribal":    ([62, 72, 96], 16, False, lambda r: LK.beat_tribal(r)),
    "headnod":   ([84, 96], 16, True,  lambda r: LK.beat_headnod(r)),
    "motorik":   ([110, 124], 16, False, lambda r: LK.beat_motorik(r)),
    "dilla":     ([84, 96], 16, True, lambda r: two_bars(
        _dg({36: [0, 7, 10], 38: [8], 42: [0, 2, 4, 6, 8, 11, 12, 14]}),
        _dg({36: [0, 5, 10], 38: [8], 42: [0, 2, 4, 6, 8, 11, 12, 14]}))),
    "funk":      ([96, 110], 16, False, lambda r: two_bars(
        _dg({36: [0, 3, 10], 38: [4, 12], 42: [0, 2, 4, 6, 8, 10, 12, 14]}),
        _dg({36: [0, 3, 7, 10], 38: [4, 12], 42: [0, 2, 4, 6, 8, 10, 12, 14], 46: [14]}))),
    "gospel68":  ([54, 66], 12, False, lambda r: two_bars(
        _dg({36: [0], 38: [6], 42: [0, 2, 4, 6, 8, 10]}, 12),
        _dg({36: [0], 38: [6], 42: [0, 2, 4, 6, 8, 10], 46: [10]}, 12), 12)),
    "sarabande": ([90, 108], 12, False, lambda r: two_bars(
        _dg({36: [0], 48: [4], 37: [8], 44: [2, 6, 10]}, 12),
        _dg({36: [0], 48: [4], 37: [8], 44: [2, 6, 10], 45: [11]}, 12), 12)),
    "tresillo":  ([96, 110], 16, False, lambda r: two_bars(
        {36: euclidean_preset_tiled("tresillo", 16), 38: grid_from_hits(16, {4, 12}),
         44: grid_from_hits(16, set(range(0, 16, 2)))})),
    "samba":     ([96, 124], 16, False, lambda r: two_bars(
        {36: grid_from_hits(16, {0, 4, 8, 12}), 37: euclidean_preset_tiled("samba", 16),
         42: grid_from_hits(16, set(range(16)))})),
    "glitch":    ([110, 124], 16, False, lambda r: two_bars(
        {36: grid_from_hits(16, {0, 4, 8, 12}), 40: euclid_grid(5, 16, r.randint(1, 4)),
         42: euclid_grid(11, 16, 1)},
        {36: grid_from_hits(16, {0, 4, 8, 12}), 40: euclid_grid(5, 16, r.randint(1, 4)),
         42: euclid_grid(11, 16, 3), 46: grid_from_hits(16, {14})})),
    "trap":      ([70, 140], 16, True, lambda r: two_bars(
        _dg({36: [0, 10], 38: [8], 42: [0, 2, 4, 5, 6, 8, 10, 12, 13, 14]}),
        _dg({36: [0, 6, 10], 38: [8], 42: [0, 1, 2, 4, 6, 8, 10, 11, 12, 14]}))),
}

PERC_DEFS = {
    "euclid-toms": lambda r: two_bars({45: euclid_grid(3, 16, 0), 47: euclid_grid(5, 16, 1),
                                       50: euclid_grid(7, 16, 3)}),
    "shaker-top":  lambda r: two_bars({44: grid_from_hits(16, set(range(16))),
                                       46: grid_from_hits(16, {6, 14})}),
    "clave":       lambda r: two_bars({37: euclidean_preset_tiled("cinquillo", 16),
                                       40: grid_from_hits(16, {0, 8})}),
    "ride-bells":  lambda r: two_bars({51: grid_from_hits(16, set(range(0, 16, 2))),
                                       50: euclid_grid(5, 16, 2)}),
}


# ---------------------------------------------------------------- pitched builders
def bass_styles(rng, root, scale, bpm):
    """-> {style: (events, is_process)}"""
    fifth = scale_degree(root, scale, 4)
    out = {}
    out["ostinato"] = (LK.bass_ostinato(rng, root, scale), False)
    out["dronepulse"] = (LK.bass_dronepulse(rng, root, scale), False)
    out["angular"] = (LK.bass_angular(rng, root, scale), False)
    out["walking"] = (LK.bass_walk(rng, root, scale), False)
    for gname in ("lament", "folia", "pachelbel"):
        cell = codex.ground_bass(root, scale, gname, 64, register=REG_BASS)
        out[gname] = (cell_ev(cell, 0), True)
    r = voice_into(root, *REG_BASS)
    acid = []
    for bar in range(2):
        for i in range(16):
            if i in (3, 11):
                continue
            p = r + (12 if i in (6, 14) else 0)
            acid.append(Event((bar * 16 + i) * STEP, STEP, min(p, REG_BASS[1] + 12), 88, 0))
    out["acid16"] = (acid, False)
    dub = []
    for bar in range(2):
        dub += [Event(bar * 16 * STEP, 6 * STEP, r, 96, 0),
                Event((bar * 16 + 8) * STEP, 2 * STEP, r + 12 if r + 12 <= 55 else r, 78, 0),
                Event((bar * 16 + 12) * STEP, 4 * STEP, voice_into(fifth, *REG_BASS), 84, 0)]
    out["dub"] = (dub, False)
    pump = [Event((b * 16 + i) * STEP, 2 * STEP,
                  r if (i // 2) % 2 == 0 else voice_into(fifth, *REG_BASS),
                  86 + (12 if i == 0 else 0), 0)
            for b in range(2) for i in range(0, 16, 2)]
    out["pump"] = (pump, False)
    return out


def melody_styles(rng, root, scale, bpm):
    out = {}
    ante, cons = P.hook_phrase(rng, root, scale, REG_MEL)
    ante = LK._rebase(ante)
    out["hook"] = (cell_ev(ante, 1) + cell_ev(cons, 1, 16), False, True)
    cell = LK._rebase(P.ostinato_cell(rng, root, scale, (62, 84), vel_base=92))
    out["cell"] = (cell_ev(cell, 1) + cell_ev(cell, 1, 16), False, False)
    for name, fn in (("phase", P.phase_melody), ("additive", P.additive_phase_melody)):
        bars = fn(rng, root, scale, 4)
        ev = []
        for bi, bar in enumerate(bars):
            for (o, d, p, v) in bar:
                ev.append(Event((bi * 16 + o) * STEP, d * STEP,
                                P.clamp_register(p + 12, *REG_MEL), v, 1))
        out[name] = (ev, True, False)
    color = [0, rng.choice([1, 2]), rng.choice([3, 4]), 2, rng.choice([5, 7])]
    talea = rng.choice([[3, 3, 2], [4, 2, 3, 5, 2], [3, 2, 3]])
    out["isorhythm"] = (cell_ev(codex.isorhythm(root, scale, color, talea, 64, REG_MEL), 1),
                        True, False)
    out["ringing"] = (cell_ev(codex.change_ring(root, scale, 4, 64, REG_MEL), 1), True, False)
    m = P.motif_scored(rng, 5, root, scale)
    dev = []
    for bi, mm in enumerate((m, P.motif_invert(m), P.motif_retrograde(m), m)):
        shift = 2 if bi == 3 else 0
        dev += P.render_motif(rng, mm, root, scale, bi * 16, degree_shift=shift,
                              register=REG_MEL, vel_base=92)
    out["motifdev"] = (cell_ev(dev, 1), True, False)
    walk = P.scale_walk(rng, 0, 6, leap_prob=0.2)
    penta = [(i * 2, 2, P.clamp_register(scale_degree(root, "minor_pentatonic", d), *REG_MEL),
              90 + rng.randint(-6, 6)) for i, d in enumerate(walk)]
    out["penta"] = (cell_ev(penta, 1) + cell_ev(penta, 1, 16), False, True)
    return out


def arp_styles(rng, root, scale, bpm):
    out = {}
    ch5 = P.spread_chord(root, scale, (0, 2, 4, 6, 7))
    out["drift16"] = (cell_ev(P.arpeggiate(rng, ch5, 32, 1, "up", REG_ARP, gate=0.85), 1), False)
    ch4 = P.spread_chord(root, scale, (0, 2, 4, 6))
    out["updown8"] = (cell_ev(P.arpeggiate(rng, ch4, 32, 2, "updown", REG_ARP, gate=0.9), 1), False)
    out["random8"] = (cell_ev(P.arpeggiate(rng, ch4, 32, 2, "random", REG_ARP,
                                           gate=0.6, accent_every=8), 1), False)
    q = [voice_into(root + s, *REG_ARP) for s in (0, 5, 10, 15, 20)]
    out["quartal"] = (cell_ev(P.arpeggiate(rng, q, 32, 2, "up", REG_ARP, gate=0.85), 1), False)
    ped = []
    tones = [voice_into(scale_degree(root, scale, d), *REG_ARP) for d in (2, 4, 7)]
    low = voice_into(root, *REG_ARP)
    for i in range(16):
        p = low if i % 2 == 0 else tones[(i // 2) % 3]
        ped.append((i * 2, 2, p, 78 + (10 if i % 8 == 0 else 0)))
    out["pedal"] = (cell_ev([(o, d, p, v) for (o, d, p, v) in ped], 1), False)
    roll = P.arpeggiate(rng, list(reversed(ch4)), 32, 4, "down", REG_ARP, gate=1.0, vel_base=70)
    out["roll"] = (cell_ev(roll, 1), False)
    return out


CHORD_CYCLES = {
    "pop":     [0, 5, 2, 6],
    "lament":  [0, -1, -2, -3],
    "sus":     [(0, "sus4"), (-2, "sus2"), (5, "sus4"), (0, "sus2")],
    "quartal": [(0, "q4"), (-2, "q4"), (3, "q4"), (0, "q4")],
}


def chord_events(rng, root, scale, cycle):
    ev, prev = [], None
    for bar, spec in enumerate(cycle):
        if isinstance(spec, tuple):
            semis, qual = spec
            chord = [root + semis + iv for iv in CHORDS[qual]]
        else:
            chord = [scale_degree(root, scale, spec + d) for d in (0, 2, 4)]
        voiced = lead_voicing(chord, prev, *REG_CHORD)
        prev = voiced
        for p in voiced:
            ev.append(Event(bar * 16 * STEP, 16 * STEP, p, 62 + rng.randint(-3, 3), 2))
    return ev


# ---------------------------------------------------------------- build
def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    for d in ("beats", "percussion", "basses", "melodies", "arps", "chords"):
        os.makedirs(os.path.join(DEST, d))
    rows = []

    def write(sub, fname, events, bpm, meter, channel, program, style, key="--", scale="--", feel="--"):
        path = os.path.join(DEST, sub, fname)
        midiwriter.write_track(path, events, [(0, bpm)], [(0, meter)],
                               channel=channel, program=program, track_name=fname[:-4])
        bars = 4
        rows.append([f"{sub}/{fname}", sub, style, key, scale, bpm, feel])

    for style, (tempos, steps, swung, fn) in BEAT_DEFS.items():
        meter = (4, 4) if steps == 16 else ((6, 8) if style == "gospel68" else (3, 4))
        for bpm in tempos:
            rng = random.Random(zlib.crc32(f"{style}|{bpm}".encode()))
            feel = TEMPO_FEEL.get(bpm, "laidback")
            ev = loop2(fn(rng), bpm, steps, feel, rng, "drums", swung=swung)
            write("beats", f"{style}_{bpm}.mid", ev, bpm, meter, 9, None, style, feel=feel)

    for style, fn in PERC_DEFS.items():
        for bpm in (62, 72, 84, 96, 110, 124):
            rng = random.Random(zlib.crc32(f"{style}|{bpm}".encode()))
            feel = TEMPO_FEEL[bpm]
            ev = loop2(fn(rng), bpm, 16, feel, rng, "drums")
            write("percussion", f"{style}_{bpm}.mid", ev, bpm, (4, 4), 9, None, style, feel=feel)

    for slot in SLOTS:
        key, bpm, root, scale, feel = slot["key"], slot["bpm"], slot["root"], slot["scale"], slot["feel"]
        rng = random.Random(zlib.crc32(f"bass|{key}".encode()))
        for style, (ev, proc) in bass_styles(rng, root, scale, bpm).items():
            done = flat(ev, bpm, 16, feel, rng) if proc else loop2(ev, bpm, 16, feel, rng, "bass")
            write("basses", f"{style}_{key}_{bpm}.mid", done, bpm, (4, 4), 0, 38, style, key, scale, feel)
        rng = random.Random(zlib.crc32(f"mel|{key}".encode()))
        for style, (ev, proc, br) in melody_styles(rng, root, scale, bpm).items():
            done = flat(ev, bpm, 16, feel, rng) if proc else loop2(ev, bpm, 16, feel, rng, "mel", breathe=br)
            write("melodies", f"{style}_{key}_{bpm}.mid", done, bpm, (4, 4), 1, slot["mel_prog"],
                  style, key, scale, feel)
        rng = random.Random(zlib.crc32(f"arp|{key}".encode()))
        for style, (ev, proc) in arp_styles(rng, root, scale, bpm).items():
            done = flat(ev, bpm, 16, feel, rng, depth=0.4)
            write("arps", f"{style}_{key}_{bpm}.mid", done, bpm, (4, 4), 1, slot["mel_prog"],
                  style, key, scale, feel)
        rng = random.Random(zlib.crc32(f"chords|{key}".encode()))
        for cname, cycle in CHORD_CYCLES.items():
            ev = flat(chord_events(rng, root, scale, cycle), bpm, 16, feel, rng, depth=0.3)
            write("chords", f"{cname}_{key}_{bpm}.mid", ev, bpm, (4, 4), 2, 89,
                  cname, key, scale, feel)

    with open(os.path.join(DEST, "INDEX.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "type", "style", "key", "scale", "bpm", "feel"])
        w.writerows(rows)
    with open(os.path.join(DEST, "README.txt"), "w") as fh:
        fh.write(__doc__)

    from collections import Counter
    c = Counter(r[1] for r in rows)
    for t, n in sorted(c.items()):
        print(f"  {t:<12} {n:>3}")
    print(f"{len(rows)} stems -> {DEST}")


if __name__ == "__main__":
    main()
