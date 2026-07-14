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
import tones                                          # noqa: E402
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

# ---- FIXED KNOB SCHEME (same on every track, per the request) -----------
# cutoff / coarse tune / release live on FILTER / MOD / SOUND on ALL tracks;
# only the FX (4th) knob's target varies by part. Coarse Tune has no standard
# CC -- bind the MOD macro to the tone's Coarse Tune internally; it still
# transmits CC81. (verified: Reference Manual + community; see fx card footer)
GLOBAL_KNOBS = [
    ("FILTER", "Cutoff",      "CC80 (or direct CC74)", 90),
    ("MOD",    "Coarse Tune", "CC81 (bind internally)", 64),
    ("FX",     "MFX depth / send (per part)", "CC82", 40),
    ("SOUND",  "Release",     "CC83 (or direct CC72)", 64),
]

# ---- tier 1b: per-part insert-MFX / sends / EQ / 4th-knob, per feel ------
# (from the tuned spec; MFX names are real 707 types -- verify exact on-unit
# wording. delay/reverb are 0-127 send amounts.)
PART_FX = {
    "drums": {
        "pushing":  dict(mfx="Overdrive (Drive 24, Tone 66, Lvl 100) -- glue+edge", delay=8, reverb=10,
                         eq="HPF35; +2@70 +2.5@4k +1.5@11k (bright/punchy)", knob="MFX depth"),
        "laidback": dict(mfx="Phonograph (Noise 22, Wow 14, warm) -- vinyl", delay=18, reverb=30,
                         eq="HPF30; +1.5@80 -1@3-4k roll>12k (round)", knob="MFX depth"),
        "ritual":   dict(mfx="Distortion (Drive 42, Tone 40, Lvl 96) -- cavern grit", delay=22, reverb=74,
                         eq="HPF40; +3@55 -2@500 -1.5>8k (dark/deep)", knob="MFX depth")},
    "bass": {
        "pushing":  dict(mfx="Overdrive (Drive 40, Tone 55, Lvl 100) -- acid bite", delay=0, reverb=4,
                         eq="HPF28; +2@100 -2@350 roll>6k", knob="MFX depth (drive)"),
        "laidback": dict(mfx="Warm Saturator (Drive 24, Tone 48) -- warm", delay=6, reverb=12,
                         eq="HPF30; +2.5@80 -1.5@300 roll>5k", knob="MFX depth (drive)"),
        "ritual":   dict(mfx="Tone Fattener / Distortion (Drive 56, Tone 34) -- snarl", delay=8, reverb=28,
                         eq="HPF25; +3@60 -2.5@400 dark>4k", knob="MFX depth (drive)")},
    "lead": {
        "pushing":  dict(mfx="Stereo Delay (1/8dot, Fbk 30, HFdamp 7k, Lvl 40)", delay=20, reverb=14,
                         eq="HPF120; +2.5@3k +1.5@10k (presence)", knob="Delay send"),
        "laidback": dict(mfx="Tape Echo (1/8, Fbk 42, Wow 20, Lvl 46) -- dubby", delay=34, reverb=40,
                         eq="HPF110; +1.5@2k +1@8k -1@500", knob="Delay send"),
        "ritual":   dict(mfx="Reverse Delay (Fbk 55, HFdamp 4k, Lvl 58) -- cavern", delay=40, reverb=84,
                         eq="HPF130; +1@1.5k roll>6k (dark)", knob="Delay send")},
    "counter": {
        "pushing":  dict(mfx="Phaser (Rate 1/8, Depth 60, Reso 40) -- movement", delay=16, reverb=12,
                         eq="HPF160; -1.5@3k +1@8k (yield to lead)", knob="Delay send"),
        "laidback": dict(mfx="JUNO Chorus + slap Stereo Delay (1/16, Fbk 12)", delay=26, reverb=34,
                         eq="HPF150; -1@2.5k +1@9k air", knob="Delay send"),
        "ritual":   dict(mfx="Ring Mod (low) / slow Phaser -- metallic", delay=34, reverb=78,
                         eq="HPF180; -1.5@2-3k roll>7k", knob="Delay send")},
    "chords": {
        "pushing":  dict(mfx="JUNO Chorus (Dep 3, Rate .6Hz) + light OD (Drive 18)", delay=10, reverb=22,
                         eq="HPF180; -1.5@400 +2@10k air", knob="Reverb send"),
        "laidback": dict(mfx="JUNO Chorus (Dep 4, Rate .4Hz) -- lush/wide", delay=20, reverb=54,
                         eq="HPF150; -1@350 +2.5@10k +1@220", knob="Reverb send"),
        "ritual":   dict(mfx="JD Multi / Stereo Chorus deep -> big reverb", delay=24, reverb=96,
                         eq="HPF220; -2@500 -1.5>8k (dark)", knob="Reverb send")},
    "arp": {
        "pushing":  dict(mfx="Stereo Delay (1/16, Fbk 28) + Step Filter/Slicer", delay=22, reverb=12,
                         eq="HPF200; +2@5k +1.5@11k (bite)", knob="Delay send"),
        "laidback": dict(mfx="Tape Echo (1/8, Fbk 34) + light JUNO Chorus", delay=32, reverb=38,
                         eq="HPF180; +1@4k +1@9k", knob="Delay send"),
        "ritual":   dict(mfx="slow Phaser (.4Hz) / Slicer -> long reverb", delay=30, reverb=80,
                         eq="HPF220; +.5@3k roll>6k", knob="Delay send")},
}

# ---- tier 3: master bus (Total Comp / EQ / MFX) per feel -----------------
MASTER = {
    "pushing":  dict(comp="3.5:1, atk 12ms, rel 120ms/Auto, thr -13dB, +3.5 makeup (~3-4dB GR, punch)",
                     eq="low +1.5@60Hz . mid -1.5@400Hz . high +2@10kHz",
                     mfx="Total MFX: light Saturator/Overdrive (Drive 12-15) or Thru"),
    "laidback": dict(comp="2.2:1, atk 28ms, rel 250ms, thr -16dB, +2 makeup (transparent, ~2dB GR)",
                     eq="low +2@80Hz . mid +1@250Hz . high +1@8kHz",
                     mfx="Total MFX: Warm Saturator (Drive 10) or Phonograph (subtle)"),
    "ritual":   dict(comp="4:1, atk 30ms, rel 400ms, thr -14dB, +3 makeup (slow weight, 4-6dB GR)",
                     eq="low +3@50Hz . mid -2@500Hz . high -1.5@8kHz (darken)",
                     mfx="Total MFX: Reverb/Isolator/Lo-Fi, subtle (~15-20% wet)"),
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
    """The per-kit 707 setup card: tones + fixed knobs + tuned insert-FX/sends/
    EQ per track + master bus + motion. One page to dial a kit in."""
    feel = kit["feel"]
    m = MASTER.get(feel, MASTER["laidback"])
    trecipe = tones.recipe(kit)
    order = ["drums", "bass", "lead", "counter", "chords", "arp"]
    L = [f"{kit['name']}  --  {kit['key']}  {kit['bpm']} bpm  feel:{feel}   "
         f"(lane: {tones.KIT_PALETTE[kit['name']]})",
         "=" * 70,
         "TEMPO: the 707 has ONE tempo per project -- set it to "
         f"{kit['bpm']} before playing (clips do NOT carry tempo).",
         "",
         "TONES  (load one per track; TRK/CLP set to CLP lets each kit keep its",
         "  own sound on a shared track -- map these to your factory/pack patches)"]
    for part in order:
        if part in trecipe:
            L.append(f"  {part:<8} {trecipe[part]}")
    L += ["",
          "FIXED KNOBS  (same on every track; [SHIFT]+[KNOB ASSIGN] to bind)"]
    for name, target, cc, val in GLOBAL_KNOBS:
        L.append(f"  {name:<7} -> {target:<28} {cc:<24} start {val}")
    L += ["  (Coarse Tune has no direct CC -- bind MOD to the tone's Coarse Tune;",
          "   the 4th knob's target is per-track, shown below.)",
          "",
          "PER-TRACK INSERT MFX / SENDS / EQ / 4th-knob   (feel: " + feel + ")"]
    for part in order:
        if not (kit.get(part) or part == "drums"):
            continue
        f = PART_FX[part][feel]
        L.append(f"  {part}")
        L.append(f"     MFX : {f['mfx']}")
        L.append(f"     send: delay {f['delay']:>3}   reverb {f['reverb']:>3}     "
                 f"FX-knob -> {f['knob']}")
        L.append(f"     EQ  : {f['eq']}")
    L += ["",
          "MASTER BUS  ([SHIFT]+[MULTI] -> Comp / EQ / MFX tabs)",
          f"  Total Comp: {m['comp']}",
          f"  Total EQ:   {m['eq']}",
          f"  {m['mfx']}",
          "",
          "MOTION  (arrangement filter/reverb arc on CC74 cutoff + CC91 reverb +",
          "  CC11 expression: intro filtered, opens to peak, washes in the break,",
          "  fades on the end). Live-record it with  usb_feed --fx --feel " + feel + ",",
          "  or ride the FILTER knob per column. Section cutoff/reverb targets:"]
    for which in ("intro", "main", "lift", "break", "peak", "end"):
        cf, rf, expr = SECTION_LEVELS[which]
        L.append(f"    {which:<6} cutoff x{cf:.2f}  reverb x{rf:.2f}  level {expr}")
    return "\n".join(L) + "\n"
