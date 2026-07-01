"""static_orchard -- 100 BPM, E dorian, 4/4 bars paired with a clipped 7/8 bar.

Kate Bush-led: the metre itself lilts (a bar cut short, phrases carried over
the bar line). Radiohead-flavoured: broken-beat, displaced snare, glitchy
hi-hat gaps. Fever Ray-flavoured: a sustained drone bass under the churn.
"""

from theory import note, scale_degree
from rhythm import grid_from_hits
from drums import KICK, SNARE, CHH, OHH, HTOM, LTOM2, SHAKER, RIM, CLAP

TITLE = "static_orchard"
BPM = 100
TS_A = (4, 4)   # 16 steps
TS_B = (7, 8)   # 14 steps

E_BASS_ROOT = note("E", 2)   # 40
E_MEL_ROOT = note("E", 4)    # 64

DRUM_NOTES = {
    "kick": (KICK, 104, 120),
    "snare": (SNARE, 98, 116),
    "clap": (CLAP, 90, 112),
    "chh": (CHH, 56, 82),
    "ohh": (OHH, 66, 88),
    "htom": (HTOM, 86, 106),
    "ltom": (LTOM2, 86, 106),
    "shaker": (SHAKER, 44, 64),
    "rim": (RIM, 60, 84),
}


def _bar_44(broken=False, busy=False):
    kick_hits = {0, 5, 10} if not broken else {0, 5, 9, 13}
    hats = set(range(16)) - ({3, 11} if broken else set())
    return {
        "kick": grid_from_hits(16, kick_hits, accents={0}),
        "snare": grid_from_hits(16, {9} if broken else {8}, accents={9} if broken else {8}),
        "chh": grid_from_hits(16, hats if busy else set(range(0, 16, 2)), accents={0}),
        "shaker": grid_from_hits(16, set(range(16))),
    }


def _bar_78(fill=False):
    # 14 steps = 7 eighth notes (2 sixteenth-steps per eighth): 0,2,4,6,8,10,12
    kick_hits = {0, 8} if not fill else {0, 6, 8}
    return {
        "kick": grid_from_hits(14, kick_hits, accents={0}),
        "clap": grid_from_hits(14, {12}, accents={12}),
        "chh": grid_from_hits(14, {0, 2, 4, 6, 8, 10, 12}, accents={0}),
        "htom": grid_from_hits(14, {10} if fill else set()),
        "shaker": grid_from_hits(14, {0, 4, 8, 12}),
    }


def _sparse_44():
    return {
        "kick": grid_from_hits(16, {0, 10}),
        "rim": grid_from_hits(16, {8}),
        "shaker": grid_from_hits(16, {0, 8}),
    }


def _sparse_78():
    return {
        "kick": grid_from_hits(14, {0}),
        "rim": grid_from_hits(14, {8}),
        "shaker": grid_from_hits(14, {0}),
    }


# bass: drone through the 4/4 bar, a short angular reply in the clipped 7/8 bar
BASS_DRONE_44 = [(0, 16, E_BASS_ROOT, 84)]
BASS_REPLY_78 = [
    (0, 4, E_BASS_ROOT, 90),
    (4, 4, scale_degree(E_BASS_ROOT, "dorian", 2), 88),   # G2
    (8, 6, scale_degree(E_BASS_ROOT, "dorian", 1), 92),    # F#2, hangs unresolved into the bar line
]

# melody: mostly silent through the 4/4 bar, a short exclamation in the 7/8 bar
# that doesn't land on a downbeat -- the answer arrives on the *next* bar's beat 1
MELODY_CRY = [
    (2, 3, scale_degree(E_MEL_ROOT, "dorian", 4), 90),     # B4
    (8, 4, scale_degree(E_MEL_ROOT, "dorian", 3), 94),      # A4
]
MELODY_ANSWER_44 = [(0, 4, E_MEL_ROOT, 86)]


def _pair(i, total, energy="verse"):
    """One (4/4, 7/8) bar pair. `i` indexes the pair within its section."""
    broken = energy in ("build",) and i % 2 == 1
    busy = energy == "build"
    fill78 = energy == "build" and i % 2 == 0

    bar_a = {
        "time_sig": TS_A, "bpm": BPM,
        "drums": _bar_44(broken=broken, busy=busy),
        "bass": [(s, d, n + (12 if energy == "build" else 0), v) for s, d, n, v in BASS_DRONE_44],
        "melody": MELODY_ANSWER_44 if i > 0 else [],
    }
    bar_b = {
        "time_sig": TS_B, "bpm": BPM,
        "drums": _bar_78(fill=fill78),
        "bass": [(s, d, n + (12 if energy == "build" else 0), v) for s, d, n, v in BASS_REPLY_78],
        "melody": MELODY_CRY,
    }
    return bar_a, bar_b


def _sparse_pair(i):
    return (
        {"time_sig": TS_A, "bpm": BPM, "drums": _sparse_44(), "bass": BASS_DRONE_44, "melody": []},
        {"time_sig": TS_B, "bpm": BPM, "drums": _sparse_78(), "bass": BASS_REPLY_78[:1], "melody": []},
    )


def _flatten_pairs(pairs, name="pair"):
    """Turn a list of (bar_a, bar_b) into the two per-time-sig section lists arrange.py expects,
    preserving order via one section per bar (time signature changes every bar here)."""
    sections = []
    for bar in [b for pair in pairs for b in pair]:
        ts = bar.pop("time_sig")
        bpm = bar.pop("bpm")
        sections.append({"name": name, "time_sig": ts, "bpm": bpm, "bars": [bar]})
    return sections


def build():
    sections = []

    sections.extend(_flatten_pairs([_sparse_pair(i) for i in range(2)], name="intro"))
    sections.extend(_flatten_pairs([_pair(i, 4, energy="verse") for i in range(4)], name="verse"))
    sections.extend(_flatten_pairs([_pair(i, 2, energy="build") for i in range(2)], name="build"))
    sections.extend(_flatten_pairs([_sparse_pair(i) for i in range(2)], name="outro"))

    return sections


def produce(result, bass_channel, melody_channel):
    """Swing the hats for a lilting, not-quite-straight feel; give bass/melody
    the most rubato of the three pieces (Bush-style push-pull); swell expression
    through the build pair."""
    import humanize
    from arrange import STEP_TICKS, section_span
    from midiwriter import cc_ramp
    from drums import CHH

    hats = [e for e in result["drums"] if e.note == CHH]
    other = [e for e in result["drums"] if e.note != CHH]
    swung_hats = humanize.swing(hats, STEP_TICKS, amount_ticks=STEP_TICKS // 5)
    drums = other + swung_hats

    bass = humanize.jitter(result["bass"], timing_ticks=14, vel_amount=8, seed=3)
    melody = humanize.jitter(result["melody"], timing_ticks=16, vel_amount=10, seed=4)

    bounds = result["section_bounds"]
    build_start, build_end = section_span(bounds, "build")
    cc_bass = cc_ramp(bass_channel, 11, build_start, build_end, 88, 122)
    cc_melody = cc_ramp(melody_channel, 11, build_start, build_end, 88, 122)

    return {
        "drums": drums,
        "bass": bass,
        "melody": melody,
        "cc": {"bass": cc_bass, "melody": cc_melody},
    }
