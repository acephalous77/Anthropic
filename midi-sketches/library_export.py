#!/usr/bin/env python3
"""Export the whole clip library into one browsable, well-organized tree:

    library/<tempo band>/<drum feel>/<MoodName>_<key>_<bpm>_<part>.mid

- TEMPO organised: top-level folders are pace bands, named with their BPM range
  and a speed word (1_Very-Slow_le56 ... 7_Fast_136up).
- MOOD / DRUM-SPEED clear: the second level is the drum feel (tribal-halftime,
  fourfloor-glitch, linndrum-song, drone-no-beat, arp-groove, ...), and every
  filename leads with the clip's mood name (from INDEX.md) plus its key and BPM.
- Each clip ships as all.mid (GM, for quick preview) + drums/bass/melody stems,
  with the drum stem folded into the MC-707 pad range (36-51).

    python library_export.py    ->  output/library/  (+ INDEX.md copied in)
"""

import os
import shutil

import catalog
import mc707

HERE = os.path.dirname(__file__)
DEST = os.path.join(HERE, "output", "library")

TEMPO_BAND = {
    "Glacial (≤56)": "1_Very-Slow_le56bpm",
    "Slow / drifting (57–72)": "2_Slow_57-72bpm",
    "Loping (73–88)": "3_Mid-Slow_73-88bpm",
    "Walking / steady (89–104)": "4_Mid_89-104bpm",
    "Pulsing (105–120)": "5_Upbeat_105-120bpm",
    "Driving (121–135)": "6_Driving_121-135bpm",
    "Urgent (136+)": "7_Fast_136up-bpm",
}


def feel_label(r):
    """A drum-speed / groove-type label for the second folder level."""
    a, meter, bpm = r["archetype"], r["meter"], r["bpm"]
    if a == "radiohead_kida":
        return {"4/4": "idioteque-glitch", "5/4": "odd-5-4",
                "10/4": "pedal-10-4", "16/8": "pyramid-3+3+4+3+3"}.get(meter, "oddmeter")
    if a == "groove":
        return "downtempo-headnod" if bpm < 100 else ("motorik-driving" if bpm >= 122 else "fourfloor")
    return {
        "halftime_drone": "halftime-drone", "broken_meter": "brokenbeat-4-4+7-8",
        "four_floor_glitch": "fourfloor-glitch", "gated_drama": "tom-gated",
        "fever_ray": "tribal-halftime", "spoken_word": "spokenword-bed",
        "meditative": "drone-no-beat", "kate_bush": "linndrum-song",
        "fever_radiohead": "arp-groove",
    }.get(a, a)


def slug(name):
    return "".join(w[:1].upper() + w[1:] for w in name.replace("-", " ").split())


def main():
    rows = catalog.build_catalog()
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)

    n = 0
    for r in rows:
        band = TEMPO_BAND[catalog.pace_bucket(r["bpm"])[0]]
        folder = os.path.join(DEST, band, feel_label(r))
        os.makedirs(folder, exist_ok=True)
        base = f"{slug(r['name'])}_{mc707.key_tag(r['key'])}_{r['bpm']}"

        mc707.remap_drum_file(os.path.join(r["dir"], "drums.mid"),
                              os.path.join(folder, f"{base}_drums.mid"))
        for part in ("bass", "melody", "all"):
            src = os.path.join(r["dir"], f"{part}.mid")
            if os.path.exists(src):
                shutil.copyfile(src, os.path.join(folder, f"{base}_{part}.mid"))
        n += 1

    # regenerate + drop the index in at the root for reference
    catalog.main()
    shutil.copyfile(os.path.join(HERE, "INDEX.md"), os.path.join(DEST, "INDEX.md"))

    print(f"organized {n} clips -> {DEST}")
    for band in sorted(set(TEMPO_BAND.values())):
        p = os.path.join(DEST, band)
        if os.path.isdir(p):
            feels = sorted(os.listdir(p))
            total = sum(len(os.listdir(os.path.join(p, fe))) // 4 for fe in feels)
            print(f"  {band:<22} {total:>3} clips   ({', '.join(feels)})")


if __name__ == "__main__":
    main()
