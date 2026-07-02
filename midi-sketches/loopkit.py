#!/usr/bin/env python3
"""Solid, ready-to-play LOOPS -- beats, rhythm sequences, and melodies -- as
short, seamless, grab-and-stack clips (the opposite of the long arrangements).

Everything here is:
  * 2 bars on a locked 16th grid, with a hit on beat 1 (no dead space),
  * organized into tempo+key FAMILIES so any beat + any bass + any melody from
    one family folder is guaranteed in-key and in-tempo -- stack them freely,
  * 707-native: drum loops use only pad notes 36-51 (no remap needed),
  * reproducible from the family seed.

    python loopkit.py            ->  output/loopkit/<family>/{beats,bass,melody}/

Layout:
    output/loopkit/<NN_Name_bpm_Key>/
        beats/   <feel>.mid            (drums, channel 10, pads 36-51)
        bass/    <style>.mid           (rhythm sequences)
        melody/  <style>.mid           (hooks / arps / ostinato cells)
        combo_preview.mid              (one beat+bass+melody stacked, GM preview)
"""

import os
import random
import shutil

import drums as D
import humanize
import midiwriter
import palette as P
from midiwriter import Event
from rhythm import euclid_grid, euclidean_preset_tiled, grid_from_hits, grid_to_events

HERE = os.path.dirname(__file__)
DEST = os.path.join(HERE, "output", "loopkit")

STEP = 120                 # ticks per 16th at PPQ 480
BAR = 16                   # steps per bar
LOOP = 2 * BAR             # 32-step (2-bar) loops
PPQ = midiwriter.PPQ
DRUM_CH = 9

# tempo+key families spanning the useful range; each is one coherent pocket.
FAMILIES = [
    # (seed, name, bpm, root_midi, scale, melody_prog, bass_prog)
    (2101, "SlowDrift",  62, 50,           "aeolian",  5, 38),   # D  aeolian  (Rhodes)
    (2102, "Midnight",   72, 54,           "phrygian", 89, 39),  # F# phrygian (pad / synth bass)
    (2103, "Halftime",   84, 52,           "dorian",   4, 33),   # E  dorian
    (2104, "HeadNod",    96, 45,           "aeolian",  11, 38),  # A  aeolian  (vibes)
    (2105, "Pulse",     110, 48,           "phrygian", 80, 38),  # C  phrygian (square lead)
    (2106, "Idioteque", 124, 43,           "aeolian",  81, 38),  # G  aeolian  (saw lead)
]

# per-voice base velocities for drum loops
VEL = {D.KICK: 112, D.SNARE: 104, D.CLAP: 100, D.RIM: 88,
       D.CHH: 80, D.OHH: 92, D.PHH: 70, D.RIDE: 84,
       D.LTOM2: 100, D.LTOM: 100, D.MTOM: 98, D.MTOM2: 96, D.HTOM: 94, D.HTOM2: 92,
       D.CRASH: 100}


# ----------------------------------------------------------------------------- beats
def _drum(grid_map, accents=None):
    """Turn {note: 32-char grid} into channel-10 events."""
    accents = accents or {}
    out = []
    for note, grid in grid_map.items():
        out += grid_to_events(grid, note, STEP, vel=VEL.get(note, 90),
                              accent_steps=accents.get(note), channel=DRUM_CH)
    return out


def _bars(a, b):
    """Concatenate two 16-step grids into a 2-bar loop."""
    return a + b


def beat_halftime(rng):
    kick = _bars(grid_from_hits(16, {0, 10}), grid_from_hits(16, {0, 7, 10}))
    snare = _bars(grid_from_hits(16, {8}), grid_from_hits(16, {8, 14}))
    chh = (grid_from_hits(16, {0, 2, 4, 6, 8, 10, 12, 14})) * 2
    ohh = _bars(grid_from_hits(16, {6}), grid_from_hits(16, {6, 15}))
    return _drum({D.KICK: kick, D.SNARE: snare, D.CHH: chh, D.OHH: ohh})


def beat_fourfloor(rng):
    kick = grid_from_hits(16, {0, 4, 8, 12}) * 2
    clap = grid_from_hits(16, {4, 12}) * 2
    chh = grid_from_hits(16, {2, 6, 10, 14}) * 2
    ohh = _bars(grid_from_hits(16, set()), grid_from_hits(16, {14}))
    return _drum({D.KICK: kick, D.CLAP: clap, D.CHH: chh, D.OHH: ohh})


def beat_broken(rng):
    kick = _bars(euclid_grid(5, 16, rng.randint(0, 3)), euclid_grid(5, 16, rng.randint(0, 3)))
    snare = grid_from_hits(16, {4, 12}) * 2
    ghost = grid_from_hits(16, {7, 15}) * 2
    hats = _bars(euclid_grid(9, 16, 1), euclid_grid(11, 16, 2))   # glitchy 16ths
    return _drum({D.KICK: kick, D.SNARE: snare, D.RIM: ghost, D.CHH: hats})


def beat_tribal(rng):
    cross = P.euclid_cross(rng, 16, [(D.LTOM2, 3, 0), (D.MTOM, 5, 1), (D.HTOM, 7, 3)])
    kick = grid_from_hits(16, {0, 8}) * 2
    rim = euclidean_preset_tiled("cinquillo", 16) * 2          # clave-ish
    gm = {D.KICK: kick, D.RIM: rim}
    for note, g in cross.items():
        gm[note] = g * 2
    return _drum(gm)


def beat_headnod(rng):
    kick = _bars(grid_from_hits(16, {0, 11}), grid_from_hits(16, {0, 6, 11}))
    snare = grid_from_hits(16, {8}) * 2
    chh = grid_from_hits(16, {0, 3, 4, 6, 8, 11, 12, 14}) * 2   # loose, swung later
    return _drum({D.KICK: kick, D.SNARE: snare, D.CHH: chh})


def beat_motorik(rng):
    kick = grid_from_hits(16, {0, 4, 8, 12}) * 2
    snare = grid_from_hits(16, {4, 12}) * 2
    chh = grid_from_hits(16, set(range(16))) * 2               # driving 16ths
    return _drum({D.KICK: kick, D.SNARE: snare, D.CHH: chh})


BEATS = [("halftime", beat_halftime, True), ("fourfloor", beat_fourfloor, False),
         ("broken", beat_broken, False), ("tribal-toms", beat_tribal, False),
         ("headnod", beat_headnod, True), ("motorik", beat_motorik, False)]


# ----------------------------------------------------------------------------- bass
def _rebase(cell):
    """Shift a (onset, dur, pitch, vel) cell so its first onset sits on step 0."""
    if not cell:
        return cell
    shift = min(o for o, *_ in cell)
    return [(o - shift, dr, p, v) for (o, dr, p, v) in cell]


def _notes_to_events(cell, channel, offset_steps=0):
    return [Event((o + offset_steps) * STEP, dr * STEP, p, v, channel) for (o, dr, p, v) in cell]


def bass_ostinato(rng, root, scale):
    cell = _rebase(P.ostinato_cell(rng, root, scale, (36, 55), vel_base=96))
    return _notes_to_events(cell, 0) + _notes_to_events(cell, 0, BAR)   # identical repeat


def bass_dronepulse(rng, root, scale):
    grid = euclidean_preset_tiled("tresillo", 16)
    fifth = P.scale_degree(root, scale, 4)
    ev = []
    for bar in range(2):
        for i, ch in enumerate(grid):
            if ch in "xX":
                pitch = fifth if i in (6, 10) else root
                ev.append(Event((bar * BAR + i) * STEP, STEP * 2, pitch, 92 + (12 if i == 0 else 0), 0))
    return ev


def bass_angular(rng, root, scale):
    ev = []
    for bar in range(2):
        for (o, dr, p, v) in P.bass_phrase(rng, root, scale, BAR, (36, 55)):
            ev.append(Event((bar * BAR + o) * STEP, dr * STEP, p, v, 0))
    return ev


def bass_walk(rng, root, scale):
    # steadier: one note per beat, mostly stepwise
    degs = P.scale_walk(rng, 0, 8, leap_prob=0.1, root_pull=0.3)
    ev = []
    for i, dg in enumerate(degs):
        p = P.clamp_register(P.scale_degree(root, scale, dg), 36, 55)
        ev.append(Event(i * 4 * STEP, 4 * STEP, p, 90 + (12 if i % 4 == 0 else 0), 0))
    return ev


BASS = [("ostinato-riff", bass_ostinato), ("drone-pulse", bass_dronepulse),
        ("angular", bass_angular), ("walking", bass_walk)]


# ----------------------------------------------------------------------------- melody
def mel_hook(rng, root, scale):
    ante, cons = P.hook_phrase(rng, root, scale, (60, 79))
    return _notes_to_events(_rebase(ante), 1) + _notes_to_events(cons, 1, BAR)


def mel_arp_up(rng, root, scale):
    chord = P.spread_chord(root, scale, (0, 2, 4, 6, 7))       # 5 tones -> coprime drift
    cell = P.arpeggiate(rng, chord, LOOP, rate=1, direction="up", register=(60, 84), gate=0.85)
    return _notes_to_events(cell, 1)


def mel_arp_updown(rng, root, scale):
    chord = P.spread_chord(root, scale, (0, 2, 4, 6))
    cell = P.arpeggiate(rng, chord, LOOP, rate=2, direction="updown", register=(60, 84), gate=0.9)
    return _notes_to_events(cell, 1)


def mel_cell(rng, root, scale):
    cell = _rebase(P.ostinato_cell(rng, root, scale, (62, 81), vel_base=92))
    return _notes_to_events(cell, 1) + _notes_to_events(cell, 1, BAR)


MELODY = [("hook", mel_hook), ("arp-drift", mel_arp_up),
          ("arp-updown", mel_arp_updown), ("ostinato-cell", mel_cell)]


# ----------------------------------------------------------------------------- glue
def _anchor(events):
    """Guarantee no dead space: any event humanized to within half a step of the
    downbeat is snapped exactly onto beat 1."""
    half = STEP // 2
    return [e._replace(start=0) if 0 <= e.start < half else e for e in events]


def _humanize(events, bpm, channel_is_drum, swung):
    if not events:
        return events
    ev = events
    if swung:
        ev = humanize.swing(ev, STEP, swing_pct=humanize.sixteenth_swing_pct(bpm))
    ev = humanize.pink_jitter(ev, bpm, PPQ, sd_ms=8 if channel_is_drum else 11,
                              seed=len(ev) * 7 + int(bpm))
    return _anchor(ev)


def _write(path, events, bpm, channel, program, name):
    midiwriter.write_track(path, events, [(0, bpm)], [(0, (4, 4))],
                           channel=channel, program=program, track_name=name)


def build_family(seed, name, bpm, root, scale, mel_prog, bass_prog, index):
    rng = random.Random(seed)
    folder = os.path.join(DEST, f"{index:02d}_{name}_{bpm}_{_keytag(root, scale)}")
    for sub in ("beats", "bass", "melody"):
        os.makedirs(os.path.join(folder, sub), exist_ok=True)

    made = {"beats": [], "bass": [], "melody": []}

    for feel, fn, swung in BEATS:
        ev = _humanize(fn(random.Random(int(rng.random() * 1e9))), bpm, True, swung)
        p = os.path.join(folder, "beats", f"{feel}.mid")
        _write(p, ev, bpm, DRUM_CH, None, f"{name}-{feel}")
        made["beats"].append((feel, ev))

    for style, fn in BASS:
        ev = _humanize(fn(random.Random(int(rng.random() * 1e9)), root, scale), bpm, False, False)
        p = os.path.join(folder, "bass", f"{style}.mid")
        _write(p, ev, bpm, 0, bass_prog, f"{name}-bass-{style}")
        made["bass"].append((style, ev))

    for style, fn in MELODY:
        ev = _humanize(fn(random.Random(int(rng.random() * 1e9)), root, scale), bpm, False, False)
        p = os.path.join(folder, "melody", f"{style}.mid")
        _write(p, ev, bpm, 1, mel_prog, f"{name}-mel-{style}")
        made["melody"].append((style, ev))

    # one stacked preview: first beat + first bass + first melody
    midiwriter.write_combined(
        os.path.join(folder, "combo_preview.mid"),
        [{"events": made["beats"][0][1], "channel": DRUM_CH, "name": "drums"},
         {"events": made["bass"][0][1], "channel": 0, "program": bass_prog, "name": "bass"},
         {"events": made["melody"][0][1], "channel": 1, "program": mel_prog, "name": "melody"}],
        [(0, bpm)], [(0, (4, 4))])

    n = sum(len(v) for v in made.values())
    return folder, n


_SCALE_TAG = {"aeolian": "m", "dorian": "dor", "phrygian": "phr", "major": "maj"}
_PC = ["C", "Cs", "D", "Ds", "E", "F", "Fs", "G", "Gs", "A", "As", "B"]


def _keytag(root, scale):
    return f"{_PC[root % 12]}{_SCALE_TAG.get(scale, 'mod')}"


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    total = 0
    for i, fam in enumerate(FAMILIES, 1):
        folder, n = build_family(*fam, index=i)
        total += n
        print(f"  {os.path.basename(folder):<26} {n:>3} loops")
    print(f"\n{total} loops across {len(FAMILIES)} families -> {DEST}")


if __name__ == "__main__":
    main()
