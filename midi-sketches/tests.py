#!/usr/bin/env python3
"""Invariant tests for the whole toolkit -- the 'can this ever silently rot'
detector. Run: python tests.py  (exits non-zero on failure).

Covers the rules we actually shipped bugs against:
  1. no dead space: every loop/stem's first onset is on (or within half a step
     of) beat 1
  2. 707-native drums: loop-pack drum stems only use pad notes 36-51
  3. change-ringing closure: a plain-hunt course returns to rounds
  4. groove invariants: accents never zero a velocity, feels never move beat 1,
     vary_cell keeps the head identical, breathe leaves real silence
  5. generator QC: a seed regenerates identically (bit-for-bit determinism)
  6. swing axis: sixteenth_swing_pct stays in the 16th-note range (50-62%),
     never the 8th-note BUR range that once broke broken_meter
"""

import os
import random
import sys

import groove as G
import generator
import humanize
from midiwriter import Event

HERE = os.path.dirname(__file__)
FAILURES = []


def check(name, cond, detail=""):
    status = "ok" if cond else "FAIL"
    print(f"  [{status}] {name}" + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        FAILURES.append(name)


def test_no_dead_space_and_pads():
    import mido
    packs = ["output/loopkit", "output/codex", "output/holy_mountain/loops", "output/stemlib"]
    # sophia stems are timeline-aligned (bass/arp enter late by design) -- bed anchors checked in sophia.py validation
    dead, offpad, n = [], [], 0
    for pack in packs:
        root = os.path.join(HERE, pack)
        if not os.path.isdir(root):
            continue
        for dirpath, _, files in os.walk(root):
            for f in files:
                if not f.endswith(".mid"):
                    continue
                n += 1
                path = os.path.join(dirpath, f)
                first = None
                for tr in mido.MidiFile(path).tracks:
                    tick = 0
                    for msg in tr:
                        tick += msg.time
                        if msg.type == "note_on" and msg.velocity > 0:
                            if first is None or tick < first:
                                first = tick
                            if msg.channel == 9 and not (36 <= msg.note <= 51):
                                offpad.append(f)
                # hocket voice B interlocks off the beat by design
                if first is not None and first > 60 and "voice-B" not in f:
                    dead.append((f, first))
    check(f"no dead space across {n} loop files", not dead, str(dead[:3]))
    check("all loop drums on pads 36-51", not offpad, str(offpad[:3]))


def test_ring_closure():
    import codex
    for bells in (3, 4, 5, 6):
        rows = codex.plain_hunt(bells, 2 * bells + 1)
        check(f"plain hunt on {bells} closes to rounds after {2*bells} rows",
              rows[-1] == rows[0] == list(range(bells)))


def test_groove_invariants():
    rng = random.Random(7)
    ev = [Event(i * 120, 120, 38, 90, 9) for i in range(16)]
    acc = G.apply_accents(ev, 120)
    check("accents keep velocities in 1..127",
          all(1 <= e.vel <= 127 for e in acc))
    check("downbeat is the accent peak",
          acc[0].vel == max(e.vel for e in acc))

    felt = G.apply_feel(ev, "laidback", 96, 480, rng)
    check("feel never moves beat 1", felt[0].start == 0)
    check("feel never sends events negative", all(e.start >= 0 for e in felt))

    cell = [(0, 2, 60, 90), (4, 2, 62, 88), (8, 2, 64, 86), (12, 4, 65, 92)]
    var = G.vary_cell(random.Random(3), cell)
    head = [n for n in cell if n[0] < 16 * 0.7]
    check("vary_cell keeps the head identical",
          [n for n in var if n[0] < 16 * 0.7][: len(head)] == head or
          all(a == b for a, b in zip(sorted(head), sorted(n for n in var if n[0] < 11))))

    br = G.breathe(cell, gap=3)
    check("breathe leaves the bar tail silent",
          all(o + d <= 13 for (o, d, _, _) in br) and br)


def test_generator_determinism():
    a = generator.generate(seed=8001, archetype="fever_ray")
    b = generator.generate(seed=8001, archetype="fever_ray")
    same = all(a["result"][p] == b["result"][p] for p in ("drums", "bass", "melody"))
    check("seed 8001 fever_ray is bit-for-bit deterministic", same)
    vels = [e.vel for e in a["result"]["drums"]]
    check("groove pass gives drums a real dynamic range (>=60)",
          max(vels) - min(vels) >= 60, f"range={max(vels)-min(vels)}")


def test_swing_axis():
    vals = [humanize.sixteenth_swing_pct(b) for b in (60, 80, 100, 120, 140, 160)]
    check("sixteenth swing stays in 50-62% (never 8th-note BUR range)",
          all(50 <= v <= 62 for v in vals), str(vals))


if __name__ == "__main__":
    for t in (test_no_dead_space_and_pads, test_ring_closure, test_groove_invariants,
              test_generator_determinism, test_swing_axis):
        print(t.__name__)
        t()
    if FAILURES:
        print(f"\n{len(FAILURES)} FAILED: {FAILURES}")
        sys.exit(1)
    print("\nall invariants hold")
