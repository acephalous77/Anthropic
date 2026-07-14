#!/usr/bin/env python3
"""Extra 'pull it up fast' views over the library, all from the same metadata:

  1. output/INDEX.csv    -- one sortable sheet: mood name, project, feel, key,
                            quality, Camelot code, BPM, tempo band, meter,
                            length, seed, folder. Open in any spreadsheet and
                            filter/sort by any combination.
  2. output/by-key/<Camelot>_<key>/<tempo>bpm/<files>  -- harmonic grouping, so
                            same/compatible keys sit together for mixing in key.
  3. output/by-part/<drums|bass|melody>/<tempo>bpm/<files>  -- every drum loop
                            in one place, every bassline, every lead -- for
                            building a track layer by layer.

Drum stems in the trees are folded to the MC-707 pad range (36-51).

    python views_export.py
"""

import csv
import os
import shutil

import catalog
import mc707
from library_export import feel_label
from project_export import PROJECT, tempo_folder, slug

HERE = os.path.dirname(__file__)
DEST_KEY = os.path.join(HERE, "output", "by-key")
DEST_PART = os.path.join(HERE, "output", "by-part")
CSV_PATH = os.path.join(HERE, "output", "INDEX.csv")

CAMELOT_MIN = {"G#": "1A", "D#": "2A", "A#": "3A", "F": "4A", "C": "5A", "G": "6A",
               "D": "7A", "A": "8A", "E": "9A", "B": "10A", "F#": "11A", "C#": "12A"}
CAMELOT_MAJ = {"B": "1B", "F#": "2B", "C#": "3B", "G#": "4B", "D#": "5B", "A#": "6B",
               "F": "7B", "C": "8B", "G": "9B", "D": "10B", "A": "11B", "E": "12B"}


def parse_key(key_desc):
    parts = key_desc.replace("-ish", "").split()
    tonic = parts[0]
    quality = parts[1] if len(parts) > 1 else "modal"
    return tonic, quality


def camelot(tonic, quality):
    # major -> B side; minor/phrygian/dorian/modal grouped on the A (minor) side
    table = CAMELOT_MAJ if quality == "major" else CAMELOT_MIN
    return table.get(tonic, "--")


def main():
    rows = catalog.build_catalog()
    for d in (DEST_KEY, DEST_PART):
        if os.path.isdir(d):
            shutil.rmtree(d)

    with open(CSV_PATH, "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["name", "project", "feel", "key", "quality", "camelot",
                    "bpm", "tempo_band", "meter", "length", "seed", "folder"])
        for r in rows:
            tonic, quality = parse_key(r["key"])
            cam = camelot(tonic, quality)
            proj = PROJECT.get(r["archetype"], "Sketches").split("_", 1)[-1]
            band = catalog.pace_bucket(r["bpm"])[0]
            w.writerow([r["name"], proj, feel_label(r), tonic, quality, cam,
                        r["bpm"], band, r["meter"], r["len"], r["seed"], r["folder"]])

            base = f"{slug(r['name'])}_{mc707.key_tag(r['key'])}_{r['bpm']}"

            # by key (harmonic)
            kfolder = os.path.join(DEST_KEY, f"{cam}_{mc707.key_tag(r['key'])}", tempo_folder(r["bpm"]))
            os.makedirs(kfolder, exist_ok=True)
            # by part
            for part in ("drums", "bass", "melody"):
                src = os.path.join(r["dir"], f"{part}.mid")
                pfolder = os.path.join(DEST_PART, part, tempo_folder(r["bpm"]))
                os.makedirs(pfolder, exist_ok=True)
                if part == "drums":
                    mc707.remap_drum_file(src, os.path.join(kfolder, f"{base}_drums.mid"))
                    mc707.remap_drum_file(src, os.path.join(pfolder, f"{base}_drums.mid"))
                else:
                    shutil.copyfile(src, os.path.join(kfolder, f"{base}_{part}.mid"))
                    shutil.copyfile(src, os.path.join(pfolder, f"{base}_{part}.mid"))
            allsrc = os.path.join(r["dir"], "all.mid")
            if os.path.exists(allsrc):
                shutil.copyfile(allsrc, os.path.join(kfolder, f"{base}_all.mid"))

    print(f"wrote {CSV_PATH} ({len(rows)} rows)")
    print(f"by-key:  {len(os.listdir(DEST_KEY))} key groups")
    print(f"by-part: drums / bass / melody, each split by tempo")


if __name__ == "__main__":
    main()
