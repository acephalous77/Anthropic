#!/usr/bin/env python3
"""Render the composed pieces to standard MIDI files.

Usage:
    python render.py                       # render all pieces
    python render.py undertow glass_repeater   # render a subset
"""

import importlib
import os
import sys

from arrange import render_piece
import midiwriter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")

PIECES = ["undertow", "static_orchard", "glass_repeater"]

BASS_CHANNEL = 0
BASS_PROGRAM = 38   # GM: Synth Bass 1
MELODY_CHANNEL = 1
MELODY_PROGRAM = 81  # GM: Lead 2 (sawtooth)


def render(piece_name):
    mod = importlib.import_module(f"pieces.{piece_name}")
    sections = mod.build()
    result = render_piece(sections, mod.DRUM_NOTES, bass_channel=BASS_CHANNEL, melody_channel=MELODY_CHANNEL)

    # Optional per-piece production pass: humanization/swing/CC automation.
    # `produce(result)` may override drums/bass/melody event lists and supply
    # cc_events per instrument; a piece with no such needs can skip it entirely.
    cc = {"drums": [], "bass": [], "melody": []}
    if hasattr(mod, "produce"):
        produced = mod.produce(result, bass_channel=BASS_CHANNEL, melody_channel=MELODY_CHANNEL)
        result = {**result, **{k: v for k, v in produced.items() if k in ("drums", "bass", "melody")}}
        cc.update(produced.get("cc", {}))

    out_dir = os.path.join(OUTPUT_DIR, piece_name)
    os.makedirs(out_dir, exist_ok=True)

    midiwriter.write_track(
        os.path.join(out_dir, "drums.mid"), result["drums"],
        result["bpm_changes"], result["time_sig_changes"],
        channel=midiwriter.DRUM_CHANNEL, track_name=f"{mod.TITLE} - drums", cc_events=cc["drums"],
    )
    midiwriter.write_track(
        os.path.join(out_dir, "bass.mid"), result["bass"],
        result["bpm_changes"], result["time_sig_changes"],
        channel=BASS_CHANNEL, program=BASS_PROGRAM, track_name=f"{mod.TITLE} - bass", cc_events=cc["bass"],
    )
    midiwriter.write_track(
        os.path.join(out_dir, "melody.mid"), result["melody"],
        result["bpm_changes"], result["time_sig_changes"],
        channel=MELODY_CHANNEL, program=MELODY_PROGRAM, track_name=f"{mod.TITLE} - melody", cc_events=cc["melody"],
    )
    midiwriter.write_combined(
        os.path.join(out_dir, "all.mid"),
        [
            {"events": result["drums"], "channel": midiwriter.DRUM_CHANNEL, "name": "drums", "cc_events": cc["drums"]},
            {"events": result["bass"], "channel": BASS_CHANNEL, "program": BASS_PROGRAM, "name": "bass",
             "cc_events": cc["bass"]},
            {"events": result["melody"], "channel": MELODY_CHANNEL, "program": MELODY_PROGRAM, "name": "melody",
             "cc_events": cc["melody"]},
        ],
        result["bpm_changes"], result["time_sig_changes"],
    )

    beats = result["total_ticks"] / midiwriter.PPQ
    seconds = sum(
        (min(next_tick, result["total_ticks"]) - tick) / midiwriter.PPQ * 60 / bpm
        for (tick, bpm), next_tick in zip(
            result["bpm_changes"],
            [t for t, _ in result["bpm_changes"][1:]] + [result["total_ticks"]],
        )
    )
    print(f"{piece_name}: {beats:.1f} beats, ~{seconds:.1f}s -> {out_dir}")


def main():
    names = sys.argv[1:] or PIECES
    for name in names:
        if name not in PIECES:
            print(f"unknown piece {name!r}, choices: {PIECES}", file=sys.stderr)
            sys.exit(1)
    for name in names:
        render(name)


if __name__ == "__main__":
    main()
