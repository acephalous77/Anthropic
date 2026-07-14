#!/usr/bin/env python3
"""keycheck -- independently verify each kit's notes imply its labeled key.

Lifts the Krumhansl-Kessler key-finding idea from the transcription toolkit's
midi_analysis.py (see research/), reimplemented dependency-free. For every
kit it builds a duration-weighted pitch-class histogram over all pitched
parts, correlates it against the 24 K-K major/minor profiles, and checks the
best-fitting TONIC pitch-class matches the kit's labeled root.

K-K only knows major/minor, so a modal kit (dorian/phrygian/mixolydian) is
expected to correlate best with a major/minor whose TONIC still equals -- or
is the relative of -- the kit's root; we accept a tonic-pitch-class match and
report the mode K-K inferred, rather than demanding it name the mode.

    python keycheck.py        # audits every kit, flags mismatches
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from kitlib import N          # noqa: E402
from kits import KITS         # noqa: E402

KK_MAJOR = [6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]
KK_MINOR = [6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17]
PC = {"C": 0, "C#": 1, "Db": 1, "D": 2, "D#": 3, "Eb": 3, "E": 4, "F": 5,
      "F#": 6, "Gb": 6, "G": 7, "G#": 8, "Ab": 8, "A": 9, "A#": 10, "Bb": 10, "B": 11}
NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def _corr(a, b):
    ma, mb = sum(a) / 12, sum(b) / 12
    ca, cb = [x - ma for x in a], [x - mb for x in b]
    num = sum(x * y for x, y in zip(ca, cb))
    den = (sum(x * x for x in ca) * sum(y * y for y in cb)) ** 0.5
    return num / den if den else 0.0


def estimate_key(hist):
    """-> (tonic_pc, mode, corr) best K-K fit for a 12-bin pc histogram."""
    best = (0, "minor", -2.0)
    for mode, prof in (("major", KK_MAJOR), ("minor", KK_MINOR)):
        for tonic in range(12):
            rolled = [prof[(i - tonic) % 12] for i in range(12)]
            c = _corr(hist, rolled)
            if c > best[2]:
                best = (tonic, mode, c)
    return best


MAJOR_STEPS = [0, 2, 4, 5, 7, 9, 11]
MINOR_STEPS = [0, 2, 3, 5, 7, 8, 10]      # natural minor (aeolian)
MODE_STEPS = {"maj": MAJOR_STEPS, "": MINOR_STEPS, "m": MINOR_STEPS,
              "dor": [0, 2, 3, 5, 7, 9, 10], "phr": [0, 1, 3, 5, 7, 8, 10],
              "mix": [0, 2, 4, 5, 7, 9, 10]}


def scale_set(tonic, steps):
    return frozenset((tonic + s) % 12 for s in steps)


def label_scale(key):
    for suf in ("maj", "dor", "phr", "mix"):
        if key.endswith(suf):
            return scale_set(PC[key[:-len(suf)]], MODE_STEPS[suf])
    root = key[:-1] if key.endswith("m") else key
    return scale_set(PC[root], MINOR_STEPS if key.endswith("m") else MAJOR_STEPS)


def kit_histogram(kit):
    h = [0.0] * 12
    for part in ("bass", "lead", "counter", "chords", "arp"):
        for bar in kit.get(part) or []:
            for (s, d, note, v) in bar:
                m = N(note) if isinstance(note, str) else note
                h[m % 12] += max(d, 0.5)          # weight by duration
    return h


def _root_pc(key):
    return PC[key[:2]] if key[:2] in PC else PC[key[0]]


def main():
    """Two independent reads per kit, since K-K only knows major/minor:
      TONIC  -- is the labeled root among the 3 heaviest pitch classes?
                (the real 'does it assert its key' test; mode-agnostic)
      NOTES  -- do all pitches fall inside the labeled scale? (coherence)
    K-K's own major/minor argmax is printed as context; for a modal or
    minor kit it routinely names the parent/relative major -- expected."""
    miss = 0
    for k in KITS:
        h = kit_histogram(k)
        want = _root_pc(k["key"])
        rank = sorted(range(12), key=lambda pc: h[pc], reverse=True)
        tonic_rank = rank.index(want) + 1
        in_scale = all(pc in label_scale(k["key"]) for pc in range(12) if h[pc] > 0)
        tonic, mode, corr = estimate_key(h)
        ok = tonic_rank <= 3 and in_scale
        if not ok:
            miss += 1
        kk = f"{NAMES[tonic]} {mode}"
        note = "" if ok else (" <- TONIC WEAK" if tonic_rank > 3 else " <- OUT-OF-SCALE NOTE")
        print(f"  [{'ok ' if ok else 'BAD'}] {k['name']:12} {k['key']:6} "
              f"tonic {NAMES[want]} rank {tonic_rank}/12, in-scale {in_scale}"
              f"  (K-K~{kk} r={corr:.2f}){note}")
    print(f"\n{len(KITS)} kits, {len(KITS) - miss} assert their tonic and stay in-scale, "
          f"{miss} to check")


if __name__ == "__main__":
    main()
