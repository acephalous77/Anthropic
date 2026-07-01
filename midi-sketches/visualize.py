#!/usr/bin/env python3
"""Text piano-roll / step-grid dump of a rendered piece, for eyeballing the
arrangement without an audio backend. Not part of the render pipeline.

Usage:
    python visualize.py undertow
    python visualize.py undertow --section verse
"""

import argparse
import importlib

from arrange import render_piece, STEP_TICKS

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def pitch_name(n):
    return f"{NOTE_NAMES[n % 12]}{n // 12 - 1}"


def dump_section(result, name, voice):
    from arrange import section_span
    start, end = section_span(result["section_bounds"], name)
    events = sorted(e for e in result[voice] if start <= e.start < end)
    steps = (end - start) // STEP_TICKS
    print(f"\n[{voice}] section={name!r} steps={steps} (bar-relative)")
    if voice == "drums":
        by_note = {}
        for e in events:
            by_note.setdefault(e.note, []).append(e)
        for note_num, evs in sorted(by_note.items()):
            row = ["."] * steps
            for e in evs:
                idx = (e.start - start) // STEP_TICKS
                if 0 <= idx < steps:
                    row[idx] = "X" if e.vel >= 100 else ("x" if e.vel >= 60 else "o")
            print(f"  {note_num:>3} {''.join(row)}")
    else:
        for e in events:
            idx = (e.start - start) // STEP_TICKS
            dur_steps = e.dur // STEP_TICKS
            bar_no = idx // 16
            print(f"  bar {bar_no:>2} step {idx % 16:>2} +{dur_steps:<2} {pitch_name(e.note):<4} vel={e.vel}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("piece")
    ap.add_argument("--section", default=None, help="limit to one section name (default: all)")
    ap.add_argument("--voice", default=None, choices=["drums", "bass", "melody"])
    args = ap.parse_args()

    mod = importlib.import_module(f"pieces.{args.piece}")
    sections = mod.build()
    result = render_piece(sections, mod.DRUM_NOTES)
    if hasattr(mod, "produce"):
        produced = mod.produce(result, bass_channel=0, melody_channel=1)
        result = {**result, **{k: v for k, v in produced.items() if k in ("drums", "bass", "melody")}}

    names = [args.section] if args.section else [b["name"] for b in result["section_bounds"]]
    voices = [args.voice] if args.voice else ["drums", "bass", "melody"]
    for name in names:
        for voice in voices:
            dump_section(result, name, voice)


if __name__ == "__main__":
    main()
