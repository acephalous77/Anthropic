#!/usr/bin/env python3
"""SD-card export for the MC-707 -- built on VERIFIED import behavior.

THE FACTS (deep-research verified against Roland's Ver.1.30 update PDF,
Reference Manual, and community testing; see MC707_FACTS.TXT):

  * SMF import is strictly ONE FILE -> ONE CLIP. Roland, verbatim: "All
    tracks included in the SMF are overwritten onto one clip." There is NO
    "Each Track" fan-out mode and NO batch import of any kind.
  * Procedure: select the target clip -> press [CLIP] -> choose "MIDI FILE"
    -> [ENTER] -> browse ROLAND/GROOVEBOX/MIDI -> [ENTER] to load.
  * Channel bytes inside the file are IGNORED for internal playback -- the
    clip plays through its track's assigned tone. So these single-clip
    files need no channel gymnastics.
  * Clip ceiling: 128 steps. (Our clips are 32-96 steps. All safe.)
  * The only per-track alternative is LIVE USB-MIDI RECORDING onto an armed
    track (see usb_feed.py) -- same per-clip granularity, no menu diving.

WHAT THIS BUILDS -- SD/ROLAND/GROOVEBOX/MIDI/<NN_KIT>/:

  T<track>_<PART>_<col><SECTION>.MID   one clip per file, named by its
      destination: track row, then clip column. T2_BASS_2MAIN.MID goes to
      track 2, clip slot 2. Import order for a playable kit fast: all the
      *_2MAIN files first (6 imports), then expand columns as needed.
  LAYOUT.TXT    per-kit card: track map, tempo, import checklist.

    python sd_export.py    ->  sd/  (copy its ROLAND folder onto your card)
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mido

import kitlib  # noqa: F401  (path setup for midi-sketches imports)
import soundlib
from kits import KITS
from kitsounds import for_kit

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
SD = os.path.join(HERE, "sd", "ROLAND", "GROOVEBOX", "MIDI")

# 707 track layout (track number -> part, suggested tone type)
TRACKS = [
    (1, "drums",   "DRUM track; TR-909/707-style kit (notes 36-51 = pads)"),
    (2, "bass",    "TONE track; bass per KIT card (synth/finger/acid)"),
    (3, "lead",    "TONE track; the kit's melody voice"),
    (4, "counter", "TONE track; second voice, softer/darker than lead"),
    (5, "chords",  "TONE track; poly pad / keys / stab"),
    (6, "arp",     "TONE track; pluck / bell / tremolo"),
]
SECTIONS = [("1_intro", "1INTRO"), ("2_main", "2MAIN"), ("3_lift", "3LIFT"),
            ("4_break", "4BREAK"), ("5_peak", "5PEAK"), ("6_end", "6END")]
MAX_STEPS = 128


def clip_steps(path):
    m = mido.MidiFile(path)
    last = 0
    for tr in m.tracks:
        t = 0
        for msg in tr:
            t += msg.time
        last = max(last, t)
    return last / (m.ticks_per_beat / 4)      # 16th-note steps


def _write_fx(fh, fx):
    """Append the SOUND FX block to a LAYOUT.TXT (no-op if the kit set no fx)."""
    if not fx:
        return
    cc, master = (fx.get("cc") or {}), fx.get("master")
    if not cc and not master:
        return
    fh.write("\nSOUND FX (dial from the computer / on the track's [SHIFT]+[SOUND])\n")
    _CCNAME = {"cutoff": "CC74", "resonance": "CC71", "attack": "CC73",
               "release": "CC72", "reverb": "CC91", "chorus": "CC92"}
    for part, params in cc.items():
        pretty = ", ".join(f"{k} {v} ({_CCNAME.get(k, '?')})" for k, v in params.items())
        fh.write(f"  {part:<8} {pretty}\n")
    if master:
        rev, dly = master.get("reverb"), master.get("delay")
        bits = []
        if rev:
            bits.append(f"reverb {rev[0]} @ {rev[1]}")
        if dly:
            bits.append(f"delay {dly[0]} @ {dly[1]}")
        if bits:
            fh.write("  master   " + " · ".join(bits) + "\n")


def main():
    root = os.path.join(HERE, "sd")
    if os.path.isdir(root):
        import shutil
        shutil.rmtree(root)
    total, too_long = 0, []
    for kit_folder in sorted(os.listdir(OUT)):
        kit_dir = os.path.join(OUT, kit_folder)
        if not os.path.isdir(kit_dir):
            continue
        num, name = kit_folder.split("_")[0], kit_folder.split("_")[1]
        dest = os.path.join(SD, f"{num}_{name.upper()}")
        os.makedirs(dest)
        kit = KITS[int(num) - 1]

        for tno, part, _tone in TRACKS:
            if not (kit.get(part) or part == "drums"):
                continue
            for section, tag in SECTIONS:
                src = os.path.join(kit_dir, part, f"{section}.mid")
                if not os.path.exists(src):
                    continue
                dst = os.path.join(dest, f"T{tno}_{part.upper()}_{tag}.MID")
                import shutil
                shutil.copyfile(src, dst)
                total += 1
                steps = clip_steps(dst)
                if steps > MAX_STEPS:
                    too_long.append((dst, steps))

        m = kit.get("meter", (4, 4))
        n_parts = sum(1 for _t, part, _x in TRACKS if kit.get(part) or part == "drums")
        with open(os.path.join(dest, "LAYOUT.TXT"), "w") as fh:
            fh.write(f"{kit['name']}  {kit['key']}  {kit['bpm']} bpm  {m[0]}/{m[1]}"
                     f"{'  SWUNG' if kit.get('swing') else ''}\n"
                     f"set project tempo to {kit['bpm']}\n\n{kit['note']}\n\nTRACK MAP\n")
            snd = for_kit(kit["name"])
            for tno, part, tone in TRACKS:
                if kit.get(part) or part == "drums":
                    chosen = snd.get(part)
                    if chosen and soundlib.known(chosen):
                        e = soundlib.TONES[chosen]
                        label = f"LOAD '{chosen}'  ({e['pack']}; {'/'.join(e['tags'])})"
                    elif chosen:                       # a name not (yet) in soundlib
                        label = f"LOAD '{chosen}'"
                    else:
                        label = tone                    # unset -> the generic hint
                    fh.write(f"  track {tno}  {part:<8} {label}\n")
            _write_fx(fh, snd.get("fx"))
            fh.write(
                "\nIMPORT (one file = one clip; there is NO batch import)\n"
                "  cursor onto the target clip slot -> [CLIP] -> MIDI FILE ->\n"
                "  [ENTER] -> pick the file -> [ENTER].\n"
                "  Filename says exactly where it goes:\n"
                "    T2_BASS_3LIFT.MID  ->  track 2, clip slot 3.\n\n"
                f"FAST PLAYABLE KIT ({n_parts} imports): all *_2MAIN files first.\n"
                "Then expand columns you'll use: 3LIFT next, then 1INTRO,\n"
                "4BREAK, 5PEAK, 6END.\n\n"
                "SCENES: because every track fills slots 1-6 in the same\n"
                "order, scene 1..6 = intro/main/lift/break/peak/end.\n"
                "Rides: 1-2-2-3 | 2-3-4-2 | 1-2-3-5-4-2-5-6\n")
        print(f"  {os.path.basename(dest)}")

    with open(os.path.join(HERE, "sd", "MC707_FACTS.TXT"), "w") as fh:
        fh.write(FACTS)
    print(f"\n{total} clip files -> {os.path.join(HERE, 'sd')}")
    if too_long:
        print("WARNING -- clips over the 128-step ceiling:", too_long)
    else:
        print("all clips within the 707's 128-step clip ceiling")


FACTS = """MC-707 IMPORT & CHANNEL FACTS (deep-research verified, firmware <= 1.82)

SMF IMPORT
  * One SMF -> one clip. Roland (Ver.1.30 update PDF), verbatim:
    "All tracks included in the SMF are overwritten onto one clip."
    A multi-track file gets FLATTENED into the selected clip. There is no
    "Each Track" mode and never has been.
  * Procedure: select the target clip slot -> press [CLIP] -> select
    "MIDI FILE" -> [ENTER] -> browse (files must be in
    ROLAND/GROOVEBOX/MIDI) -> [ENTER] to load.
  * NO batch import exists: no multi-select, no folder import, no editor
    that pushes clips, no drag-and-drop while running (USB Storage mode
    halts the unit). Budget ~30-60s per clip and import what you'll use.
  * Clips max out at 128 steps (all files in this card are 32-96 steps).
  * Be on firmware 1.80+ (latest is 1.82): 1.80 fixed a bug dropping notes
    when step 128 held a note-off, and a Receive-filter import bug.

CHANNELS
  * Channel bytes inside an imported file are IGNORED for internal
    playback -- the clip sounds through its track's assigned tone. You
    never need to edit channels for these files.
  * Track MIDI settings live in two places:
      [SHIFT] + track [SEL]  -> track settings -> MIDI tab
        (Tx MIDI OUT1/OUT2/USB toggles -- for driving external gear)
      [SHIFT] + [KNOB ASSIGN] -> SET -> MIDI
        (the per-track channel map; default track n = channel n)
    These matter only for external MIDI in/out, incl. the USB-record path.
  * 8 tracks total; any track can be TONE, DRUM, DRUM+COMP, or LOOPER
    (only one DRUM+COMP). Make track 1 a DRUM track for these kits.

THE ONLY PER-TRACK ALTERNATIVE: LIVE USB RECORDING (see usb_feed.py)
  Arm a track (enable its MIDI receive, or turn on MIDI Rx Auto Channel so
  input follows the selected track), cursor onto the target clip, set clip
  length with [MEASURE], press [REC] then [START/STOP], and stream the
  part from a computer over USB MIDI. Same one-clip-at-a-time granularity,
  but zero file-browser menu diving -- some prefer it.

.mpj PROJECT FILES
  Still an undocumented Roland binary; no tool reads or writes it. A valid
  .mpj copied into ROLAND/GROOVEBOX/PROJECT loads whole -- so ONE manually
  assembled kit project can be duplicated/renamed on the card as a
  template. Assemble once, clone forever.
"""


if __name__ == "__main__":
    main()
