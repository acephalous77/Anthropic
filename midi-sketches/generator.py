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

import random

import palette
import humanize as hz
import rhythm
from analysis import shannon_entropy, melodic_intervals, zipf_slope
from arrange import render_piece, section_span, STEP_TICKS
from midiwriter import cc_ramp, CC_EXPRESSION, CC_REVERB_SEND, CC_BRIGHTNESS, PPQ
from rhythm import grid_from_hits
from theory import NOTE_NAMES, note_in_range, scale_degree
from drums import KICK, SNARE, CLAP, RIM, CHH, OHH, HTOM, MTOM2, LTOM2, SHAKER, choke_hihats

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
                                swell_section="build", swing_pct=hz.bur_swing_pct(bpm), reverb_swell=True)

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


ARCHETYPES = {
    "halftime_drone": halftime_drone,
    "broken_meter": broken_meter,
    "four_floor_glitch": four_floor_glitch,
    "gated_drama": gated_drama,
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


def generate(seed=None, archetype=None, root=None, scale=None, bpm=None, max_attempts=5):
    """Build, render, and QC one clip. Returns a dict with the rendered result
    plus the metadata (seed/archetype/title/bpm/root/scale) needed to label it."""
    if seed is None:
        seed = random.SystemRandom().randrange(2 ** 31)

    archetype_name = archetype or random.Random(seed).choice(list(ARCHETYPES))
    if archetype_name not in ARCHETYPES:
        raise KeyError(f"unknown archetype {archetype_name!r}, choices: {list(ARCHETYPES)}")

    problems = []
    for attempt in range(max_attempts):
        rng = random.Random(seed * 1000 + attempt)
        spec = ARCHETYPES[archetype_name](rng, root=root, scale=scale, bpm=bpm)
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
            }

    raise RuntimeError(f"seed {seed} ({archetype_name}) failed QC after {max_attempts} attempts: {problems}")
