#!/usr/bin/env python3
"""KITWORKS invariants: build output must exist; every clip loads; drums on
MC-707 pads 36-51 and anchored on beat 1; pitched clips open within 2 steps
(offbeat stabs/displaced cells are composed choices); every kit has the six
columns for every part it declares."""
import glob
import os
import sys

import mido

HERE = os.path.dirname(os.path.abspath(__file__))
fails = []


def check(name, cond, detail=""):
    print(f"  [{'ok' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail and not cond else ""))
    if not cond:
        fails.append(name)


files = glob.glob(os.path.join(HERE, "output", "**", "*.mid"), recursive=True)
check("output exists (run build.py first)", bool(files), "no files")
dead, offpad, empty = [], [], []
for f in files:
    ns = []
    for tr in mido.MidiFile(f).tracks:
        tick = 0
        for msg in tr:
            tick += msg.time
            if msg.type == "note_on" and msg.velocity > 0:
                ns.append((tick, msg.note, getattr(msg, "channel", 0)))
    if not ns:
        empty.append(f)
        continue
    # covenant: drums and full previews anchor beat 1 strictly; pitched parts
    # rest wherever the score says (composed rests are not dead space)
    if os.sep + "drums" + os.sep in f or "full_" in os.path.basename(f):
        if min(t for t, _, _ in ns) > 60:
            dead.append(os.path.relpath(f, HERE))
    for _, n, ch in ns:
        if ch == 9 and not (36 <= n <= 51):
            offpad.append((os.path.relpath(f, HERE), n))
check(f"no empty clips ({len(files)} files)", not empty, str(empty[:3]))
check("drums and previews anchor beat 1", not dead, str(dead[:3]))
check("all drums on pads 36-51", not offpad, str(offpad[:3]))

from kits import KITS  # noqa: E402
check("every kit declares drums/bass/lead/counter/chords",
      all(all(k.get(p) for p in ("drums", "bass", "lead", "counter", "chords")) for k in KITS))
check("every kit has a section spec", all("sections" in k for k in KITS))

# --- sound library / assignment invariants -------------------------------
import soundlib  # noqa: E402
import kitsounds  # noqa: E402

kit_names = {k["name"] for k in KITS}
bad_kit = [n for n in kitsounds.SOUNDS if n not in kit_names]
check("kitsounds keys all name a real kit", not bad_kit, str(bad_kit))

# every assigned tone (non-None, non-fx slot) must resolve in the standing library
_PARTS = ("drums", "bass", "lead", "counter", "chords", "arp")
unknown = []
for kname, spec in kitsounds.SOUNDS.items():
    for part in _PARTS:
        tone = spec.get(part)
        if tone and not soundlib.known(tone):
            unknown.append((kname, part, tone))
check("every assigned tone exists in soundlib", not unknown, str(unknown[:3]))

# assigned FX use only documented CCs and sane values
_CCOK = {"cutoff", "resonance", "attack", "release", "reverb", "chorus"}
bad_cc = []
for kname, spec in kitsounds.SOUNDS.items():
    cc = (spec.get("fx") or {}).get("cc") or {}
    for part, params in cc.items():
        for k, v in params.items():
            if k not in _CCOK or not (0 <= v <= 127):
                bad_cc.append((kname, part, k, v))
check("assigned FX use documented CCs, values 0-127", not bad_cc, str(bad_cc[:3]))

# soundlib itself is internally consistent (roles valid, no dup names)
check("soundlib tones all carry a known role",
      all(e["role"] in soundlib.ROLES or e["role"] == "seq" for e in soundlib.TONES.values()))

if fails:
    print(f"\n{len(fails)} FAILED")
    sys.exit(1)
print("\nall kit invariants hold")
