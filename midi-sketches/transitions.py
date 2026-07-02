#!/usr/bin/env python3
"""TRANSITIONS -- the connective tissue between clips that live sets need:
fills, risers, turnarounds, and stops (improvement plan phase 5).

Everything is 707-native (drums on pads 36-51), starts with a hit on beat 1
(clip-launch safe), and is groove-engined. Drum transitions are key-agnostic;
the pitched risers come in the six core slot keys.

    transitions/
      fills/        <style>_<bpm>.mid      1 bar: groove front, fill back
      risers/       <style>_<bpm>.mid      2 bars: building tension into a drop
      turnarounds/  full_<bpm>.mid         2 bars: groove bar + fill bar
      stops/        stop_<bpm>.mid         1 bar: one downbeat hit, then air
      pitched/      climb_<Key>_<bpm>.mid  2-bar scale climb, crescendo

    python transitions.py   ->  output/transitions/
"""

import csv
import os
import random
import shutil
import zlib

import groove as G
import midiwriter
from midiwriter import Event
from songcraft import anchor, voice_into
from theory import scale_degree

HERE = os.path.dirname(__file__)
DEST = os.path.join(HERE, "output", "transitions")
PPQ = midiwriter.PPQ
STEP = PPQ // 4

TEMPOS = [72, 84, 96, 110, 124]
FEEL = {72: "ritual", 84: "laidback", 96: "laidback", 110: "pushing", 124: "pushing"}

SLOTS = [("Dm", 62, 50, "aeolian"), ("Fsphr", 72, 54, "phrygian"),
         ("Edor", 84, 52, "dorian"), ("Am", 96, 45, "aeolian"),
         ("Cphr", 110, 48, "phrygian"), ("Gm", 124, 43, "aeolian")]


def _hit(step, note, vel, dur=1):
    return Event(step * STEP, dur * STEP, note, min(127, vel), 9)


def _groove_front(rng):
    """The first half-bar of a generic groove, so the clip launches seamlessly."""
    ev = [_hit(0, 36, 106), _hit(4, 38, 92), _hit(6, 36, 88)]
    ev += [_hit(s, 42, 70 + rng.randint(-4, 4)) for s in (0, 2, 4, 6)]
    return ev


# ---------------------------------------------------------------- fills (1 bar)
def fill_tomrun(rng):
    ev = _groove_front(rng)
    toms = [41, 45, 47, 48, 50, 48, 47, 50]
    for i in range(8):
        ev.append(_hit(8 + i, toms[i], 72 + i * 6))
    return ev


def fill_snarebuild(rng):
    ev = _groove_front(rng)
    for i in range(8):
        ev.append(_hit(8 + i, 38, 56 + i * 8))
    return ev


def fill_kickroll(rng):
    ev = _groove_front(rng)
    ev += [_hit(8, 38, 94), _hit(10, 42, 72)]
    for i, s in enumerate((12, 13, 14, 15)):
        ev.append(_hit(s, 36, 84 + i * 10))
    return ev


def fill_clapcascade(rng):
    ev = _groove_front(rng)
    for i, s in enumerate((8, 10, 12, 13, 14, 15)):
        ev.append(_hit(s, 39, 66 + i * 9))
    return ev


def fill_hatchoke(rng):
    ev = _groove_front(rng)
    ev += [_hit(8, 36, 100), _hit(10, 46, 96), _hit(12, 46, 104, dur=2)]
    ev.append(_hit(15, 42, 60))          # the choke tick before the drop
    return ev


FILLS = {"tomrun": fill_tomrun, "snarebuild": fill_snarebuild, "kickroll": fill_kickroll,
         "clapcascade": fill_clapcascade, "hatchoke": fill_hatchoke}


# ---------------------------------------------------------------- risers (2 bars)
def riser_snare(rng):
    """8ths -> 16ths snare crescendo across 2 bars -- the classic build."""
    ev = [_hit(0, 36, 104)]
    for s in range(0, 16, 2):
        ev.append(_hit(s, 38, 48 + s * 2))
    for s in range(16, 32):
        ev.append(_hit(s, 38, 66 + (s - 16) * 4))
    return ev


def riser_tomclimb(rng):
    ev = [_hit(0, 36, 104)]
    ladder = [41, 43, 45, 47, 48, 50]
    for i, s in enumerate(range(0, 32, 2)):
        note = ladder[min(len(ladder) - 1, i * len(ladder) // 16)]
        ev.append(_hit(s, note, 58 + i * 4))
        if s >= 24:
            ev.append(_hit(s + 1, note, 50 + i * 4))
    return ev


RISERS = {"snare": riser_snare, "tomclimb": riser_tomclimb}


# ---------------------------------------------------------------- stops / turnarounds
def stop_bar(rng):
    """One downbeat hit, then a bar of air -- the drama move."""
    return [_hit(0, 36, 112), _hit(0, 49, 108, dur=4)]


def turnaround(rng):
    groove = [_hit(0, 36, 106), _hit(4, 38, 94), _hit(6, 36, 86), _hit(10, 36, 90), _hit(12, 38, 96)]
    groove += [_hit(s, 42, 70) for s in range(0, 16, 2)]
    fill = [e._replace(start=e.start + 16 * STEP) for e in fill_tomrun(rng)]
    return groove + fill


# ---------------------------------------------------------------- pitched climbs
def pitched_climb(rng, root, scale):
    """A 2-bar scale climb, low to high, crescendo -- tension into a section."""
    ev = []
    for i, s in enumerate(range(0, 32, 2)):
        pitch = voice_into(scale_degree(root, scale, i), 48, 88)
        ev.append(Event(s * STEP, 2 * STEP, pitch, min(127, 52 + i * 4), 1))
    return ev


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    for d in ("fills", "risers", "turnarounds", "stops", "pitched"):
        os.makedirs(os.path.join(DEST, d))
    rows = []

    def write(sub, fname, ev, bpm, channel=9, program=None):
        midiwriter.write_track(os.path.join(DEST, sub, fname), ev, [(0, bpm)], [(0, (4, 4))],
                               channel=channel, program=program, track_name=fname[:-4])
        rows.append([f"{sub}/{fname}", sub, bpm])

    for bpm in TEMPOS:
        feel = FEEL[bpm]
        for style, fn in FILLS.items():
            rng = random.Random(zlib.crc32(f"fill|{style}|{bpm}".encode()))
            ev = anchor(G.apply_feel(fn(rng), feel, bpm, PPQ, rng), STEP)
            write("fills", f"{style}_{bpm}.mid", ev, bpm)
        for style, fn in RISERS.items():
            rng = random.Random(zlib.crc32(f"riser|{style}|{bpm}".encode()))
            ev = anchor(G.apply_feel(fn(rng), "machine", bpm, PPQ, rng), STEP)
            write("risers", f"{style}_{bpm}.mid", ev, bpm)
        rng = random.Random(zlib.crc32(f"turn|{bpm}".encode()))
        write("turnarounds", f"full_{bpm}.mid",
              anchor(G.apply_feel(turnaround(rng), feel, bpm, PPQ, rng), STEP), bpm)
        rng = random.Random(zlib.crc32(f"stop|{bpm}".encode()))
        write("stops", f"stop_{bpm}.mid", stop_bar(rng), bpm)

    for key, bpm, root, scale in SLOTS:
        rng = random.Random(zlib.crc32(f"climb|{key}".encode()))
        ev = anchor(G.apply_feel(pitched_climb(rng, root, scale), "machine", bpm, PPQ, rng), STEP)
        write("pitched", f"climb_{key}_{bpm}.mid", ev, bpm, channel=1, program=81)

    with open(os.path.join(DEST, "INDEX.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["file", "type", "bpm"])
        w.writerows(rows)
    with open(os.path.join(DEST, "README.txt"), "w") as fh:
        fh.write(__doc__)
    print(f"{len(rows)} transition clips -> {DEST}")


if __name__ == "__main__":
    main()
