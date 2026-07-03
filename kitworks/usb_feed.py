#!/usr/bin/env python3
"""usb_feed -- stream a clip over USB MIDI so the MC-707 records it live.

The one verified per-track alternative to menu imports (see
sd/MC707_FACTS.TXT): arm a clip on the 707 and RECORD the part as this
script streams it in. Same one-clip granularity, zero file-browser diving.

707 SETUP (once)
  * connect USB (or DIN MIDI IN); [SHIFT]+[KNOB ASSIGN] -> SET -> MIDI:
      Sync Mode : AUTO or MIDI   (follow our Start + clock)
      Rx Auto Ch: ON             (input follows the selected track)
        -- or leave it OFF and match channels: default map is
           track n = channel n, which is what our filenames encode.
  * cursor onto the target clip, set its length with [MEASURE]
  * press [REC], then [START/STOP] -- the 707 waits for our clock.

THEN, on the computer (needs: pip install mido python-rtmidi)
  python usb_feed.py --list                          # find the 707's port
  python usb_feed.py sd/.../T2_BASS_2MAIN.MID        # channel 2, from the name
  python usb_feed.py FILE.MID --port MC-707 --channel 3 --loops 4

We send MIDI Start, one count-in bar of clock, then the notes at the
file's own tempo -- looped --loops times so you can punch REC on any
pass -- then All-Notes-Off and Stop.
"""

import argparse
import os
import re
import sys
import time

import mido

CLOCKS_PER_QUARTER = 24


def load_clip(path):
    """-> (notes [(sec, msg)], tempo_us, quarters_per_bar, bar_count)"""
    m = mido.MidiFile(path)
    tempo, meter = 500000, (4, 4)
    notes, last_tick = [], 0
    for tr in m.tracks:
        t = 0
        for msg in tr:
            t += msg.time
            if msg.type == "set_tempo":
                tempo = msg.tempo
            elif msg.type == "time_signature":
                meter = (msg.numerator, msg.denominator)
            elif msg.type in ("note_on", "note_off"):
                notes.append((t, msg))
                last_tick = max(last_tick, t)
    spt = tempo / 1e6 / m.ticks_per_beat                # seconds per tick
    qpb = meter[0] * 4 / meter[1]                       # quarters per bar
    bar_ticks = qpb * m.ticks_per_beat
    # ceil to whole bars, forgiving the few ticks the groove polish pushes
    # a final note-off past the barline (else loops drift off the 707 grid)
    bars = max(1, int((last_tick / bar_ticks) - 0.1) + 1)
    notes.sort(key=lambda p: p[0])
    return [(t * spt, msg) for t, msg in notes], tempo, qpb, bars


def build_timeline(notes, tempo, qpb, bars, channel, loops, count_in):
    """Merge count-in, clock, looped notes, and stop into one (sec, msg) list."""
    spq = tempo / 1e6                                   # seconds per quarter
    loop_len = bars * qpb * spq                         # bar-rounded loop spacing
    lead = count_in * qpb * spq
    total = lead + loops * loop_len
    ev = [(0.0, mido.Message("songpos", pos=0)), (0.0, mido.Message("start"))]
    n_clocks = int(total / (spq / CLOCKS_PER_QUARTER)) + 1
    ev += [(i * spq / CLOCKS_PER_QUARTER, mido.Message("clock"))
           for i in range(n_clocks)]
    for k in range(loops):
        off = lead + k * loop_len
        ev += [(off + t, msg.copy(channel=channel)) for t, msg in notes]
    ev.append((total + 0.05, mido.Message("control_change", channel=channel,
                                          control=123, value=0)))
    ev.append((total + 0.10, mido.Message("stop")))
    ev.sort(key=lambda p: p[0])
    return ev, total


def channel_from_name(path):
    """T3_LEAD_2MAIN.MID -> wire channel 2 (track 3 = channel 3, 0-based 2)."""
    m = re.match(r"T(\d+)_", os.path.basename(path))
    return int(m.group(1)) - 1 if m else None


def pick_port(want):
    names = mido.get_output_names()
    if not names:
        sys.exit("no MIDI output ports found -- is the 707 connected?")
    if want:
        hits = [n for n in names if want.lower() in n.lower()]
        if not hits:
            sys.exit(f"no port matching {want!r}; available: {names}")
        return hits[0]
    hits = [n for n in names if "707" in n or "MC-" in n]
    return hits[0] if hits else names[0]


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("file", nargs="?", help="clip .MID to stream")
    ap.add_argument("--list", action="store_true", help="list MIDI out ports")
    ap.add_argument("--port", help="output port (substring match)")
    ap.add_argument("--channel", type=int,
                    help="MIDI channel 1-16 (default: track number from a "
                         "T<n>_ filename, else 1)")
    ap.add_argument("--loops", type=int, default=4,
                    help="times to repeat the clip (default 4)")
    ap.add_argument("--count-in", type=int, default=1,
                    help="count-in bars of clock before notes (default 1)")
    ap.add_argument("--dry-run", action="store_true",
                    help="print the plan; send nothing")
    a = ap.parse_args()

    if a.list:
        try:
            for n in mido.get_output_names():
                print(n)
        except Exception as e:
            sys.exit(f"could not open a MIDI backend ({e}); "
                     "run: pip install python-rtmidi")
        return
    if not a.file:
        ap.error("give a clip file, or --list")

    ch = (a.channel - 1) if a.channel else channel_from_name(a.file)
    if ch is None:
        ch = 0
    if not 0 <= ch <= 15:
        sys.exit("--channel must be 1-16")

    notes, tempo, qpb, bars = load_clip(a.file)
    if not notes:
        sys.exit(f"{a.file}: no notes")
    bpm = round(6e7 / tempo, 1)
    ev, total = build_timeline(notes, tempo, qpb, bars, ch, a.loops, a.count_in)
    print(f"{os.path.basename(a.file)}: {bars} bar(s) @ {bpm} bpm, "
          f"{len(notes) // 2} notes -> channel {ch + 1}, "
          f"{a.count_in}-bar count-in, x{a.loops} = {total:.1f}s")
    if a.dry_run:
        return

    try:
        port = pick_port(a.port)
    except Exception as e:
        sys.exit(f"could not open a MIDI backend ({e}); "
                 "run: pip install python-rtmidi")
    print(f"streaming to {port!r} -- arm the clip ([REC] then [START/STOP]) now")
    with mido.open_output(port) as out:
        t0 = time.monotonic()
        for t, msg in ev:
            wait = t0 + t - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            out.send(msg)
    print("done -- hit [REC] off on the 707 and check the clip")


if __name__ == "__main__":
    main()
