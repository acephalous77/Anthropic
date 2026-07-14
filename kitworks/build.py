#!/usr/bin/env python3
"""Build the whole KITWORKS collection -> output/ + INDEX.csv.

    python build.py
"""
import csv
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import kitlib
import fx
from kits import KITS

HERE = os.path.dirname(os.path.abspath(__file__))
DEST = os.path.join(HERE, "output")


def main():
    if os.path.isdir(DEST):
        shutil.rmtree(DEST)
    os.makedirs(DEST)
    rows, total = [], 0
    print("KITWORKS -- hand-composed kits, six section columns per part\n")
    for i, kit in enumerate(KITS, 1):
        folder, n = kitlib.build_kit(kit, i, DEST)
        with open(os.path.join(folder, "FX_SETUP.txt"), "w") as fh:
            fh.write(fx.setup_card(kit))
        total += n
        parts = [p for p in ("drums", "bass", "lead", "counter", "chords", "arp") if kit.get(p)]
        m = kit.get("meter", (4, 4))
        rows.append([i, kit["name"], kit["key"], kit["bpm"], f"{m[0]}/{m[1]}",
                     kit["feel"], "yes" if kit.get("swing") else "", ",".join(parts), n])
        print(f"  {os.path.basename(folder):<30} {len(parts)} parts  {n:>2} clips")
    with open(os.path.join(DEST, "INDEX.csv"), "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["n", "kit", "key", "bpm", "meter", "feel", "swing", "parts", "clips"])
        w.writerows(rows)
    print(f"\n{total} clips across {len(KITS)} kits -> {DEST}")


if __name__ == "__main__":
    main()
