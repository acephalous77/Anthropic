#!/usr/bin/env python3
"""THE HOLY MOUNTAIN -- Magnum Opus: a moving alchemical arrangement.

Inspired by Jodorowsky's *The Holy Mountain* (the Alchemist transmuting base
matter into gold; the ascent past the seven planetary figures; the final
"zoom back camera -- this is maya, illusion"). Unlike the loop kits, this is a
single composed JOURNEY that transmutes one *prima materia* motif through the
seven stages of the Great Work. The same structural motif changes colour as
the mode brightens stage by stage, while register rises, tempo accelerates,
and density arcs from a tolling void to a full coniunctio and back to dust.

  1 Prima Materia   52  octatonic  -- the base matter, a tolling void
  2 Nigredo         58  octatonic  -- blackening / putrefaction, fragmented
  3 Cauda Pavonis   72  whole-tone -- the peacock's tail, iridescent 7/8 wobble
  4 Albedo          84  dorian     -- whitening / purification, washing 16ths
  5 Citrinitas     100  lydian     -- the solar yellow, motif becomes a hook
  6 Rubedo         116  major      -- the reddening, motif + its inversion wed
  7 Zoom Back       80  octatonic  -- "this is maya" -- thins, transfigures, dissolves

    python holy_mountain.py   ->  output/holy_mountain/{drums,bass,melody,all}.mid
                                   + loops/<stage>/ (707-ready per-stage loops)
"""

import os
import random
import shutil

import arrange
import humanize
import mc707
import midiwriter
import palette as P
from rhythm import grid_from_hits
from theory import scale_degree

HERE = os.path.dirname(__file__)
DEST = os.path.join(HERE, "output", "holy_mountain")
PPQ = midiwriter.PPQ
STEP = arrange.STEP_TICKS

TONIC = 2          # D -- one substance for the whole journey; only the mode changes
BASS_PROG = 48     # string ensemble (bowed drone / union)
MEL_PROG = 19      # church organ (the ascent); overridden per stage below

# drum voices kept inside the MC-707 pad range (36-51) so the piece is 707-native
DV = {
    "kick": (36, 104, 122), "toll": (41, 92, 114), "rim": (37, 70, 90),
    "snare": (38, 100, 118), "clap": (39, 98, 116),
    "chh": (42, 70, 94), "ohh": (46, 86, 108), "ride": (51, 80, 102),
    "mtom": (45, 98, 116), "htom": (48, 94, 112), "crash": (49, 102, 122),
}

# the prima materia -- a rising-arch contour (scale degrees). Realized in each
# stage's mode, the SAME degrees sound dark in octatonic and golden in lydian.
MOTIF = [0, 1, 2, 1, 4, 2]


# ------------------------------------------------------------------ melody transmutation
def _fill(root, scale, degs, durs, steps, register, vel, rng, rise=0):
    """Tile a (degrees, durations) motif across a bar of `steps`, in `scale`."""
    out, pos, i = [], 0, 0
    while pos < steps:
        d = min(durs[i % len(durs)], steps - pos)
        deg = degs[i % len(degs)] + rise
        pitch = P.clamp_register(scale_degree(root, scale, deg), *register)
        out.append((pos, d, pitch, max(1, min(127, vel + rng.randint(-4, 4)))))
        pos += d
        i += 1
    return out


def stage_melody(st, root, rng, bar_idx):
    scale, steps, reg, vel = st["scale"], st["steps"], st["reg"], st["mvel"]
    degs, durs, tf = list(st["degs"]), list(st["durs"]), st["transform"]
    rise = 0
    if tf == "invert":
        degs = [-d for d in degs]
    elif tf == "fragment":
        degs = degs[: max(2, len(degs) // 2 + 1)]
    elif tf == "augment":
        durs = [d * 2 for d in durs]
    elif tf == "hook":
        degs = degs + [7, 4, 0]                 # rise to the octave, resolve
    elif tf == "dissolve":
        vel = max(28, vel - bar_idx * 14)       # fade over the coda bars
        rise = 7 if bar_idx == 0 else (0 if bar_idx < 3 else -7)
    if bar_idx % 2 == 1 and tf in ("augment", "hook", "union"):
        rise += 7                               # answer the phrase an octave up
    return _fill(root, scale, degs, durs, steps, reg, vel, rng, rise)


def stage_union(st, root, rng, bar_idx):
    """Rubedo: the motif and its inversion sounding together -- the wedding of
    opposites. Returns the second (inverted) voice for the union channel."""
    scale, steps, vel = st["scale"], st["steps"], st["mvel"] - 8
    degs = [-d for d in st["degs"]]
    reg = (st["reg"][0] + 7, st["reg"][1])
    return _fill(root, scale, degs, st["durs"], steps, reg, vel, rng)


# ------------------------------------------------------------------ bass
def stage_bass(st, root, rng, bar_idx):
    scale, steps, kind = st["scale"], st["steps"], st["bass"]
    reg = (33, 51)
    r = P.clamp_register(scale_degree(root, scale, 0), *reg)
    fifth = P.clamp_register(scale_degree(root, scale, -3), *reg)   # a fifth below
    if kind == "drone":
        return [(0, steps, r, 92)] + ([(steps // 2, steps // 2, fifth, 80)] if bar_idx % 2 else [])
    if kind == "pulse":
        beats = [b for b in range(0, steps, 4)]
        return [(b, min(4, steps - b), r if k % 2 == 0 else fifth,
                 90 + (10 if b == 0 else 0)) for k, b in enumerate(beats)]
    if kind == "walk":
        degs = [0, -1, -3, -1]
        return [(i * 4, 4, P.clamp_register(scale_degree(root, scale, degs[i % 4]), *reg),
                 88 + (10 if i == 0 else 0)) for i in range(steps // 4)]
    if kind == "groove":
        hits = [0, 3, 6, 8, 11, 14]
        return [(h, 2, r if h in (0, 8) else fifth, 86 + (12 if h == 0 else 0)) for h in hits if h < steps]
    if kind == "drive":
        return [(i * 2, 2, r if i % 2 == 0 else fifth, 84 + (14 if i % 4 == 0 else 0))
                for i in range(steps // 2)]
    return [(0, steps, r, 80)]


# ------------------------------------------------------------------ drums
def _g(hits, steps, accents=()):
    return grid_from_hits(steps, {h for h in hits if 0 <= h < steps},
                          accents={h for h in accents if 0 <= h < steps})


def stage_drums(st, rng, bar_idx, last_bar):
    steps, kind = st["steps"], st["drums"]
    mid = steps // 2
    d = {}
    if kind == "void":
        d["kick"] = _g([0, mid], steps, {0})
        d["toll"] = _g([0], steps, {0})
        if bar_idx == 0:
            d["crash"] = _g([0], steps, {0})
        if bar_idx % 2:
            d["rim"] = _g([mid + 2], steps)
    elif kind == "toll":
        d["kick"] = _g([0, mid], steps, {0})
        d["toll"] = _g([0, mid + 4], steps, {0})
        d["ohh"] = _g([steps - 2], steps)
        if bar_idx % 2:
            d["rim"] = _g([3, mid + 3], steps)
    elif kind == "shimmer":
        d["ride"] = _g(list(range(0, steps, 2)), steps, {0})
        d["htom"] = _g([mid + 1], steps)
        if bar_idx % 2 == 0:
            d["kick"] = _g([0], steps, {0})
    elif kind == "wash":
        d["chh"] = _g(list(range(steps)), steps, set(range(0, steps, 4)))
        d["kick"] = _g([0, mid], steps, {0})
        d["snare"] = _g([mid], steps, {mid})
        if bar_idx % 2:
            d["clap"] = _g([mid], steps)
    elif kind == "golden":
        d["kick"] = _g([0, mid], steps, {0})
        d["ride"] = _g(list(range(0, steps, 2)), steps, {0, mid})
        d["clap"] = _g([4, 12], steps, {4, 12})
        d["ohh"] = _g([6, 14], steps)
    elif kind == "triumph":
        d["kick"] = _g([0, 6, 8, 14], steps, {0, 8})
        d["snare"] = _g([4, 12], steps, {4, 12})
        d["ohh"] = _g(list(range(0, steps, 2)), steps)
        d["mtom"] = _g([7], steps)
        d["htom"] = _g([15], steps)
        if bar_idx == 0 or last_bar:
            d["crash"] = _g([0], steps, {0})
        if last_bar:
            d["mtom"] = _g([8, 10, 12], steps)      # a fill into the coda
            d["htom"] = _g([9, 11, 13, 14], steps)
    elif kind == "fade":
        if bar_idx == 0:
            d["kick"] = _g([0], steps, {0})
            d["crash"] = _g([0], steps, {0})
        elif bar_idx == 1:
            d["kick"] = _g([0], steps)
        # bars 2+ : silence -- the illusion dissolves
    return d


# ------------------------------------------------------------------ the Great Work
STAGES = [
    dict(name="1_PrimaMateria", scale="octatonic", bpm=52, ts=(4, 4), bars=6,
         degs=[0, 1, 0, -1], durs=[4, 2, 2, 8], reg=(40, 55), mvel=70,
         transform="raw", drums="void", bass="drone", mprog=95),      # 95 = pad (sweep)
    dict(name="2_Nigredo", scale="octatonic", bpm=58, ts=(4, 4), bars=6,
         degs=[0, 1, 3, 1, 0, -1], durs=[3, 1, 4, 2, 2, 4], reg=(40, 58), mvel=78,
         transform="fragment", drums="toll", bass="drone", mprog=95),
    dict(name="3_CaudaPavonis", scale="whole_tone", bpm=72, ts=(7, 8), bars=6,
         degs=MOTIF, durs=[2, 1, 2, 1, 3, 2, 3], reg=(55, 72), mvel=84,
         transform="invert", drums="shimmer", bass="pulse", mprog=11),  # 11 = vibraphone
    dict(name="4_Albedo", scale="dorian", bpm=84, ts=(4, 4), bars=8,
         degs=MOTIF, durs=[2, 2, 2, 2, 4, 4], reg=(55, 74), mvel=88,
         transform="augment", drums="wash", bass="walk", mprog=4),      # 4 = Rhodes
    dict(name="5_Citrinitas", scale="lydian", bpm=100, ts=(4, 4), bars=8,
         degs=MOTIF, durs=[2, 1, 1, 2, 2, 2, 3, 3], reg=(64, 86), mvel=94,
         transform="hook", drums="golden", bass="groove", mprog=19, organum=True),  # organ
    dict(name="6_Rubedo", scale="major", bpm=116, ts=(4, 4), bars=10,
         degs=MOTIF + [7], durs=[2, 2, 1, 1, 2, 2, 2, 4], reg=(60, 88), mvel=100,
         transform="union", drums="triumph", bass="drive", mprog=62, organum=True),  # brass
    dict(name="7_ZoomBack", scale="octatonic", bpm=80, ts=(4, 4), bars=6,
         degs=[7, 4, 2, 0], durs=[4, 4, 4, 4], reg=(64, 90), mvel=76,
         transform="dissolve", drums="fade", bass="drone", mprog=95),
]


def build():
    rng = random.Random(1973)     # the year of the film
    root = 12 * 3 + TONIC         # D as the fixed substance
    sections, mel2 = [], []       # mel2 = the union / inversion voice (Rubedo)
    prog_changes, organum_events = [], []

    for st in STAGES:
        st["steps"] = arrange.bar_steps(st["ts"])
        bars = []
        for bi in range(st["bars"]):
            last = bi == st["bars"] - 1
            bar = {"drums": stage_drums(st, rng, bi, last),
                   "bass": stage_bass(st, root, rng, bi),
                   "melody": stage_melody(st, root, rng, bi)}
            bars.append(bar)
        sections.append({"name": st["name"], "time_sig": st["ts"], "bpm": st["bpm"], "bars": bars})

    result = arrange.render_piece(sections, DV)

    # second voices: Rubedo union (inversion) + Citrinitas/Rubedo organum fifths,
    # rendered by walking the same section spans and offsetting into place.
    result["melody2"], result["organum"] = _second_voices(sections, root, rng, result)
    return result, sections


def _second_voices(sections, root, rng, result):
    """Build the union-inversion voice (Rubedo) and organum-fifth voice
    (Citrinitas + Rubedo) as separate event lists aligned to section starts."""
    union_ev, organ_ev = [], []
    tick = 0
    by_name = {st["name"]: st for st in STAGES}
    for sec in sections:
        st = by_name[sec["name"]]
        steps = st["steps"]
        for bi in range(len(sec["bars"])):
            if st["transform"] == "union":
                for (s, d, n, v) in stage_union(st, root, rng, bi):
                    union_ev.append(midiwriter.Event(tick + s * STEP, d * STEP, n, v, 2))
            if st.get("organum"):
                for (s, d, n, v) in sec["bars"][bi]["melody"]:
                    if 0 <= n + 7 <= 127:
                        organ_ev.append(midiwriter.Event(tick + s * STEP, d * STEP, n + 7,
                                                         max(1, int(v * 0.7)), 3))
            tick += arrange.bar_ticks(st["ts"])
    return union_ev, organ_ev


def _humanize(events, sd=10):
    if not events:
        return events
    ev = humanize.pink_jitter(events, 96, PPQ, sd_ms=sd, seed=len(events))
    half = STEP // 2
    return [e._replace(start=0) if 0 <= e.start < half else e for e in ev]


def write_piece(result):
    os.makedirs(DEST, exist_ok=True)
    bpmc, tsc = result["bpm_changes"], result["time_sig_changes"]
    drums = _humanize(result["drums"], 8)
    bass = _humanize(result["bass"])
    mel = _humanize(result["melody"])
    mel2 = _humanize(result["melody2"])
    organ = _humanize(result["organum"])

    midiwriter.write_track(os.path.join(DEST, "drums.mid"), drums, bpmc, tsc,
                           channel=9, track_name="Holy Mountain - drums")
    midiwriter.write_track(os.path.join(DEST, "bass.mid"), bass, bpmc, tsc,
                           channel=0, program=BASS_PROG, track_name="Holy Mountain - bass")
    midiwriter.write_track(os.path.join(DEST, "melody.mid"), mel, bpmc, tsc,
                           channel=1, program=MEL_PROG, track_name="Holy Mountain - melody")
    # 707-native drums
    mc707.remap_drum_file(os.path.join(DEST, "drums.mid"),
                          os.path.join(DEST, "drums_mc707.mid"))

    tracks = [{"events": drums, "channel": 9, "name": "drums"},
              {"events": bass, "channel": 0, "program": BASS_PROG, "name": "bass"},
              {"events": mel, "channel": 1, "program": MEL_PROG, "name": "melody"},
              {"events": mel2, "channel": 2, "program": 52, "name": "union"},     # choir aahs
              {"events": organ, "channel": 3, "program": 19, "name": "organum"}]
    midiwriter.write_combined(os.path.join(DEST, "all.mid"), tracks, bpmc, tsc)


def write_stage_loops(sections):
    """Export each constant-4/4 stage's first 2 bars as a 707-ready loop."""
    loops = os.path.join(DEST, "loops")
    root = 12 * 3 + TONIC
    by_name = {st["name"]: st for st in STAGES}
    for sec in sections:
        st = by_name[sec["name"]]
        if st["ts"] != (4, 4):
            continue
        mini = [{"name": sec["name"], "time_sig": (4, 4), "bpm": st["bpm"],
                 "bars": sec["bars"][:2]}]
        r = arrange.render_piece(mini, DV)
        # the groove pass: metric accents + a ceremonial feel (structure intact)
        import groove as G
        grng = random.Random(1973 + st["bpm"])
        r["drums"] = G.apply_feel(G.apply_accents(r["drums"], STEP, depth=0.9),
                                  "ritual", st["bpm"], PPQ, grng, anchor_ticks=PPQ * 4)
        r["bass"] = G.apply_feel(G.apply_accents(r["bass"], STEP, depth=0.5),
                                 "ritual", st["bpm"], PPQ, grng)
        r["melody"] = G.apply_feel(G.apply_accents(r["melody"], STEP, depth=0.5),
                                   "ritual", st["bpm"], PPQ, grng)
        folder = os.path.join(loops, sec["name"])
        os.makedirs(folder, exist_ok=True)
        midiwriter.write_track(os.path.join(folder, "drums.mid"), r["drums"],
                               r["bpm_changes"], r["time_sig_changes"], channel=9)
        mc707.remap_drum_file(os.path.join(folder, "drums.mid"),
                              os.path.join(folder, "drums.mid"))
        midiwriter.write_track(os.path.join(folder, "bass.mid"), r["bass"],
                               r["bpm_changes"], r["time_sig_changes"], channel=0, program=BASS_PROG)
        midiwriter.write_track(os.path.join(folder, "melody.mid"), r["melody"],
                               r["bpm_changes"], r["time_sig_changes"], channel=1, program=st["mprog"])


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    result, sections = build()
    write_piece(result)
    write_stage_loops(sections)

    total_beats = result["total_ticks"] / PPQ
    with open(os.path.join(DEST, "README.txt"), "w") as fh:
        fh.write(_README)
    print(f"THE HOLY MOUNTAIN -- {len(STAGES)} stages, "
          f"{sum(s['bars'] for s in STAGES)} bars, ~{total_beats:.0f} beats")
    for st in STAGES:
        print(f"  {st['name']:<16} {st['bpm']:>3} bpm  {st['ts'][0]}/{st['ts'][1]:<2} "
              f"{st['scale']:<11} {st['transform']}")
    print(f"-> {DEST}  (all.mid + stems + drums_mc707.mid + loops/)")


_README = """THE HOLY MOUNTAIN -- Magnum Opus (a moving alchemical arrangement)
=================================================================
Inspired by Jodorowsky's *The Holy Mountain*. One prima-materia motif is
transmuted through the seven stages of the Great Work: the same structural
motif changes colour as the mode brightens, register rises, tempo climbs,
and the arrangement swells from a tolling void to a full coniunctio, then
dissolves ("this is maya, illusion").

  1 Prima Materia   52  octatonic   the base matter, a tolling void
  2 Nigredo         58  octatonic   blackening / putrefaction, fragmented motif
  3 Cauda Pavonis   72  whole-tone  the peacock's tail, iridescent 7/8 wobble,
                                    motif inverted, shimmering vibraphone
  4 Albedo          84  dorian      whitening, washing 16ths, motif augmented
  5 Citrinitas     100  lydian      the solar gold (#4), motif becomes a hook,
                                    organum fifths
  6 Rubedo         116  major       the reddening -- the motif sounds together
                                    with its own inversion (union of opposites),
                                    full tribal-electronic drums
  7 Zoom Back       80  octatonic   the illusion dissolves -- thins, transfigures

FILES
  all.mid            the whole journey (drums, bass, melody, union, organum)
  drums/bass/melody.mid   stems
  drums_mc707.mid    drums folded to the 707 pads (36-51)
  loops/<stage>/     each 4/4 stage's first 2 bars as a 707-ready loop
                     (grab a single stage to groove on)

Reproducible: `python holy_mountain.py` (seed 1973, the year of the film)."""


if __name__ == "__main__":
    main()
