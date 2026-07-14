#!/usr/bin/env python3
"""usb_feed -- drive the MC-707 over USB MIDI: record clips in, or sequence
the matrix out.

Four modes (all verified against sd/MC707_FACTS.TXT's MIDI map -- default
channels track n = ch n, control channel = 16):

  STREAM (default)  arm a clip on the 707 and RECORD a part as this streams
                    it in -- the per-track alternative to menu import.
      python usb_feed.py sd/.../T2_BASS_2MAIN.MID       # channel from the name

  SELECT            fire a Program Change to launch a clip on a track
                    (PC clip-1 on the track's channel).
      python usb_feed.py --select 2 3                   # track 2, clip 3

  SCENE             recall a scene (PC scene-1 on ch 16).
      python usb_feed.py --scene 4

  ARRANGE           BE the clock and sequence scenes -- song mode from the
                    field-guide rides. Sends Start + clock at --bpm, fires
                    each scene at the bar, loops --repeat times, then Stop.
      python usb_feed.py --arrange 1,2,2,3 --bpm 114 --bars 4 --repeat 2

707 SETUP (once)
  * connect USB (or DIN MIDI IN); [SHIFT]+[KNOB ASSIGN] -> SET -> MIDI:
      Sync Mode : AUTO or MIDI   (follow our Start + clock -- needed for
                                  STREAM and ARRANGE)
      Rx Auto Ch: ON             (STREAM: input follows the selected track;
                                  or leave OFF and match channels by name)
  * STREAM: cursor onto the target clip, set length with [MEASURE], press
    [REC] then [START/STOP] -- the 707 waits for our clock.
  * SELECT/SCENE/ARRANGE: just have the clips/scenes loaded; we launch them.

Needs: pip install mido python-rtmidi   (python usb_feed.py --list for ports)
"""

import argparse
import os
import re
import sys
import time

import mido

CLOCKS_PER_QUARTER = 24
CONTROL_CHANNEL = 15        # MIDI ch 16 (0-based) -- scene recall / control
TAG_WHICH = {"1INTRO": "intro", "2MAIN": "main", "3LIFT": "lift",
             "4BREAK": "break", "5PEAK": "peak", "6END": "end"}


def _fx_timeline(path, channel, bars, qpb, tempo, loops, count_in, feel):
    """CC motion (filter/reverb/expression) for the clip being streamed, so a
    live-record pass captures it as 707 motion. Part+section come from the
    T<n>_<PART>_<col><SECTION> filename; falls back to nothing if unparseable."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    import fx
    stem = os.path.basename(path).rsplit(".", 1)[0].split("_")
    if len(stem) < 3:
        return []
    part, which = stem[1].lower(), TAG_WHICH.get(stem[2].upper())
    if which is None or part not in fx.PART_VOICE:
        return []
    bar_steps = int(round(qpb * 4))
    ccs = fx.clip_cc(part, which, channel, bars, bar_steps, feel)
    spq = tempo / 1e6
    spt = spq / 480.0                       # our files are PPQ 480
    lead, loop_len = count_in * qpb * spq, bars * qpb * spq
    out = []
    for k in range(loops):
        off = lead + k * loop_len
        for cc in ccs:
            out.append((off + cc.tick * spt,
                        mido.Message("control_change", control=cc.controller,
                                     value=cc.value, channel=cc.channel)))
    return out


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


def clip_pc(track, clip):
    """Launch clip N on a track: PC clip-1 on that track's channel (1-based)."""
    return mido.Message("program_change", program=clip - 1, channel=track - 1)


def scene_pc(scene):
    """Recall scene N: PC scene-1 on the control channel (16)."""
    return mido.Message("program_change", program=scene - 1, channel=CONTROL_CHANNEL)


def build_arrange(scenes, bpm, bars, repeat):
    """Clock-driven scene sequence: Start, clock at bpm, one scene PC per
    `bars`-long slot, looped `repeat` times, then Stop. Assumes 4/4 slots."""
    spq = 60.0 / bpm                                    # seconds per quarter
    hold = bars * 4 * spq                               # seconds per scene slot
    seq = scenes * repeat
    total = len(seq) * hold
    ev = [(0.0, mido.Message("songpos", pos=0)), (0.0, mido.Message("start"))]
    n_clocks = int(total / (spq / CLOCKS_PER_QUARTER)) + 1
    ev += [(i * spq / CLOCKS_PER_QUARTER, mido.Message("clock"))
           for i in range(n_clocks)]
    for k, sc in enumerate(seq):
        ev.append((k * hold, scene_pc(sc)))
    ev.append((total + 0.05, mido.Message("stop")))
    ev.sort(key=lambda p: p[0])
    return ev, total


def stream(port_name, ev):
    """Send a timed (seconds, message) list in real time."""
    with mido.open_output(port_name) as out:
        t0 = time.monotonic()
        for t, msg in ev:
            wait = t0 + t - time.monotonic()
            if wait > 0:
                time.sleep(wait)
            out.send(msg)


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


def _pick_or_die(want):
    try:
        return pick_port(want)
    except Exception as e:
        sys.exit(f"could not open a MIDI backend ({e}); run: pip install python-rtmidi")


def _send_or_die(want, ev):
    stream(_pick_or_die(want), ev)


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
    ap.add_argument("--fx", action="store_true",
                    help="also stream this clip's filter/reverb/expression motion "
                         "(part+section read from the filename) so the record pass "
                         "captures it as 707 motion")
    ap.add_argument("--feel", default="laidback",
                    choices=["laidback", "pushing", "ritual"],
                    help="feel tilt for --fx motion (default laidback)")
    ap.add_argument("--select", nargs=2, type=int, metavar=("TRACK", "CLIP"),
                    help="launch clip CLIP on track TRACK (both 1-based) and exit")
    ap.add_argument("--scene", type=int, metavar="N",
                    help="recall scene N (1-based) and exit")
    ap.add_argument("--arrange", metavar="SCENES",
                    help="comma-separated scene numbers to sequence as clock master")
    ap.add_argument("--bpm", type=float, default=120,
                    help="tempo for --arrange (default 120)")
    ap.add_argument("--bars", type=int, default=4,
                    help="bars to hold each scene in --arrange (default 4)")
    ap.add_argument("--repeat", type=int, default=1,
                    help="times to cycle the --arrange sequence (default 1)")
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

    # --- one-shot SELECT / SCENE -------------------------------------------
    if a.select or a.scene is not None:
        if a.select:
            track, clip = a.select
            if not (1 <= track <= 8 and 1 <= clip <= 16):
                sys.exit("--select TRACK 1-8 CLIP 1-16")
            msg, what = clip_pc(track, clip), f"launch track {track} clip {clip}"
        else:
            if not 1 <= a.scene <= 128:
                sys.exit("--scene must be 1-128")
            msg, what = scene_pc(a.scene), f"recall scene {a.scene}"
        print(what + (f"  ({msg})" if a.dry_run else ""))
        if a.dry_run:
            return
        _send_or_die(a.port, [(0.0, msg)])
        print("sent")
        return

    # --- ARRANGE (scene sequencer, clock master) ---------------------------
    if a.arrange:
        try:
            scenes = [int(s) for s in a.arrange.split(",") if s.strip()]
        except ValueError:
            sys.exit("--arrange wants comma-separated scene numbers, e.g. 1,2,2,3")
        if not scenes or any(not 1 <= s <= 128 for s in scenes):
            sys.exit("--arrange scenes must be 1-128")
        ev, total = build_arrange(scenes, a.bpm, a.bars, a.repeat)
        ride = "-".join(map(str, scenes))
        print(f"arrange {ride} x{a.repeat} @ {a.bpm} bpm, {a.bars} bars each "
              f"= {total:.1f}s ({len(scenes) * a.repeat} scene changes)")
        if a.dry_run:
            return
        port = _pick_or_die(a.port)
        print(f"sequencing to {port!r} -- set the 707 to slave (Sync AUTO/MIDI) now")
        stream(port, ev)
        print("done -- sent Stop")
        return

    if not a.file:
        ap.error("give a clip file, or --list / --select / --scene / --arrange")

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
    fx_note = ""
    if a.fx:
        fxev = _fx_timeline(a.file, ch, bars, qpb, tempo, a.loops, a.count_in, a.feel)
        ev += fxev
        ev.sort(key=lambda p: p[0])
        fx_note = f", +{len(fxev)} fx CC ({a.feel})" if fxev else " (no fx: name unparsed)"
    print(f"{os.path.basename(a.file)}: {bars} bar(s) @ {bpm} bpm, "
          f"{len(notes) // 2} notes -> channel {ch + 1}, "
          f"{a.count_in}-bar count-in, x{a.loops} = {total:.1f}s{fx_note}")
    if a.dry_run:
        return

    port = _pick_or_die(a.port)
    print(f"streaming to {port!r} -- arm the clip ([REC] then [START/STOP]) now")
    stream(port, ev)
    print("done -- hit [REC] off on the 707 and check the clip")


if __name__ == "__main__":
    main()
