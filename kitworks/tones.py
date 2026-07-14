"""tones.py -- a distinct tone recipe per kit, so the 33 kits stop sounding
the same.

The problem: an imported clip plays through its TRACK's assigned tone, and the
707 ignores the program/channel bytes in the SMF. So every kit sounds identical
unless each one loads its own tones. This gives every kit a per-track patch
recipe -- a category + a descriptor -- chosen for cohesion within the kit and
CONTRAST between kits.

These name factory ZEN-Core categories / patch characters, not exact patch
numbers (those vary by firmware and by which purchased packs are installed).
Map each line to the closest patch in your own library -- factory first, then
your packs -- when you build the kit's project. When this session runs on your
machine (with /downloads mounted) I can point these at your actual pack patches.
"""

# palette = a coherent per-part set of patch characters for a genre lane.
# Keeping ~16 lanes and spreading the 33 kits across them (never two neighbours
# on the same lane) is what makes the collection sound varied.
PALETTES = {
    "trip_noir":    dict(drums="Kit: dusty/vinyl breaks (soft, roomy)", bass="Bass: round sub / P-bass",
                         lead="Keys: dark Rhodes / FM EP", counter="Voice: airy 'oohs' pad",
                         chords="Pad: warm analog str", arp="Bell: soft celesta"),
    "techno_steel": dict(drums="Kit: TR-909 (hard, dry)", bass="Synth Bass: reese/detuned saw",
                         lead="Lead: hollow saw / acid", counter="Synth: metallic blip",
                         chords="Synth: filtered stab", arp="Pluck: short saw pluck"),
    "acid_rave":    dict(drums="Kit: 909+claps (bright)", bass="Synth Bass: TB-303 acid",
                         lead="Lead: resonant square", counter="Synth: zap",
                         chords="Synth: rave organ stab", arp="Pluck: acid pluck"),
    "house_warm":   dict(drums="Kit: house (punchy kick, crisp hat)", bass="Synth Bass: plucky round",
                         lead="Keys: house organ / piano", counter="Voice: diva chop",
                         chords="Keys: filtered e-piano stab", arp="Pluck: ping pluck"),
    "indie_band":   dict(drums="Kit: acoustic (tight, live)", bass="Bass: fingered electric",
                         lead="Synth: warm poly / clean guitar-ish", counter="Synth: soft square",
                         chords="Pad: warm poly", arp="Pluck: nylon-ish"),
    "synthwave":    dict(drums="Kit: LinnDrum/gated (big snare)", bass="Synth Bass: octave analog",
                         lead="Lead: bright supersaw", counter="Synth: PWM line",
                         chords="Pad: JP-8 poly", arp="Pluck: bright saw arp"),
    "darkwave":     dict(drums="Kit: gated toms/dry", bass="Synth Bass: growl saw",
                         lead="Lead: cold saw", counter="Synth: glass",
                         chords="Pad: cathedral str", arp="Bell: dark bell"),
    "dream_pop":    dict(drums="Kit: soft/brushed", bass="Bass: round sub",
                         lead="Bell: glassy sine-bell", counter="Voice: 'aah' pad",
                         chords="Pad: shimmer", arp="Bell: music box"),
    "post_rock":    dict(drums="Kit: live/roomy", bass="Bass: fingered electric",
                         lead="Synth: tremolo/e-bow", counter="Str: cello line",
                         chords="Pad: tremolo strings", arp="Pluck: chiming delay pluck"),
    "garage_2step": dict(drums="Kit: garage (crisp, swung hats)", bass="Synth Bass: dub sub",
                         lead="Synth: vocal-chop stab", counter="Voice: pitched chop",
                         chords="Keys: filtered organ stab", arp=None),
    "krautrock":    dict(drums="Kit: motorik (dry, steady)", bass="Synth Bass: 8th ostinato analog",
                         lead="Lead: hypnotic saw", counter="Synth: phased line",
                         chords="Pad: slow analog", arp="Pluck: motorik pluck"),
    "neofolk":      dict(drums="Perc: frame drum / hand perc", bass="Bass: upright-ish round",
                         lead="Wind: flute / low whistle", counter="Str: viol drone",
                         chords="Pad: bowed drone", arp=None),
    "goth_blues":   dict(drums="Kit: big room 12/8 stomp", bass="Bass: baritone/round",
                         lead="Guitar: slide/dist lead", counter="Organ: dark organ",
                         chords="Organ: church organ", arp=None),
    "ambient_bed":  dict(drums="Kit: whisper (soft kick, tick)", bass="Bass: soft sub",
                         lead="Bell: vibraphone / soft mallet", counter="Str: low strings pad",
                         chords="Pad: warm glass", arp=None),
    "dub_downtempo":dict(drums="Kit: dub (deep kick, rim, tape)", bass="Synth Bass: deep dub sub",
                         lead="Keys: spring-reverb keys", counter="Voice: dub stab",
                         chords="Organ: skank organ stab", arp=None),
    "art_pop":      dict(drums="Kit: hybrid (electronic+live)", bass="Synth Bass: round moog",
                         lead="Synth: brooding saw", counter="Voice: choir",
                         chords="Pad: wide analog", arp=None),
}

# each kit -> its lane. Neighbours in the collection deliberately differ.
KIT_PALETTE = {
    "Nightpulse": "trip_noir",    "Glasskid": "art_pop",       "Hillrunner": "indie_band",
    "Lowgold": "trip_noir",       "Seaglass": "dream_pop",     "Ironveil": "techno_steel",
    "Holloway": "trip_noir",      "Morningvow": "post_rock",   "Duskwire": "indie_band",
    "Autoglide": "krautrock",     "Veilfire": "synthwave",     "Palefen": "darkwave",
    "Redloam": "goth_blues",      "Chromehall": "synthwave",   "Thornfield": "neofolk",
    "Brightwork": "house_warm",   "Saltcode": "garage_2step",  "Mirrorlake": "dream_pop",
    "Nightshift": "trip_noir",    "Stonecircle": "neofolk",    "Acidbath": "acid_rave",
    "Winterlight": "post_rock",   "Fellwater": "indie_band",   "Emberlark": "ambient_bed",
    "Tidewheel": "krautrock",     "Blackfathom": "darkwave",   "Stillharbor": "ambient_bed",
    "Voltline": "house_warm",     "Ashfall": "dub_downtempo",  "Ghostloom": "art_pop",
    "Ironglass": "techno_steel",  "Reedmarsh": "ambient_bed",  "Tarblack": "dub_downtempo",
}


def recipe(kit):
    """-> {part: patch descriptor} for a kit (arp only if the kit has one)."""
    pal = PALETTES[KIT_PALETTE[kit["name"]]]
    out = {}
    for part in ("drums", "bass", "lead", "counter", "chords", "arp"):
        if (kit.get(part) or part == "drums") and pal.get(part):
            out[part] = pal[part]
    return out


def card(kit):
    lane = KIT_PALETTE[kit["name"]]
    lines = [f"TONES  (lane: {lane} -- load one per track; map to your packs)"]
    for part, patch in recipe(kit).items():
        lines.append(f"  {part:<8} {patch}")
    return "\n".join(lines) + "\n"
