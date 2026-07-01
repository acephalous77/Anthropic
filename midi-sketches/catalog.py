#!/usr/bin/env python3
"""Give every generated clip an evocative name that suggests its pace / tone /
mood -- derived from the music itself (tempo, meter, register, major-vs-minor
lean, density) -- and write a browsable INDEX.md grouped by pace.

Names are deterministic per seed, so re-running is stable. This does not touch
the audio: it reads output/generated/*/all.mid and writes INDEX.md.
"""

import glob
import os
from collections import Counter

import mido

HERE = os.path.dirname(__file__)
GEN = os.path.join(HERE, "output", "generated")

# --- word banks, chosen by analysed attribute; seed indexes within a bank ---
TONE = {
    "phrygian_dark": ["Obsidian", "Umbral", "Cinder", "Charcoal", "Nightshade", "Tar"],
    "dark": ["Shadow", "Slate", "Ash", "Smoke", "Iron", "Dusk"],
    "deep": ["Abyssal", "Tectonic", "Subterranean", "Fathom", "Undertow", "Bedrock"],
    "cold": ["Frost", "Arctic", "Glacier", "Pale", "Winter", "Steel"],
    "warm": ["Ember", "Amber", "Rust", "Copper", "Hearth", "Gold"],
    "bright": ["Glass", "Silver", "Dawn", "Halo", "Lumen", "Clear"],
}
MOOD = {
    "still": ["Drift", "Hush", "Veil", "Stillness", "Reverie", "Lull", "Expanse"],
    "trance": ["Trance", "Spell", "Mantra", "Incantation", "Ritual", "Séance"],
    "pulse": ["Pulse", "Engine", "Motor", "Current", "Circuit", "Throb"],
    "glitch": ["Static", "Fracture", "Flicker", "Stutter", "Fault", "Signal"],
    "drama": ["Surge", "Swell", "Ascent", "Reckoning", "Tide", "Bloom"],
    "groove": ["Strut", "Saunter", "Sway", "Roll", "Prowl", "Shuffle"],
    "offkilter": ["Lilt", "Stagger", "Cross-step", "Wend", "Tilt", "Askew"],
}

# pace buckets by BPM -> (heading, adjective)
def pace_bucket(bpm):
    if bpm <= 56:
        return "Glacial (≤56)", "Glacial"
    if bpm <= 72:
        return "Slow / drifting (57–72)", "Slow"
    if bpm <= 88:
        return "Loping (73–88)", "Loping"
    if bpm <= 104:
        return "Walking / steady (89–104)", "Walking"
    if bpm <= 120:
        return "Pulsing (105–120)", "Pulsing"
    if bpm <= 135:
        return "Driving (121–135)", "Driving"
    return "Urgent (136+)", "Urgent"


def analyse(path):
    mid = mido.MidiFile(path)
    bpm = 120
    ts = (4, 4)
    for t in mid.tracks:
        for m in t:
            if m.type == "set_tempo":
                bpm = round(mido.tempo2bpm(m.tempo))
                break
        else:
            continue
        break
    for t in mid.tracks:
        for m in t:
            if m.type == "time_signature":
                ts = (m.numerator, m.denominator)
                break
    drum, tonal, bass = [], [], []
    for t in mid.tracks:
        for m in t:
            if m.type == "note_on" and m.velocity > 0:
                (drum if m.channel == 9 else tonal).append(m.note)
                if m.channel == 0:
                    bass.append(m.note)
    return {
        "bpm": bpm, "ts": ts, "length": mid.length,
        "drum": drum, "tonal": tonal, "bass": bass,
        "min_pitch": min(tonal) if tonal else 60,
    }


def brightness(a):
    """Guess minor/major/phrygian lean from pitch classes relative to a guessed tonic."""
    if not a["bass"]:
        return "dark", "minor-ish"
    tonic = Counter(p % 12 for p in a["bass"]).most_common(1)[0][0]
    pcs = {p % 12 for p in a["tonal"]}
    has_b2 = (tonic + 1) % 12 in pcs
    minor3 = (tonic + 3) % 12 in pcs
    major3 = (tonic + 4) % 12 in pcs
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    if has_b2 and minor3:
        return "phrygian_dark", f"{names[tonic]} phrygian-ish"
    if major3 and not minor3:
        return "bright", f"{names[tonic]} major-ish"
    if minor3:
        return "dark", f"{names[tonic]} minor-ish"
    return "cold", f"{names[tonic]} modal"


def mood_bucket(archetype, ts, a):
    density = len(a["tonal"]) / max(a["length"], 1)
    if archetype in ("meditative",):
        return "still"
    if archetype == "spoken_word":
        return "still"
    if archetype == "fever_ray":
        return "trance"
    if archetype == "gated_drama":
        return "drama"
    if archetype == "four_floor_glitch":
        return "glitch"
    if archetype == "groove":
        return "groove" if a["bpm"] < 105 else "pulse"
    if archetype == "radiohead_kida":
        return "glitch" if ts == (4, 4) else "offkilter"
    if archetype == "broken_meter":
        return "offkilter"
    if archetype == "halftime_drone":
        return "trance" if density < 1.2 else "pulse"
    return "pulse"


def tone_bucket(archetype, tone_key, a):
    if a["min_pitch"] <= 40 and archetype in ("meditative", "fever_ray", "spoken_word", "halftime_drone"):
        return "deep"
    if archetype == "groove":
        return {"motorik": "cold", "fourfloor": "cold"}.get(None, "cold") if a["bpm"] >= 105 else "warm"
    if archetype == "spoken_word":
        return "warm"
    return tone_key


def name_for(seed, archetype, a, offset=0):
    tone_key, key_desc = brightness(a)
    tb = tone_bucket(archetype, tone_key, a)
    mb = mood_bucket(archetype, a["ts"], a)
    tone_word = TONE[tb][(seed + offset) % len(TONE[tb])]
    mood_word = MOOD[mb][(seed // 7 + offset * 3 + int(a["length"])) % len(MOOD[mb])]
    return f"{tone_word} {mood_word}", key_desc


def fmt_len(sec):
    return f"{int(sec // 60)}:{int(sec % 60):02d}"


def main():
    rows = []
    used_names = set()
    for d in sorted(glob.glob(os.path.join(GEN, "*"))):
        allmid = os.path.join(d, "all.mid")
        if not os.path.exists(allmid):
            continue
        folder = os.path.basename(d)
        seed = int("".join(c for c in folder.split("_")[0] if c.isdigit()))
        archetype = folder.split("_", 1)[1]
        a = analyse(allmid)
        offset, name, key_desc = 0, None, None
        while offset < 60:                      # bump word choices until the name is unique
            name, key_desc = name_for(seed, archetype, a, offset)
            if name not in used_names:
                break
            offset += 1
        used_names.add(name)
        num, den = a["ts"]
        rows.append({
            "name": name, "archetype": archetype, "key": key_desc,
            "meter": f"{num}/{den}", "bpm": a["bpm"], "len": fmt_len(a["length"]),
            "seed": seed, "folder": folder,
        })

    order = ["Glacial (≤56)", "Slow / drifting (57–72)", "Loping (73–88)",
             "Walking / steady (89–104)", "Pulsing (105–120)", "Driving (121–135)", "Urgent (136+)"]
    by_pace = {h: [] for h in order}
    for r in rows:
        by_pace[pace_bucket(r["bpm"])[0]].append(r)

    lines = ["# Clip index — named by pace / tone / mood", "",
             f"{len(rows)} generated clips. Names are evocative labels derived from each clip's own "
             "tempo, meter, register, major/minor lean, and density — grouped below by pace. "
             "Every clip lives at `output/generated/<folder>/` with `drums`/`bass`/`melody`/`all` MIDI; "
             "reproduce any from its seed.", ""]
    for h in order:
        group = sorted(by_pace[h], key=lambda r: (r["archetype"], r["bpm"]))
        if not group:
            continue
        lines.append(f"## {h}")
        lines.append("")
        lines.append("| Name | Feel | Key | Meter | BPM | Length | Seed / folder |")
        lines.append("|---|---|---|---|---|---|---|")
        for r in group:
            lines.append(f"| **{r['name']}** | {r['archetype']} | {r['key']} | {r['meter']} | "
                         f"{r['bpm']} | {r['len']} | `{r['folder']}` |")
        lines.append("")

    out = os.path.join(HERE, "INDEX.md")
    with open(out, "w") as f:
        f.write("\n".join(lines))
    print(f"wrote {out} ({len(rows)} clips)")
    for h in order:
        n = len(by_pace[h])
        if n:
            print(f"  {h:<28} {n}")


if __name__ == "__main__":
    main()
