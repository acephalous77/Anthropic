#!/usr/bin/env python3
"""Generate fresh, seeded drum/bass/melody clips (as opposed to render.py,
which re-renders the fixed hand-composed pieces in pieces/*.py).

Usage:
    python generate.py                          # one random clip, random seed
    python generate.py --seed 42                 # reproducible: same seed -> same clip
    python generate.py --seed 42 --archetype broken_meter
    python generate.py --seed 42 --root D --scale dorian --bpm 90
    python generate.py --count 6                  # a batch of 6 different clips
"""

import argparse
import os
import sys

import generator
import midiwriter

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output", "generated")

BASS_CHANNEL = 0
BASS_PROGRAM = 38    # GM: Synth Bass 1
MELODY_CHANNEL = 1
MELODY_PROGRAM = 81  # GM: Lead 2 (sawtooth)


def write_clip(spec, out_dir):
    result = spec["result"]
    cc = spec["cc"]
    # a spec may override the GM program (e.g. spoken_word uses a warm pad, not a lead)
    bass_prog = spec.get("bass_program") or BASS_PROGRAM
    mel_prog = spec.get("melody_program") or MELODY_PROGRAM
    os.makedirs(out_dir, exist_ok=True)

    midiwriter.write_track(
        os.path.join(out_dir, "drums.mid"), result["drums"],
        result["bpm_changes"], result["time_sig_changes"],
        channel=midiwriter.DRUM_CHANNEL, track_name=f"{spec['title']} - drums", cc_events=cc["drums"],
    )
    midiwriter.write_track(
        os.path.join(out_dir, "bass.mid"), result["bass"],
        result["bpm_changes"], result["time_sig_changes"],
        channel=BASS_CHANNEL, program=bass_prog, track_name=f"{spec['title']} - bass", cc_events=cc["bass"],
    )
    midiwriter.write_track(
        os.path.join(out_dir, "melody.mid"), result["melody"],
        result["bpm_changes"], result["time_sig_changes"],
        channel=MELODY_CHANNEL, program=mel_prog, track_name=f"{spec['title']} - melody", cc_events=cc["melody"],
    )
    midiwriter.write_combined(
        os.path.join(out_dir, "all.mid"),
        [
            {"events": result["drums"], "channel": midiwriter.DRUM_CHANNEL, "name": "drums", "cc_events": cc["drums"]},
            {"events": result["bass"], "channel": BASS_CHANNEL, "program": bass_prog, "name": "bass",
             "cc_events": cc["bass"]},
            {"events": result["melody"], "channel": MELODY_CHANNEL, "program": mel_prog, "name": "melody",
             "cc_events": cc["melody"]},
        ],
        result["bpm_changes"], result["time_sig_changes"],
    )


def spec_card(spec, out_dir):
    result = spec["result"]
    beats = result["total_ticks"] / midiwriter.PPQ
    bars = sum(1 for _ in result["section_bounds"])
    seconds = sum(
        (min(next_tick, result["total_ticks"]) - tick) / midiwriter.PPQ * 60 / bpm
        for (tick, bpm), next_tick in zip(
            result["bpm_changes"],
            [t for t, _ in result["bpm_changes"][1:]] + [result["total_ticks"]],
        )
    )
    retry_note = f" (passed QC after {spec['attempt']} retr{'y' if spec['attempt'] == 1 else 'ies'})" if spec["attempt"] else ""
    print(f"{spec['title']}  [seed {spec['seed']}, {spec['archetype']}]")
    print(f"  key: {spec['root']} {spec['scale']}   tempo: {spec['bpm']} BPM   "
          f"~{seconds:.1f}s over {len(result['section_bounds'])} sections{retry_note}")
    if spec.get("zipf_slope") is not None:
        print(f"  zipf rank-frequency slope: {spec['zipf_slope']:.2f} (R^2={spec['zipf_r2']:.2f}) -- "
              f"aesthetically-typical music clusters near -1 (Manaris et al. 2005), informational only")
    print(f"  -> {out_dir}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", type=int, default=None, help="omit for a fresh random seed each run")
    ap.add_argument("--archetype", choices=list(generator.ARCHETYPES), default=None,
                     help="omit to pick randomly (from --seed)")
    ap.add_argument("--root", default=None, help="e.g. D, F#, Bb -- omit to pick randomly")
    ap.add_argument("--scale", default=None, help="e.g. aeolian, dorian, phrygian -- omit to pick randomly")
    ap.add_argument("--bpm", type=int, default=None, help="omit to pick from the archetype's tasteful range")
    ap.add_argument("--phases", type=int, default=None,
                     help="growth stages for archetypes that support it (fever_ray: 2 or 3); longer clip")
    ap.add_argument("--mode", default=None,
                     help="sub-mode for archetypes that support it (radiohead_kida: "
                          "odd5 / pedal10 / idioteque / pyramid)")
    ap.add_argument("--melody-program", type=int, default=None, dest="melody_program",
                     help="GM program (0-127) for the melody track, e.g. 11 vibraphone, 52 choir, 4 e.piano")
    ap.add_argument("--bass-program", type=int, default=None, dest="bass_program",
                     help="GM program (0-127) for the bass track, e.g. 35 fretless, 33 finger, 38 synth bass")
    ap.add_argument("--count", type=int, default=1, help="generate this many clips (each gets its own seed)")
    ap.add_argument("--out", default=OUTPUT_DIR, help="output root directory")
    args = ap.parse_args()

    for i in range(args.count):
        seed = args.seed if (args.seed is not None and args.count == 1) else (
            args.seed + i if args.seed is not None else None)
        try:
            spec = generator.generate(seed=seed, archetype=args.archetype, root=args.root,
                                       scale=args.scale, bpm=args.bpm, phases=args.phases, mode=args.mode)
        except RuntimeError as exc:
            print(f"generation failed: {exc}", file=sys.stderr)
            sys.exit(1)

        # CLI instrument overrides win over any per-spec default
        if args.melody_program is not None:
            spec["melody_program"] = args.melody_program
        if args.bass_program is not None:
            spec["bass_program"] = args.bass_program

        out_dir = os.path.join(args.out, f"seed{spec['seed']}_{spec['archetype']}")
        write_clip(spec, out_dir)
        spec_card(spec, out_dir)


if __name__ == "__main__":
    main()
