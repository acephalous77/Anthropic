#!/usr/bin/env python3
"""Build a USB-ready export for the Roland MC-707 with self-describing filenames.

Every generated clip is copied into `output/mc707_import/` with:
  - a filename that identifies it -- <MoodName>_<key>_<bpm>_<part>.mid -- so the
    files are distinguishable in the 707's import browser (no more identical
    'drums.mid' everywhere);
  - drums pre-folded into the 707's 16-pad range (36-51);
  - grouped into pace-numbered folders (1_Glacial ... 7_Urgent) so they sort in
    a sensible order on the box.

The mood names match INDEX.md exactly (shared naming in catalog.py). Import the
per-part stems onto separate 707 tracks. Re-run after generating new clips.

    python mc707_export.py
"""

import os
import shutil

import catalog
import mc707

HERE = os.path.dirname(__file__)
DEST = os.path.join(HERE, "output", "mc707_import")

PACE_FOLDER = {
    "Glacial (≤56)": "1_Glacial",
    "Slow / drifting (57–72)": "2_Slow",
    "Loping (73–88)": "3_Loping",
    "Walking / steady (89–104)": "4_Walking",
    "Pulsing (105–120)": "5_Pulsing",
    "Driving (121–135)": "6_Driving",
    "Urgent (136+)": "7_Urgent",
}


def slug(name):
    """'Steel Engine' -> 'SteelEngine' (FAT/707-safe, no spaces)."""
    return "".join(w[:1].upper() + w[1:] for w in name.replace("-", " ").split())


def main():
    rows = catalog.build_catalog()
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)

    n_files = 0
    for r in rows:
        pace_heading = catalog.pace_bucket(r["bpm"])[0]
        folder = os.path.join(DEST, PACE_FOLDER[pace_heading])
        os.makedirs(folder, exist_ok=True)
        base = f"{slug(r['name'])}_{mc707.key_tag(r['key'])}_{r['bpm']}"

        # drums: remap into the 707 pad range as we copy
        mc707.remap_drum_file(os.path.join(r["dir"], "drums.mid"),
                              os.path.join(folder, f"{base}_drums.mid"))
        # bass / melody: copy verbatim (notes are what the 707 uses; tone is set on the box)
        for part in ("bass", "melody"):
            shutil.copyfile(os.path.join(r["dir"], f"{part}.mid"),
                            os.path.join(folder, f"{base}_{part}.mid"))
        n_files += 3

    print(f"wrote {n_files} files for {len(rows)} clips -> {DEST}")
    for heading, sub in PACE_FOLDER.items():
        p = os.path.join(DEST, sub)
        if os.path.isdir(p):
            print(f"  {sub:<12} {len(os.listdir(p)) // 3} clips")
    print("\nEach clip is 3 files (drums/bass/melody). Import the stems onto separate")
    print("707 tracks; drums are already folded into pads 36-51.")


if __name__ == "__main__":
    main()
