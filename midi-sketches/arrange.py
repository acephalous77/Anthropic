"""Stack bars (with their own time signature/tempo) into absolute-tick events for a whole piece.

A piece is a list of sections; each section is a dict:
    {"name": str, "time_sig": (num, den), "bpm": float, "bars": [bar, ...]}
Each bar is a dict with up to three keys:
    "drums":  {voice_name: grid_string, ...}   -- grid length must equal bar_steps(time_sig)
    "bass":   [(start_step, dur_steps, note, vel), ...]
    "melody": [(start_step, dur_steps, note, vel), ...]
Missing keys/voices in a bar mean silence for that part in that bar.
"""

from midiwriter import Event, PPQ
from rhythm import grid_to_events

STEP_TICKS = PPQ // 4  # sixteenth note

DRUM_CHANNEL = 9


def bar_ticks(time_sig):
    num, den = time_sig
    ticks = PPQ * 4 * num / den
    assert ticks == int(ticks), f"time signature {time_sig} does not divide evenly at ppq={PPQ}"
    return int(ticks)


def bar_steps(time_sig):
    ticks = bar_ticks(time_sig)
    assert ticks % STEP_TICKS == 0, f"bar of {ticks} ticks isn't a whole number of 16th-note steps"
    return ticks // STEP_TICKS


def render_piece(sections, drum_notes, bass_channel=0, melody_channel=1):
    """drum_notes: {voice_name: (note_num, vel, accent_vel)}. Returns dict of event lists + tempo/meter maps."""
    bar_start = 0
    bpm_changes = []
    time_sig_changes = []
    section_bounds = []
    drum_events, bass_events, melody_events = [], [], []
    last_bpm, last_ts = None, None

    for section in sections:
        ts = section["time_sig"]
        bpm = section["bpm"]
        steps = bar_steps(ts)
        section_start = bar_start
        for bar in section["bars"]:
            if bpm != last_bpm:
                bpm_changes.append((bar_start, bpm))
                last_bpm = bpm
            if ts != last_ts:
                time_sig_changes.append((bar_start, ts))
                last_ts = ts

            for voice, grid in bar.get("drums", {}).items():
                assert len(grid) == steps, (
                    f"section {section['name']!r}: {voice} grid has {len(grid)} steps, expected {steps}"
                )
                note_num, vel, accent_vel = drum_notes[voice]
                drum_events.extend(
                    grid_to_events(grid, note_num, STEP_TICKS, start_tick=bar_start,
                                   vel=vel, accent_vel=accent_vel, channel=DRUM_CHANNEL)
                )

            for start_step, dur_steps, note_num, vel in bar.get("bass", []):
                assert 0 <= start_step and start_step + dur_steps <= steps, (
                    f"section {section['name']!r}: bass note out of bar bounds"
                )
                bass_events.append(Event(bar_start + start_step * STEP_TICKS,
                                          dur_steps * STEP_TICKS, note_num, vel, bass_channel))

            for start_step, dur_steps, note_num, vel in bar.get("melody", []):
                assert 0 <= start_step and start_step + dur_steps <= steps, (
                    f"section {section['name']!r}: melody note out of bar bounds"
                )
                melody_events.append(Event(bar_start + start_step * STEP_TICKS,
                                            dur_steps * STEP_TICKS, note_num, vel, melody_channel))

            bar_start += bar_ticks(ts)

        section_bounds.append({"name": section["name"], "start": section_start, "end": bar_start})

    return {
        "drums": drum_events,
        "bass": bass_events,
        "melody": melody_events,
        "bpm_changes": bpm_changes,
        "time_sig_changes": time_sig_changes,
        "section_bounds": merge_section_bounds(section_bounds),
        "total_ticks": bar_start,
    }


def merge_section_bounds(bounds):
    """Collapse consecutive entries that share a name into a single (start, end) span --
    useful when a section is emitted one bar at a time (e.g. alternating time signatures)."""
    merged = []
    for b in bounds:
        if merged and merged[-1]["name"] == b["name"] and merged[-1]["end"] == b["start"]:
            merged[-1]["end"] = b["end"]
        else:
            merged.append(dict(b))
    return merged


def section_span(bounds, name):
    """Return (start, end) for the first section bounds entry matching `name`."""
    for b in bounds:
        if b["name"] == name:
            return b["start"], b["end"]
    raise KeyError(f"no section named {name!r} in bounds {bounds}")
