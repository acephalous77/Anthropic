#!/usr/bin/env python3
"""SD-card export for the MC-707: the closest legitimate thing to shipping
.mpj project files.

WHY NOT .mpj: the MC-707 project format is an undocumented proprietary
binary (patches, events, parameters, appended audio). No public spec or
authoring tool exists; fabricated files risk rejection or project
corruption. See PROJECT_RECIPE.TXT for the safe template workflow.

HOW THE 707 ACTUALLY IMPORTS (verified): SMF import lands on the CURRENTLY
SELECTED track. Mode "All Tracks" = merge the whole SMF to one clip; mode
"Each Track" = fan the SMF's tracks out into consecutive CLIPS on that one
track. So the file you import per track must be ONE PART whose tracks are
its SECTIONS -- then "Each Track" gives that track its 6 section clips, and
because every track fills clip slots 1-6 in the same order, scene columns
1-6 line up as intro/main/lift/break/peak/end.

WHAT THIS BUILDS -- SD/ROLAND/GROOVEBOX/MIDI/<NN_KIT>/:

  IMPORT/T1_DRUMS.MID .. T6_ARP.MID
      ONE per-part SMF; its 6 tracks are the 6 sections (S1_INTRO..S6_END).
      Select that track on the 707, SMF-import this file with mode "Each
      Track" -> the track's clip slots 1-6 become the section clips. Six
      imports (one per part) lay out the whole kit.
  PARTS/T1_DRUMS_1.MID ...
      the bulletproof fallback: one clip per file (no mode to get wrong),
      named target-track + section. Import one at a time onto its track.
  LAYOUT.TXT
      the per-kit track map + the exact import procedure.

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


SECTION_LABELS = ["S1_INTRO", "S2_MAIN", "S3_LIFT", "S4_BREAK", "S5_PEAK", "S6_END"]


def per_part_smf(kit_dir, part):
    """One format-1 SMF for a PART whose tracks are its 6 SECTIONS -- import
    with 'Each Track' to fan the sections into that track's 6 clip slots."""
    out = mido.MidiFile(ticks_per_beat=480, type=1)
    meta_added = False
    n = 0
    for section, label in zip(SECTIONS, SECTION_LABELS):
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
            tr.name = label
            out.tracks.append(tr)
            n += 1
    return (out, n) if n else (None, 0)


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
        import_dir = os.path.join(dest, "IMPORT")
        os.makedirs(import_dir)
        for tno, part, ch, _tone in TRACKS:
            if not (kit.get(part) or part == "drums"):
                continue
            smf, n = per_part_smf(kit_dir, part)
            if smf:
                smf.save(os.path.join(import_dir, f"T{tno}_{part.upper()}.MID"))
                total += 1
            for section in SECTIONS:
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
            fh.write("\nSCENE COLUMNS (clip slots 1-6, same order on every track)\n"
                     "  1 intro   2 main   3 lift   4 break   5 peak   6 end\n"
                     "  rides: 1-2-2-3 | 2-3-4-2 | 1-2-3-5-4-2-5-6\n\n"
                     "IMPORT (6 imports = whole kit)\n"
                     "  for each track T1..T6:\n"
                     "    1. select that track on the 707\n"
                     "    2. UTILITY > SMF IMPORT > IMPORT/T<n>_<part>.MID\n"
                     "    3. mode = EACH TRACK  (fans the 6 sections into clip slots 1-6)\n"
                     "  fallback: PARTS/T<n>_<part>_<col>.MID = one clip, import to\n"
                     "            track n, clip slot <col>, any mode.\n")
        print(f"  {os.path.basename(dest)}")

    with open(os.path.join(HERE, "sd", "PROJECT_RECIPE.TXT"), "w") as fh:
        fh.write(RECIPE)
    print(f"\n{total} files -> {os.path.join(HERE, 'sd')}  "
          f"(copy the ROLAND folder to your SD card)")


RECIPE = """MC-707: LAYING A KIT OUT ACROSS TRACKS (the verified procedure)

WHY NO .mpj: the project format is undocumented Roland binary; no public
spec or authoring tool exists (the community's format repo is empty). A
fabricated .mpj can be rejected or corrupt a project. So the layout ships
inside importable MIDI, and you assemble each kit on the box in ~2 minutes.

HOW SMF IMPORT WORKS ON THE 707 (this is the key fact):
  - Import lands on the CURRENTLY SELECTED track (not spread across tracks).
  - Mode "All Tracks" merges the whole SMF into ONE clip.
  - Mode "Each Track" fans the SMF's tracks into consecutive CLIPS on that
    track.
  So to get one PART's six SECTIONS down a track's clip column, you import
  that part's file (its tracks ARE the sections) with mode "Each Track".

ONE TIME -- THE TEMPLATE (~5 min, optional but recommended)
  Make a project, name it TEMPLATE, set tracks 1-6 to drum-kit / bass /
  lead / counter / chords / arp tones (T7-T8 free for live/Sophia). Save.
  Copy + rename it per kit so tones are preset; then just do the imports.

PER KIT -- SIX IMPORTS (~2 min)
  1. Open the project; set project tempo from LAYOUT.TXT.
  2. Select TRACK 1. UTILITY > SMF IMPORT >
     ROLAND/GROOVEBOX/MIDI/<KIT>/IMPORT/T1_DRUMS.MID, mode EACH TRACK.
     -> track 1 clip slots 1-6 are now intro/main/lift/break/peak/end.
  3. Select TRACK 2, import IMPORT/T2_BASS.MID the same way. Repeat for
     T3_LEAD, T4_COUNTER, T5_CHORDS, T6_ARP (skip any a kit doesn't have).
  4. Save. Now every SCENE column plays a full section across all parts:
     scene 1 = intro, 2 = main, 3 = lift, 4 = break, 5 = peak, 6 = end.
     Perform by launching scenes: 1-2-2-3 | 2-3-4-2 | 1-2-3-5-4-2-5-6.

  Not getting clean 6-clip fan-out on your firmware? Use PARTS/ instead:
  each file is ONE clip -- import PARTS/T2_BASS_2.MID onto track 2 slot 2,
  etc. More imports, zero ambiguity.

TROUBLESHOOTING
  - Drums silent? Track 1 must be a DRUM-KIT tone (notes 36-51 = the pads).
  - Wrong pitch/octave? Confirm project tempo and that you imported to the
    intended track before launching.
"""


if __name__ == "__main__":
    main()
