"""MC-707 helpers: fold the drum notes into the groovebox's 16-pad range and
slice loop-length clips out of a rendered arrangement.

The MC-707 (and MC-101) drum kits expose 16 pads mapped to MIDI notes 36-51.
Anything outside that range triggers no pad, so the extended hand-percussion
this generator uses (congas/claves/cabasa/cowbell/shaker/tambourine at 54-75)
has to be folded down onto in-range pads. The core kit voices already match
the 707's TR kits (kick 36, snare 38, clap 39, closed/open hat 42/46, toms
41-50, crash 49, ride 51), so those pass through unchanged.

MC707_DRUM_MAP is a best-effort default for a standard TR-style kit -- verify
against your loaded kit on the box and adjust (every pad's sound is visible on
the 707; tell me your kit's pad layout and I'll retarget any that are off).
"""

from midiwriter import Event

# source note -> MC-707 pad note (36-51). In-range core voices are identity;
# out-of-range percussion is folded onto the nearest sensible pad.
MC707_DRUM_MAP = {
    35: 36,  # acoustic bass drum -> kick pad
    36: 36,  # kick
    37: 37,  # rim / side stick
    38: 38,  # snare
    39: 39,  # clap
    40: 40,  # electric snare
    41: 41,  # low tom
    42: 42,  # closed hat
    43: 43,  # tom
    44: 44,  # pedal hat
    45: 45,  # tom
    46: 46,  # open hat
    47: 47,  # tom
    48: 48,  # hi tom / perc
    49: 49,  # crash
    50: 50,  # hi tom / perc
    51: 51,  # ride
    # --- folded extended percussion ---
    54: 49,  # tambourine  -> crash/jingle pad
    56: 37,  # cowbell     -> perc/rim pad
    63: 50,  # conga hi    -> hi tom pad
    64: 45,  # conga lo    -> low-mid tom pad
    65: 50,  # timbale hi  -> hi tom pad
    66: 45,  # timbale lo  -> low-mid tom pad
    67: 37,  # agogo hi    -> perc pad
    68: 37,  # agogo lo    -> perc pad
    69: 44,  # cabasa      -> pedal-hat/tick pad
    70: 44,  # shaker      -> pedal-hat/tick pad
    75: 40,  # claves      -> perc/rim pad
}

DRUM_MAPS = {
    "gm": None,               # identity (leave GM notes as-is)
    "mc707": MC707_DRUM_MAP,
}


def remap_drum_events(events, mapping):
    """Return drum events with each note remapped through `mapping` (None = identity)."""
    if not mapping:
        return events
    return [e._replace(note=mapping.get(e.note, e.note)) for e in events]


def remap_drum_file(src, dst, mapping=MC707_DRUM_MAP):
    """Read an existing drum .mid, fold every channel-10 note into the 707 pad
    range, and save to `dst` (leaves other channels untouched)."""
    import mido
    mid = mido.MidiFile(src)
    for track in mid.tracks:
        for msg in track:
            if msg.type in ("note_on", "note_off") and getattr(msg, "channel", None) == 9:
                msg.note = mapping.get(msg.note, msg.note)
    mid.save(dst)


_KEY_SUFFIX = {"phrygian": "phr", "major": "maj", "minor": "m", "modal": "mod"}


def key_tag(key_desc):
    """Compress a 'F minor-ish' / 'E phrygian-ish' description to a short filename tag
    like 'Fm' / 'Ephr' / 'Cmaj' / 'Dmod'."""
    parts = key_desc.replace("-ish", "").split()
    root = parts[0].replace("#", "s") if parts else "X"
    quality = _KEY_SUFFIX.get(parts[1], "") if len(parts) > 1 else ""
    return f"{root}{quality}"


def _value_at(changes, tick, default):
    """The value of a (tick, value) change-list that is in effect at `tick`."""
    val = default
    for t, v in changes:
        if t <= tick:
            val = v
        else:
            break
    return val


def slice_loop(result, cc, ppq, section, n_bars):
    """Extract the first `n_bars` of `section`, re-based to tick 0, as a self-
    contained loop. Returns (loop_result, loop_cc) shaped like render output.
    Only meaningful for constant-metre sections (skips odd-metre ones upstream).
    """
    bounds = {b["name"]: b for b in result["section_bounds"]}
    if section not in bounds:
        raise KeyError(f"no section named {section!r}")
    s, e = bounds[section]["start"], bounds[section]["end"]
    num, den = _value_at(result["time_sig_changes"], s, (4, 4))
    bpm = _value_at(result["bpm_changes"], s, 120)
    bar = ppq * 4 * num // den
    win = min(n_bars * bar, e - s)

    def take(events):
        out = []
        for ev in events:
            if s <= ev.start < s + win:
                st = ev.start - s
                out.append(ev._replace(start=st, dur=min(ev.dur, win - st)))
        return out

    def take_cc(ccs):
        return [c._replace(tick=c.tick - s) for c in ccs if s <= c.tick < s + win]

    loop = {
        "drums": take(result["drums"]),
        "bass": take(result["bass"]),
        "melody": take(result["melody"]),
        "bpm_changes": [(0, bpm)],
        "time_sig_changes": [(0, (num, den))],
        "section_bounds": [{"name": section, "start": 0, "end": win}],
        "total_ticks": win,
    }
    loop_cc = {k: take_cc(v) for k, v in cc.items()}
    return loop, loop_cc


def auto_loop_section(result):
    """Pick a good section to loop from: the non-intro/outro section with the most
    drum hits (the meatiest groove/verse), preferring constant 4/4."""
    skip = {"intro", "outro", "settle", "dissolve", "breakdown", "tail"}
    best, best_hits = None, -1
    for b in result["section_bounds"]:
        if b["name"] in skip:
            continue
        num, den = _value_at(result["time_sig_changes"], b["start"], (4, 4))
        if (num, den) != (4, 4):
            continue
        hits = sum(1 for e in result["drums"] if b["start"] <= e.start < b["end"])
        if hits > best_hits:
            best, best_hits = b["name"], hits
    # fall back to the first section if nothing matched
    return best or result["section_bounds"][0]["name"]
