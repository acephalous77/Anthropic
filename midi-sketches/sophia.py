#!/usr/bin/env python3
"""SOPHIA BEDS -- long, mix-and-match backing beds for impromptu singing.

Design (see SOPHIA_PLAN.md for the full rationale):
  * LONG: ~2-3 min, shaped intro -> A -> lift -> A -> lift -> tail
    so the energy rises and thins and invites phrasing.
  * CLEAR VOCAL REGISTER: pads live below C4, arps above C5, bass in the
    basement -- the middle octave belongs to the singer.
  * LEARNABLE HARMONY: one chord cycle per family, repeating every few bars,
    with nearest-inversion voice leading so the pad moves smoothly.
  * PITCH ANCHOR: each family ships a soft root drone stem for warming up.
  * MIX & MATCH: stems share the family's key/tempo/feel; timeline-aligned.
  * 707-NATIVE drums (pads 36-51 only), reproducible from seed.

Volume 2 (families 07-14) adds what a singer misses in vol. 1:
  * 6/8 gospel sway (Cradle) and a 3/4 La Folia ground (Folia) -- the first
    compound/triple meters in the collection; the triple lilt rocks a voice.
  * sus-chord harmony with NO thirds (Quarry): the singer decides whether the
    music is major or minor -- the bed asks, the melody answers.
  * the Andalusian cadence with real major chords via chromatic chord specs
    (Duende): Am-G-F-E, flamenco's pull-to-resolution.
  * call-and-response trading (Trade): every 3rd+4th bar the band drops to
    drums+drone -- her answer space, built into the form.
  * a rubato bed with no drums at all (Vigil): pads breathing in F lydian,
    chords changing every 2 bars, for singing outside meter.
  * a key-area journey (Ascent): the same chords reordered each round so the
    tonal center lifts from A minor to C major and back -- a built-in bridge.
  * a mixolydian folk vamp (Reel): I-bVII-IV-I under an accordion.

    python sophia.py    ->  output/sophia/<NN_Name_bpm_Key>/
"""

import os
import random
import shutil

import groove as G
import midiwriter
from midiwriter import Event
from rhythm import grid_from_hits
from theory import CHORDS, scale_degree

HERE = os.path.dirname(__file__)
DEST = os.path.join(HERE, "output", "sophia")
PPQ = midiwriter.PPQ
STEP = PPQ // 4

# registers: keep the singer's octave (~C4-C5) free of busy movement
REG_BASS = (33, 50)
REG_PAD = (46, 59)     # pad tops out below C4 -- fully under the voice
REG_ARP = (74, 93)     # above C5
REG_DRONE = (36, 47)


def F(seed, name, bpm, root, scale, cycle, feel, pad, arp, bass, **kw):
    d = dict(seed=seed, name=name, bpm=bpm, root=root, scale=scale, cycle=cycle,
             feel=feel, pad_prog=pad, arp_prog=arp, bass_prog=bass,
             meter=(4, 4), rounds=None, trade_spec=None, trade_by_round=None,
             rubato=False, cycles_by_round=None, chord_per=1, has_drums=True,
             call=False, call_prog=42)
    d.update(kw)
    return d


FAMILIES = [
    # -------- volume 1 (unchanged output; verified byte-identical) --------
    F(3101, "Ember",    72, 45, "aeolian", [0, 5, 2, 6],    "laidback", 4,  11, 38),   # A:  i VI III VII
    F(3102, "Vesper",   64, 50, "dorian",  [0, 3, 0, 3],    "ritual",   16, 46, 33),   # D:  i IV vamp
    F(3103, "Sable",    80, 43, "aeolian", [0, -1, -2, -3], "laidback", 48, 24, 32),   # G:  lament descent
    F(3104, "Aurora",   88, 48, "major",   [0, 4, 5, 3],    "laidback", 89, 10, 33),   # C:  I V vi IV
    F(3105, "Nocturne", 68, 42, "aeolian", [0, -1, -2, -1], "ritual",   52, 108, 38),  # F#: i VII VI VII
    F(3106, "Solstice", 96, 50, "major",   [0, 4, 5, 3],    "pushing",  5,  12, 33),   # D:  I V vi IV
    # -------- volume 2 --------
    F(3107, "Cradle",   54, 43, "major",   [0, 3, 0, 4],    "laidback", 19, 46, 32,
      meter=(6, 8)),                                        # G: I IV I V, gospel 6/8 sway
    F(3108, "Duende",   76, 45, "aeolian",                  # A: Am G F E -- Andalusian cadence,
      [0, (-2, "maj"), (-4, "maj"), (-5, "maj")], "ritual", 48, 24, 32),  # real major chords
    F(3109, "Quarry",   66, 50, "major",                    # D: sus chords, NO thirds --
      [(0, "sus4"), (-2, "sus2"), (5, "sus4"), (0, "sus2")], "laidback", 89, 10, 38),
    F(3110, "Folia",    96, 50, "aeolian", [0, -3, 0, -1, 2, -1, 0, -3], "ritual", 48, 6, 32,
      meter=(3, 4), rounds=4),                                        # D: La Folia ground, sarabande 3/4
    F(3111, "Reel",     84, 50, "mixolydian", [0, -1, 3, 0], "laidback", 21, 25, 32),  # D: I bVII IV I
    F(3112, "Trade",    92, 48, "dorian",  [0, 3, 0, 3],    "laidback", 4,  11, 33,
      trade_spec=(4, (2, 3))),                              # C: neo-soul, band drops bars 3-4
    F(3113, "Vigil",    56, 53, "lydian",  [0, 1],          "ritual",   95, 46, 42,
      rubato=True, has_drums=False, chord_per=2),           # F: no drums, chords float 2-bar
    F(3114, "Ascent",   80, 45, "aeolian", [0, 5, 2, 6],    "laidback", 50, 98, 38,
      rounds=3, cycles_by_round=[[0, 5, 2, 6], [2, 6, 0, 5], [0, 5, 2, 6]]),
    # Ascent: round 2 reorders the SAME chords so C major becomes home -- a bridge.
    # -------- volume 3: The Dialogue (ambiguity + silence, then fused) --------
    F(3115, "Aperture", 72, 52, "dorian",                   # E: quartal stacks -- the 'So What'
      [(0, "q4"), (-2, "q4"), (3, "q4"), (0, "q4")], "laidback", 4, 11, 33),  # rootless openness
    F(3116, "Hollow",   62, 43, "aeolian",                  # G: open fifths ONLY -- maximal
      [(0, "5"), (-4, "5"), (-2, "5"), (0, "5")], "ritual", 48, 46, 32,       # ambiguity, organum tone
      chord_per=2),
    F(3117, "Antiphon", 76, 45, "dorian", [0, 3, 0, -1],    # A: a low cantor phrase calls
      "ritual", 19, 46, 32, call=True),                     # (bars 1-2), she answers (bars 3-4)
    F(3118, "Sparring", 100, 41, "dorian", [0, 3, 0, 3],    # F: 1-bar trades -- band, her,
      "laidback", 4, 11, 33, trade_spec=(2, (1,))),         # band, her. Quick reflexes.
    F(3119, "Yield",    84, 45, "dorian", [0, 3, 4, 0],     # A: the gaps GROW round by round:
      "laidback", 4, 11, 33, rounds=3,                      # 1 bar, then 2, then 3 of every 4
      trade_by_round=[(4, (3,)), (4, (2, 3)), (4, (1, 2, 3))]),
    F(3120, "Oracle",   78, 52, "major",                    # E: the fusion -- thirdless harmony
      [(0, "sus4"), (-2, "sus2"), (5, "sus4"), (0, "q4")],  # AND trading silence at once
      "ritual", 95, 10, 38, trade_spec=(4, (2, 3))),
]


def _g(hits, accents=(), steps=16):
    return grid_from_hits(steps, set(hits), accents=set(accents))


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
    # vol. 2 -- Cradle/Folia cells are 12 steps (6/8 and 3/4)
    "Cradle":   dict(full={"36": _g([0], [0], 12), "38": _g([6], [6], 12), "42": _g([0, 2, 4, 6, 8, 10], (), 12)},
                     lift_add={"51": _g([0, 3, 6, 9], (), 12)}),
    "Folia":    dict(full={"36": _g([0], [0], 12), "48": _g([4], [4], 12), "37": _g([8], (), 12), "44": _g([2, 6, 10], (), 12)},
                     lift_add={"51": _g([0, 4, 8], (), 12)}),
    "Duende":   dict(full={"36": _g([0, 8], [0]), "37": _g([3, 7, 11, 14]), "48": _g([12]), "44": _g([2, 6, 10])},
                     lift_add={"46": _g([14]), "45": _g([10])}),
    "Quarry":   dict(full={"36": _g([0, 10], [0]), "37": _g([8]), "44": _g([4, 12])},
                     lift_add={"42": _g([2, 6, 10, 14])}),
    "Reel":     dict(full={"36": _g([0, 8], [0]), "38": _g([4, 12]), "42": _g([0, 2, 4, 6, 8, 10, 12, 14])},
                     lift_add={"46": _g([6, 14])}),
    "Trade":    dict(full={"36": _g([0, 7, 10], [0]), "38": _g([4, 12], [12]), "42": _g([0, 2, 3, 6, 8, 10, 11, 14])},
                     lift_add={"46": _g([14])}),
    "Ascent":   dict(full={"36": _g([0, 8], [0]), "38": _g([4, 12]), "42": _g([0, 2, 4, 6, 8, 10, 12, 14])},
                     lift_add={"46": _g([6])}),
    # vol. 3
    "Aperture": dict(full={"36": _g([0, 10], [0]), "51": _g([0, 2, 4, 6, 8, 10, 12, 14], [0, 8]), "37": _g([4, 12])},
                     lift_add={"46": _g([14])}),
    "Hollow":   dict(full={"36": _g([0, 8], [0]), "41": _g([0], [0]), "46": _g([14])},
                     lift_add={"51": _g([0, 4, 8, 12])}),
    "Antiphon": dict(full={"36": _g([0, 8], [0]), "44": _g([4, 12]), "37": _g([6, 14])},
                     lift_add={"42": _g([0, 2, 4, 6, 8, 10, 12, 14])}),
    "Sparring": dict(full={"36": _g([0, 7, 10], [0]), "38": _g([4, 12], [12]), "42": _g([0, 2, 3, 4, 6, 8, 10, 11, 12, 14])},
                     lift_add={"46": _g([14])}),
    "Yield":    dict(full={"36": _g([0, 8], [0]), "38": _g([4, 12]), "42": _g([0, 2, 4, 6, 8, 10, 12, 14])},
                     lift_add={"46": _g([6, 14])}),
    "Oracle":   dict(full={"36": _g([0, 10], [0]), "45": _g([7]), "48": _g([12]), "44": _g([4, 12])},
                     lift_add={"42": _g([2, 6, 10, 14])}),
}
SPARSE_BY = {16: {"36": _g([0, 8], [0]), "44": _g([12])},
             12: {"36": _g([0, 6], [0], 12), "44": _g([9], (), 12)}}


def voice_into(pitch, lo, hi):
    while pitch < lo:
        pitch += 12
    while pitch > hi:
        pitch -= 12
    return pitch


def triad(root, scale, degree, seventh=False):
    degs = (0, 2, 4, 6) if seventh else (0, 2, 4)
    return [scale_degree(root, scale, degree + d) for d in degs]


def chord_of(root, scale, spec, seventh=False):
    """spec: scale degree (int, diatonic triad) OR (semitones, quality) for a
    chromatic chord -- how Duende gets its real E major inside A minor, and
    Quarry its thirdless sus voicings."""
    if isinstance(spec, tuple):
        semis, quality = spec
        return [root + semis + iv for iv in CHORDS[quality]]
    return triad(root, scale, spec, seventh)


def chord_root_fifth(root, scale, spec):
    if isinstance(spec, tuple):
        semis, _ = spec
        return root + semis, root + semis + 7
    return scale_degree(root, scale, spec), scale_degree(root, scale, spec + 4)


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


def grids_events(grids, bar_i, bar_t, vel_map=None):
    ev = []
    for note_s, grid in grids.items():
        note = int(note_s)
        vel = (vel_map or {}).get(note, {36: 106, 38: 96, 42: 72, 44: 62, 46: 84,
                                          45: 92, 48: 88, 37: 70, 51: 74}.get(note, 84))
        for i, ch in enumerate(grid):
            if ch in "xX":
                v = min(127, vel + (14 if ch == "X" else 0))
                ev.append(Event(bar_i * bar_t + i * STEP, STEP, note, v, 9))
    return ev


def build_plan(fam):
    cycle = fam["cycle"]
    if fam["rubato"]:
        return [("intro", 2, "sparse", cycle, None), ("flow", 12, "rubato", cycle, None),
                ("swell", 8, "rubato_lift", cycle, None), ("flow2", 12, "rubato", cycle, None),
                ("tail", 6, "sparse", cycle, None)]
    rounds = fam["rounds"] or (2 if fam["bpm"] < 88 else 3)
    cbr = fam["cycles_by_round"] or [cycle] * rounds
    tbr = fam["trade_by_round"]
    plan = [("intro", 2, "sparse", cbr[0], None)]
    for r in range(rounds):
        cyc = cbr[r % len(cbr)]
        gaps = tbr[r % len(tbr)] if tbr else fam["trade_spec"]
        plan += [(f"A{r}", 8, "full", cyc, gaps), (f"lift{r}", 8, "lift", cyc, None)]
    plan += [("tail", 6, "sparse", cbr[-1], None)]
    return plan


BASS_PATTERNS = {16: ((0, 3), (8, 2), (11, 3)), 12: ((0, 3), (6, 2), (9, 3))}


def build_family(fam, index):
    seed, name, bpm = fam["seed"], fam["name"], fam["bpm"]
    root, scale, feel = fam["root"], fam["scale"], fam["feel"]
    meter = fam["meter"]
    bar_steps = meter[0] * 16 // meter[1]
    bar_t = bar_steps * STEP
    rng = random.Random(seed)

    plan = build_plan(fam)
    total_bars = sum(n for _, n, *_ in plan)
    tail_start = total_bars - 6

    beats = BEATS.get(name, {})
    full = beats.get("full", {})
    lift_grids = {**full, **beats.get("lift_add", {})}
    sparse = SPARSE_BY[bar_steps]

    drums, bass, pad, arp, drone, call = [], [], [], [], [], []
    call_cells = None
    if fam["call"]:
        import palette as P
        call_cells = P.hook_phrase(rng, root, scale, (48, 58), vel_base=76)
    prev_voicing = None
    bar_i = 0

    for sec, n_bars, kind, cycle, gaps in plan:
        for b in range(n_bars):
            fade = 1.0
            if bar_i >= tail_start:
                fade = max(0.35, 1.0 - (bar_i - tail_start) * 0.12)
            trading = gaps is not None and (b % gaps[0]) in gaps[1]

            # the cantor: a low call phrase in bars 1-2 of each 4; 3-4 are hers
            if call_cells and kind == "full" and b % 4 in (0, 1):
                cell = call_cells[b % 4]
                for (o, d, p, v) in cell:
                    call.append(Event(bar_i * bar_t + o * STEP, d * STEP, p,
                                      max(1, round(v * fade)), 5))

            # --- drums
            if fam["has_drums"]:
                if kind in ("sparse",):
                    drums += [e._replace(vel=max(1, round(e.vel * 0.8 * fade)))
                              for e in grids_events(sparse, bar_i, bar_t)]
                elif kind in ("full", "lift"):
                    grids = lift_grids if kind == "lift" else full
                    if b == n_bars - 1:                     # section-end fill
                        grids = G.vary_grids(rng, grids, bar_steps)
                    drums += grids_events(grids, bar_i, bar_t)

            # --- harmony: cycle runs in full/lift/rubato; sparse holds home
            ci = (b // fam["chord_per"]) % len(cycle)
            spec = cycle[ci] if kind != "sparse" else cycle[0]
            seventh = kind == "lift"                        # lifts brighten with 7ths
            chord = chord_of(root, scale, spec, seventh=seventh)

            if kind in ("rubato", "rubato_lift"):
                if bar_i % 2 == 0:                          # chords float, 2 bars each
                    voiced = lead_voicing(chord, prev_voicing, *REG_PAD)
                    prev_voicing = voiced
                    for p in voiced:
                        pad.append(Event(bar_i * bar_t, 2 * bar_t, p,
                                         max(1, round(56 * fade) + rng.randint(-3, 3)), 2))
                    broot, _ = chord_root_fifth(root, scale, spec)
                    bass.append(Event(bar_i * bar_t, 2 * bar_t,
                                      voice_into(broot, *REG_BASS), max(1, round(54 * fade)), 0))
                if kind == "rubato_lift":                   # sparse high shimmer
                    tones = sorted(voice_into(t, *REG_ARP) for t in chord)
                    for k, o in enumerate(range(0, bar_steps, 4)):
                        arp.append(Event(bar_i * bar_t + o * STEP, 3 * STEP,
                                         tones[k % len(tones)], max(1, round(44 * fade)), 3))
            elif not trading:
                voiced = lead_voicing(chord, prev_voicing, *REG_PAD)
                prev_voicing = voiced
                pvel = round((58 if kind != "lift" else 64) * fade)
                for p in voiced:
                    pad.append(Event(bar_i * bar_t, bar_t,
                                     p, max(1, pvel + rng.randint(-3, 3)), 2))

                # --- bass: root on 1, fifth answers -- gentle, chord-locked
                if kind != "sparse":
                    br, bf = chord_root_fifth(root, scale, spec)
                    broot = voice_into(br, *REG_BASS)
                    bfifth = voice_into(bf, *REG_BASS)
                    (o1, d1), (o2, d2), (o3, d3) = BASS_PATTERNS[bar_steps]
                    pat = [(o1, d1, broot, 96), (o2, d2, bfifth, 84), (o3, d3, broot, 86)]
                    if b % 4 == 3:
                        pat = [(o, d, voice_into(p, *REG_BASS), v)
                               for (o, d, p, v) in G.vary_cell(rng, pat, bar_steps)]
                    for (o, d, p, v) in pat:
                        bass.append(Event(bar_i * bar_t + o * STEP, d * STEP, p,
                                          max(1, round(v * fade)), 0))

                # --- arp: only in lifts, high and quiet (shimmer, not lead)
                if kind == "lift":
                    tones = [voice_into(t, *REG_ARP)
                             for t in chord_of(root, scale, spec, seventh=True)]
                    order = sorted(tones) if b % 2 == 0 else sorted(tones, reverse=True)
                    for k, o in enumerate(range(0, bar_steps, 2)):
                        arp.append(Event(bar_i * bar_t + o * STEP, round(STEP * 1.6),
                                         order[k % len(order)],
                                         max(1, round((50 + (8 if k == 0 else 0)) * fade)), 3))

            # --- drone: the singer's pitch anchor, restruck every 2 bars
            if bar_i % 2 == 0:
                drone.append(Event(bar_i * bar_t, 2 * bar_t, voice_into(root, *REG_DRONE),
                                   max(1, round(46 * fade)), 4))
            bar_i += 1

    # groove pass: accents + one family feel across every stem (shared pocket)
    frng = random.Random(seed + 7)
    tsc = [(0, meter)]
    if drums:
        drums = G.apply_accents(drums, STEP, bar_steps=bar_steps, depth=0.9)
        drums = G.apply_feel(drums, feel, bpm, PPQ, frng, anchor_ticks=bar_t)
    bass = G.apply_feel(G.apply_accents(bass, STEP, bar_steps=bar_steps, depth=0.4),
                        feel, bpm, PPQ, frng)
    arp = G.apply_feel(arp, feel, bpm, PPQ, frng)
    call = G.apply_feel(call, feel, bpm, PPQ, frng) if call else call
    half = STEP // 2
    fix = lambda evs: [e._replace(start=0) if 0 <= e.start < half else e for e in evs]
    drums, bass, arp, call = fix(drums), fix(bass), fix(arp), fix(call)

    qual = {"major": "maj", "dorian": "dor", "mixolydian": "mix", "lydian": "lyd"}.get(scale, "m")
    key = f"{['C','Cs','D','Ds','E','F','Fs','G','Gs','A','As','B'][root % 12]}{qual}"
    mtag = "" if meter == (4, 4) else f"_{meter[0]}-{meter[1]}"
    folder = os.path.join(DEST, f"{index:02d}_{name}_{bpm}_{key}{mtag}")
    os.makedirs(folder, exist_ok=True)
    bpmc = [(0, bpm)]

    stems = [("drums.mid", drums, 9, None), ("bass.mid", bass, 0, fam["bass_prog"]),
             ("pad.mid", pad, 2, fam["pad_prog"]), ("arp.mid", arp, 3, fam["arp_prog"]),
             ("call.mid", call, 5, fam["call_prog"]), ("drone.mid", drone, 4, 89)]
    tracks = []
    for fname, evs, ch, prog in stems:
        if not evs:
            continue
        midiwriter.write_track(os.path.join(folder, fname), evs, bpmc, tsc,
                               channel=ch, program=prog,
                               track_name=f"{name}-{fname.split('.')[0]}")
        tracks.append({"events": evs, "channel": ch, "program": prog,
                       "name": fname.split(".")[0]})
    midiwriter.write_combined(os.path.join(folder, "bed_full.mid"), tracks, bpmc, tsc)

    secs = total_bars * bar_t / PPQ * 60 / bpm
    return folder, total_bars, secs


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    print("SOPHIA BEDS -- singable backing, stems mix & match within a family")
    for i, fam in enumerate(FAMILIES, 1):
        folder, bars, secs = build_family(fam, i)
        print(f"  {os.path.basename(folder):<26} {bars} bars  ~{int(secs//60)}:{int(secs%60):02d}")
    with open(os.path.join(DEST, "README.txt"), "w") as fh:
        fh.write(_README)
    print(f"-> {DEST}")


_README = """SOPHIA BEDS -- backing for impromptu singing
=============================================
Fourteen families, each a key + tempo + mood + chord cycle that repeats
(learn it in one pass, then sing). Beds run ~2-3 minutes:
   intro (drone+pulse establishes the key) -> groove -> lift (arps, 7ths,
   brighter) -> groove -> lift -> tail (thins out for a final phrase).

VOLUME 1
  01_Ember_72_Am        i-VI-III-VII        warm Rhodes, head-nod
  02_Vesper_64_Ddor     i-IV vamp           organ, ceremonial toms
  03_Sable_80_Gm        lament descent      strings, halftime
  04_Aurora_88_Cmaj     I-V-vi-IV           warm pad, soft four-floor
  05_Nocturne_68_Fsm    i-VII-VI-VII        choir, very spare
  06_Solstice_96_Dmaj   I-V-vi-IV           e-piano, driving

VOLUME 2 -- new shapes a singer can lean on
  07_Cradle_54_Gmaj_6-8   I-IV-I-V in 6/8: the gospel sway. Triple meter
                          rocks the voice; church organ, harp lifts.
  08_Duende_76_Am         the Andalusian cadence Am-G-F-E with REAL major
                          chords: flamenco's pull. Palmas rims, strings.
  09_Quarry_66_Dsus       sus chords only -- NO thirds anywhere. The bed
                          never says major or minor; the singer decides.
  10_Folia_96_Dm_3-4      La Folia -- the ground Renaissance musicians
                          improvised over for 300 years. Sarabande 3/4,
                          8-bar cycle, harpsichord lifts.
  11_Reel_84_Dmix         mixolydian folk vamp I-bVII-IV-I, accordion.
  12_Trade_92_Cdor        call-and-response: bars 3-4 of every 4 the band
                          drops to drums+drone. That silence is her turn.
  13_Vigil_56_Flyd        NO DRUMS. Pads floating in F lydian, chords
                          every 2 bars, harp swells -- singing outside
                          meter, rubato.
  14_Ascent_80_Am         the same four chords reordered each round: home
                          shifts Am -> C major -> Am. A built-in bridge --
                          when the floor brightens, the voice follows.

VOLUME 3 -- The Dialogue: the bed withholds, the voice supplies
  15_Aperture_72_Edor     quartal stacks (fourths) -- rootless jazz-modal float
  16_Hollow_62_Gm         bare open fifths, nothing else -- she supplies ALL color
  17_Antiphon_76_Ador     a low cantor phrase calls bars 1-2, bars 3-4 are hers
                          (call.mid is its own stem -- drop it to silence him)
  18_Sparring_100_Fdor    1-bar trades: band, her, band, her. Fast reflexes.
  19_Yield_84_Ador        the gaps grow: 1 bar of 4, then 2, then 3 -- the band
                          trusts her more the longer she sings
  20_Oracle_78_E          the fusion: thirdless harmony AND trading silence

STEMS (all share the family's key/tempo/feel -- stack any subset):
  bed_full.mid   the whole mix, ready to sing over
  drums.mid      707 pads 36-51 only, groove-engine feel  (absent in Vigil)
  bass.mid       chord roots + fifths, in the basement
  pad.mid        the chord cycle, voiced BELOW the vocal register with
                 smooth nearest-inversion voice leading
  arp.mid        high shimmer, ABOVE the vocal register, lifts only
  drone.mid      soft root anchor -- warm up to it, or keep it under all

THE SINGER'S OCTAVE (~C4-C5) IS EMPTY ON PURPOSE. Nothing melodic competes.

Stems are TIMELINE-ALIGNED with bed_full: drop any subset into the same
clip slots / DAW tracks and they line up. bass.mid starts after the 2-bar
intro and arp.mid waits for the first lift -- intentional, not a glitch.
drums / pad / drone all start on beat 1.

Repeat/extend: python sophia.py (seeded); add a family = one line in
FAMILIES. Chord cycles take scale degrees (diatonic) or (semitones,
quality) tuples (chromatic/sus chords).
"""


if __name__ == "__main__":
    main()
