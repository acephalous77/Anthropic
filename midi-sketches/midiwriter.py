"""Turn note-event lists into standard MIDI files, via mido."""

from collections import namedtuple

import mido

PPQ = 480
DRUM_CHANNEL = 9  # GM percussion channel (0-indexed channel 10)

# Event.start/dur are in ticks. channel=DRUM_CHANNEL implies the GM drum kit.
Event = namedtuple("Event", "start dur note vel channel")


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


def _note_track(events, channel, program, track_name):
    track = mido.MidiTrack()
    track.append(mido.MetaMessage("track_name", name=track_name, time=0))
    if program is not None:
        track.append(mido.Message("program_change", program=program, channel=channel, time=0))

    pairs = []
    for ev in events:
        pairs.append((ev.start, 1, mido.Message("note_on", note=ev.note, velocity=ev.vel, channel=ev.channel, time=0)))
        pairs.append((ev.start + ev.dur, 0, mido.Message("note_off", note=ev.note, velocity=0, channel=ev.channel, time=0)))
    # note_off before note_on when they land on the same tick (priority 0 < 1)
    pairs.sort(key=lambda p: (p[0], p[1]))

    last = 0
    for tick, _, msg in pairs:
        msg.time = tick - last
        track.append(msg)
        last = tick
    return track


def write_track(path, events, bpm_changes, time_sig_changes, channel=0, program=None,
                 track_name="track", ppq=PPQ):
    """Write a single-instrument standard MIDI file."""
    mid = mido.MidiFile(ticks_per_beat=ppq)
    mid.tracks.append(_meta_track(bpm_changes, time_sig_changes, track_name))
    mid.tracks.append(_note_track(events, channel, program, track_name))
    mid.save(path)


def write_combined(path, tracks, bpm_changes, time_sig_changes, ppq=PPQ):
    """Merge several instrument event-lists into one multi-track file for preview.

    tracks: list of dicts with keys events/channel/program/name.
    """
    mid = mido.MidiFile(ticks_per_beat=ppq)
    mid.tracks.append(_meta_track(bpm_changes, time_sig_changes, "tempo/meta"))
    for t in tracks:
        mid.tracks.append(_note_track(t["events"], t["channel"], t.get("program"), t["name"]))
    mid.save(path)
