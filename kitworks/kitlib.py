"""kitlib -- the authoring engine for KITWORKS, the hand-composed kit project.

A kit is one Python file in kits/ holding a KIT dict: explicit drum grids,
bass/lead/counter/chords/arp note lists (every note chosen), and a section
spec. This engine renders each part as SIX section clips:

    1_intro   stripped statement          4_break   the floor drops
    2_main    the song as written         5_peak    lift + fills every 2 bars
    3_lift    chorus energy               6_end     2-bar cadence that CLOSES

plus stacked previews (full_main / full_lift / full_peak) and a kit card.
The groove engine (from midi-sketches) supplies micro-timing polish only;
all velocities are written.
"""

import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.append(os.path.join(os.path.dirname(HERE), "midi-sketches"))

import groove as G            # noqa: E402
import humanize               # noqa: E402
import midiwriter             # noqa: E402
from midiwriter import Event  # noqa: E402
from songcraft import anchor  # noqa: E402

PPQ = midiwriter.PPQ
STEP = PPQ // 4

_PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
       "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}


def N(name):
    """'F#2' -> MIDI number (C4 = 60)."""
    return (int(name[-1]) + 1) * 12 + _PC[name[:-1]]


def H(*pairs):
    """hits helper: H(0,106, 8,96) -> [(0,106), (8,96)]"""
    return list(zip(pairs[::2], pairs[1::2]))


def _n(x):
    return N(x) if isinstance(x, str) else x


def bars_to_events(bars, channel, bar_steps):
    ev = []
    for bi, bar in enumerate(bars):
        for (s, d, note, v) in bar:
            ev.append(Event((bi * bar_steps + s) * STEP, d * STEP, _n(note),
                            max(1, min(127, v)), channel))
    return ev


def drum_bars(bars, bar_steps):
    ev = []
    for bi, bar in enumerate(bars):
        for note, hits in bar.items():
            for (s, v) in hits:
                ev.append(Event((bi * bar_steps + s) * STEP, STEP, note,
                                max(1, min(127, v)), 9))
    return ev


# ---------------------------------------------------------------- variations
def drums_variation(kit, which):
    spec = kit["sections"]
    main = kit["drums"]

    def lifted(bar, crash):
        nb = {n: list(h) for n, h in bar.items()}
        for n, hits in spec["lift_add"].items():
            nb[n] = nb.get(n, []) + list(hits)
        if crash:
            nb[49] = nb.get(49, []) + [(0, 100)]
        return nb

    if which == "main":
        return main
    if which == "intro":
        keep = set(spec["intro"])
        return [{n: [(s, max(1, int(v * 0.85))) for (s, v) in hits]
                 for n, hits in bar.items() if n in keep} for bar in main]
    if which == "lift":
        return [lifted(bar, bi == 0) for bi, bar in enumerate(main)]
    if which == "peak":                     # lift energy, the written fill every 2 bars
        A, B = main[0], main[3]
        return [lifted(A, True), lifted(B, False), lifted(A, False), lifted(B, False)]
    if which == "break":
        return spec["brk"]
    if which == "end":                      # the written fill, then the landing hit
        return [main[3], {36: H(0, 108), 49: H(0, 102)}]
    return main


def bass_variation(bars, which, bar_steps):
    if which == "main":
        return bars
    if which == "intro":
        return [[(0, bar_steps, b[0][2], max(1, b[0][3] - 8))] for b in bars]
    if which in ("lift", "peak"):
        out = []
        for bar in bars:
            nb = list(bar)
            for (s, d, note, v) in bar:
                nb.append((s, d, _n(note) + 12, max(1, int(v * 0.55))))
            out.append(nb)
        return out
    if which == "break":
        return [[(0, bar_steps, b[0][2], max(1, b[0][3] - 12))] for b in bars[:3]] + [bars[3]]
    return [bars[3], [(0, bar_steps, bars[0][0][2], max(1, bars[0][0][3] - 4))]]   # end


def lead_variation(bars, which, bar_steps):
    if which == "main":
        return bars
    if which == "intro":
        return [bars[0], bars[1], [], []]
    if which in ("lift", "peak"):
        out = []
        for bar in bars:
            nb = list(bar)
            for (s, d, note, v) in bar:
                nb.append((s, d, _n(note) + 12, max(1, v - 24)))
            out.append(nb)
        return out
    if which == "break":
        a, b = bars[1], bars[3]
        fo = lambda bar: min((s for (s, d, n, v) in bar), default=99)
        if fo(b) < fo(a):
            a, b = b, a
        return [a, [], b, []]
    # end: the written last bar, then the landing note held
    last = bars[3] if bars[3] else bars[0]
    (s, d, note, v) = last[-1]
    return [last, [(0, bar_steps, note, max(1, v - 6))]]


def chords_variation(bars, which, bar_steps):
    strikes = {16: (0, 4, 8, 12), 12: (0, 3, 6, 9), 24: (0, 6, 12, 18)}[bar_steps]

    def held(bar, drop=0, dv=6):
        first = min(s for (s, d, n, v) in bar)
        return [(first, bar_steps - first, _n(n) + drop, max(1, v - dv))
                for (s, d, n, v) in bar if s == first]

    if which == "main":
        return bars
    if which == "intro":
        return [held(b) for b in bars]
    if which in ("lift", "peak"):
        boost = 8 if which == "peak" else 0
        out = []
        for bar in bars:
            first = min(s for (s, d, n, v) in bar)
            tones = [(n, v) for (s, d, n, v) in bar if s == first]
            nb = []
            for k, st in enumerate(strikes):
                for (n, v) in tones:
                    nb.append((st, 2, n, max(1, (v + 8 + boost) if k % 2 == 0 else (v - 6 + boost))))
            out.append(nb)
        return out
    if which == "break":
        return [held(b, drop=-12, dv=10) for b in bars]
    return [bars[3], held(bars[0], dv=2)]     # end: last change, then home held


def arp_variation(bars, which, bar_steps):
    if which == "main":
        return bars
    if which == "intro":
        return [[t for i, t in enumerate(bar) if i % 2 == 0] for bar in bars]
    if which in ("lift", "peak"):
        return [[(s, d, _n(n) + 12, v + (6 if which == "peak" else 0))
                 for (s, d, n, v) in bar] for bar in bars]
    if which == "break":
        return [[(s, d, _n(n) - 12, max(1, v - 8))
                 for i, (s, d, n, v) in enumerate(bar) if i % 2 == 0] for bar in bars]
    return [bars[3], [bars[0][0]] if bars[0] else []]    # end: last bar, one first note


VARIATIONS = [("1_intro", "intro"), ("2_main", "main"), ("3_lift", "lift"),
              ("4_break", "break"), ("5_peak", "peak"), ("6_end", "end")]
PREVIEWS = {"2_main": "full_main", "3_lift": "full_lift", "5_peak": "full_peak"}


def polish(events, kit, rng):
    if not events:
        return events
    ev = events
    if kit.get("swing"):
        ev = humanize.swing(ev, STEP * 2,
                            swing_pct=humanize.sixteenth_swing_pct(kit["bpm"]))
    ev = G.apply_feel(ev, kit["feel"], kit["bpm"], PPQ, rng,
                      anchor_ticks=kit.get("bar_steps", 16) * STEP if ev[0].channel == 9 else None)
    return anchor(ev, STEP)


def build_kit(kit, index, dest):
    rng = random.Random(7000 + index)
    bar_steps = kit.get("bar_steps", 16)
    meter = kit.get("meter", (4, 4))
    bpmc, tsc = [(0, kit["bpm"])], [(0, meter)]
    pr = kit["progs"]
    folder = os.path.join(dest, f"{index:02d}_{kit['name']}_{kit['key']}_{kit['bpm']}")

    parts = {"drums": (lambda w: drum_bars(drums_variation(kit, w), bar_steps), 9, None)}
    for pname, ch, var in (("bass", 0, bass_variation), ("lead", 1, lead_variation),
                           ("counter", 4, lead_variation), ("chords", 2, chords_variation),
                           ("arp", 3, arp_variation)):
        if kit.get(pname):
            parts[pname] = (lambda w, p=pname, vf=var: bars_to_events(
                vf(kit[p], w, bar_steps), dict(bass=0, lead=1, counter=4, chords=2, arp=3)[p],
                bar_steps), ch, pr.get(pname))

    previews = {v: [] for v in PREVIEWS}
    n_files = 0
    for part, (make, ch, prog) in parts.items():
        pdir = os.path.join(folder, part)
        os.makedirs(pdir, exist_ok=True)
        for fname, which in VARIATIONS:
            evs = polish(make(which), kit, rng)
            if not evs:
                continue
            midiwriter.write_track(os.path.join(pdir, f"{fname}.mid"), evs, bpmc, tsc,
                                   channel=ch, program=prog,
                                   track_name=f"{kit['name']}-{part}-{which}")
            n_files += 1
            if fname in previews:
                previews[fname].append({"events": evs, "channel": ch, "program": prog,
                                        "name": part})
    for fname, out in PREVIEWS.items():
        if previews[fname]:
            midiwriter.write_combined(os.path.join(folder, f"{out}.mid"),
                                      previews[fname], bpmc, tsc)
    with open(os.path.join(folder, "KIT.txt"), "w") as fh:
        fh.write(f"{kit['name']}  --  {kit['key']}  {kit['bpm']} bpm  "
                 f"{meter[0]}/{meter[1]}  feel:{kit['feel']}"
                 f"{'  (swung)' if kit.get('swing') else ''}\n\n{kit['note']}\n\n"
                 f"parts: {', '.join(parts)}\n"
                 "columns: 1_intro  2_main  3_lift  4_break  5_peak  6_end\n"
                 "suggested rides:  1-2-2-3 | 2-3-4-2 | 1-2-3-5-4-2-5-6\n")
    return folder, n_files
