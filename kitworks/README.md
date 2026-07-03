# KITWORKS

The active project. Hand-composed, interlocking song kits for the MC-707 —
**every note chosen** (the generative library that preceded this lives on in
`../midi-sketches/` as legacy and engine-room).

## What a kit is
One musical idea executed completely: a recognizable beat, a bass written
against the kick and the changes, a lead with a memorable shape, a counter
voice living in the lead's silences, hand-voiced chords, sometimes an arp.
One file per kit in `kits/` — open it like a score, change notes, rebuild.

## Sections
Every part renders as SIX clips (load them down one 707 clip column):

    1_intro   stripped statement       4_break   the floor drops
    2_main    the song as written      5_peak    lift + the fill every 2 bars
    3_lift    chorus energy            6_end     2-bar cadence that CLOSES

Rides: `1-2-2-3 | 2-3-4-2 | 1-2-3-5-4-2-5-6`. Previews: `full_main`,
`full_lift`, `full_peak`. Each kit folder has a `KIT.txt` card.

## Workflow
    python build.py     # -> output/ (all kits + INDEX.csv)
    python tests.py     # invariants

## Adding a kit
Copy any `kits/kNN_*.py`, renumber, rewrite the notes. Keep the covenant:
drums on pads 36-51, a hit on (or within a breath of) beat 1, every velocity
deliberate, the parts written against each other. Swing is 8th-note shuffle
applied to ALL parts. Then `python build.py && python tests.py`.
