#!/usr/bin/env python3
"""TERMINAL LIGHT -- a 16-song concept album on the beautiful, solemn end of
the world.

ARCHITECTURE
  * The album is one giant LAMENT TETRACHORD: its four sides descend
    A -> G -> F -> E, the Dido ground stretched across the whole record.
        Side A  THE ANNOUNCEMENT   (A roots)  tracks 1-4
        Side B  GRIEFWORK          (G roots)  tracks 5-8
        Side C  FAREWELLS          (F roots)  tracks 9-12
        Side D  EVANESCENCE        (E roots)  tracks 13-16
  * One ALBUM MOTIF is stated in track 1, returns through the record in
    different transforms, and closes track 16 in E MAJOR -- the picardy
    third as afterglow.
  * Every engine in the toolkit plays a narrative role: trading gaps for
    stunned silence, change-ringing for the last cathedral, thirdless
    harmony for an unnamed prayer, growing gaps as the world withdraws.

Each track: output/album/<NN_Slug>/ stems (drums/bass/pad/arp/lead/second/
drone) + song.mid. Drums use only MC-707 pads 36-51. Seeded, reproducible.

    python album.py
"""

import os
import random
import shutil

import codex
import groove as G
import midiwriter
import palette as P
import stemlib as SL
from midiwriter import Event
from rhythm import grid_from_hits
from sophia import lead_voicing, voice_into
from theory import CHORDS, scale_degree

HERE = os.path.dirname(__file__)
DEST = os.path.join(HERE, "output", "album")
PPQ = midiwriter.PPQ
STEP = PPQ // 4

REG_BASS, REG_PAD, REG_LEAD, REG_ARP = (33, 50), (46, 60), (60, 82), (74, 94)

# the album motif: circles home, dips below (solemn), returns (beautiful)
MOTIF = [0, 2, 3, 2, 0, -1, 0]
MOTIF_DURS = {16: [2, 2, 4, 2, 2, 2, 2], 12: [2, 2, 2, 2, 2, 1, 1],
              20: [3, 3, 4, 3, 3, 2, 2]}

A, Gk, F, E = 45, 43, 41, 40    # the tetrachord roots


def T(n, title, root, scale, bpm, meter, beat, lead, cycle, feel, progs, **kw):
    d = dict(n=n, title=title, root=root, scale=scale, bpm=bpm, meter=meter,
             beat=beat, lead=lead, cycle=cycle, feel=feel, progs=progs,
             form="standard", chorus_cycle=None, organum=False, transform="raw",
             trade=None, trade_by_verse=None, call=False, note="")
    d.update(kw)
    return d


# progs: (bass, pad, arp, lead, second)
TRACKS = [
    # ---- SIDE A -- THE ANNOUNCEMENT ----
    T(1, "First Light, Last Light", A, "aeolian", 66, (4, 4), "halftime", "motif",
      [0, 5, 2, 6], "ritual", (48, 89, 46, 19, 19), form="hymn", organum=True,
      note="the motif stated plainly; organ and organum fifths; the bell of the news"),
    T(2, "The Broadcast", A, "phrygian", 84, (4, 4), "broken", "phase",
      [0, -1, 0, -1], "pushing", (38, 95, 80, 80, 95), trade=(4, (3,)),
      note="glitch and stunned silences -- every 4th bar the band cuts out"),
    T(3, "Gathering at the Shore", A, "dorian", 76, (6, 8), "gospel68", "hook",
      [0, 3, 0, 4], "laidback", (32, 19, 46, 4, 19),
      note="a 6/8 sway; people arriving with blankets and lanterns"),
    T(4, "Sky Full of Endings", A, "aeolian", 92, (4, 4), "headnod", "hook",
      [0, 5, 2, 6], "laidback", (33, 50, 11, 5, 50), form="long",
      chorus_cycle=[2, 6, 0, 5], organum=True,
      note="meteors mistaken for fireworks; the chorus lifts into C major"),
    # ---- SIDE B -- GRIEFWORK ----
    T(5, "Lament of the Cartographers", Gk, "aeolian", 60, (3, 4), "sarabande", "motif",
      [0, -1, -2, -3], "ritual", (32, 48, 24, 42, 48), transform="invert",
      note="a sarabande over the lament ground itself; maps of vanishing places"),
    T(6, "Unsent Letters", Gk, "dorian", 72, (4, 4), "dilla", "hook",
      [0, 3, 0, 3], "laidback", (33, 4, 11, 4, 4), trade=(4, (2, 3)),
      note="half of every phrase is the silence where the words should go"),
    T(7, "The Orchards Bloom Anyway", Gk, "lydian", 88, (4, 4), "bossa", "additive",
      [0, 1, 0, 1], "laidback", (32, 89, 10, 89, 89),
      note="nature indifferent and dazzling; the brightest track on the record"),
    T(8, "Procession", Gk, "phrygian", 68, (4, 4), "tribal", "iso",
      [0, -1, 0, -1], "ritual", (38, 48, 46, 89, 48), organum=True,
      note="candle-march; an isorhythm carries the line like a litany"),
    # ---- SIDE C -- FAREWELLS ----
    T(9, "Last Dance at the Observatory", F, "major", 104, (4, 4), "fourfloor", "hook",
      [0, 4, 5, 3], "pushing", (33, 5, 12, 5, 5), form="long",
      note="the last party; everyone dancing under the dome, telescopes aimed at it"),
    T(10, "Quartal Prayer", F, "major", 56, (4, 4), "none", "motif",
      [(0, "sus4"), (-2, "sus2"), (5, "q4"), (0, "sus2")], "ritual",
      (42, 95, 46, 95, 95), form="hymn", transform="augment",
      note="a prayer with no third -- it never names what it prays to"),
    T(11, "Two Chairs Facing the Sea", F, "major", 63, (6, 8), "gospel68", "hook",
      [0, 3, 4, 0], "laidback", (32, 4, 46, 42, 71), call=True, form="hymn",
      note="a duet: cello asks, clarinet answers; two chairs, one horizon"),
    T(12, "The Museum of Us", F, "aeolian", 80, (5, 4), "museum54", "phase",
      [0, 5, 2, 6], "laidback", (38, 48, 11, 4, 48),
      note="wandering the exhibits in 5/4 -- the pulse never quite settles"),
    # ---- SIDE D -- EVANESCENCE ----
    T(13, "Thin Air", E, "dorian", 74, (4, 4), "headnod", "additive",
      [0, 3, 0, 3], "laidback", (33, 95, 10, 11, 95),
      note="a Glass-additive line that keeps growing as things turn transparent"),
    T(14, "Change-Ringing for the Last Cathedral", E, "aeolian", 100, (4, 4),
      "fourfloor", "ring", [0, -1, -2, -1], "ritual", (32, 19, 14, 14, 19),
      organum=True,
      note="the towers ring a full course and come back to rounds -- home, then done"),
    T(15, "The Great Quiet", E, "phrygian", 52, (4, 4), "sparseonly", "motif",
      [(0, "5"), (-2, "5"), (-4, "5"), (0, "5")], "ritual", (42, 48, 46, 52, 48),
      transform="fragment", trade_by_verse=[(4, (3,)), (4, (2, 3)), (4, (1, 2, 3))],
      note="open fifths and growing gaps; the band withdraws bar by bar"),
    T(16, "Afterglow", E, "major", 58, (4, 4), "none", "motif",
      [0, 3, 0, 4], "ritual", (42, 89, 46, 89, 89), form="hymn", transform="lift",
      note="the motif returns in E major -- the picardy third; a single high E remains"),
]

FORMS = {
    "standard": [("intro", 4, "sparse"), ("verse", 8, "verse"), ("chorus", 8, "chorus"),
                 ("verse2", 8, "verse"), ("chorus2", 8, "chorus"), ("bridge", 4, "bridge"),
                 ("chorus3", 8, "chorus"), ("outro", 8, "sparse")],
    "long":     [("intro", 4, "sparse"), ("verse", 8, "verse"), ("chorus", 8, "chorus"),
                 ("verse2", 8, "verse"), ("chorus2", 8, "chorus"), ("bridge", 8, "bridge"),
                 ("verse3", 8, "verse"), ("chorus3", 8, "chorus"), ("outro", 8, "sparse")],
    "hymn":     [("intro", 4, "sparse"), ("verse", 8, "verse"), ("chorus", 8, "chorus"),
                 ("verse2", 8, "verse"), ("chorus2", 8, "chorus"), ("outro", 8, "sparse")],
}


# ---------------------------------------------------------------- drums
def beat_cells(track, rng, bar_steps):
    """One-bar full/sparse drum cells for the track's beat style."""
    style = track["beat"]
    mid = bar_steps // 2
    sparse = {36: grid_from_hits(bar_steps, {0, mid}), 44: grid_from_hits(bar_steps, {mid + mid // 2})}
    if style == "none":
        return None, sparse
    if style == "sparseonly":
        return sparse, sparse
    if style == "museum54":   # 5/4: pulse in 3+3+2+2 groupings over 20 steps
        full = {36: grid_from_hits(20, {0, 6, 12, 16}), 42: grid_from_hits(20, set(range(0, 20, 2))),
                38: grid_from_hits(20, {12}), 44: grid_from_hits(20, {6, 16})}
        return full, sparse
    tempos, steps, swung, fn = SL.BEAT_DEFS[style]
    ev = fn(rng)
    full = {}
    for e in ev:
        if e.start < steps * STEP:
            full.setdefault(e.note, set()).add(e.start // STEP)
    full = {n: grid_from_hits(steps, hits) for n, hits in full.items()}
    return full, sparse


DRUM_VEL = {36: 106, 38: 96, 40: 90, 42: 72, 44: 62, 46: 84, 45: 92, 48: 88,
            41: 94, 37: 70, 51: 76, 39: 96, 43: 92, 47: 90, 50: 88}


def drums_for_bar(grids, bar_i, bar_steps, scale_vel=1.0):
    ev = []
    for note, grid in grids.items():
        for i, c in enumerate(grid):
            if c in "xX":
                v = max(1, round(DRUM_VEL.get(note, 84) * scale_vel))
                ev.append(Event((bar_i * bar_steps + i) * STEP, STEP, note, v, 9))
    return ev


# ---------------------------------------------------------------- harmony helpers
def chord_of(root, scale, spec, seventh=False):
    if isinstance(spec, tuple):
        semis, qual = spec
        return [root + semis + iv for iv in CHORDS[qual]]
    degs = (0, 2, 4, 6) if seventh else (0, 2, 4)
    return [scale_degree(root, scale, spec + d) for d in degs]


def chord_root(root, scale, spec):
    return root + spec[0] if isinstance(spec, tuple) else scale_degree(root, scale, spec)


# ---------------------------------------------------------------- lead techniques
def fill_motif(rng, root, scale, total_steps, bar_steps, transform, vel=88):
    degs, durs = list(MOTIF), list(MOTIF_DURS[bar_steps])
    if transform == "invert":
        degs = [-d for d in degs]
    elif transform == "fragment":
        degs, durs = degs[:4], durs[:4]
    elif transform == "augment":
        durs = [d * 2 for d in durs]
    elif transform == "lift":
        degs = [d + 7 for d in degs]          # transfigured an octave up
    out, pos, i = [], 0, 0
    while pos < total_steps:
        d = min(durs[i % len(durs)], total_steps - pos)
        pitch = P.clamp_register(scale_degree(root, scale, degs[i % len(degs)]), *REG_LEAD)
        out.append((pos, d, pitch, max(1, min(127, vel + rng.randint(-5, 5)))))
        pos += d
        i += 1
    return out


def lead_section(track, rng, kind, n_bars, bar_steps, hook):
    """Section-length lead material as (onset, dur, pitch, vel) from step 0."""
    root, scale, tech = track["root"] + 12, track["scale"], track["lead"]
    total = n_bars * bar_steps
    if kind == "sparse":
        return []
    if kind == "bridge":
        return fill_motif(rng, root, scale, min(total, bar_steps * 2), bar_steps, "fragment", vel=74)
    if kind == "chorus":
        ante, cons = hook
        out = []
        for b in range(n_bars):
            cell = G.breathe(ante if b % 2 == 0 else cons, bar_steps, gap=2)
            out += [(b * bar_steps + o, d, p, v) for (o, d, p, v) in cell]
        return out
    # verses: the track's technique
    if tech == "motif":
        return fill_motif(rng, root, scale, total, bar_steps, track["transform"])
    if tech == "hook":
        ante, cons = hook
        out = []
        for b in range(n_bars):
            src = ante if b % 4 in (0, 2) else cons
            cell = G.breathe([(o, d, p - 12 if p - 12 >= REG_LEAD[0] else p, max(1, v - 12))
                              for (o, d, p, v) in src], bar_steps, gap=3)
            out += [(b * bar_steps + o, d, p, v) for (o, d, p, v) in cell]
        return out
    if tech == "phase":
        bars = P.phase_melody(rng, root, scale, n_bars, bar_steps=bar_steps)
        return [(bi * bar_steps + o, d, P.clamp_register(p, *REG_LEAD), v)
                for bi, bar in enumerate(bars) for (o, d, p, v) in bar]
    if tech == "additive":
        bars = P.additive_phase_melody(rng, root, scale, n_bars, bar_steps=bar_steps)
        return [(bi * bar_steps + o, d, P.clamp_register(p, *REG_LEAD), v)
                for bi, bar in enumerate(bars) for (o, d, p, v) in bar]
    if tech == "iso":
        color = [0, 2, 1, 4, 2]
        talea = [3, 3, 2] if bar_steps == 12 else [3, 2, 3, 5, 3]
        return codex.isorhythm(root, scale, color, talea, total, REG_LEAD)
    if tech == "ring":
        return codex.change_ring(root, scale, 4, total, REG_LEAD)
    return []


# ---------------------------------------------------------------- track builder
def build_track(track):
    rng = random.Random(4000 + track["n"])
    root, scale, bpm, meter = track["root"], track["scale"], track["bpm"], track["meter"]
    bar_steps = meter[0] * 16 // meter[1]
    bar_t = bar_steps * STEP
    feel = track["feel"]
    full_gr, sparse_gr = beat_cells(track, rng, bar_steps)
    hook = P.hook_phrase(rng, root + 12, scale, REG_LEAD)
    plan = FORMS[track["form"]]
    total_bars = sum(n for _, n, _ in plan)
    fade_start = total_bars - plan[-1][1]

    drums, bass, pad, arp, lead, second, drone = [], [], [], [], [], [], []
    prev_voicing = None
    bar_i = 0
    verse_i = 0

    for sec, n_bars, kind in plan:
        cycle = track["chorus_cycle"] if (kind == "chorus" and track["chorus_cycle"]) else track["cycle"]
        gaps = None
        if kind == "verse":
            tbv = track["trade_by_verse"]
            gaps = tbv[verse_i % len(tbv)] if tbv else track["trade"]
            verse_i += 1
        sec_lead = lead_section(track, rng, kind, n_bars, bar_steps, hook)
        sec_start = bar_i

        for b in range(n_bars):
            fade = 1.0
            if bar_i >= fade_start:
                fade = max(0.3, 1.0 - (bar_i - fade_start) * 0.11)
            elif bar_i < plan[0][1]:
                fade = 0.72 + 0.28 * bar_i / plan[0][1]
            trading = gaps is not None and (b % gaps[0]) in gaps[1]

            # drums
            if kind == "sparse" or full_gr is None:
                if sparse_gr and not (track["beat"] == "none" and kind != "sparse"):
                    drums += drums_for_bar(sparse_gr, bar_i, bar_steps, 0.8 * fade)
            elif kind in ("verse", "chorus", "bridge"):
                gr = full_gr
                if kind == "bridge":
                    gr = {n: g for n, g in list(full_gr.items())[:2]}
                if b == n_bars - 1:
                    gr = G.vary_grids(rng, gr, bar_steps)
                drums += drums_for_bar(gr, bar_i, bar_steps, (1.0 if kind == "chorus" else 0.92) * fade)

            # harmony
            spec = cycle[b % len(cycle)] if kind != "sparse" else cycle[0]
            chord = chord_of(root, scale, spec, seventh=(kind == "chorus"))
            if not trading:
                voiced = lead_voicing(chord, prev_voicing, *REG_PAD)
                prev_voicing = voiced
                pvel = round((56 if kind != "chorus" else 63) * fade)
                for p in voiced:
                    pad.append(Event(bar_i * bar_t, bar_t, p, max(1, pvel + rng.randint(-3, 3)), 2))
                if kind != "sparse":
                    br = voice_into(chord_root(root, scale, spec), *REG_BASS)
                    bf = voice_into(chord_root(root, scale, spec) + 7, *REG_BASS)
                    mid = bar_steps // 2
                    for (o, d, p, v) in ((0, 3, br, 96), (mid, 2, bf, 82), (mid + 3, min(3, bar_steps - mid - 3), br, 86)):
                        if d > 0:
                            bass.append(Event((bar_i * bar_steps + o) * STEP, d * STEP, p,
                                              max(1, round(v * fade)), 0))
                if kind == "chorus":
                    tones = sorted(voice_into(t, *REG_ARP) for t in chord)
                    for k, o in enumerate(range(0, bar_steps, 2)):
                        arp.append(Event((bar_i * bar_steps + o) * STEP, round(STEP * 1.6),
                                         tones[k % len(tones)], max(1, round(48 * fade)), 3))

            if bar_i % 2 == 0:
                drone.append(Event(bar_i * bar_t, 2 * bar_t, voice_into(root, 36, 47),
                                   max(1, round(44 * fade)), 6))
            bar_i += 1

        # lead + organum/call second voice, placed at section start
        for (o, d, p, v) in sec_lead:
            t0 = (sec_start * bar_steps + o) * STEP
            fade = 1.0 if sec_start < fade_start else 0.7
            lead.append(Event(t0, d * STEP, p, max(1, round(v * fade)), 1))
            if track["organum"] and kind == "chorus" and p + 7 <= 127:
                second.append(Event(t0, d * STEP, p + 7, max(1, round(v * 0.65)), 4))
            if track["call"] and kind == "verse" and (o // bar_steps) % 4 in (2, 3):
                second.append(Event(t0, d * STEP, min(127, p + 5), max(1, round(v * 0.8)), 4))

    frng = random.Random(9000 + track["n"])
    half = STEP // 2
    fix = lambda evs: [e._replace(start=0) if 0 <= e.start < half else e for e in evs]
    drums = fix(G.apply_feel(G.apply_accents(drums, STEP, bar_steps, depth=0.85),
                             feel, bpm, PPQ, frng, anchor_ticks=bar_t))
    bass = fix(G.apply_feel(G.apply_accents(bass, STEP, bar_steps, depth=0.4), feel, bpm, PPQ, frng))
    lead = fix(G.apply_feel(G.apply_accents(lead, STEP, bar_steps, depth=0.5), feel, bpm, PPQ, frng))
    arp = fix(G.apply_feel(arp, feel, bpm, PPQ, frng))
    second = fix(G.apply_feel(second, feel, bpm, PPQ, frng))

    slug = "".join(w.capitalize() for w in track["title"].replace(",", "").replace("'", "").split())
    folder = os.path.join(DEST, f"{track['n']:02d}_{slug}")
    os.makedirs(folder, exist_ok=True)
    bpmc, tsc = [(0, bpm)], [(0, meter)]
    bp, pp, ap, lp, sp = track["progs"]
    stems = [("drums", drums, 9, None), ("bass", bass, 0, bp), ("pad", pad, 2, pp),
             ("arp", arp, 3, ap), ("lead", lead, 1, lp), ("second", second, 4, sp),
             ("drone", drone, 6, 89)]
    tracks_out = []
    for name, evs, ch, prog in stems:
        if not evs:
            continue
        midiwriter.write_track(os.path.join(folder, f"{name}.mid"), evs, bpmc, tsc,
                               channel=ch, program=prog, track_name=f"{track['title']} - {name}")
        tracks_out.append({"events": evs, "channel": ch, "program": prog, "name": name})
    midiwriter.write_combined(os.path.join(folder, "song.mid"), tracks_out, bpmc, tsc)
    secs = total_bars * bar_t / PPQ * 60 / bpm
    return folder, total_bars, secs


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST)
    print("TERMINAL LIGHT -- sixteen songs for a beautiful, solemn end\n")
    total = 0
    lines = []
    sides = {1: "SIDE A -- THE ANNOUNCEMENT", 5: "SIDE B -- GRIEFWORK",
             9: "SIDE C -- FAREWELLS", 13: "SIDE D -- EVANESCENCE"}
    for tr in TRACKS:
        if tr["n"] in sides:
            print(sides[tr["n"]])
            lines.append(f"\n## {sides[tr['n']]}\n")
        folder, bars, secs = build_track(tr)
        total += secs
        mm, ss = int(secs // 60), int(secs % 60)
        key = f"{['C','C#','D','D#','E','F','F#','G','G#','A','A#','B'][tr['root']%12]} {tr['scale']}"
        m = f"{tr['meter'][0]}/{tr['meter'][1]}"
        print(f"  {tr['n']:>2}. {tr['title']:<38} {key:<12} {m:<4} {tr['bpm']:>3}bpm  {mm}:{ss:02d}")
        lines.append(f"**{tr['n']}. {tr['title']}** — {key}, {m}, {tr['bpm']} bpm, {mm}:{ss:02d}  \n{tr['note']}\n")
    with open(os.path.join(DEST, "LINER_NOTES.md"), "w") as fh:
        fh.write(_LINER + "\n".join(lines))
    print(f"\ntotal {int(total//60)}:{int(total%60):02d}  ->  {DEST}")


_LINER = """# TERMINAL LIGHT
*sixteen songs for a beautiful, solemn end of the world*

The album is one giant lament: its four sides descend A → G → F → E, the
Dido tetrachord stretched across the whole record. A single motif — stated
plainly in the first track — returns through the album transformed
(inverted for the cartographers, augmented into prayer, fragmented in the
great quiet) and closes the record in E major: the picardy third as
afterglow. Stems per track: drums (MC-707 pads), bass, pad, arp, lead,
second (organum/duet voice), drone. song.mid is the full mix.
"""


if __name__ == "__main__":
    main()
