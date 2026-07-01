"""Generative archetypes: fresh, seeded drum/bass/melody clips built from the
same vocabulary as the hand-composed pieces in pieces/*.py, but with the
specific choices (key, tempo, rhythmic density, bassline contour, melodic
motif, section lengths) drawn from a constrained random-number generator
instead of fixed literals.

Each archetype corresponds to one of the three composed pieces' techniques:
    halftime_drone    ~ undertow       (Fever Ray drone + Radiohead bass angularity)
    broken_meter       ~ static_orchard (Kate Bush metric lilt + broken-beat drums)
    four_floor_glitch  ~ glass_repeater (Idioteque pulse + n-against-4 polymeter)

`generate()` picks/derives everything from one seed, renders it, runs a small
quality-control pass, and regenerates (from a derived sub-seed) if the result
looks degenerate -- e.g. an empty or single-note melody.
"""

import inspect
import random

import palette
import humanize as hz
import rhythm
from analysis import shannon_entropy, melodic_intervals, zipf_slope
from arrange import render_piece, section_span, STEP_TICKS
from midiwriter import cc_ramp, CC_EXPRESSION, CC_REVERB_SEND, CC_BRIGHTNESS, PPQ
from rhythm import grid_from_hits
from theory import NOTE_NAMES, note_in_range, scale_degree
from drums import (KICK, SNARE, CLAP, RIM, CHH, OHH, HTOM, MTOM2, LTOM2, SHAKER, choke_hihats,
                    CONGA_HI, CONGA_LO, CABASA, CLAVES, COWBELL, TAMBOURINE)

DRUM_BANK = {
    "kick": (KICK, 106, 122),
    "snare": (SNARE, 100, 118),
    "ghost_snare": (SNARE, 22, 32),  # ghost-note velocity: audible but clearly subordinate (~15-35 range)
    "clap": (CLAP, 92, 114),
    "rim": (RIM, 62, 86),
    "chh": (CHH, 58, 86),
    "ohh": (OHH, 68, 92),
    "shaker": (SHAKER, 46, 66),
    "htom": (HTOM, 86, 106),
    "mtom": (MTOM2, 86, 106),
    "ltom": (LTOM2, 86, 106),
}

# A tribal/hand-percussion bank for the fever_ray archetype: claves, congas,
# cabasa, cowbell instead of a rock kit, plus low velocities everywhere for
# the sparse, meticulous, "tone over rhythm" feel of the first album.
FEVER_DRUMS = {
    "kick": (KICK, 98, 116),
    "clap": (CLAP, 82, 104),
    "rim": (RIM, 58, 82),
    "claves": (CLAVES, 64, 88),
    "shaker": (SHAKER, 38, 58),
    "cabasa": (CABASA, 42, 62),
    "conga_hi": (CONGA_HI, 76, 98),
    "conga_lo": (CONGA_LO, 80, 102),
    "ltom": (LTOM2, 82, 104),
    "mtom": (MTOM2, 82, 104),
    "cowbell": (COWBELL, 66, 90),
    "tamb": (TAMBOURINE, 50, 70),
}

_ADJ = ["hollow", "glass", "static", "pale", "slow", "far", "dry", "cold", "low", "loose", "bent"]
_NOUN = ["orbit", "current", "harbor", "antenna", "tide", "engine", "hush", "fracture", "weather", "signal", "wire"]


def _title(rng, tag):
    return f"{rng.choice(_ADJ)}_{rng.choice(_NOUN)}_{tag}"


def _clip_to_bar(notes, steps):
    """Drop/shorten (start, dur, note, vel) tuples so none run past the bar."""
    out = []
    for start, dur, note_num, vel in notes:
        if start >= steps:
            continue
        out.append((start, min(dur, steps - start), note_num, vel))
    return out


def _default_produce(rng, bpm, bass_sd_ms=8, bass_vel=6, mel_sd_ms=12, mel_vel=8,
                      swell_section=None, release_section=None, swing_pct=None, reverb_swell=False):
    """A reusable production hook: bass/melody timing gets 1/f-correlated deviation
    (see humanize.py -- not independent jitter, per the groove-perception research)
    plus independent velocity variation; optional practitioner-style hat swing
    (Roger Linn/MPC percentage); an expression (CC11) swell/release keyed to named
    sections, optionally paired with a CC91 reverb-send swell for a gated-reverb-style
    build. Seeds are drawn once here (not inside the closure) so the result is still
    reproducible."""
    bass_seed = rng.randint(0, 1_000_000)
    mel_seed = rng.randint(0, 1_000_000)
    bass_vel_seed = rng.randint(0, 1_000_000)
    mel_vel_seed = rng.randint(0, 1_000_000)

    def produce(result, bass_channel, melody_channel):
        bass = hz.pink_jitter(result["bass"], bpm, PPQ, sd_ms=bass_sd_ms, seed=bass_seed)
        bass = hz.jitter(bass, vel_amount=bass_vel, seed=bass_vel_seed)
        melody = hz.pink_jitter(result["melody"], bpm, PPQ, sd_ms=mel_sd_ms, seed=mel_seed)
        melody = hz.jitter(melody, vel_amount=mel_vel, seed=mel_vel_seed)
        drums = result["drums"]
        if swing_pct:
            hats = [e for e in drums if e.note == CHH]
            other = [e for e in drums if e.note != CHH]
            drums = other + hz.swing(hats, STEP_TICKS, swing_pct=swing_pct, eighth_ticks=STEP_TICKS * 2)

        cc = {"drums": [], "bass": [], "melody": []}
        bounds = result["section_bounds"]
        if swell_section:
            s, e = section_span(bounds, swell_section)
            cc["bass"] += cc_ramp(bass_channel, CC_EXPRESSION, s, e, 90, 126)
            cc["melody"] += cc_ramp(melody_channel, CC_EXPRESSION, s, e, 90, 126)
            if reverb_swell:
                cc["bass"] += cc_ramp(bass_channel, CC_REVERB_SEND, s, e, 30, 90)
                cc["melody"] += cc_ramp(melody_channel, CC_REVERB_SEND, s, e, 30, 90)
        if release_section:
            s, e = section_span(bounds, release_section)
            cc["bass"] += cc_ramp(bass_channel, CC_EXPRESSION, s, e, 126, 88)
            cc["melody"] += cc_ramp(melody_channel, CC_EXPRESSION, s, e, 126, 88)
            if reverb_swell:
                cc["bass"] += cc_ramp(bass_channel, CC_REVERB_SEND, s, e, 90, 40)
                cc["melody"] += cc_ramp(melody_channel, CC_REVERB_SEND, s, e, 90, 40)
        return {"drums": drums, "bass": bass, "melody": melody, "cc": cc}

    return produce


# ---------------------------------------------------------------- archetypes

def halftime_drone(rng, root=None, scale=None, bpm=None):
    root_name = root or rng.choice(NOTE_NAMES)
    scale = scale or rng.choice(["aeolian", "dorian"])
    bpm = bpm or rng.randint(76, 92)
    bass_root = note_in_range(root_name, 28, 55)
    mel_root = note_in_range(root_name, 60, 76)

    # occasionally reach for a documented named rhythm (Toussaint 2005) instead of
    # a random Euclidean roll -- tresillo/bossa both tile cleanly onto a 16-step bar
    if rng.random() < 0.3:
        base_kick = rhythm.euclidean_preset_tiled(rng.choice(["tresillo", "bossa"]), 16, rotate=rng.choice([0, 0, 8]))
    else:
        base_kick = palette.kick_pattern(rng, 16, pulse_choices=(3, 3, 4))
    fill_kick = palette.kick_pattern(rng, 16, pulse_choices=(4, 4, 5), downbeat_bias=0.8)
    hats = palette.hats_pattern(rng, 16, density="med")
    busy_hats = palette.hats_pattern(rng, 16, density="busy")
    snare_pos = 8
    ghost_pos = rng.choice([11, 13, 14])
    bass = palette.bass_phrase(rng, bass_root, scale, 16, register=(24, 55))
    call_motif = palette.motif_scored(rng, rng.choice([3, 4]), mel_root, scale)
    pickup = rng.choice([1, 2, 3])
    strong_steps = {0, 8}

    def drum_bar(fill=False, ghost=False, busy=False):
        out = {
            "kick": fill_kick if fill else base_kick,
            "snare": grid_from_hits(16, {snare_pos}, accents={snare_pos}),
            "chh": busy_hats if busy else hats,
            "shaker": grid_from_hits(16, set(range(16)), accents={0, 4, 8, 12}),
        }
        if ghost:
            out["ghost_snare"] = grid_from_hits(16, {ghost_pos})
        return out

    def sparse_bar():
        return {"kick": grid_from_hits(16, {0, 10}), "rim": grid_from_hits(16, {10}),
                "shaker": grid_from_hits(16, {0, 4, 8, 12}, accents={0})}

    sections = []
    sections.append({"name": "intro", "time_sig": (4, 4), "bpm": bpm, "bars": [
        {"drums": sparse_bar(), "bass": [(0, 16, bass_root, 82)], "melody": []}
        for _ in range(rng.randint(2, 4))
    ]})

    n_verse = rng.choice([6, 8])
    verse_bars = []
    for i in range(n_verse):
        is_answer = i % 2 == 1
        ghost = not is_answer
        drums = drum_bar(fill=(is_answer and i == n_verse - 1), ghost=ghost)
        if is_answer:
            melody = _clip_to_bar(palette.render_motif(rng, call_motif, mel_root, scale, pickup,
                                                        register=(58, 80), vel_base=90), 16)
            melody = palette.resolve_consonance(bass, melody, bass_root, scale, strong_steps)
        else:
            melody = []
        verse_bars.append({"drums": drums, "bass": bass, "melody": melody})
    sections.append({"name": "verse", "time_sig": (4, 4), "bpm": bpm, "bars": verse_bars})

    n_build = rng.randint(3, 5)
    build_bars = []
    shift = 0
    inverted_motif = palette.motif_invert(call_motif)
    for i in range(n_build):
        shift += rng.choice([1, 1, 2])
        drums = drum_bar(busy=True)
        bass_t = bass if i < n_build // 2 else [(s, d, n + 12, v) for s, d, n, v in bass]
        # alternate the climbing sequence with its inversion for varied repetition, not a loop
        source_motif = inverted_motif if i % 2 == 1 else call_motif
        melody = _clip_to_bar(palette.render_motif(rng, source_motif, mel_root, scale, 0, degree_shift=shift,
                                                    register=(60, 84), vel_base=94 + i), 16)
        melody = palette.resolve_consonance(bass_t, melody, bass_root, scale, strong_steps)
        build_bars.append({"drums": drums, "bass": bass_t, "melody": melody})
    sections.append({"name": "build", "time_sig": (4, 4), "bpm": bpm, "bars": build_bars})

    n_outro = rng.randint(3, 4)
    outro_bars = []
    for i in range(n_outro):
        if i == n_outro - 2:
            melody = [(0, 8, mel_root, 76)]
        elif i == n_outro - 1:
            melody = [(0, 16, mel_root, 68)]
        else:
            melody = []
        outro_bars.append({"drums": sparse_bar(), "bass": [(0, 16, bass_root, 78)], "melody": melody})
    sections.append({"name": "outro", "time_sig": (4, 4), "bpm": bpm, "bars": outro_bars})

    produce = _default_produce(rng, bpm, bass_sd_ms=8, bass_vel=6, mel_sd_ms=13, mel_vel=8,
                                swell_section="build", release_section="outro")

    return {"title": _title(rng, "drone"), "bpm": bpm, "root": root_name, "scale": scale,
            "sections": sections, "drum_notes": DRUM_BANK, "produce": produce}


def broken_meter(rng, root=None, scale=None, bpm=None):
    root_name = root or rng.choice(NOTE_NAMES)
    scale = scale or rng.choice(["dorian", "aeolian"])
    bpm = bpm or rng.randint(92, 108)
    bass_root = note_in_range(root_name, 30, 52)
    mel_root = note_in_range(root_name, 60, 78)

    kick_a = palette.kick_pattern(rng, 16, pulse_choices=(3, 3, 4))
    kick_b = palette.kick_pattern(rng, 14, pulse_choices=(2, 2, 3))
    hats_a = palette.hats_pattern(rng, 16, density="med")
    hats_b = grid_from_hits(14, set(range(0, 14, 2)), accents={0})
    snare_a_pos = rng.choice([8, 9])
    clap_b_pos = rng.choice([10, 12])

    bass_a = [(0, 16, bass_root, 84)]
    bass_b = palette.bass_phrase(rng, bass_root, scale, 14, register=(26, 55))
    cry = palette.motif_scored(rng, rng.choice([2, 3]), mel_root, scale)
    cry_notes = _clip_to_bar(
        palette.render_motif(rng, cry, mel_root, scale, rng.choice([1, 2]), register=(60, 82), vel_base=92), 14)
    cry_notes = palette.resolve_consonance(bass_b, cry_notes, bass_root, scale, {0, 8})
    answer_note = [(0, 4, mel_root, 86)]

    def bar_a(broken=False, busy=False):
        return {
            "kick": kick_a if not broken else palette.kick_pattern(rng, 16, pulse_choices=(4, 5)),
            "snare": grid_from_hits(16, {snare_a_pos}, accents={snare_a_pos}),
            "chh": hats_a if not busy else palette.hats_pattern(rng, 16, density="busy"),
            "shaker": grid_from_hits(16, set(range(16))),
        }

    def bar_b(fill=False):
        return {
            "kick": kick_b,
            "clap": grid_from_hits(14, {clap_b_pos}, accents={clap_b_pos}),
            "chh": hats_b,
            "htom": grid_from_hits(14, {10}) if fill else grid_from_hits(14, set()),
            "shaker": grid_from_hits(14, {0, 4, 8, 12}),
        }

    def sparse_a():
        return {"kick": grid_from_hits(16, {0, 10}), "rim": grid_from_hits(16, {8}),
                "shaker": grid_from_hits(16, {0, 8})}

    def sparse_b():
        return {"kick": grid_from_hits(14, {0}), "rim": grid_from_hits(14, {8}),
                "shaker": grid_from_hits(14, {0})}

    def pair(i, energy):
        broken = energy == "build" and i % 2 == 1
        busy = energy == "build"
        fillb = energy == "build" and i % 2 == 0
        octshift = 12 if energy == "build" else 0
        a = {"time_sig": (4, 4), "bpm": bpm, "drums": bar_a(broken=broken, busy=busy),
             "bass": [(s, d, n + octshift, v) for s, d, n, v in bass_a],
             "melody": answer_note if i > 0 else []}
        b = {"time_sig": (7, 8), "bpm": bpm, "drums": bar_b(fill=fillb),
             "bass": [(s, d, n + octshift, v) for s, d, n, v in bass_b],
             "melody": cry_notes}
        return a, b

    def sparse_pair():
        return ({"time_sig": (4, 4), "bpm": bpm, "drums": sparse_a(), "bass": bass_a, "melody": []},
                {"time_sig": (7, 8), "bpm": bpm, "drums": sparse_b(), "bass": bass_b[:1], "melody": []})

    def flatten(pairs, name):
        out = []
        for bar_pair in pairs:
            for bar in bar_pair:
                ts = bar.pop("time_sig")
                bp = bar.pop("bpm")
                out.append({"name": name, "time_sig": ts, "bpm": bp, "bars": [bar]})
        return out

    sections = []
    sections += flatten([sparse_pair() for _ in range(rng.randint(2, 3))], "intro")
    sections += flatten([pair(i, "verse") for i in range(rng.randint(3, 5))], "verse")
    sections += flatten([pair(i, "build") for i in range(rng.randint(2, 3))], "build")
    sections += flatten([sparse_pair() for _ in range(2)], "outro")

    produce = _default_produce(rng, bpm, bass_sd_ms=15, bass_vel=8, mel_sd_ms=18, mel_vel=10,
                                swell_section="build", swing_pct=hz.sixteenth_swing_pct(bpm), reverb_swell=True)

    return {"title": _title(rng, "orchard"), "bpm": bpm, "root": root_name, "scale": scale,
            "sections": sections, "drum_notes": DRUM_BANK, "produce": produce}


def four_floor_glitch(rng, root=None, scale=None, bpm=None):
    root_name = root or rng.choice(NOTE_NAMES)
    scale = scale or rng.choice(["phrygian", "aeolian"])
    bpm = bpm or rng.randint(114, 128)
    bass_root = note_in_range(root_name, 24, 42)
    mel_root = note_in_range(root_name, 62, 74)

    bass = palette.bass_phrase(rng, bass_root, scale, 16, register=(24, 46), vel_range=(88, 106))
    drone = [(0, 16, bass_root, 80)]
    n_verse1 = rng.randint(6, 8)
    n_break = rng.randint(2, 4)
    n_verse2 = rng.randint(3, 5)
    phase1 = palette.phase_melody(rng, mel_root, scale, n_verse1, bpm=bpm)
    # verse2 occasionally swaps in the Glass/Reich-style additive process (growing
    # cell) instead of the fixed n-against-4 phase cell, for a second flavour of
    # "melody against the bar" within the same archetype
    phase2 = (palette.additive_phase_melody(rng, mel_root, scale, n_verse2) if rng.random() < 0.4
              else palette.phase_melody(rng, mel_root, scale, n_verse2, bpm=bpm))

    def pulse_bar(glitch=False):
        hats = palette.hats_pattern(rng, 16, density="busy", glitch_prob=1.0 if glitch else 0.0)
        out = {"kick": grid_from_hits(16, {0, 4, 8, 12}, accents={0, 8}),
               "clap": grid_from_hits(16, {8}, accents={8}), "chh": hats}
        if glitch:
            out["ohh"] = grid_from_hits(16, {15})
        return out

    def break_bar():
        return {"kick": grid_from_hits(16, {0}, accents={0}), "chh": grid_from_hits(16, {0, 4, 8, 12})}

    sections = [
        {"name": "intro", "time_sig": (4, 4), "bpm": bpm, "bars": [
            {"drums": {"kick": grid_from_hits(16, {0, 8}, accents={0})}, "bass": drone, "melody": []}
            for _ in range(rng.randint(2, 3))
        ]},
        {"name": "verse", "time_sig": (4, 4), "bpm": bpm, "bars": [
            {"drums": pulse_bar(glitch=(i % 2 == 1)), "bass": bass, "melody": phase1[i]}
            for i in range(n_verse1)
        ]},
        {"name": "break", "time_sig": (4, 4), "bpm": bpm, "bars": [
            {"drums": break_bar(), "bass": drone, "melody": []} for _ in range(n_break)
        ]},
        {"name": "verse2", "time_sig": (4, 4), "bpm": bpm, "bars": [
            {"drums": pulse_bar(glitch=(i % 2 == 0)), "bass": bass, "melody": phase2[i]}
            for i in range(n_verse2)
        ]},
        {"name": "outro", "time_sig": (4, 4), "bpm": bpm, "bars": [
            {"drums": {"kick": grid_from_hits(16, {0, 8} if i == 0 else {0})},
             "bass": drone if i == 0 else [(0, 16, bass_root, 70)], "melody": []}
            for i in range(2)
        ]},
    ]

    def produce(result, bass_channel, melody_channel):
        bounds = result["section_bounds"]
        v1s, v1e = section_span(bounds, "verse")
        bs, be = section_span(bounds, "break")
        v2s, v2e = section_span(bounds, "verse2")

        def sweep(channel):
            lo, mid, hi = rng.randint(32, 48), rng.randint(96, 118), rng.randint(40, 56)
            return (cc_ramp(channel, CC_BRIGHTNESS, v1s, v1e, lo, mid)
                    + cc_ramp(channel, CC_BRIGHTNESS, bs, be, mid, hi)
                    + cc_ramp(channel, CC_BRIGHTNESS, v2s, v2e, hi, rng.randint(108, 124)))

        return {"drums": result["drums"], "bass": result["bass"], "melody": result["melody"],
                "cc": {"drums": [], "bass": sweep(bass_channel), "melody": sweep(melody_channel)}}

    return {"title": _title(rng, "repeater"), "bpm": bpm, "root": root_name, "scale": scale,
            "sections": sections, "drum_notes": DRUM_BANK, "produce": produce}


def gated_drama(rng, root=None, scale=None, bpm=None):
    """A deliberately *narrow* blend, not a 3-way average: Kate Bush's tom-heavy,
    no-hats/no-cymbals gated-reverb groove plus Fever Ray's static drone-bass
    harmony -- Radiohead's glitch hats are left out on purpose (they'd fight
    the toms-instead-of-cymbals aesthetic), and Bush's dramatic wide vocal
    leaps are reserved for one structural bridge (in 3/2, with a relative-major
    lift) rather than blended through the whole clip, so the drama reads as an
    event instead of a constant clash with the verse's narrow, chant-like line.
    """
    root_name = root or rng.choice(NOTE_NAMES)
    scale = scale or "aeolian"
    bpm = bpm or rng.randint(107, 140)
    bass_root = note_in_range(root_name, 28, 48)
    mel_root = note_in_range(root_name, 62, 78)
    fifth = palette.clamp_register(scale_degree(bass_root, scale, 4), bass_root - 6, bass_root + 6)

    def groove_bar(steps=16, delay_hit=True):
        kick_pos = {0, steps // 2}
        snare_pos = {steps // 4, steps * 3 // 4}
        toms = set(range(2, steps, 4)) - kick_pos - snare_pos
        out = {
            "kick": grid_from_hits(steps, kick_pos, accents=kick_pos),
            "snare": grid_from_hits(steps, snare_pos, accents=snare_pos),
            "htom": grid_from_hits(steps, toms),
        }
        if delay_hit:
            out["rim"] = grid_from_hits(steps, {max(0, steps // 2 - 1)})
        return out

    def sparse_bar(steps=16):
        return {"kick": grid_from_hits(steps, {0}), "rim": grid_from_hits(steps, {steps // 2})}

    def bass_pulse(steps, root_pitch, alt_pitch):
        half = steps // 2
        second = alt_pitch if rng.random() < 0.4 else root_pitch
        return [(0, half, root_pitch, rng.randint(78, 92)), (half, steps - half, second, rng.randint(80, 96))]

    chant = palette.motif(rng, rng.choice([2, 3]), leap_prob=0.05, root_pull=0.4, max_leap=2)
    drama = palette.motif(rng, rng.choice([3, 4]), leap_prob=0.45, root_pull=0.05, max_leap=8)
    rel_bass_root, rel_mel_root = bass_root + 3, mel_root + 3  # relative-major lift for the bridge

    def flat(bars, name):
        out = []
        for bar in bars:
            ts, bp = bar.pop("time_sig"), bar.pop("bpm")
            out.append({"name": name, "time_sig": ts, "bpm": bp, "bars": [bar]})
        return out

    sections = []
    sections.append({"name": "intro", "time_sig": (4, 4), "bpm": bpm, "bars": [
        {"drums": sparse_bar(), "bass": [(0, 16, bass_root, 76)], "melody": []}
        for _ in range(rng.randint(2, 3))
    ]})

    n_verse = rng.randint(6, 8)
    verse_bars = []
    for i in range(n_verse):
        extend = (i == n_verse - 2)  # one bar occasionally stretched to 6/4 to extend the phrase
        steps = 24 if extend else 16
        ts = (6, 4) if extend else (4, 4)
        melody = _clip_to_bar(palette.render_motif(rng, chant, mel_root, scale, 2,
                                                    register=(58, 76), vel_base=68), steps) if i % 3 == 2 else []
        bass = bass_pulse(steps, bass_root, fifth)
        melody = palette.resolve_consonance(bass, melody, bass_root, scale, {0, steps // 2})
        verse_bars.append({"time_sig": ts, "bpm": bpm,
                            "drums": groove_bar(steps=steps), "bass": bass, "melody": melody})
    sections += flat(verse_bars, "verse")

    bridge_bars = []
    for i in range(2):
        steps = 24
        bass = bass_pulse(steps, rel_bass_root, palette.clamp_register(
            scale_degree(rel_bass_root, "major", 4), rel_bass_root - 6, rel_bass_root + 6))
        melody = _clip_to_bar(palette.render_motif(rng, drama, rel_mel_root, "major", 0,
                                                    register=(62, 86), vel_base=100 + i * 4), steps)
        melody = palette.resolve_consonance(bass, melody, rel_bass_root, "major", {0, 8, 16})
        bridge_bars.append({"time_sig": (3, 2), "bpm": bpm,
                             "drums": groove_bar(steps=steps, delay_hit=False), "bass": bass, "melody": melody})
    sections += flat(bridge_bars, "bridge")

    n_verse2 = rng.randint(3, 4)
    verse2_bars = []
    for i in range(n_verse2):
        melody = _clip_to_bar(palette.render_motif(rng, chant, mel_root, scale, 1,
                                                     register=(58, 76), vel_base=72), 16) if i % 2 == 1 else []
        bass = bass_pulse(16, bass_root, fifth)
        melody = palette.resolve_consonance(bass, melody, bass_root, scale, {0, 8})
        verse2_bars.append({"drums": groove_bar(), "bass": bass, "melody": melody})
    sections.append({"name": "verse2", "time_sig": (4, 4), "bpm": bpm, "bars": verse2_bars})

    sections.append({"name": "outro", "time_sig": (4, 4), "bpm": bpm, "bars": [
        {"drums": sparse_bar(), "bass": [(0, 16, bass_root, 68)], "melody": []}
        for _ in range(2)
    ]})

    bass_seed, bass_vel_seed = rng.randint(0, 1_000_000), rng.randint(0, 1_000_000)
    mel_seed, mel_vel_seed = rng.randint(0, 1_000_000), rng.randint(0, 1_000_000)

    def produce(result, bass_channel, melody_channel):
        bass = hz.pink_jitter(result["bass"], bpm, PPQ, sd_ms=9, seed=bass_seed)
        bass = hz.jitter(bass, vel_amount=6, seed=bass_vel_seed)
        melody = hz.pink_jitter(result["melody"], bpm, PPQ, sd_ms=12, seed=mel_seed)
        melody = hz.jitter(melody, vel_amount=8, seed=mel_vel_seed)
        bounds = result["section_bounds"]
        bs, be = section_span(bounds, "bridge")
        cc = {"drums": [], "bass": [], "melody": []}
        cc["bass"] += cc_ramp(bass_channel, CC_REVERB_SEND, bs, be, 40, 110)
        cc["melody"] += cc_ramp(melody_channel, CC_REVERB_SEND, bs, be, 40, 110)
        cc["bass"] += cc_ramp(bass_channel, CC_EXPRESSION, bs, be, 95, 127)
        cc["melody"] += cc_ramp(melody_channel, CC_EXPRESSION, bs, be, 95, 127)
        return {"drums": result["drums"], "bass": bass, "melody": melody, "cc": cc}

    return {"title": _title(rng, "drama"), "bpm": bpm, "root": root_name, "scale": scale,
            "sections": sections, "drum_notes": DRUM_BANK, "produce": produce}


def fever_ray(rng, root=None, scale=None, bpm=None, phases=2):
    """Fever Ray, first-album flavour (~'If I Had a Heart', 'When I Grow Up',
    'Keep the Streets Empty for Me'): a very slow half-time feel, a deep pulsing
    pedal-tone sub-bass that barely moves, sparse-but-detailed *tribal/hand*
    percussion (claves, congas, shaker, clap -- no rock backbeat, no cymbals),
    a dark minor/phrygian mode, and a low, narrow, chant-like melody that
    repeats obsessively rather than developing. 'Tone over rhythm', heavy
    reverb, lots of space.

    `phases` (2 or 3) sets how many growth stages the arrangement moves through
    before its peak: each phase keeps the same chant DNA but varies it (transpose
    up a scale step, then invert the contour) and thickens the tribal percussion,
    so a long clip grows in slow, hypnotic waves rather than looping one groove.
    """
    phases = max(1, min(3, phases))
    root_name = root or rng.choice(NOTE_NAMES)
    scale = scale or rng.choice(["aeolian", "aeolian", "phrygian"])  # mostly natural minor, sometimes darker
    bpm = bpm or rng.randint(68, 92)
    bass_root = note_in_range(root_name, 26, 40)     # deep sub
    mel_root = note_in_range(root_name, 55, 67)      # low, pitched-down chant register
    low7 = scale_degree(bass_root, scale, 6, octave_shift=-1)  # the b7 a step below the root

    # A short chant cell -- very narrow, root-heavy -- reused obsessively.
    chant = palette.motif_scored(rng, rng.choice([2, 3]), mel_root, scale,
                                  attempts=6, leap_prob=0.05, root_pull=0.35, max_leap=2)
    chant_pickup = rng.choice([0, 2, 4])

    def drone_pulse(octave=0, sparse=False):
        """The throbbing pedal-tone bass: root on a tresillo-ish pulse, dipping to
        the b7 below now and then; almost no harmonic movement."""
        positions = [0, 6, 10] if sparse else [0, 3, 6, 8, 11, 14]
        notes = []
        for i, p in enumerate(positions):
            end = positions[i + 1] if i + 1 < len(positions) else 16
            pitch = (low7 if (p in (11, 10) and rng.random() < 0.3) else bass_root) + 12 * octave
            notes.append((p, end - p, pitch, rng.randint(86, 102)))
        return notes

    def perc_bar(density=0):
        """Tribal half-time groove whose layers accrue with `density` (0 sparse ->
        3 full peak): deep kick + offbeat claves + backbeat clap first, then hand
        drums + cabasa, then cowbell/toms/tambourine."""
        if density < 0:  # intro/outro texture: just shaker + a clave
            return {"shaker": grid_from_hits(16, set(range(0, 16, 2)), accents={0}),
                    "claves": grid_from_hits(16, {0, 10})}
        out = {
            "kick": grid_from_hits(16, {0, 6, 10} if density >= 3 else {0, 10}, accents={0}),
            "clap": grid_from_hits(16, {8}, accents={8}),
            "claves": grid_from_hits(16, {3, 6, 11, 14}),
            "shaker": grid_from_hits(16, set(range(16)), accents={0, 8}),
        }
        if density >= 1:
            out["conga_lo"] = grid_from_hits(16, {4, 12})
            out["conga_hi"] = grid_from_hits(16, {7, 15})
            out["cabasa"] = grid_from_hits(16, {2, 6, 10, 14})
        if density >= 2:
            out["cowbell"] = grid_from_hits(16, {0, 8})
            out["ltom"] = grid_from_hits(16, {2, 10})
        if density >= 3:
            out["conga_hi"] = grid_from_hits(16, {7, 13, 15})
            out["tamb"] = grid_from_hits(16, {12})
            out["shaker"] = grid_from_hits(16, set(range(16)), accents={0, 4, 8, 12})
        return out

    def phase_material(p):
        """The chant variation + percussion density + register for growth stage `p`.
        Same chant DNA throughout -- transposed up a step in phase 1, contour
        inverted in phase 2 -- so it reads as one idea evolving, not new phrases."""
        if p == 0:
            return chant, 0, 0, (53, 69)          # base chant, sparse, low
        if p == 1:
            return chant, 1, 1, (55, 71)          # up a scale step, mid density
        return palette.motif_invert(chant), 0, 2, (55, 72)  # inverted contour, fuller

    sections = []
    sections.append({"name": "intro", "time_sig": (4, 4), "bpm": bpm, "bars": [
        {"drums": perc_bar(-1), "bass": drone_pulse(sparse=True), "melody": []}
        for _ in range(rng.randint(3, 4))
    ]})

    verse_len = rng.choice([8, 10])
    for p in range(phases):
        motif_p, dshift, density, reg = phase_material(p)
        vbase = 72 + p * 6
        stage_bars = []
        for i in range(verse_len):
            # obsessive repetition; a resting bar every 4th only in the first phase (it fills in as it grows)
            rest = (i % 4 == 3) and p == 0
            if rest:
                melody = []
            else:
                melody = _clip_to_bar(palette.render_motif(rng, motif_p, mel_root, scale, chant_pickup,
                                                            degree_shift=dshift, register=reg,
                                                            vel_base=vbase, vel_spread=6), 16)
                melody = palette.resolve_consonance(drone_pulse(), melody, bass_root, scale, {0, 8})
            stage_bars.append({"drums": perc_bar(density), "bass": drone_pulse(), "melody": melody})
        sections.append({"name": f"phase{p + 1}", "time_sig": (4, 4), "bpm": bpm, "bars": stage_bars})

    # peak: full percussion, bass lifts an octave halfway, chant at its highest/loudest
    n_build = rng.randint(6, 8)
    peak_motif, peak_shift, _, _ = phase_material(phases - 1)
    build_bars = []
    for i in range(n_build):
        octave = 1 if i >= n_build // 2 else 0
        melody = _clip_to_bar(palette.render_motif(rng, peak_motif, mel_root, scale, chant_pickup,
                                                    degree_shift=peak_shift, register=(55, 74),
                                                    vel_base=90 + min(i, 6), vel_spread=6), 16)
        melody = palette.resolve_consonance(drone_pulse(octave), melody, bass_root, scale, {0, 8})
        build_bars.append({"drums": perc_bar(3), "bass": drone_pulse(octave), "melody": melody})
    sections.append({"name": "build", "time_sig": (4, 4), "bpm": bpm, "bars": build_bars})

    outro_bars = []
    for i in range(rng.randint(3, 4)):
        melody = [(0, 16, mel_root, 66)] if i == 0 else []
        outro_bars.append({"drums": perc_bar(-1), "bass": drone_pulse(sparse=True), "melody": melody})
    sections.append({"name": "outro", "time_sig": (4, 4), "bpm": bpm, "bars": outro_bars})

    # Heavy reverb send throughout (the cavernous first-album space), swelling into the build;
    # expression lifts through the build and releases in the outro. No swing -- it's straight and hypnotic.
    reverb_base = rng.randint(55, 75)
    bass_seed, bass_vel_seed = rng.randint(0, 1_000_000), rng.randint(0, 1_000_000)
    mel_seed, mel_vel_seed = rng.randint(0, 1_000_000), rng.randint(0, 1_000_000)

    def produce(result, bass_channel, melody_channel):
        bass = hz.pink_jitter(result["bass"], bpm, PPQ, sd_ms=10, seed=bass_seed)
        bass = hz.jitter(bass, vel_amount=6, seed=bass_vel_seed)
        melody = hz.pink_jitter(result["melody"], bpm, PPQ, sd_ms=14, seed=mel_seed)
        melody = hz.jitter(melody, vel_amount=6, seed=mel_vel_seed)
        bounds = result["section_bounds"]
        bs, be = section_span(bounds, "build")
        os_, oe = section_span(bounds, "outro")
        cc = {"drums": [], "bass": [], "melody": []}
        for ch in (bass_channel, melody_channel):
            key = "bass" if ch == bass_channel else "melody"
            cc[key] += cc_ramp(ch, CC_REVERB_SEND, 0, bs, reverb_base, reverb_base)
            cc[key] += cc_ramp(ch, CC_REVERB_SEND, bs, be, reverb_base, 120)
            cc[key] += cc_ramp(ch, CC_EXPRESSION, bs, be, 92, 126)
            cc[key] += cc_ramp(ch, CC_EXPRESSION, os_, oe, 126, 80)
        return {"drums": result["drums"], "bass": bass, "melody": melody, "cc": cc}

    return {"title": _title(rng, "feverray"), "bpm": bpm, "root": root_name, "scale": scale,
            "sections": sections, "drum_notes": FEVER_DRUMS, "produce": produce}


RADIOHEAD_DRUMS = {
    "kick": (KICK, 104, 120),
    "snare": (SNARE, 96, 116),
    "clap": (CLAP, 90, 112),
    "rim": (RIM, 64, 88),
    "chh": (CHH, 54, 84),
    "ohh": (OHH, 66, 90),
    "shaker": (SHAKER, 44, 64),
    "ltom": (LTOM2, 84, 104),
    "mtom": (MTOM2, 84, 104),
}


def radiohead_kida(rng, root=None, scale=None, bpm=None, mode=None):
    """Kid A / Amnesiac-era Radiohead. Picks one of four modes, each a documented
    device from that period:
      - 'odd5'      -> 5/4 (Morning Bell / 15 Step): programmed beat + handclaps,
                       economical bass stressing chord tones to ground the metre.
      - 'pedal10'   -> 10/4 (Everything In Its Right Place): a one-note pedal
                       ostinato under a repeating modal phrase, sparse glitch beat.
      - 'idioteque' -> 4/4 with a 5-step melodic cell over the 16-step bar
                       (5-against-4 grouping dissonance), stuttering glitch drums.
      - 'pyramid'   -> Pyramid Song's 3+3+4+3+3 grouping (a 16/8 bar), swung and
                       sparse, bass articulating the five uneven groups.
    Modal (phrygian/dorian/aeolian), pedal-point, non-functional harmony
    throughout, and a *terminally climactic form* (Osborn): rather than
    recapitulating the opening, the arrangement ends on NEW climactic material
    (motif_b), reached by developing the opening motif (retrograde / fragment /
    augmentation) through the middle.
    """
    root_name = root or rng.choice(NOTE_NAMES)
    scale = scale or rng.choice(["phrygian", "dorian", "aeolian"])
    mode = mode or rng.choice(["odd5", "pedal10", "idioteque", "pyramid"])
    bass_root = note_in_range(root_name, 33, 48)
    mel_root = note_in_range(root_name, 60, 74)

    motif_a = palette.motif_scored(rng, rng.choice([3, 4]), mel_root, scale,
                                    attempts=6, leap_prob=0.18, root_pull=0.2)
    motif_b = palette.motif_scored(rng, rng.choice([3, 4, 5]), mel_root, scale,
                                    attempts=6, leap_prob=0.32, root_pull=0.08)  # new, wider climax idea

    def glitch(steps, drop_prob):
        return palette.hats_pattern(rng, steps, density="busy", glitch_prob=drop_prob)

    force_cell = None
    if mode == "odd5":
        ts, steps = (5, 4), 20
        bpm = bpm or rng.randint(88, 104)

        def d_main(peak=False):
            out = {"kick": grid_from_hits(steps, {0, 6, 12} | ({16} if peak else set()), accents={0}),
                   "clap": grid_from_hits(steps, {8, 16}, accents={8}),
                   "chh": glitch(steps, 0.3 if peak else 0.7),
                   "shaker": grid_from_hits(steps, set(range(0, steps, 2)))}
            if peak:
                out["ltom"] = grid_from_hits(steps, {4, 14})
            return out

        def b_main(peak=False):
            oc = 12 if peak else 0
            return [(0, 6, bass_root + oc, 100), (6, 2, scale_degree(bass_root, scale, 2) + oc, 88),
                    (8, 4, scale_degree(bass_root, scale, 4) + oc, 94), (12, 8, bass_root + oc, 96)]
    elif mode == "pedal10":
        ts, steps = (10, 4), 40
        bpm = bpm or rng.randint(118, 128)

        def d_main(peak=False):
            out = {"kick": grid_from_hits(steps, {0, 20} | ({10, 30} if peak else set()), accents={0}),
                   "rim": grid_from_hits(steps, {10, 30}),
                   "chh": glitch(steps, 0.6),
                   "shaker": grid_from_hits(steps, set(range(0, steps, 2)), accents={0, 20})}
            if peak:
                out["clap"] = grid_from_hits(steps, {8, 28}, accents={8})
            return out

        def b_main(peak=False):
            oc = 12 if peak else 0
            # pedal ostinato: dominated by the root, with an occasional b7 dip and an
            # octave drop for subtle movement (EIIRP-ish, and enough to clear the
            # "near-static" QC guard without losing the pedal character)
            b7 = scale_degree(bass_root, scale, 6, octave_shift=-1)
            notes = []
            for j, p in enumerate(range(0, steps, 4)):
                pitch = b7 if j == 5 else (bass_root - 12 if j == 8 else bass_root)
                notes.append((p, 4, pitch + oc, rng.randint(88, 100)))
            return notes
    elif mode == "idioteque":
        ts, steps = (4, 4), 16
        bpm = bpm or rng.randint(128, 140)
        force_cell = 5  # 5-against-4 grouping dissonance

        def d_main(peak=False):
            out = {"kick": grid_from_hits(steps, {0, 7, 10} | ({4} if peak else set()), accents={0}),
                   "clap": grid_from_hits(steps, {4, 12}, accents={4, 12}),
                   "chh": glitch(steps, 0.9),
                   "ohh": grid_from_hits(steps, {15})}
            if peak:
                out["ltom"] = grid_from_hits(steps, {2, 6, 11})
            return out

        def b_main(peak=False):
            oc = 12 if peak else 0
            return [(0, 4, bass_root + oc, 100), (6, 2, scale_degree(bass_root, scale, 4) + oc, 90),
                    (8, 4, bass_root + oc, 98), (12, 4, scale_degree(bass_root, scale, 2) + oc, 92)]
    else:  # pyramid: 3+3+4+3+3 eighth-note groups = a 16/8 bar of 32 sixteenth-steps
        ts, steps = (16, 8), 32
        bpm = bpm or rng.randint(76, 88)
        groups = [0, 6, 12, 20, 26]  # sixteenth-step starts of the five uneven groups

        def d_main(peak=False):
            out = {"kick": grid_from_hits(steps, {0, 20}, accents={0}),
                   "rim": grid_from_hits(steps, set(groups)),
                   "shaker": grid_from_hits(steps, set(range(0, steps, 2)))}
            if peak:
                out["clap"] = grid_from_hits(steps, {12, 26}, accents={12})
                out["ltom"] = grid_from_hits(steps, {6, 26})
            return out

        def b_main(peak=False):
            oc = 12 if peak else 0
            return [(g, (groups[i + 1] if i + 1 < len(groups) else steps) - g,
                     (bass_root if i % 2 == 0 else scale_degree(bass_root, scale, 4)) + oc, rng.randint(88, 100))
                    for i, g in enumerate(groups)]

    def d_intro():
        return {"chh": glitch(steps, 0.5), "shaker": grid_from_hits(steps, set(range(0, steps, 2)), accents={0})}

    def bar(drums, peak=False, melody=None):
        b = b_main(peak=peak)
        mel = palette.resolve_consonance(b, melody or [], bass_root, scale, {0})
        return {"time_sig": ts, "bpm": bpm, "drums": drums, "bass": b, "melody": mel}

    sections = []
    sections.append({"name": "intro", "time_sig": ts, "bpm": bpm, "bars": [
        {"drums": d_intro(), "bass": b_main(), "melody": []} for _ in range(rng.randint(2, 3))]})

    # main: the opening motif as a displaced modal cell (grouping dissonance)
    n_main = rng.choice([4, 6])
    main_mel = palette.phase_melody(rng, mel_root, scale, n_main, bar_steps=steps, cell_len=force_cell, bpm=bpm)
    sections.append({"name": "main", "time_sig": ts, "bpm": bpm,
                     "bars": [bar(d_main(), melody=main_mel[i]) for i in range(n_main)]})

    # develop: the SAME motif put through a development operator (retrograde / fragment / augmentation),
    # displaced and transposed bar to bar -- motivic growth, not a new tune
    n_dev = rng.choice([4, 6])
    dev = rng.choice([palette.motif_retrograde(motif_a),
                      palette.motif_fragment(motif_a, length=max(2, len(motif_a) - 1)),
                      palette.motif_augment(motif_a)])
    dev_bars = []
    for i in range(n_dev):
        mel = _clip_to_bar(palette.render_motif(rng, dev, mel_root, scale, (i * 2) % 6,
                                                degree_shift=i % 3, register=(58, 76), vel_base=82), steps)
        dev_bars.append(bar(d_main(), melody=mel))
    sections.append({"name": "develop", "time_sig": ts, "bpm": bpm, "bars": dev_bars})

    # terminal climax: NEW material (motif_b), highest/loudest, full kit + octave bass -- the piece ends here
    n_clx = rng.choice([4, 6])
    clx_bars = []
    for i in range(n_clx):
        mel = _clip_to_bar(palette.render_motif(rng, motif_b, mel_root, scale, 0, degree_shift=2,
                                                register=(64, 80), vel_base=96 + min(i, 6)), steps)
        clx_bars.append(bar(d_main(peak=True), peak=True, melody=mel))
    sections.append({"name": "climax", "time_sig": ts, "bpm": bpm, "bars": clx_bars})

    # short tail: thin out on the new idea, no return to the opening
    sections.append({"name": "tail", "time_sig": ts, "bpm": bpm, "bars": [
        bar(d_intro(), melody=[(0, min(steps, 16), mel_root + 2, 74)]),
        {"time_sig": ts, "bpm": bpm, "drums": {"shaker": grid_from_hits(steps, {0})}, "bass": b_main(), "melody": []}]})

    bass_seed, bass_vel_seed = rng.randint(0, 1_000_000), rng.randint(0, 1_000_000)
    mel_seed, mel_vel_seed = rng.randint(0, 1_000_000), rng.randint(0, 1_000_000)

    def produce(result, bass_channel, melody_channel):
        # programmed beats stay tight (quantized); only bass/melody get 1/f timing.
        bass = hz.pink_jitter(result["bass"], bpm, PPQ, sd_ms=8, seed=bass_seed)
        bass = hz.jitter(bass, vel_amount=6, seed=bass_vel_seed)
        melody = hz.pink_jitter(result["melody"], bpm, PPQ, sd_ms=10, seed=mel_seed)
        melody = hz.jitter(melody, vel_amount=8, seed=mel_vel_seed)
        bounds = result["section_bounds"]
        ms, _ = section_span(bounds, "main")
        cs, ce = section_span(bounds, "climax")
        cc = {"drums": [], "bass": [], "melody": []}
        for ch, key in ((bass_channel, "bass"), (melody_channel, "melody")):
            # IDM-style filter opening across the whole build into the climax, then expression peak
            cc[key] += cc_ramp(ch, CC_BRIGHTNESS, ms, ce, 45, 118)
            cc[key] += cc_ramp(ch, CC_EXPRESSION, ms, cs, 92, 116)
            cc[key] += cc_ramp(ch, CC_EXPRESSION, cs, ce, 116, 127)
        return {"drums": result["drums"], "bass": bass, "melody": melody, "cc": cc}

    return {"title": _title(rng, f"kida_{mode}"), "bpm": bpm, "root": root_name, "scale": scale,
            "sections": sections, "drum_notes": RADIOHEAD_DRUMS, "produce": produce}


def spoken_word(rng, root=None, scale=None, bpm=None, phases=2):
    """A backing *bed* for spoken word, mixing all three inspirations for a
    specific function: hold a hypnotic, spacious groove and leave the midrange
    open for a voice. Fever Ray's deep drone/pedal bass and soft tribal-hand
    percussion; Radiohead's pedal-point modal harmony (no chord changes to pull
    focus); Kate Bush's sustained-atmosphere pad instead of a lead line. The
    'melody' here is NOT a tune -- it's slow sustained pad tones (root / 5th /
    b7 / b3) that change every few bars with lots of rests, so nothing competes
    with the words. Slow-to-mid, dark, low dynamics, heavy reverb.

    `phases` (2-4) sets how many beat-bed + harmony-interlude pairs it moves
    through, and thus length -- each phase is a beat-driven bed (for a stanza)
    followed by a chordal harmony interlude where the drums drop out and the pad
    holds sustained chords (a breath between stanzas). Longer for a longer poem.
    It swells gently rather than climaxing (a bed should support, not steal the
    scene).
    """
    phases = max(1, min(4, phases))
    root_name = root or rng.choice(NOTE_NAMES)
    scale = scale or rng.choice(["aeolian", "dorian", "phrygian"])
    bpm = bpm or rng.randint(68, 92)
    bass_root = note_in_range(root_name, 28, 42)          # deep drone
    pad_root = note_in_range(root_name, 52, 64)           # low-mid pad, under the voice
    b7 = scale_degree(bass_root, scale, 6, octave_shift=-1)
    fifth = scale_degree(bass_root, scale, 4)

    def pedal_bass(octave=0):
        # a drone: root held most of the bar, occasionally a b7 or 5th tail -- no real movement
        if rng.random() < 0.35:
            seq = [(0, 12, bass_root), (12, 4, rng.choice([b7, fifth]))]
        else:
            seq = [(0, 16, bass_root)]
        return [(s, d, p + 12 * octave, rng.randint(80, 92)) for s, d, p in seq]

    def groove(density=0):
        # soft, spacious, half-time-ish; no busy hats (keep sibilance range clear for the voice)
        out = {
            "kick": grid_from_hits(16, {0} if density == 0 else {0, 10}, accents={0}),
            "rim": grid_from_hits(16, {6, 14}),
            "shaker": grid_from_hits(16, set(range(0, 16, 2)), accents={0, 8}),
        }
        if density >= 1:
            out["cabasa"] = grid_from_hits(16, {4, 12})
            out["conga_lo"] = grid_from_hits(16, {8})
        if density >= 2:
            out["clap"] = grid_from_hits(16, {8}, accents={8})
            out["claves"] = grid_from_hits(16, {3, 11})
        return out

    # the bed pad's slow rotation -- single pedal-ish scale tones, changing every couple of bars
    pad_cycle = rng.choice([[0, 6, 4, 2], [0, 4, 0, 6], [0, 2, 6, 4]])

    def pad_note(idx, register, vel):
        deg = pad_cycle[idx % len(pad_cycle)]
        note = palette.clamp_register(scale_degree(pad_root, scale, deg), *register)
        return [(0, 16, note, vel + rng.randint(-4, 4))]

    def scale_chord(deg, register, vel, seventh=False):
        # a diatonic (in-key) chord voiced upward, whole chord octave-shifted so its
        # root sits in `register` -- a sustained whole-bar pad chord
        idxs = [deg, deg + 2, deg + 4] + ([deg + 6] if seventh else [])
        tones = [scale_degree(pad_root, scale, i) for i in idxs]
        lo, hi = register
        while tones[0] < lo:
            tones = [t + 12 for t in tones]
        while tones[0] > hi:
            tones = [t - 12 for t in tones]
        return [(0, 16, t, max(1, min(127, vel + rng.randint(-4, 4)))) for t in tones]

    # tonic-centric modal progression for the harmony interludes (i - VII - VI - i, etc.)
    harmony_prog = rng.choice([[0, 6, 5, 0], [0, 5, 6, 0], [0, 3, 6, 0], [0, 6, 0, 5]])

    sections = []
    sections.append({"name": "intro", "time_sig": (4, 4), "bpm": bpm, "bars": [
        {"drums": {"shaker": grid_from_hits(16, set(range(0, 16, 2)), accents={0})},
         "bass": pedal_bass(), "melody": []} for _ in range(rng.randint(3, 4))]})

    pad_idx = 0
    for p in range(phases):
        # --- beat bed (a stanza): groove + drone + occasional single pad tone ---
        density = min(p, 2)
        reg = (50, 63) if p == 0 else (52, 66)
        vel = 56 + p * 4
        bed = []
        for i in range(8):
            if i % 3 == 2:
                melody = []                    # rest bar -- space
            else:
                if i % 2 == 0:
                    pad_idx += 1
                melody = pad_note(pad_idx, reg, vel)
            bed.append({"drums": groove(density), "bass": pedal_bass(), "melody": melody})
        sections.append({"name": f"bed{p + 1}", "time_sig": (4, 4), "bpm": bpm, "bars": bed})

        # --- harmony interlude (a breath): drums drop, pad holds sustained chords ---
        interlude = []
        for i in range(6):
            chord_deg = harmony_prog[(i // 2) % len(harmony_prog)]     # change chord every 2 bars
            chord = scale_chord(chord_deg, (52, 70), 60 + p * 3, seventh=(p >= 1))
            drums = {"shaker": grid_from_hits(16, {0})} if i % 2 == 0 else {}   # faint pulse, mostly silent
            interlude.append({"drums": drums, "bass": pedal_bass(), "melody": chord})
        sections.append({"name": f"harmony{p + 1}", "time_sig": (4, 4), "bpm": bpm, "bars": interlude})

    # gentle lift (not a climax): fuller chord + a higher airy tone, then settle
    lift = []
    for i in range(6):
        chord = scale_chord(harmony_prog[i % len(harmony_prog)], (54, 72), 66, seventh=True)
        high = palette.clamp_register(scale_degree(pad_root, scale, pad_cycle[i % len(pad_cycle)] + 7), 67, 84)
        melody = chord + ([(8, 8, high, 56)] if i % 2 == 1 else [])
        lift.append({"drums": groove(2), "bass": pedal_bass(1 if i >= 3 else 0), "melody": melody})
    sections.append({"name": "lift", "time_sig": (4, 4), "bpm": bpm, "bars": lift})

    sections.append({"name": "outro", "time_sig": (4, 4), "bpm": bpm, "bars": [
        {"drums": {"shaker": grid_from_hits(16, {0, 8})}, "bass": pedal_bass(),
         "melody": scale_chord(0, (52, 70), 52) if i == 0 else []} for i in range(rng.randint(3, 4))]})

    reverb_base = rng.randint(70, 90)   # cavernous bed
    bass_seed, mel_seed = rng.randint(0, 1_000_000), rng.randint(0, 1_000_000)

    def produce(result, bass_channel, melody_channel):
        bass = hz.pink_jitter(result["bass"], bpm, PPQ, sd_ms=9, seed=bass_seed)
        melody = hz.pink_jitter(result["melody"], bpm, PPQ, sd_ms=12, seed=mel_seed)
        bounds = result["section_bounds"]
        ls, le = section_span(bounds, "lift")
        cc = {"drums": [], "bass": [], "melody": []}
        for ch, key in ((bass_channel, "bass"), (melody_channel, "melody")):
            cc[key] += cc_ramp(ch, CC_REVERB_SEND, 0, ls, reverb_base, reverb_base)
            cc[key] += cc_ramp(ch, CC_REVERB_SEND, ls, le, reverb_base, 118)
            cc[key] += cc_ramp(ch, CC_EXPRESSION, ls, le, 96, 118)
        return {"drums": result["drums"], "bass": bass, "melody": melody, "cc": cc}

    return {"title": _title(rng, "spokenbed"), "bpm": bpm, "root": root_name, "scale": scale,
            "sections": sections, "drum_notes": FEVER_DRUMS, "produce": produce,
            "melody_program": 89, "bass_program": 38}  # 89 = Pad 2 (warm), for a sustained bed voice


ARCHETYPES = {
    "halftime_drone": halftime_drone,
    "broken_meter": broken_meter,
    "four_floor_glitch": four_floor_glitch,
    "gated_drama": gated_drama,
    "fever_ray": fever_ray,
    "radiohead_kida": radiohead_kida,
    "spoken_word": spoken_word,
}


# ------------------------------------------------------------------- driver

def _qc(result):
    """Heuristic checks that catch a degenerate roll (empty/monotone parts) --
    real problems (bad tick math, out-of-bar notes) already raise in arrange.py."""
    problems = []
    if not result["melody"]:
        problems.append("empty melody")
    if not result["bass"]:
        problems.append("empty bass")
    if not result["drums"]:
        problems.append("empty drums")
    if len(set(e.note for e in result["melody"])) < 2:
        problems.append("melody uses fewer than 2 distinct pitches")
    if len(set(e.note for e in result["bass"])) < 2:
        problems.append("bass uses fewer than 2 distinct pitches")
    for label, events in (("bass", result["bass"]), ("melody", result["melody"])):
        for e in events:
            if not (0 <= e.note <= 127):
                problems.append(f"{label} note {e.note} out of MIDI range")
            if e.dur <= 0:
                problems.append(f"{label} non-positive duration")
        pitches = [e.note for e in sorted(events, key=lambda e: e.start)]
        if len(pitches) >= 4:
            ent = shannon_entropy(melodic_intervals(pitches))
            if ent < 0.15:
                problems.append(f"{label} interval entropy too low ({ent:.2f} bits) -- likely near-static")
    return problems


def generate(seed=None, archetype=None, root=None, scale=None, bpm=None, phases=None, mode=None,
             max_attempts=5):
    """Build, render, and QC one clip. Returns a dict with the rendered result
    plus the metadata (seed/archetype/title/bpm/root/scale) needed to label it.
    `phases`/`mode` are passed through only to archetypes that accept them
    (fever_ray takes `phases`; radiohead_kida takes `mode`)."""
    if seed is None:
        seed = random.SystemRandom().randrange(2 ** 31)

    archetype_name = archetype or random.Random(seed).choice(list(ARCHETYPES))
    if archetype_name not in ARCHETYPES:
        raise KeyError(f"unknown archetype {archetype_name!r}, choices: {list(ARCHETYPES)}")

    fn = ARCHETYPES[archetype_name]
    params = inspect.signature(fn).parameters
    extra = {}
    if phases is not None and "phases" in params:
        extra["phases"] = phases
    if mode is not None and "mode" in params:
        extra["mode"] = mode

    problems = []
    for attempt in range(max_attempts):
        rng = random.Random(seed * 1000 + attempt)
        spec = fn(rng, root=root, scale=scale, bpm=bpm, **extra)
        result = render_piece(spec["sections"], spec["drum_notes"])
        produced = spec["produce"](result, bass_channel=0, melody_channel=1)
        result = {**result, **{k: v for k, v in produced.items() if k in ("drums", "bass", "melody")}}
        result["drums"] = choke_hihats(result["drums"])
        cc = produced.get("cc", {"drums": [], "bass": [], "melody": []})

        problems = _qc(result)
        if not problems:
            all_pitches = [e.note for e in result["bass"]] + [e.note for e in result["melody"]]
            slope, r2 = zipf_slope(all_pitches)
            return {
                "seed": seed, "attempt": attempt, "archetype": archetype_name,
                "title": spec["title"], "bpm": spec["bpm"], "root": spec["root"], "scale": spec["scale"],
                "result": result, "cc": cc, "zipf_slope": slope, "zipf_r2": r2,
                "melody_program": spec.get("melody_program"), "bass_program": spec.get("bass_program"),
            }

    raise RuntimeError(f"seed {seed} ({archetype_name}) failed QC after {max_attempts} attempts: {problems}")
