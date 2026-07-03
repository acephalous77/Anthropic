#!/usr/bin/env python3
"""SD-card export for the MC-707: the closest legitimate thing to shipping
.mpj project files.

WHY NOT .mpj: the MC-707 project format is an undocumented proprietary
binary (patches, events, parameters, appended audio). No public spec or
authoring tool exists; fabricated files risk rejection or project
corruption. See PROJECT_RECIPE.TXT for the safe template workflow.

WHAT THIS BUILDS instead -- SD/ROLAND/GROOVEBOX/MIDI/<NN_KIT>/:

  S1_INTRO.MID .. S6_END.MID
      one MULTI-TRACK SMF per section column: drums/bass/lead/counter/
      chords/arp as separate named tracks on their own channels. The 707's
      SMF import (FW 1.30+) can spread an SMF's tracks across clips -- one
      import lays out a whole scene column.
  PARTS/T1_DRUMS_1.MID ...
      every part clip named by TARGET TRACK + COLUMN for one-at-a-time
      import; browser-friendly uppercase names.
  LAYOUT.TXT
      the track map (track / part / channel / suggested 707 tone) and the
      column-to-section map for this kit.

    python sd_export.py    ->  sd/  (copy its ROLAND folder onto your card)
"""

import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import mido

import kitlib  # noqa: F401  (path setup for midi-sketches imports)
from kits import KITS

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
SD = os.path.join(HERE, "sd", "ROLAND", "GROOVEBOX", "MIDI")

# 707 track layout: track number -> (part, midi channel, suggested tone)
TRACKS = [
    (1, "drums",   10, "Drum kit (TR-909/TR-707 style kit; pads 36-51)"),
    (2, "bass",    1,  "Bass tone per KIT.txt vibe (synth/finger/acid)"),
    (3, "lead",    2,  "Lead voice -- the kit's melody instrument"),
    (4, "counter", 5,  "Second voice -- softer/darker than lead"),
    (5, "chords",  3,  "Poly pad / keys / stab tone"),
    (6, "arp",     4,  "Pluck / bell / tremolo tone"),
]
SECTIONS = ["1_intro", "2_main", "3_lift", "4_break", "5_peak", "6_end"]


def merged_section_smf(kit_dir, section):
    """One format-1 SMF: every part's clip for this section as its own track."""
    out = mido.MidiFile(ticks_per_beat=480, type=1)
    meta_added = False
    n_tracks = 0
    for tno, part, ch, _tone in TRACKS:
        src = os.path.join(kit_dir, part, f"{section}.mid")
        if not os.path.exists(src):
            continue
        src_mid = mido.MidiFile(src)
        if not meta_added:
            meta = src_mid.tracks[0]
            meta.name = "TEMPO"
            out.tracks.append(meta)                       # tempo/meter track
            meta_added = True
        for tr in src_mid.tracks[1:]:
            tr.name = f"T{tno}_{part.upper()}"
            out.tracks.append(tr)
            n_tracks += 1
    return (out, n_tracks) if n_tracks else (None, 0)


def main():
    root = os.path.join(HERE, "sd")
    if os.path.isdir(root):
        shutil.rmtree(root)
    total = 0
    for kit_folder in sorted(os.listdir(OUT)):
        kit_dir = os.path.join(OUT, kit_folder)
        if not os.path.isdir(kit_dir):
            continue
        num, name = kit_folder.split("_")[0], kit_folder.split("_")[1]
        dest = os.path.join(SD, f"{num}_{name.upper()}")
        parts_dir = os.path.join(dest, "PARTS")
        os.makedirs(parts_dir)

        kit = KITS[int(num) - 1]
        for section in SECTIONS:
            smf, n = merged_section_smf(kit_dir, section)
            if smf:
                col = section.split("_")[0]
                sname = section.split("_")[1].upper()
                smf.save(os.path.join(dest, f"S{col}_{sname}.MID"))
                total += 1
            for tno, part, ch, _t in TRACKS:
                src = os.path.join(kit_dir, part, f"{section}.mid")
                if os.path.exists(src):
                    shutil.copyfile(src, os.path.join(
                        parts_dir, f"T{tno}_{part.upper()}_{section[0]}.MID"))
                    total += 1

        m = kit.get("meter", (4, 4))
        with open(os.path.join(dest, "LAYOUT.TXT"), "w") as fh:
            fh.write(f"{kit['name']}  {kit['key']}  {kit['bpm']} bpm  {m[0]}/{m[1]}"
                     f"{'  SWUNG' if kit.get('swing') else ''}\n"
                     f"set project tempo to {kit['bpm']}\n\n{kit['note']}\n\nTRACK MAP\n")
            for tno, part, ch, tone in TRACKS:
                if kit.get(part) or part == "drums":
                    fh.write(f"  track {tno}  {part:<8} ch{ch:<3} {tone}\n")
            fh.write("\nCLIP COLUMNS (scenes)\n"
                     "  1 intro   2 main   3 lift   4 break   5 peak   6 end\n"
                     "  rides: 1-2-2-3 | 2-3-4-2 | 1-2-3-5-4-2-5-6\n\n"
                     "IMPORT\n"
                     "  S<n>_<name>.MID  = whole section column in ONE multi-track\n"
                     "                     SMF import (choose per-track placement)\n"
                     "  PARTS/T<t>_<part>_<col>.MID = single clip -> track t, column col\n")
        print(f"  {os.path.basename(dest)}")

    with open(os.path.join(HERE, "sd", "PROJECT_RECIPE.TXT"), "w") as fh:
        fh.write(RECIPE)
    print(f"\n{total} files -> {os.path.join(HERE, 'sd')}  "
          f"(copy the ROLAND folder to your SD card)")


RECIPE = """MC-707 PROJECTS -- THE SAFE PATH (and why there are no .mpj files here)

The .mpj project format is an undocumented Roland binary (tones, events,
parameters, appended audio). No public spec or authoring tool exists --
the community's one attempt at documenting it is an empty repo. A file I
fabricated would be rejected by the unit at best, or corrupt a project at
worst. So the layout ships INSIDE multi-track MIDI files instead, plus
this one-time recipe:

ONE TIME -- MAKE THE TEMPLATE PROJECT (~5 min)
  1. Create a new project. Name it TEMPLATE.
  2. Lay out tracks 1-6 exactly as in any kit's LAYOUT.TXT:
       T1 drum kit / T2 bass / T3 lead / T4 counter / T5 chords / T6 arp
     (leave T7/T8 free for Sophia/live layers). Pick a default tone per
     track -- per-kit tone tweaks are one knob later.
  3. Save. On the SD card this becomes one .mpj in ROLAND/PROJECT.

PER KIT (~3 min)
  4. Copy TEMPLATE.mpj on the card (or use the unit's project copy),
     rename to the kit (e.g. K01_NIGHTPULSE.mpj). Track layout done.
  5. Open the project, set tempo from LAYOUT.TXT.
  6. UTILITY > SMF IMPORT: pick the kit's S1..S6 files from
     ROLAND/GROOVEBOX/MIDI/<KIT>/ -- each multi-track import lays one
     whole section column across the tracks. (Or import PARTS/ files
     one clip at a time; names say exactly where each goes.)
  7. Save. That kit is now a permanent, correctly-laid-out project.

OFFER: drop your saved TEMPLATE.mpj into kitworks/ and I'll add a script
that stamps out all 22 renamed project copies automatically -- cloning
your own valid file is safe; inventing one is not.
"""


if __name__ == "__main__":
    main()
