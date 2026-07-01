#!/usr/bin/env python3
"""Export the library organized BY PROJECT -- the creative vein each clip came
from -- then by tempo, with mood-named files:

    projects/<NN_Project>/<tempo>bpm/<MoodName>_<key>_<bpm>_<part>.mid

Projects group the archetypes by what they're for (a Fever Ray session, the
Kid A/Amnesiac Radiohead set, Kate Bush songs, spoken-word beds, meditative
drones, DJ grooves, ...). Inside each project, clips are sorted into tempo
folders, filenames lead with the mood name, and drum stems are folded to the
MC-707 pad range (36-51). all.mid is included for preview.

    python project_export.py   ->  output/projects/  (+ INDEX.md)
"""

import os
import shutil

import catalog
import mc707

HERE = os.path.dirname(__file__)
GEN = os.path.join(HERE, "output", "generated")
DEST = os.path.join(HERE, "output", "projects")

PROJECT = {
    "fever_ray": "1_Fever-Ray_first-album",
    "radiohead_kida": "2_Radiohead_KidA-Amnesiac",
    "kate_bush": "3_Kate-Bush_songs",
    "fever_radiohead": "4_Fever-x-Radiohead",
    "spoken_word": "5_Spoken-Word_poetry-beds",
    "meditative": "6_Meditative_deep-drones",
    "groove": "7_DJ-Grooves_for-mixing",
    "halftime_drone": "8_Sketches_original-blends",
    "broken_meter": "8_Sketches_original-blends",
    "four_floor_glitch": "8_Sketches_original-blends",
    "gated_drama": "8_Sketches_original-blends",
}

# the three fixed hand-composed pieces everything grew from
FOUNDATIONS = {
    "undertow": ("0_Original-Compositions", "Undertow"),
    "static_orchard": ("0_Original-Compositions", "StaticOrchard"),
    "glass_repeater": ("0_Original-Compositions", "GlassRepeater"),
}

_TEMPO = {
    "Glacial (≤56)": "le56", "Slow / drifting (57–72)": "57-72",
    "Loping (73–88)": "73-88", "Walking / steady (89–104)": "89-104",
    "Pulsing (105–120)": "105-120", "Driving (121–135)": "121-135", "Urgent (136+)": "136up",
}


def tempo_folder(bpm):
    return f"{_TEMPO[catalog.pace_bucket(bpm)[0]]}bpm"


def slug(name):
    return "".join(w[:1].upper() + w[1:] for w in name.replace("-", " ").split())


def emit(src_dir, project, name, key_tag, bpm):
    folder = os.path.join(DEST, project, tempo_folder(bpm))
    os.makedirs(folder, exist_ok=True)
    base = f"{slug(name)}_{key_tag}_{bpm}"
    mc707.remap_drum_file(os.path.join(src_dir, "drums.mid"),
                          os.path.join(folder, f"{base}_drums.mid"))
    for part in ("bass", "melody", "all"):
        s = os.path.join(src_dir, f"{part}.mid")
        if os.path.exists(s):
            shutil.copyfile(s, os.path.join(folder, f"{base}_{part}.mid"))


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    n = 0

    for r in catalog.build_catalog():
        project = PROJECT.get(r["archetype"], "9_Other")
        emit(r["dir"], project, r["name"], mc707.key_tag(r["key"]), r["bpm"])
        n += 1

    # the fixed originals (output/<name>/), not under generated
    for folder, (project, title) in FOUNDATIONS.items():
        d = os.path.join(HERE, "output", folder)
        if os.path.isdir(d):
            a = catalog.analyse(os.path.join(d, "all.mid"))
            _, key_desc = catalog.brightness(a)
            emit(d, project, title, mc707.key_tag(key_desc), a["bpm"])
            n += 1

    catalog.main()
    shutil.copyfile(os.path.join(HERE, "INDEX.md"), os.path.join(DEST, "INDEX.md"))

    print(f"organized {n} clips by project -> {DEST}")
    for project in sorted(os.listdir(DEST)):
        p = os.path.join(DEST, project)
        if os.path.isdir(p):
            clips = sum(len(os.listdir(os.path.join(p, t))) // 4 for t in os.listdir(p))
            tempos = ", ".join(sorted(os.listdir(p)))
            print(f"  {project:<28} {clips:>3} clips   ({tempos})")


if __name__ == "__main__":
    main()
