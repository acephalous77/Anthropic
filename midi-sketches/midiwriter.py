"""Turn note-event lists into standard MIDI files, via mido."""

from collections import namedtuple

import mido

PPQ = 480
DRUM_CHANNEL = 9  # GM percussion channel (0-indexed channel 10)

# Event.start/dur are in ticks. channel=DRUM_CHANNEL implies the GM drum kit.
Event = namedtuple("Event", "start dur note vel channel")

# CCEvent.tick is absolute ticks; controller is the CC number (11=expression, 74=brightness/cutoff, ...).
CCEvent = namedtuple("CCEvent", "tick controller value channel")


def cc_ramp(channel, controller, start_tick, end_tick, start_val, end_val, step_ticks=PPQ // 8):
    """Linearly interpolated CC automation from start_val to end_val across [start_tick, end_tick)."""
    events = []
    span = max(end_tick - start_tick, step_ticks)
    tick = start_tick
    while tick < end_tick:
        frac = (tick - start_tick) / span
        value = round(start_val + (end_val - start_val) * frac)
        events.append(CCEvent(tick, controller, max(0, min(127, value)), channel))
        tick += step_ticks
    events.append(CCEvent(end_tick, controller, end_val, channel))
    return events


def _meta_track(bpm_changes, time_sig_changes, track_name):
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name=track_name, time=0))
    markers = []
    for tick, bpm in bpm_changes:
        markers.append((tick, mido.MetaMessage("set_tempo", tempo=mido.bpm2tempo(bpm), time=0)))
    for tick, (num, den) in time_sig_changes:
        markers.append((tick, mido.MetaMessage("time_signature", numerator=num, denominator=den, time=0)))
    markers.sort(key=lambda m: m[0])
    last = 0
    for tick, msg in markers:
        msg.time = tick - last
        track.append(msg)
        last = tick
    return track


def _note_track(events, channel, program, track_name, cc_events=None):
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name=track_name, time=0))
    if program is not None:
        track.append(mido.Message("program_change", program=program, channel=channel, time=0))

    pairs = []
    for ev in events:
        pairs.append((ev.start, 1, mido.Message("note_on", note=ev.note, velocity=ev.vel, channel=ev.channel, time=0)))
        pairs.append((ev.start + ev.dur, 0, mido.Message("note_off", note=ev.note, velocity=0, channel=ev.channel, time=0)))
    for cc in (cc_events or []):
        pairs.append((cc.tick, 0, mido.Message("control_change", control=cc.controller, value=cc.value,
                                                channel=cc.channel, time=0)))
    # note_off/CC before note_on when they land on the same tick (priority 0 < 1)
    pairs.sort(key=lambda p: (p[0], p[1]))

    last = 0
    for tick, _, msg in pairs:
        msg.time = tick - last
        track.append(msg)
        last = tick
    return track


def write_track(path, events, bpm_changes, time_sig_changes, channel=0, program=None,
                 track_name="track", ppq=PPQ, cc_events=None):
    """Write a single-instrument standard MIDI file."""
    mid = mido.MidiFile(ticks_per_beat=ppq)
    mid.tracks.append(_meta_track(bpm_changes, time_sig_changes, track_name))
    mid.tracks.append(_note_track(events, channel, program, track_name, cc_events=cc_events))
    mid.save(path)


def write_combined(path, tracks, bpm_changes, time_sig_changes, ppq=PPQ):
    """Merge several instrument event-lists into one multi-track file for preview.

    tracks: list of dicts with keys events/channel/program/name/cc_events.
    """
    mid = mido.MidiFile(ticks_per_beat=ppq)
    mid.tracks.append(_meta_track(bpm_changes, time_sig_changes, "tempo/meta"))
    for t in tracks:
        mid.tracks.append(_note_track(t["events"], t["channel"], t.get("program"), t["name"],
                                       cc_events=t.get("cc_events")))
    mid.save(path)
