#!/usr/bin/env python3
"""songs.py -- stitch a kit's section clips into full-length song arrangements.

The kits render as six loopable section columns; this walks an arrangement
(an ordered list of sections) and concatenates each part's section clips at
the right bar offset into one continuous multi-track song MIDI -- so you can
audition a whole tune, not just a loop, and so the section order matches what
`usb_feed --arrange` fires on the 707.

    python songs.py            # every kit, both arrangements -> songs/

Each song is a combined file (drums/bass/lead/counter/chords/arp on their
channels). The arrangement's scene order (1..6 = intro/main/lift/break/peak/
end) is exactly the ride you'd drive live.
"""

import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import kitlib as K            # noqa: E402
import midiwriter            # noqa: E402
import fx                     # noqa: E402
from kits import KITS         # noqa: E402

OUT = os.path.join(HERE, "songs")
STEP = K.STEP
SEC_VAR = dict(K.VARIATIONS)  # "1_intro" -> "intro", ...

# arrangements as (section-key, ...) using the six columns; scene numbers are
# the column's leading digit, so these double as usb_feed --arrange rides
ARRANGEMENTS = {
    "short": ["1_intro", "2_main", "3_lift", "2_main", "6_end"],
    "full":  ["1_intro", "2_main", "2_main", "3_lift", "4_break",
              "2_main", "3_lift", "5_peak", "6_end"],
}


def _section_bars(which):
    return 2 if which == "end" else 4      # matches the variation/pad_clip lengths


def _part_makers(kit):
    """Same part->(make, channel, program) map build_kit uses, so songs render
    identically to the section clips."""
    bar_steps = kit.get("bar_steps", 16)
    pr = kit["progs"]
    ch_of = {"bass": 0, "lead": 1, "counter": 4, "chords": 2, "arp": 3}
    parts = {"drums": (lambda w: K.drum_bars(K.drums_variation(kit, w), bar_steps), 9, None)}
    for pname, var in (("bass", K.bass_variation), ("lead", K.lead_variation),
                       ("counter", K.lead_variation), ("chords", K.chords_variation),
                       ("arp", K.arp_variation)):
        if kit.get(pname):
            parts[pname] = (
                lambda w, p=pname, vf=var: K.bars_to_events(
                    vf(kit[p], w, bar_steps), ch_of[p], bar_steps),
                ch_of[pname], pr.get(pname))
    return parts


def render_song(kit, index, arrangement):
    rng = random.Random(7000 + index)      # same seed as build_kit -> same feel
    bar_steps = kit.get("bar_steps", 16)
    bar_ticks = bar_steps * STEP
    parts = _part_makers(kit)
    tracks = []
    for name, (make, ch, prog) in parts.items():
        events, offset_bars = [], 0
        for sec in arrangement:
            which = SEC_VAR[sec]
            evs = K.polish(make(which), kit, rng)
            shift = offset_bars * bar_ticks
            events += [e._replace(start=e.start + shift) for e in evs]
            offset_bars += _section_bars(which)
        if events:
            cc = fx.song_cc(name, arrangement, ch, bar_steps, kit["feel"])
            tracks.append({"events": events, "channel": ch, "program": prog,
                           "name": name, "cc_events": cc})
    total_bars = sum(_section_bars(SEC_VAR[s]) for s in arrangement)
    return tracks, total_bars


def main():
    if os.path.isdir(OUT):
        import shutil
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    meterless = 0
    for i, kit in enumerate(KITS, 1):
        meter = kit.get("meter", (4, 4))
        bpmc, tsc = [(0, kit["bpm"])], [(0, meter)]
        for arr_name, arrangement in ARRANGEMENTS.items():
            tracks, bars = render_song(kit, i, arrangement)
            tag = f"{i:02d}_{kit['name']}_{kit['key']}_{arr_name}"
            path = os.path.join(OUT, f"{tag}.mid")
            midiwriter.write_combined(path, tracks, bpmc, tsc)
        print(f"  {i:02d} {kit['name']:12} short + full ({bars} bars @ {kit['bpm']})")
    print(f"\n{len(KITS) * len(ARRANGEMENTS)} songs -> {OUT}")
    print("scene rides:  short = 1-2-3-2-6   full = 1-2-2-3-4-2-3-5-6")


if __name__ == "__main__":
    main()
