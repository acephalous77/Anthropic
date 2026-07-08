"""fx.py -- a filter / effects / compression setup for the kits, grounded in
the MC-707's verified signal flow and MIDI map.

Signal flow (707 Reference / cheat sheet section 1, 8):
    tone -> FILTER/MOD/FX knob macros -> insert MFX (per track) ->
    Delay send + Reverb send -> Master -> Total MFX -> Total Comp -> Total EQ

This module supplies three tiers that map onto that chain:

  1. PER-PART VOICE (static) -- a cutoff/resonance start point, an insert-MFX
     choice, and delay/reverb send levels per part, tilted by the kit's feel.
     Rendered into a dial-in card (setup_card); dial by hand or via the macro
     knobs. These are recommendations, not automatable beyond the macros.

  2. MOTION (CC automation) -- the arrangement's dynamics as filter + reverb +
     expression moves. Verified-automatable CCs only:
         CC74 cutoff, CC71 resonance, CC11 expression, CC91 reverb send.
     (Delay send and MFX type have no documented CC, so they stay static.)
     Each section has a target openness/wash/level; within a clip we sit at
     that level with a small shape, and across a SONG we ramp between sections
     for the big intro->peak arc. The 707 records incoming CC as motion
     (firmware 1.8), so usb_feed can print these into a clip; they also make
     the song previews audibly move in a DAW.

  3. MASTER BUS (static) -- Total Comp + Total EQ settings per feel, the glue
     you set once under [SHIFT]+[MULTI] -> Comp / EQ tabs.

VERIFIED-vs-ASSUMED: the CC numbers, macro assignments, send routing, and comp/
EQ location are from the pasted cheat sheet (section 12/6/8). The specific
values (cutoff points, ratios, send amounts) are my musical defaults -- sensible
starting points, made to be turned.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import kitlib as K                                    # noqa: E402
from midiwriter import (CCEvent, cc_ramp, CC_BRIGHTNESS, CC_RESONANCE,  # noqa: E402
                        CC_EXPRESSION, CC_REVERB_SEND, CC_PAN)

STEP = K.STEP
CC_CUTOFF = CC_BRIGHTNESS      # 74, the de-facto cutoff; the FILTER macro (80) mirrors it

# ---- tier 1: per-part voice (static dial-in), before feel tilt ----------
# cutoff/reso/sends are 0-127; mfx names a 707 insert type; pan is -/+ from center
PART_VOICE = {
    "drums":   dict(cutoff=122, reso=8,  mfx="MFX Comp (bus glue) or none", delay=6,  reverb=16, pan=0),
    "bass":    dict(cutoff=98,  reso=16, mfx="Saturator / MFX Compressor",  delay=0,  reverb=8,  pan=0),
    "lead":    dict(cutoff=112, reso=30, mfx="Stereo/Tempo Delay (1/8 dot)", delay=52, reverb=38, pan=8),
    "counter": dict(cutoff=104, reso=24, mfx="Chorus + short Delay",         delay=30, reverb=46, pan=-14),
    "chords":  dict(cutoff=92,  reso=20, mfx="Chorus -> Reverb wash",        delay=12, reverb=62, pan=16),
    "arp":     dict(cutoff=118, reso=34, mfx="Ping-Pong Delay",              delay=56, reverb=44, pan=-20),
}

# feel tilt: (cutoff_delta, reverb_delta, comp_character)
FEEL_TILT = {
    "pushing":  dict(cutoff=+8,  reverb=-10),   # brighter, drier, punchier
    "laidback": dict(cutoff=0,   reverb=+6),    # warm, roomy
    "ritual":   dict(cutoff=-10, reverb=+16),   # dark, cavernous
}

# ---- tier 2: per-section targets (openness, reverb wash, level) ---------
# fractions of each part's base; the arrangement's dynamic shape lives here
SECTION_LEVELS = {   # which: (cutoff_frac, reverb_frac, expr_0_127)
    "intro": (0.55, 1.15, 92),
    "main":  (1.00, 1.00, 110),
    "lift":  (1.15, 1.10, 120),
    "break": (0.45, 1.60, 84),
    "peak":  (1.30, 1.20, 126),
    "end":   (0.80, 1.35, 100),
}

# ---- tier 3: master bus (Total Comp / EQ) per feel ----------------------
MASTER = {
    "pushing":  dict(comp="ratio 4:1, attack 8ms, release 120ms, thr -14dB, +4 makeup (punch/glue)",
                     eq="low +2 @80Hz, mid -2 @500Hz, high +3 @8kHz (scooped, forward)"),
    "laidback": dict(comp="ratio 2.5:1, attack 25ms, release 180ms, thr -12dB, +2 makeup (gentle glue)",
                     eq="low +1 @90Hz, mid flat, high +2 @10kHz (air)"),
    "ritual":   dict(comp="ratio 2:1, attack 40ms, release 250ms, thr -10dB, +2 makeup (slow, transparent)",
                     eq="low +2 @70Hz, mid -1 @400Hz, high +1 @6kHz (warm, soft top)"),
}


def voice(part, feel):
    """Per-part static setup with the feel tilt applied (clamped 0-127)."""
    v = dict(PART_VOICE[part])
    t = FEEL_TILT.get(feel, FEEL_TILT["laidback"])
    v["cutoff"] = max(20, min(127, v["cutoff"] + t["cutoff"]))
    v["reverb"] = max(0, min(127, v["reverb"] + t["reverb"]))
    return v


def _lvl(part, which, feel):
    """Resolve a section's (cutoff, reverb, expr) absolute CC targets for a part."""
    cf, rf, expr = SECTION_LEVELS[which]
    v = voice(part, feel)
    return (max(15, min(127, round(v["cutoff"] * cf))),
            max(0, min(127, round(v["reverb"] * rf))), expr)


def clip_cc(part, which, channel, n_bars, bar_steps, feel):
    """CC motion for a single section clip: sit at the section's target with a
    small in-clip shape (a rise through a lift/peak, a fade across the end)."""
    cutoff, reverb, expr = _lvl(part, which, feel)
    end = n_bars * bar_steps * STEP
    ev = [CCEvent(0, CC_RESONANCE, voice(part, feel)["reso"], channel),
          CCEvent(0, CC_PAN, 64 + voice(part, feel)["pan"], channel),
          CCEvent(0, CC_REVERB_SEND, reverb, channel)]
    if which in ("lift", "peak"):                      # open up across the clip
        ev += cc_ramp(channel, CC_CUTOFF, 0, end, max(15, cutoff - 22), cutoff)
        ev += cc_ramp(channel, CC_EXPRESSION, 0, end, expr - 12, expr)
    elif which == "end":                               # settle / fade
        ev += cc_ramp(channel, CC_CUTOFF, 0, end, cutoff, max(15, cutoff - 18))
        ev += cc_ramp(channel, CC_EXPRESSION, 0, end, expr, expr - 20)
    else:
        ev += [CCEvent(0, CC_CUTOFF, cutoff, channel), CCEvent(0, CC_EXPRESSION, expr, channel)]
    return ev


def song_cc(part, arrangement, channel, bar_steps, feel):
    """CC motion across a whole arrangement: ramp cutoff/reverb/expression
    between consecutive sections so the filter opens intro->peak and the
    reverb washes in the break -- the big arc a single clip can't carry."""
    seq = [dict(K.VARIATIONS)[s] for s in arrangement]
    bars = [2 if w == "end" else 4 for w in seq]
    ev = [CCEvent(0, CC_RESONANCE, voice(part, feel)["reso"], channel),
          CCEvent(0, CC_PAN, 64 + voice(part, feel)["pan"], channel)]
    bar_ticks = bar_steps * STEP
    pos = 0
    prev = None
    for which, nb in zip(seq, bars):
        start = pos * bar_ticks
        cur = _lvl(part, which, feel)
        if prev is None:
            prev = cur
        # glide to the new section's targets over the FIRST bar, then hold --
        # so each section takes on its character promptly (the break closes at
        # its downbeat, the peak opens at its downbeat) instead of lagging
        glide = start + min(bar_ticks, nb * bar_ticks)
        for cc, a, b in ((CC_CUTOFF, prev[0], cur[0]),
                         (CC_REVERB_SEND, prev[1], cur[1]),
                         (CC_EXPRESSION, prev[2], cur[2])):
            ev += cc_ramp(channel, cc, start, glide, a, b)
            ev.append(CCEvent((pos + nb) * bar_ticks - 1, cc, b, channel))  # hold to block end
        prev = cur
        pos += nb
    return ev


def setup_card(kit):
    """The per-kit 707 dial-in card: track voices + master bus + how to apply."""
    feel = kit["feel"]
    m = MASTER.get(feel, MASTER["laidback"])
    lines = [f"{kit['name']}  --  {kit['key']}  {kit['bpm']} bpm  feel:{feel}",
             "FILTER / EFFECTS / COMPRESSION dial-in (starting points -- turn them)",
             "", "PER-TRACK  (cutoff/reso are CC74/71; sends are [SEL]+C3 delay / +C4 reverb)"]
    order = ["drums", "bass", "lead", "counter", "chords", "arp"]
    for part in order:
        if not (kit.get(part) or part == "drums"):
            continue
        v = voice(part, feel)
        pan = "C" if v["pan"] == 0 else (f"R{v['pan']}" if v["pan"] > 0 else f"L{-v['pan']}")
        lines.append(f"  {part:<8} cut {v['cutoff']:>3}  reso {v['reso']:>2}  "
                     f"dly {v['delay']:>2}  rev {v['reverb']:>2}  pan {pan:<4}  MFX: {v['mfx']}")
    lines += ["",
              "MASTER BUS  ([SHIFT]+[MULTI] -> Comp / EQ tabs)",
              f"  Total Comp: {m['comp']}",
              f"  Total EQ:   {m['eq']}",
              "",
              "MOTION  (the arrangement's filter/reverb arc rides CC74 cutoff + CC91",
              "  reverb + CC11 expression; intro filtered, opens to peak, washes in the",
              "  break, fades on the end). Two ways onto the 707:",
              "   * live-record it -- usb_feed --fx streams the motion while you record",
              "     the clip (firmware 1.8 captures incoming CC as motion); or",
              "   * dial the section levels by hand on the FILTER knob per column.",
              "  Section cutoff targets (drums shown; each part scales from its base):"]
    dv = voice("bass", feel)["cutoff"]
    for which in ("intro", "main", "lift", "break", "peak", "end"):
        cf, rf, expr = SECTION_LEVELS[which]
        lines.append(f"    {which:<6} cutoff x{cf:.2f}  reverb x{rf:.2f}  level {expr}")
    return "\n".join(lines) + "\n"
