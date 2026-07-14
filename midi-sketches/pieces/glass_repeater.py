"""glass_repeater -- 122 BPM, F# phrygian, four-on-the-floor pulse with glitchy hats.

Radiohead-led: an insistent electronic pulse (Idioteque-ish) with stuttering,
dropout hi-hats. Fever Ray-flavoured: a deep, octave-jumping synth-bass pulse.
Kate Bush-flavoured: an obsessively repeating melodic cell that is 5 steps
long against the 16-step (4/4) bar, so it drifts in and out of phase with
the beat instead of looping in place -- a controlled 5-against-4 polymeter.
"""

from theory import note, scale_degree
from rhythm import grid_from_hits
from drums import KICK, CLAP, CHH, OHH, HTOM

TITLE = "glass_repeater"
BPM = 122
TS = (4, 4)

FS_BASS_ROOT = note("F#", 1)   # 30
FS_BASS_OCT = note("F#", 2)    # 42
FS_MEL_ROOT = note("F#", 4)    # 66

DRUM_NOTES = {
    "kick": (KICK, 108, 124),
    "clap": (CLAP, 92, 114),
    "chh": (CHH, 60, 86),
    "ohh": (OHH, 70, 92),
    "htom": (HTOM, 84, 104),
}

BASS_PULSE = [
    (0, 4, FS_BASS_ROOT, 104),
    (4, 2, FS_BASS_OCT, 90),
    (6, 2, FS_BASS_ROOT, 90),
    (8, 4, FS_BASS_ROOT, 104),
    (12, 2, scale_degree(FS_BASS_ROOT, "phrygian", 2), 92),   # A1, phrygian b3
    (14, 2, FS_BASS_ROOT, 88),
]
BASS_DRONE = [(0, 16, FS_BASS_ROOT, 80)]


def _pulse_bar(glitch=False):
    hats = (
        grid_from_hits(16, set(range(16)) - {2, 6, 10, 14}, accents={0, 8})
        if glitch else
        grid_from_hits(16, set(range(16)), accents={0, 4, 8, 12})
    )
    out = {
        "kick": grid_from_hits(16, {0, 4, 8, 12}, accents={0, 8}),
        "clap": grid_from_hits(16, {8}, accents={8}),
        "chh": hats,
    }
    if glitch:
        out["ohh"] = grid_from_hits(16, {15})
    return out


def _break_bar():
    return {
        "kick": grid_from_hits(16, {0}, accents={0}),
        "chh": grid_from_hits(16, {0, 4, 8, 12}),
    }


def _phase_melody(n_bars, vel_base=90):
    """Tile a 5-step melodic cell across n_bars of 16 steps -- it re-phases against
    the bar line every bar (16 % 5 == 1), splitting sustained notes at bar lines
    where needed so each bar's event list stays self-contained."""
    cell = [
        (2, 0, vel_base + 8),   # F# (root)
        (1, 1, vel_base - 6),   # G (phrygian b2 -- the dark neighbour tone)
        (2, 2, vel_base),       # A (phrygian b3)
    ]
    total_steps = n_bars * 16
    bars_out = [[] for _ in range(n_bars)]
    pos = 0
    ci = 0
    while pos < total_steps:
        dur, degree, vel = cell[ci % len(cell)]
        dur = min(dur, total_steps - pos)
        if dur <= 0:
            break
        note_num = scale_degree(FS_MEL_ROOT, "phrygian", degree)
        remaining = dur
        cur = pos
        while remaining > 0:
            bar_idx = cur // 16
            local = cur % 16
            take = min(remaining, 16 - local)
            bars_out[bar_idx].append((local, take, note_num, vel))
            cur += take
            remaining -= take
        pos += dur
        ci += 1
    return bars_out


def build():
    sections = []

    sections.append({
        "name": "intro", "time_sig": TS, "bpm": BPM,
        "bars": [
            {"drums": {"kick": grid_from_hits(16, {0, 8}, accents={0})}, "bass": BASS_DRONE, "melody": []}
            for _ in range(2)
        ],
    })

    verse_melody = _phase_melody(8)
    verse_bars = []
    for i in range(8):
        verse_bars.append({
            "drums": _pulse_bar(glitch=(i % 2 == 1)),
            "bass": BASS_PULSE,
            "melody": verse_melody[i],
        })
    sections.append({"name": "verse", "time_sig": TS, "bpm": BPM, "bars": verse_bars})

    sections.append({
        "name": "break", "time_sig": TS, "bpm": BPM,
        "bars": [
            {"drums": _break_bar(), "bass": BASS_DRONE, "melody": []}
            for _ in range(4)
        ],
    })

    verse2_melody = _phase_melody(4)
    verse2_bars = []
    for i in range(4):
        verse2_bars.append({
            "drums": _pulse_bar(glitch=(i % 2 == 0)),
            "bass": BASS_PULSE,
            "melody": verse2_melody[i],
        })
    sections.append({"name": "verse2", "time_sig": TS, "bpm": BPM, "bars": verse2_bars})

    sections.append({
        "name": "outro", "time_sig": TS, "bpm": BPM,
        "bars": [
            {"drums": {"kick": grid_from_hits(16, {0} if i == 1 else {0, 8})},
             "bass": BASS_DRONE if i == 0 else [(0, 16, FS_BASS_ROOT, 70)],
             "melody": []}
            for i in range(2)
        ],
    })

    return sections


def produce(result, bass_channel, melody_channel):
    """Everything stays machine-quantized -- the point is the mechanical pulse and
    the exact 5-against-4 phase drift -- but a CC74 (brightness/cutoff) sweep opens
    and closes the filter across verse -> break -> verse2, the classic "the machine
    is breathing" IDM production move."""
    from arrange import section_span
    from midiwriter import cc_ramp

    bounds = result["section_bounds"]
    v1_start, v1_end = section_span(bounds, "verse")
    b_start, b_end = section_span(bounds, "break")
    v2_start, v2_end = section_span(bounds, "verse2")

    def sweep(channel):
        return (
            cc_ramp(channel, 74, v1_start, v1_end, 40, 112)
            + cc_ramp(channel, 74, b_start, b_end, 112, 46)
            + cc_ramp(channel, 74, v2_start, v2_end, 46, 118)
        )

    return {
        "drums": result["drums"],
        "bass": result["bass"],
        "melody": result["melody"],
        "cc": {"bass": sweep(bass_channel), "melody": sweep(melody_channel)},
    }
