"""undertow -- 84 BPM, D aeolian, straight 4/4 with a half-time-feel groove.

Fever Ray-led: sparse tribal/electronic drums, a sustained low drone bass.
Kate Bush-flavoured: the melody enters/leaves in long breaths, call-and-response.
Radiohead-flavoured: angular, asymmetrically-subdivided bassline under the drone.
"""

from theory import note, scale_degree
from rhythm import grid_from_hits
from drums import KICK, SNARE, CHH, OHH, HTOM, MTOM2, SHAKER, RIM

TITLE = "undertow"
BPM = 84
TS = (4, 4)

D_BASS_ROOT = note("D", 2)     # 38
D_MEL_ROOT = note("D", 4)      # 62

DRUM_NOTES = {
    "kick": (KICK, 106, 122),
    "snare": (SNARE, 100, 118),
    "ghost_snare": (SNARE, 38, 46),   # same drum, quieter hits -- a live-feel ghost note
    "chh": (CHH, 58, 84),
    "ohh": (OHH, 68, 90),
    "shaker": (SHAKER, 46, 66),
    "htom": (HTOM, 88, 108),
    "mtom": (MTOM2, 88, 108),
    "rim": (RIM, 62, 86),
}

# -- bass phrase: long root sustain, then an angular descending/ascending run
#    under the backbeat (durations 6,2,3,2,3 steps -- deliberately lopsided)
BASS_PHRASE = [
    (0, 6, D_BASS_ROOT, 95),
    (6, 2, scale_degree(D_BASS_ROOT, "aeolian", 6, -1), 88),   # C2, passing tone below root
    (8, 3, scale_degree(D_BASS_ROOT, "aeolian", 2), 92),        # F2
    (11, 2, scale_degree(D_BASS_ROOT, "aeolian", 3), 88),       # G2
    (13, 3, D_BASS_ROOT, 90),
]

BASS_DRONE = [(0, 16, D_BASS_ROOT, 82)]

# -- melody: a "call" landing on the half-time backbeat, entering every other bar
MELODY_CALL = [
    (2, 2, D_MEL_ROOT, 88),                                     # D4 pickup
    (7, 1, scale_degree(D_MEL_ROOT, "aeolian", 2), 86),          # F4
    (8, 4, scale_degree(D_MEL_ROOT, "aeolian", 4), 96),          # A4, sustained over the backbeat
    (14, 2, scale_degree(D_MEL_ROOT, "aeolian", 3), 84),         # G4 tail
]
MELODY_CALL_FILL = MELODY_CALL + [(15, 1, D_MEL_ROOT, 70)]       # tiny extra pickup into next bar's downbeat


def _groove_bar(fill=False, busy_hats=False, ghost_steps=frozenset()):
    kick_hits = {0, 6, 11} if not fill else {0, 6, 9, 11}
    out = {
        "kick": grid_from_hits(16, kick_hits),
        "snare": grid_from_hits(16, {8}, accents={8}),
        "chh": grid_from_hits(16, set(range(0, 16, 2)) if not busy_hats else set(range(16)),
                               accents={0, 8}),
        "shaker": grid_from_hits(16, set(range(16)), accents={0, 4, 8, 12}),
        "htom": grid_from_hits(16, {15} if fill else set()),
    }
    if ghost_steps:
        out["ghost_snare"] = grid_from_hits(16, set(ghost_steps))
    return out


def _sparse_bar():
    return {
        "kick": grid_from_hits(16, {0, 10}),
        "rim": grid_from_hits(16, {10}),
        "shaker": grid_from_hits(16, set(range(0, 16, 4)), accents={0}),
    }


def _build_bar(step_up):
    kick_hits = {0, 4, 6, 8, 11, 14}
    return {
        "kick": grid_from_hits(16, kick_hits, accents={0, 8}),
        "snare": grid_from_hits(16, {8}, accents={8}),
        "chh": grid_from_hits(16, set(range(16)), accents={0, 4, 8, 12}),
        "htom": grid_from_hits(16, {2, 10} if step_up % 2 == 0 else set()),
        "mtom": grid_from_hits(16, {6, 14} if step_up % 2 == 1 else set()),
        "shaker": grid_from_hits(16, set(range(16))),
    }


def build():
    sections = []

    # intro: drone + sparse kick, no bass motion yet, room to breathe
    sections.append({
        "name": "intro", "time_sig": TS, "bpm": BPM,
        "bars": [
            {"drums": _sparse_bar(), "bass": BASS_DRONE, "melody": []}
            for _ in range(4)
        ],
    })

    # verse: full half-time groove, melody answers every other bar
    verse_bars = []
    for i in range(8):
        is_last_pair_bar = i in (3, 7)
        # melody rests on even bars ("response" bars) -- a quiet ghost snare fills that space instead
        ghost = {13} if i % 2 == 0 else set()
        drums = _groove_bar(fill=is_last_pair_bar, ghost_steps=ghost)
        bass = BASS_PHRASE
        melody = (MELODY_CALL_FILL if is_last_pair_bar else MELODY_CALL) if i % 2 == 1 else []
        verse_bars.append({"drums": drums, "bass": bass, "melody": melody})
    sections.append({"name": "verse", "time_sig": TS, "bpm": BPM, "bars": verse_bars})

    # build: toms/hats intensify, bassline pushes up an octave on top, melody continuous & climbing
    build_bars = []
    for i in range(4):
        drums = _build_bar(i)
        bass = [(s, d, n + 12 if i >= 2 else n, v) for (s, d, n, v) in BASS_PHRASE]
        climb = [
            (0, 3, scale_degree(D_MEL_ROOT, "aeolian", 4 + i), 92 + i),
            (4, 3, scale_degree(D_MEL_ROOT, "aeolian", 3 + i), 90 + i),
            (8, 4, scale_degree(D_MEL_ROOT, "aeolian", 5 + i), 98 + i),
            (13, 3, scale_degree(D_MEL_ROOT, "aeolian", 2 + i), 88 + i),
        ]
        build_bars.append({"drums": drums, "bass": bass, "melody": climb})
    sections.append({"name": "build", "time_sig": TS, "bpm": BPM, "bars": build_bars})

    # outro: back to the drone, melody resolves down to the tonic and stops
    outro_bars = []
    for i in range(4):
        drums = _sparse_bar()
        bass = BASS_DRONE
        if i == 2:
            melody = [(0, 6, scale_degree(D_MEL_ROOT, "aeolian", 2), 78), (8, 8, D_MEL_ROOT, 74)]
        elif i == 3:
            melody = [(0, 16, D_MEL_ROOT, 68)]
        else:
            melody = []
        outro_bars.append({"drums": drums, "bass": bass, "melody": melody})
    sections.append({"name": "outro", "time_sig": TS, "bpm": BPM, "bars": outro_bars})

    return sections


def produce(result, bass_channel, melody_channel):
    """Drums stay machine-tight; bass and melody get subtle human timing/dynamics,
    plus an expression swell through the build and a release back down in the outro."""
    import humanize
    from arrange import section_span
    from midiwriter import cc_ramp

    bass = humanize.jitter(result["bass"], timing_ticks=6, vel_amount=6, seed=1)
    melody = humanize.jitter(result["melody"], timing_ticks=10, vel_amount=8, seed=2)

    bounds = result["section_bounds"]
    build_start, build_end = section_span(bounds, "build")
    outro_start, outro_end = section_span(bounds, "outro")

    cc_bass = (cc_ramp(bass_channel, 11, build_start, build_end, 92, 127)
               + cc_ramp(bass_channel, 11, outro_start, outro_end, 127, 88))
    cc_melody = (cc_ramp(melody_channel, 11, build_start, build_end, 92, 127)
                 + cc_ramp(melody_channel, 11, outro_start, outro_end, 127, 88))

    return {
        "drums": result["drums"],
        "bass": bass,
        "melody": melody,
        "cc": {"bass": cc_bass, "melody": cc_melody},
    }
