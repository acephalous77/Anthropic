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
from kits import KITS

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


def _bar_ticks(m):
    num, den = 4, 4
    for tr in m.tracks:
        for msg in tr:
            if msg.type == "time_signature":
                num, den = msg.numerator, msg.denominator
                break
    return int(num * 4 / den * m.ticks_per_beat)


def pad_clip(src, dst, target_bars):
    """Copy src->dst forcing the clip to span EXACTLY target_bars whole bars.

    The 707 takes an imported clip's length from the SMF, so a part whose
    last note ends mid-bar would import short and loop out of phase with the
    rest of its scene column. We clamp any groove-overhang note-off back to
    the barline and stretch End-Of-Track to the exact loop length, so every
    clip in a column is the same length and scenes stay locked.
    """
    m = mido.MidiFile(src)
    target = _bar_ticks(m) * target_bars
    for tr in m.tracks:
        abs_t, out, open_count = 0, [], {}
        for msg in tr:
            abs_t += msg.time
            at = min(abs_t, target)
            if msg.type == "note_on" and msg.velocity > 0:
                if abs_t >= target:
                    continue                       # a note starting at/after the loop point
                open_count[(msg.channel, msg.note)] = open_count.get((msg.channel, msg.note), 0) + 1
                out.append((at, msg))
            elif msg.type in ("note_off",) or (msg.type == "note_on" and msg.velocity == 0):
                k = (msg.channel, msg.note)
                if open_count.get(k, 0) > 0:       # keep offs for notes we actually opened
                    open_count[k] -= 1
                    out.append((at, msg))          # clamp its off to <= target
            elif msg.type == "end_of_track":
                continue                           # re-added below at exact length
            else:
                out.append((min(abs_t, target), msg))
        out.sort(key=lambda p: (p[0], p[1].type != "note_off"))  # offs before ons at a tick
        tr.clear()
        last = 0
        for at, msg in out:
            msg.time = at - last
            tr.append(msg)
            last = at
        tr.append(mido.MetaMessage("end_of_track", time=max(0, target - last)))
    m.save(dst)


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
                pad_clip(src, dst, target_bars=2 if tag == "6END" else 4)
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
            for tno, part, tone in TRACKS:
                if kit.get(part) or part == "drums":
                    fh.write(f"  track {tno}  {part:<8} {tone}\n")
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
