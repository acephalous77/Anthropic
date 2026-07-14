#!/usr/bin/env python3
"""A/B demo of the groove engine: the SAME musical material (same seeds, same
patterns, 96 bpm A aeolian -- the HeadNod family) rendered two ways:

  old/  the current loop pipeline: flat per-voice velocities, uniform pink
        jitter, a 2-bar cell repeated verbatim.
  new/  the groove engine: ghost notes, metric accent hierarchy, laid-back
        role-based microtiming (snare drags, bass sits behind the kick),
        AAAB repetition (3 identical statements, then a varied turnaround),
        and a melody that breathes (real rests at phrase ends).

    python ab_demo.py   ->  output/ab_demo/{old,new}/{drums,bass,melody,combo}.mid
"""

import os
import random
import shutil

import groove as G
import humanize
import loopkit as LK
import midiwriter
import palette as P
from midiwriter import Event
from rhythm import grid_to_events

HERE = os.path.dirname(__file__)
DEST = os.path.join(HERE, "output", "ab_demo")

BPM = 96
ROOT, SCALE = 45, "aeolian"          # the HeadNod family: A aeolian
STEP, BAR = LK.STEP, LK.BAR
PPQ = midiwriter.PPQ
MEL_PROG, BASS_PROG = 11, 38         # vibraphone / synth bass

# the head-nod drum cell (one bar), as grids -- identical source for both renders
DRUM_CELL = {
    "kick":  "x.....x....x....".replace("x", "x"),   # 0, 6, 11 -> see below
    "snare": "........x.......",
    "chh":   "x..xx.x.x..xx.x.",
}
DRUM_CELL["kick"] = "".join("x" if i in (0, 6, 11) else "." for i in range(16))
DRUM_NOTE = {"kick": (36, 112), "snare": (38, 104), "chh": (42, 80)}


def drum_events_from(grids, bar_offset=0):
    ev = []
    for voice, grid in grids.items():
        note, vel = DRUM_NOTE.get(voice, (45, 98))
        ev += grid_to_events(grid, note, STEP, start_tick=bar_offset * BAR * STEP,
                             vel=vel, channel=9)
    return ev


def material():
    """The shared musical material, from fixed seeds."""
    bass_cell = LK._rebase(P.ostinato_cell(random.Random(4104), ROOT, SCALE, (36, 55), vel_base=96))
    ante, cons = P.hook_phrase(random.Random(5104), ROOT, SCALE, (60, 79))
    return bass_cell, LK._rebase(ante), cons


# ------------------------------------------------------------------ OLD pipeline
def render_old():
    bass_cell, ante, cons = material()
    drums = drum_events_from(DRUM_CELL, 0) + drum_events_from(DRUM_CELL, 1)
    drums = LK._humanize(drums, BPM, True, True)          # swing + uniform jitter
    bass = LK._notes_to_events(bass_cell, 0) + LK._notes_to_events(bass_cell, 0, BAR)
    bass = LK._humanize(bass, BPM, False, False)
    mel = LK._notes_to_events(ante, 1) + LK._notes_to_events(cons, 1, BAR)
    mel = LK._humanize(mel, BPM, False, False)
    return drums, bass, mel


# ------------------------------------------------------------------ NEW pipeline
def render_new():
    rng = random.Random(6104)
    bass_cell, ante, cons = material()

    # drums: enrich ONE cell with ghosts, tile AAAB with a varied turnaround bar
    cell_ev = drum_events_from(DRUM_CELL, 0)
    cell_ev = G.add_ghosts(rng, cell_ev, STEP, density=0.5)
    cell_ev = G.apply_accents(cell_ev, STEP, depth=1.1)
    b_grids = G.vary_grids(rng, DRUM_CELL)
    drums = []
    for bar_i in range(4):
        if bar_i < 3:
            drums += [e._replace(start=e.start + bar_i * BAR * STEP) for e in cell_ev]
        else:
            bev = drum_events_from(b_grids, 0)
            bev = G.add_ghosts(rng, bev, STEP, density=0.65)
            bev = G.apply_accents(bev, STEP, depth=1.1)
            drums += [e._replace(start=e.start + bar_i * BAR * STEP) for e in bev]
    drums = humanize.swing(drums, STEP, swing_pct=humanize.sixteenth_swing_pct(BPM))
    drums = G.apply_feel(drums, "laidback", BPM, PPQ, rng, anchor_ticks=BAR * STEP)

    # bass: AAAB phrase from the same cell, accent hierarchy, sits behind the kick
    bass_bars = G.phrase_cells(rng, bass_cell, plan="AAAB")
    bass = G.cells_to_events(bass_bars, STEP, channel=0)
    bass = G.apply_accents(bass, STEP, depth=0.7)
    bass = G.apply_feel(bass, "laidback", BPM, PPQ, rng)

    # melody: question / answer / question / varied answer -- and it BREATHES
    a = G.breathe(ante, gap=3)
    c = G.breathe(cons, gap=4)
    mel_bars = [a, c, a, G.vary_cell(rng, c)]
    mel = G.cells_to_events(mel_bars, STEP, channel=1)
    mel = G.apply_accents(mel, STEP, depth=0.55)
    mel = G.apply_feel(mel, "laidback", BPM, PPQ, rng)
    return drums, bass, mel


def write_set(folder, drums, bass, mel):
    os.makedirs(folder, exist_ok=True)
    bpmc, tsc = [(0, BPM)], [(0, (4, 4))]
    midiwriter.write_track(os.path.join(folder, "drums.mid"), drums, bpmc, tsc, channel=9)
    midiwriter.write_track(os.path.join(folder, "bass.mid"), bass, bpmc, tsc,
                           channel=0, program=BASS_PROG)
    midiwriter.write_track(os.path.join(folder, "melody.mid"), mel, bpmc, tsc,
                           channel=1, program=MEL_PROG)
    midiwriter.write_combined(os.path.join(folder, "combo.mid"),
                              [{"events": drums, "channel": 9, "name": "drums"},
                               {"events": bass, "channel": 0, "program": BASS_PROG, "name": "bass"},
                               {"events": mel, "channel": 1, "program": MEL_PROG, "name": "melody"}],
                              bpmc, tsc)


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    write_set(os.path.join(DEST, "old"), *render_old())
    write_set(os.path.join(DEST, "new"), *render_new())
    with open(os.path.join(DEST, "README.txt"), "w") as fh:
        fh.write(__doc__ + _LISTEN)
    print(f"A/B demo -> {DEST}  (old/ = current pipeline, new/ = groove engine)")


_LISTEN = """
WHAT TO LISTEN FOR (same notes, different life):

  drums   old: every hit at fixed velocity, uniformly smeared timing.
          new: ghost snare ticks between backbeats, downbeats lean forward,
               snare drags ~16ms behind (the head-nod), bar 4 turns around.
  bass    old: the riff loops verbatim, one dynamic level.
          new: same riff 3x IDENTICAL (that's the hook), 4th bar varied;
               notes on strong beats speak, weak beats tuck under;
               the whole line sits ~9ms behind the kick.
  melody  old: wall-to-wall notes, never inhales.
          new: question / answer / question / varied answer, with a real
               rest at the end of each phrase -- the return lands because
               there was silence before it.
"""


if __name__ == "__main__":
    main()
