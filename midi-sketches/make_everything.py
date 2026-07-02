#!/usr/bin/env python3
"""Build THE definitive everything-zip. One registry of every pack; each entry
regenerates itself, so the zip can never silently miss content the way the
slowpacks once vanished from the organized exports.

    python make_everything.py            # regenerate all packs + zip
    python make_everything.py --no-gen   # zip whatever is on disk

Adding a new pack later = one line in PACKS. If a pack's folder is missing and
it has no generator, the build FAILS LOUDLY instead of shipping without it.
"""

import argparse
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "output")
ZIP = os.path.join(OUT, "midi-sketches-everything")

# (zip folder name, output path, generator script or None)
PACKS = [
    ("00_foundation-pieces/undertow", "undertow", "render.py"),
    ("00_foundation-pieces/static_orchard", "static_orchard", None),
    ("00_foundation-pieces/glass_repeater", "glass_repeater", None),
    ("01_library-146", "generated", None),                    # committed clips
    ("02_loopkit", "loopkit", "loopkit.py"),
    ("03_codex", "codex", "codex.py"),
    ("04_holy-mountain", "holy_mountain", "holy_mountain.py"),
    ("05_slowpacks_60-74bpm", "slowpacks", None),
    ("06_clippack-feverhead-120", "clippack_feverhead_120", None),
    ("07_instrument-audition", "instrument_set_40001_kida_odd5", None),
    ("08_ab-demo", "ab_demo", "ab_demo.py"),
    ("09_sophia-beds", "sophia", "sophia.py"),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-gen", action="store_true", help="zip what's on disk")
    args = ap.parse_args()

    if not args.no_gen:
        for script in sorted({s for _, _, s in PACKS if s}):
            print(f"generating: {script}")
            subprocess.run([sys.executable, os.path.join(HERE, script)],
                           check=True, cwd=HERE, stdout=subprocess.DEVNULL)

    stage = ZIP
    if os.path.isdir(stage):
        shutil.rmtree(stage)
    os.makedirs(stage)

    total = 0
    for zname, src, script in PACKS:
        srcdir = os.path.join(OUT, src)
        if not os.path.isdir(srcdir):
            raise SystemExit(f"MISSING PACK: {src} (regenerate with {script or 'git checkout'})")
        dst = os.path.join(stage, zname)
        shutil.copytree(srcdir, dst)
        n = sum(1 for _, _, fs in os.walk(dst) for f in fs if f.endswith(".mid"))
        total += n
        print(f"  {zname:<34} {n:>4} .mid")

    for extra in ("INDEX.csv",):
        p = os.path.join(OUT, extra)
        if os.path.exists(p):
            shutil.copyfile(p, os.path.join(stage, extra))
    idx = os.path.join(HERE, "INDEX.md")
    if os.path.exists(idx):
        shutil.copyfile(idx, os.path.join(stage, "INDEX.md"))

    archive = shutil.make_archive(ZIP, "zip", OUT, os.path.basename(ZIP))
    shutil.rmtree(stage)
    print(f"\n{total} .mid files -> {archive}")
    return archive


if __name__ == "__main__":
    main()
