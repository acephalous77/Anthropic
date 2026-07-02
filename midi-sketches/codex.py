#!/usr/bin/env python3
"""CODEX -- loops built from historical & esoteric compositional practice.

Same grab-and-stack loop format as loopkit (2 bars, 16th grid, hit on beat 1,
707-native drums on pads 36-51), but the pitch/rhythm material comes from real
old techniques instead of pop patterns:

  * ISORHYTHM (Ars Nova -- Machaut, Vitry, 14th c.): a repeating rhythm cycle
    (talea) of a different length than the pitch cycle (color), so the two
    phase against each other -- long melody from tiny coprime material.
  * CHANGE RINGING (English campanology, ~1600s; group theory): permute a fixed
    set of bells by plain hunting; a full course returns to "rounds" exactly at
    the loop boundary, so it repeats seamlessly.
  * GROUND BASS (Baroque passacaglia/chaconne): historical repeating basses --
    the lament descending tetrachord (Dido), La Folia, Romanesca, Passamezzo
    antico, Pachelbel.
  * HOCKET (Notre-Dame school, 13th c.; also Aka pygmy & gamelan kotekan): one
    line split between two interlocking voices.
  * ORGANUM (Musica Enchiriadis, 9th c.): parallel fifths -- the medieval tone.
  * ESOTERIC SCALES: Messiaen modes (whole-tone, octatonic), Scriabin's mystic
    chord, Byzantine double-harmonic, Hungarian minor, Phrygian-dominant.

THEME -- Musica Universalis (music of the spheres): families are the seven
classical planets, each with its own mode, tempo, technique, and archaic tone.

    python codex.py    ->  output/codex/<NN_Planet_bpm_Scale>/{beats,bass,melody}/
"""

import os
import shutil

import loopkit as LK
import midiwriter
import palette as P
from theory import scale_degree

DEST = os.path.join(LK.HERE, "output", "codex")
STEP, BAR, LOOP, DRUM_CH = LK.STEP, LK.BAR, LK.LOOP, LK.DRUM_CH

_PC = ["C", "Cs", "D", "Ds", "E", "F", "Fs", "G", "Gs", "A", "As", "B"]
_SCALE_ABBR = {"hirajoshi": "hira", "whole_tone": "whole", "octatonic": "octa",
               "mystic": "mystic", "lydian": "lyd", "phrygian_dominant": "freygish",
               "dorian": "dor", "byzantine": "byz", "hungarian_minor": "hungmin"}


def _tag(root, scale):
    return f"{_PC[root % 12]}-{_SCALE_ABBR.get(scale, scale)}"


# ============================================================ historical techniques
def isorhythm(root, scale, color, talea, total_steps, register, vel_base=92):
    """Cycle a pitch series (color) against a rhythm series (talea) of a
    different length; the isorhythmic accent falls on each restart of the talea."""
    cell, onset, i = [], 0, 0
    while onset < total_steps:
        dur = talea[i % len(talea)]
        deg = color[i % len(color)]
        dur = min(dur, total_steps - onset)
        pitch = P.clamp_register(scale_degree(root, scale, deg), *register)
        accent = 12 if i % len(talea) == 0 else 0
        cell.append((onset, dur, pitch, min(127, vel_base + accent)))
        onset += dur
        i += 1
    return cell


def plain_hunt(n, rows):
    """Plain-hunting change ringing on n bells: `rows` successive permutations.
    A full course is 2n rows and returns to rounds -- pick rows = 2n for a loop
    that closes cleanly."""
    perm = list(range(n))
    out = [perm[:]]
    for r in range(1, rows):
        newp = perm[:]
        i = 0 if r % 2 == 1 else 1     # first change swaps from the front
        while i + 1 < n:
            newp[i], newp[i + 1] = newp[i + 1], newp[i]
            i += 2
        perm = newp
        out.append(perm[:])
    return out


def change_ring(root, scale, n_bells, total_steps, register, vel_base=90):
    """A peal: one bell struck per 16th, permuted row by row via plain hunting.
    With n_bells dividing total_steps and rows = total_steps/n_bells a multiple
    of 2*n_bells, the loop ends on rounds."""
    bells = [scale_degree(root, scale, d) for d in range(n_bells)]
    rows = plain_hunt(n_bells, total_steps // n_bells)
    cell, onset = [], 0
    for row in rows:
        for j, b in enumerate(row):
            pitch = P.clamp_register(bells[b], *register)
            accent = 12 if j == 0 else 0        # stress the lead bell of each row
            cell.append((onset, 1, pitch, min(127, vel_base + accent)))
            onset += 1
    return cell[:total_steps]


# Historical grounds as scale-degree root sequences (negative = below the tonic),
# realized diatonically in whatever mode the family uses.
GROUNDS = {
    "lament":     [0, -1, -2, -3],                    # descending tetrachord (Dido's Lament)
    "folia":      [0, -3, 0, -1, 2, -1, 0, -3],       # La Folia (i-V-i-VII-III-VII-i-V)
    "romanesca":  [2, -1, 0, -3],                     # descending-third ground
    "passamezzo": [0, -1, 0, -3, 2, -1, 0, -3],       # Passamezzo antico
    "pachelbel":  [0, -3, -2, 2, 3, 0, 3, -3],        # Canon bass (I-V-vi-iii-IV-I-IV-V)
}


def ground_bass(root, scale, name, total_steps, register=(36, 55), vel_base=96):
    degs = GROUNDS[name]
    seg = total_steps // len(degs)
    cell = []
    for i, deg in enumerate(degs):
        onset = i * seg
        dur = (total_steps - onset) if i == len(degs) - 1 else seg
        pitch = P.clamp_register(scale_degree(root, scale, deg), *register)
        cell.append((onset, dur, pitch, vel_base + (10 if i == 0 else 0)))
    return cell


def hocket(cell):
    """Split a melodic cell into two interlocking voices (odd/even onsets)."""
    a = [n for k, n in enumerate(cell) if k % 2 == 0]
    b = [n for k, n in enumerate(cell) if k % 2 == 1]
    return a, b


# ============================================================ planetary families
# (index, planet, day, bpm, root, scale, technique, mel_prog, bass_prog, beats)
#   technique: ("iso", color, talea) | ("ring", n_bells) | ("hocket-ring", n)
#              | ("mystic-arp",) | ("hook",);  bass: ground name or "drone"
PLANETS = [
    dict(i=1, planet="Luna", day="Mon", bpm=60, root=54, scale="hirajoshi",
         mel=("iso", [0, 2, 1, 4, 2], [3, 3, 2]), bass="lament",
         mel_prog=10, bass_prog=89, beats=["halftime", "headnod"], organum=False,
         note="silvery koto over a tidal lament tetrachord"),
    dict(i=2, planet="Mercury", day="Wed", bpm=132, root=50, scale="whole_tone",
         mel=("ring", 4), bass="drone",
         mel_prog=6, bass_prog=38, beats=["motorik", "broken"], organum=False,
         note="mercurial harpsichord change-ringing in Messiaen's whole-tone"),
    dict(i=3, planet="Venus", day="Fri", bpm=88, root=52, scale="mystic",
         mel=("mystic-arp",), bass="romanesca",
         mel_prog=46, bass_prog=32, beats=["headnod", "halftime"], organum=False,
         note="Scriabin mystic-chord harp over a Romanesca ground"),
    dict(i=4, planet="Sol", day="Sun", bpm=100, root=55, scale="lydian",
         mel=("iso", [0, 2, 4, 5, 6], [3, 2, 3, 5, 1]), bass="pachelbel",
         mel_prog=19, bass_prog=48, beats=["fourfloor", "motorik"], organum=True,
         note="radiant Lydian isorhythm, organum fifths, Canon ground"),
    dict(i=5, planet="Mars", day="Tue", bpm=120, root=45, scale="phrygian_dominant",
         mel=("hocket-ring", 4), bass="passamezzo",
         mel_prog=61, bass_prog=38, beats=["broken", "motorik"], organum=True,
         note="martial Freygish peal, hocketed between two brass voices"),
    dict(i=6, planet="Jupiter", day="Thu", bpm=96, root=43, scale="dorian",
         mel=("hook",), bass="folia",
         mel_prog=48, bass_prog=48, beats=["halftime", "fourfloor"], organum=True,
         note="majestic Dorian hook over La Folia, organum-thickened"),
    dict(i=7, planet="Saturn", day="Sat", bpm=52, root=48, scale="octatonic",
         mel=("iso", [0, 1, 3, 4, 6], [4, 2, 2, 4, 3, 1]), bass="lament",
         mel_prog=14, bass_prog=48, beats=["halftime"], organum=False,
         note="leaden octatonic isorhythm on tubular bells, long talea"),
]


def build_melody(rng, fam):
    root, scale = fam["root"], fam["scale"]
    reg = (60, 84)
    tech = fam["mel"]
    kind = tech[0]
    if kind == "iso":
        return isorhythm(root, scale, tech[1], tech[2], LOOP, reg)
    if kind == "ring":
        return change_ring(root, scale, tech[1], LOOP, reg)
    if kind == "hocket-ring":
        return change_ring(root, scale, tech[1], LOOP, reg)   # split later
    if kind == "mystic-arp":
        chord = P.spread_chord(root, scale, (0, 1, 2, 3, 4, 5))  # the mystic chord voiced up
        return P.arpeggiate(rng, chord, LOOP, rate=1, direction="updown",
                            register=reg, gate=0.85)
    # hook
    ante, cons = P.hook_phrase(rng, root, scale, reg)
    return LK._rebase(ante) + [(o + BAR, d, p, v) for (o, d, p, v) in cons]


def build_family(fam):
    rng = LK.random.Random(9000 + fam["i"])
    root, scale, bpm = fam["root"], fam["scale"], fam["bpm"]
    folder = os.path.join(DEST, f"{fam['i']:02d}_{fam['planet']}_{bpm}_{_tag(root, scale)}")
    for sub in ("beats", "bass", "melody"):
        os.makedirs(os.path.join(folder, sub), exist_ok=True)

    # beats: reuse loopkit's feels that fit this planet's character
    beat_fns = dict((name, (fn, sw)) for name, fn, sw in LK.BEATS)
    first_beat = None
    for feel in fam["beats"]:
        fn, sw = beat_fns[feel]
        ev = LK._humanize(fn(LK.random.Random(int(rng.random() * 1e9))), bpm, True, sw)
        LK._write(os.path.join(folder, "beats", f"{feel}.mid"), ev, bpm, DRUM_CH, None,
                  f"{fam['planet']}-{feel}")
        first_beat = first_beat or ev

    # bass: historical ground, or a modal drone-pulse
    if fam["bass"] == "drone":
        bass_cell = None
        bass_ev = LK._humanize(LK.bass_dronepulse(rng, root, scale), bpm, False, False)
    else:
        bass_cell = ground_bass(root, scale, fam["bass"], LOOP)
        bass_ev = LK._humanize(LK._notes_to_events(bass_cell, 0), bpm, False, False)
    LK._write(os.path.join(folder, "bass", f"{fam['bass']}.mid"), bass_ev, bpm, 0,
              fam["bass_prog"], f"{fam['planet']}-bass")

    # melody via the family's technique
    mel_cell = build_melody(rng, fam)
    if fam["mel"][0] == "hocket-ring":
        va, vb = hocket(mel_cell)
        mel_ev = LK._humanize(LK._notes_to_events(va, 1), bpm, False, False)
        vb_ev = LK._humanize(LK._notes_to_events(vb, 2), bpm, False, False)
        LK._write(os.path.join(folder, "melody", "hocket_voice-A.mid"), mel_ev, bpm, 1,
                  fam["mel_prog"], f"{fam['planet']}-hocketA")
        LK._write(os.path.join(folder, "melody", "hocket_voice-B.mid"), vb_ev, bpm, 2,
                  fam["mel_prog"], f"{fam['planet']}-hocketB")
        combo_extra = {"events": vb_ev, "channel": 2, "program": fam["mel_prog"], "name": "hocketB"}
    else:
        mel_ev = LK._humanize(LK._notes_to_events(mel_cell, 1), bpm, False, False)
        name = {"iso": "isorhythm", "ring": "change-ringing",
                "mystic-arp": "mystic-arp", "hook": "hook"}[fam["mel"][0]]
        LK._write(os.path.join(folder, "melody", f"{name}.mid"), mel_ev, bpm, 1,
                  fam["mel_prog"], f"{fam['planet']}-{name}")
        combo_extra = None

    # organum: a parallel-fifth doubling (medieval tone) as its own stem + in combo
    if fam["organum"]:
        org_cell = P.harmonize(mel_cell, 7)
        org_ev = LK._humanize(LK._notes_to_events(org_cell, 3), bpm, False, False)
        LK._write(os.path.join(folder, "melody", "organum-fifths.mid"), org_ev, bpm, 3,
                  fam["mel_prog"], f"{fam['planet']}-organum")
        if combo_extra is None:
            combo_extra = {"events": org_ev, "channel": 3, "program": fam["mel_prog"], "name": "organum"}

    tracks = [{"events": first_beat, "channel": DRUM_CH, "name": "drums"},
              {"events": bass_ev, "channel": 0, "program": fam["bass_prog"], "name": "bass"},
              {"events": mel_ev, "channel": 1, "program": fam["mel_prog"], "name": "melody"}]
    if combo_extra:
        tracks.append(combo_extra)
    midiwriter.write_combined(os.path.join(folder, "combo_preview.mid"), tracks,
                              [(0, bpm)], [(0, (4, 4))])

    n = len(fam["beats"]) + 1 + (2 if fam["mel"][0] == "hocket-ring" else 1) + (1 if fam["organum"] else 0)
    return folder, n, fam["note"]


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    lines, total = [], 0
    for fam in PLANETS:
        folder, n, note = build_family(fam)
        total += n
        base = os.path.basename(folder)
        print(f"  {base:<26} {n:>2} loops   {note}")
        lines.append(f"{base}\n    {note}")
    with open(os.path.join(DEST, "README.txt"), "w") as fh:
        fh.write(_README + "\n\n" + "\n".join(lines) + "\n")
    print(f"\n{total} loops across {len(PLANETS)} planetary families -> {DEST}")


_README = """CODEX -- loops from historical & esoteric practice (music of the spheres)
========================================================================
Same stack-anything format as loopkit (2-bar, 16th-grid, hit on beat 1,
707-native drums on pads 36-51), but built from old techniques:

  isorhythm (talea vs color, 14th c.) . change ringing (plain hunt) .
  ground bass (lament / Folia / Romanesca / Passamezzo / Pachelbel) .
  hocket (interlocking voices) . organum (parallel fifths) .
  Messiaen / Scriabin / Byzantine / Freygish scales.

Seven families = the seven classical planets, each its own mode + technique
+ archaic instrument tone. Inside each: beats/ bass/ melody/ + combo_preview.
Melody stems named for the technique; 'organum-fifths' and 'hocket_voice-B'
are extra interlocking/parallel voices you can layer or leave out."""


if __name__ == "__main__":
    main()
