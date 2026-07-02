#!/usr/bin/env python3
"""SOPHIA BEDS -- long, mix-and-match backing beds for impromptu singing.

Design (see SOPHIA_PLAN.md for the full rationale):
  * LONG: 40-56 bars (~2-3 min), shaped intro -> A -> lift -> A -> lift -> tail
    so the energy rises and thins and invites phrasing.
  * CLEAR VOCAL REGISTER: pads live below C4, arps above C5, bass in the
    basement -- the middle octave belongs to the singer.
  * LEARNABLE HARMONY: one 4-chord cycle per family, repeating every 4 bars,
    with nearest-inversion voice leading so the pad moves smoothly.
  * PITCH ANCHOR: each family ships a soft root drone stem for warming up.
  * MIX & MATCH: drums/bass/pad/arp/drone stems all share the family's key,
    tempo, and groove-engine feel; bed_full.mid is the ready mix.
  * 707-NATIVE drums (pads 36-51 only), reproducible from seed.

    python sophia.py    ->  output/sophia/<NN_Name_bpm_Key>/
"""

import os
import random
import shutil

import groove as G
import midiwriter
from midiwriter import Event
from rhythm import grid_from_hits
from theory import scale_degree

HERE = os.path.dirname(__file__)
DEST = os.path.join(HERE, "output", "sophia")
PPQ = midiwriter.PPQ
STEP = PPQ // 4
BAR = 16
BAR_T = BAR * STEP

# registers: keep the singer's octave (~C4-C5) free of busy movement
REG_BASS = (33, 50)
REG_PAD = (46, 59)     # pad tops out below C4 -- fully under the voice
REG_ARP = (74, 93)     # above C5
REG_DRONE = (36, 47)

FAMILIES = [
    # seed name        bpm root scale     chord cycle (scale degrees)  feel       pad arp bass
    (3101, "Ember",     72, 45, "aeolian", [0, 5, 2, 6],  "laidback", 4,  11, 38),   # A:  i VI III VII
    (3102, "Vesper",    64, 50, "dorian",  [0, 3, 0, 3],  "ritual",   16, 46, 33),   # D:  i IV vamp
    (3103, "Sable",     80, 43, "aeolian", [0, -1, -2, -3], "laidback", 48, 24, 32), # G:  lament descent
    (3104, "Aurora",    88, 48, "major",   [0, 4, 5, 3],  "laidback", 89, 10, 33),   # C:  I V vi IV
    (3105, "Nocturne",  68, 42, "aeolian", [0, -1, -2, -1], "ritual",  52, 108, 38), # F#: i VII VI VII
    (3106, "Solstice",  96, 50, "major",   [0, 4, 5, 3],  "pushing",  5,  12, 33),   # D:  I V vi IV
]

# drum cells per family character (pad-range voices only), 1 bar each
def _g(hits, accents=()):
    return grid_from_hits(BAR, set(hits), accents=set(accents))


BEATS = {
    "Ember":    dict(full={"36": _g([0, 6, 11], [0]), "38": _g([8], [8]), "42": _g([2, 5, 10, 13]), "44": _g([4, 12])},
                     lift_add={"46": _g([14])}),
    "Vesper":   dict(full={"36": _g([0, 8], [0]), "45": _g([3, 11]), "48": _g([6]), "37": _g([12])},
                     lift_add={"51": _g([0, 4, 8, 12])}),
    "Sable":    dict(full={"36": _g([0, 10], [0]), "38": _g([8], [8]), "42": _g([0, 2, 4, 6, 8, 10, 12, 14])},
                     lift_add={"46": _g([6])}),
    "Aurora":   dict(full={"36": _g([0, 4, 8, 12], [0]), "38": _g([4, 12]), "44": _g([2, 6, 10, 14])},
                     lift_add={"46": _g([14])}),
    "Nocturne": dict(full={"36": _g([0], [0]), "37": _g([10]), "44": _g([4, 12])},
                     lift_add={"45": _g([8])}),
    "Solstice": dict(full={"36": _g([0, 4, 8, 12], [0]), "38": _g([4, 12]), "42": _g([2, 6, 10, 14]), "44": _g([0, 8])},
                     lift_add={"46": _g([6, 14])}),
}
SPARSE = {"36": _g([0, 8], [0]), "44": _g([12])}


def voice_into(pitch, lo, hi):
    while pitch < lo:
        pitch += 12
    while pitch > hi:
        pitch -= 12
    return pitch


def triad(root, scale, degree, seventh=False):
    degs = (0, 2, 4, 6) if seventh else (0, 2, 4)
    return [scale_degree(root, scale, degree + d) for d in degs]


def lead_voicing(chord, prev, lo, hi):
    """Voice each chord tone into register, choosing octaves nearest the
    previous voicing (smooth pad movement -- no jumps to distract the singer)."""
    voiced = []
    for i, p in enumerate(chord):
        p = voice_into(p, lo, hi)
        if prev:
            target = prev[min(i, len(prev) - 1)]
            for cand in (p - 12, p, p + 12):
                if lo <= cand <= hi and abs(cand - target) < abs(p - target):
                    p = cand
        voiced.append(p)
    return voiced


def grids_events(grids, bar_i, vel_map=None):
    ev = []
    for note_s, grid in grids.items():
        note = int(note_s)
        vel = (vel_map or {}).get(note, {36: 106, 38: 96, 42: 72, 44: 62, 46: 84,
                                          45: 92, 48: 88, 37: 70, 51: 74}.get(note, 84))
        for i, ch in enumerate(grid):
            if ch in "xX":
                v = min(127, vel + (14 if ch == "X" else 0))
                ev.append(Event(bar_i * BAR_T + i * STEP, STEP, note, v, 9))
    return ev


def build_family(seed, name, bpm, root, scale, cycle, feel, pad_prog, arp_prog, bass_prog, index):
    rng = random.Random(seed)
    rounds = 2 if bpm < 88 else 3
    plan = [("intro", 2, "sparse")]
    for _ in range(rounds):
        plan += [("A", 8, "full"), ("lift", 8, "lift")]
    plan += [("tail", 6, "sparse")]
    total_bars = sum(n for _, n, _ in plan)

    beats = BEATS[name]
    full = beats["full"]
    lift_grids = {**full, **beats["lift_add"]}

    drums, bass, pad, arp, drone = [], [], [], [], []
    prev_voicing = None
    bar_i = 0
    tail_start = total_bars - 6

    for sec, n_bars, kind in plan:
        for b in range(n_bars):
            fade = 1.0
            if bar_i >= tail_start:
                fade = max(0.35, 1.0 - (bar_i - tail_start) * 0.12)

            # --- drums
            if kind == "sparse":
                drums += [e._replace(vel=max(1, round(e.vel * 0.8 * fade)))
                          for e in grids_events(SPARSE, bar_i)]
            else:
                grids = lift_grids if kind == "lift" else full
                if b == n_bars - 1:                     # section-end fill
                    grids = G.vary_grids(rng, grids)
                drums += grids_events(grids, bar_i)

            # --- harmony: the cycle runs in full/lift; sparse holds the tonic
            deg = cycle[b % len(cycle)] if kind != "sparse" else cycle[0]
            seventh = kind == "lift"                    # lift brightens with 7ths
            chord = triad(root, scale, deg, seventh=seventh)
            voiced = lead_voicing(chord, prev_voicing, *REG_PAD)
            prev_voicing = voiced
            pvel = round((58 if kind != "lift" else 64) * fade)
            for p in voiced:
                pad.append(Event(bar_i * BAR_T, BAR_T, p, max(1, pvel + rng.randint(-3, 3)), 2))

            # --- bass: root on 1, fifth answers -- gentle, chord-locked
            if kind != "sparse":
                broot = voice_into(scale_degree(root, scale, deg), *REG_BASS)
                bfifth = voice_into(scale_degree(root, scale, deg + 4), *REG_BASS)
                pat = [(0, 3, broot, 96), (8, 2, bfifth, 84), (11, 3, broot, 86)]
                if b % 4 == 3:
                    pat = [(o, d, voice_into(p, *REG_BASS), v)
                           for (o, d, p, v) in G.vary_cell(rng, pat)]
                for (o, d, p, v) in pat:
                    bass.append(Event(bar_i * BAR_T + o * STEP, d * STEP, p,
                                      max(1, round(v * fade)), 0))

            # --- arp: only in lifts, high and quiet (shimmer, not lead)
            if kind == "lift":
                tones = [voice_into(t, *REG_ARP) for t in triad(root, scale, deg, seventh=True)]
                order = sorted(tones) if b % 2 == 0 else sorted(tones, reverse=True)
                for k, o in enumerate(range(0, BAR, 2)):
                    arp.append(Event(bar_i * BAR_T + o * STEP, round(STEP * 1.6),
                                     order[k % len(order)],
                                     max(1, round((50 + (8 if k == 0 else 0)) * fade)), 3))

            # --- drone: the singer's pitch anchor, restruck every 2 bars
            if bar_i % 2 == 0:
                dro = voice_into(root, *REG_DRONE)
                drone.append(Event(bar_i * BAR_T, 2 * BAR_T, dro,
                                   max(1, round(46 * fade)), 4))
            bar_i += 1

    # groove pass: accents + one family feel across every stem (shared pocket)
    frng = random.Random(seed + 7)
    tsc = [(0, (4, 4))]
    drums = G.apply_accents(drums, STEP, depth=0.9)
    drums = G.apply_feel(drums, feel, bpm, PPQ, frng, anchor_ticks=BAR_T)
    bass = G.apply_feel(G.apply_accents(bass, STEP, depth=0.4), feel, bpm, PPQ, frng)
    arp = G.apply_feel(arp, feel, bpm, PPQ, frng)
    half = STEP // 2
    fix = lambda evs: [e._replace(start=0) if 0 <= e.start < half else e for e in evs]
    drums, bass, arp = fix(drums), fix(bass), fix(arp)

    key = f"{['C','Cs','D','Ds','E','F','Fs','G','Gs','A','As','B'][root % 12]}{'maj' if scale == 'major' else ('dor' if scale == 'dorian' else 'm')}"
    folder = os.path.join(DEST, f"{index:02d}_{name}_{bpm}_{key}")
    os.makedirs(folder, exist_ok=True)
    bpmc = [(0, bpm)]

    midiwriter.write_track(os.path.join(folder, "drums.mid"), drums, bpmc, tsc,
                           channel=9, track_name=f"{name}-drums")
    midiwriter.write_track(os.path.join(folder, "bass.mid"), bass, bpmc, tsc,
                           channel=0, program=bass_prog, track_name=f"{name}-bass")
    midiwriter.write_track(os.path.join(folder, "pad.mid"), pad, bpmc, tsc,
                           channel=2, program=pad_prog, track_name=f"{name}-pad")
    midiwriter.write_track(os.path.join(folder, "arp.mid"), arp, bpmc, tsc,
                           channel=3, program=arp_prog, track_name=f"{name}-arp")
    midiwriter.write_track(os.path.join(folder, "drone.mid"), drone, bpmc, tsc,
                           channel=4, program=89, track_name=f"{name}-drone")
    midiwriter.write_combined(
        os.path.join(folder, "bed_full.mid"),
        [{"events": drums, "channel": 9, "name": "drums"},
         {"events": bass, "channel": 0, "program": bass_prog, "name": "bass"},
         {"events": pad, "channel": 2, "program": pad_prog, "name": "pad"},
         {"events": arp, "channel": 3, "program": arp_prog, "name": "arp"},
         {"events": drone, "channel": 4, "program": 89, "name": "drone"}],
        bpmc, tsc)

    secs = total_bars * 4 * 60 / bpm
    return folder, total_bars, secs


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    print("SOPHIA BEDS -- singable backing, stems mix & match within a family")
    for i, fam in enumerate(FAMILIES, 1):
        folder, bars, secs = build_family(*fam, index=i)
        print(f"  {os.path.basename(folder):<22} {bars} bars  ~{int(secs//60)}:{int(secs%60):02d}")
    with open(os.path.join(DEST, "README.txt"), "w") as fh:
        fh.write(_README)
    print(f"-> {DEST}")


_README = """SOPHIA BEDS -- backing for impromptu singing
=============================================
Six families, each a key + tempo + mood + 4-chord cycle that repeats every
4 bars (learn it in one pass, then sing). Each bed runs ~2-3 minutes:
   intro (drone+pulse establishes the key) -> groove -> lift (arps, 7ths,
   brighter) -> groove -> lift -> tail (thins out for a final phrase).

  01_Ember_72_Am        i-VI-III-VII        warm Rhodes, head-nod
  02_Vesper_64_Ddor     i-IV vamp           organ, ceremonial toms
  03_Sable_80_Gm        lament descent      strings, halftime
  04_Aurora_88_Cmaj     I-V-vi-IV           warm pad, soft four-floor
  05_Nocturne_68_Fsm    i-VII-VI-VII        choir, very spare
  06_Solstice_96_Dmaj   I-V-vi-IV           e-piano, driving

STEMS (all share the family's key/tempo/feel -- stack any subset):
  bed_full.mid   the whole mix, ready to sing over
  drums.mid      707 pads 36-51 only, groove-engine feel
  bass.mid       chord roots + fifths, in the basement
  pad.mid        the chord cycle, voiced BELOW the vocal register with
                 smooth nearest-inversion voice leading
  arp.mid        high shimmer, ABOVE the vocal register, lifts only
  drone.mid      soft root anchor -- warm up to it, or keep it under all

THE SINGER'S OCTAVE (~C4-C5) IS EMPTY ON PURPOSE. Nothing melodic competes.

Stems are TIMELINE-ALIGNED with bed_full: drop any subset into the same
clip slots / DAW tracks and they line up. That means bass.mid starts after
the 2-bar intro and arp.mid waits for the first lift -- intentional, not a
glitch. drums / pad / drone all start on beat 1.

Repeat/extend: python sophia.py (seeded); add a family = one line in
FAMILIES (seed, name, bpm, root, scale, chord cycle, feel, programs).
"""


if __name__ == "__main__":
    main()
