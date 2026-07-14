#!/usr/bin/env python3
"""soundlib.py -- the STANDING SOUND LIBRARY for KITWORKS.

Every tone a kit is allowed to name lives here, grouped by the pack that
provides it and tagged by role + character. This is the single source of truth:
`kitsounds.py` assigns tones to kit parts by their exact on-box name, and
`tests.py` checks that every assignment resolves to a real entry here.

NAMES ARE VERBATIM as they appear on the MC-707 screen -- including Roland's own
spellings (e.g. 'Cin Before Sunse', 'NK Beauity vox', 'Cin Inerstellar'). Keep
them byte-exact so the name on the card matches the name you scroll to.

A tone only EXISTS on your box if its pack is installed. The .svz artist packs
load via ZEN Core; the .sdz Sound Packs load via the Roland Cloud installer.
See PACKS below for the four you have loaded.

  from soundlib import by_role, resolve, PACKS
  by_role('bass')                 # every bass-ish tone across all installed packs
  resolve('NK Deep Bass')         # -> full entry, or KeyError if unknown
"""

# --- the packs loaded on the box (ROLAND/SOUND) ------------------------------
# 'kind': svz = ZEN-Core tone bank (tones only); sdz = Sound Pack (tones + kits
# + samples). 'names': 'exact' = extracted from the file / verified; 'from_box'
# = must be read off the MC-707 screen and pasted into TONES below.
PACKS = {
    "factory": {
        "kind": "built-in", "names": "verified",
        "desc": "3000+ ZEN-Core factory tones, 80+ drum kits. Always present.",
    },
    "analog_dreams": {
        "kind": "svz", "file": "AnalogDreams.svz", "count": 50, "names": "exact",
        "desc": "Roland artist pack -- vintage analog polys, Juno/Jupiter, acid "
                "bass, retro leads (designers NK / SR).",
    },
    "cinematica": {
        "kind": "svz", "file": "Cinematica.svz", "count": 50, "names": "exact",
        "desc": "Roland artist pack -- cinematic pads, atmospheres, choirs, "
                "evolving textures (LFO / 'Cin ' prefix).",
    },
    "lofi_throwback": {
        "kind": "sdz", "file": "MCZ004_LoFiTbck.sdz", "count": 48, "names": "from_box",
        "desc": "Roland MC/MV Production Pack by Wave Alchemy -- boom-bap / 90s "
                "RnB: dusty EPs, tape keys, vinyl drums. 16 kits, 64 clips.",
    },
    "future_pop": {
        "kind": "sdz", "file": "MCZ002_Ftrpop.sdz", "count": 48, "names": "from_box",
        "desc": "Roland MC/MV Production Pack -- modern future-pop synths, plucks, "
                "vocal chops. 16 kits, 64 clips. (Free pack.)",
    },
}

# --- role vocabulary ---------------------------------------------------------
# Every tone declares ONE primary role so `by_role` can offer real choices.
ROLES = ["bass", "lead", "pad", "atmos", "keys", "bell", "pluck", "arp",
         "vox", "brass", "poly", "drums", "fx"]

# --- factory favorites (verbatim from Roland's MC-707 Sound List) ------------
# A small, curated shortlist per role -- the reliable go-to factory tones, so a
# kit can stay all-factory without owning any pack. Extend freely.
_FACTORY = [
    # name,             role,     tags
    ("Dark Sub",        "bass",   ["dark", "sub", "hollow"]),
    ("Wide Syn Brass",  "brass",  ["bright", "wide", "saw"]),
    ("Super Saw Lead",  "lead",   ["bright", "supersaw", "big"]),
    ("Fuzz Lead",       "lead",   ["dirty", "aggressive"]),
    ("Air Lead",        "lead",   ["airy", "soft", "vocal"]),
    ("Detuned EP 1",    "keys",   ["detuned", "cold", "electric"]),
    ("Wurly EP",        "keys",   ["warm", "electric", "vintage"]),
    ("Dyno EP",         "keys",   ["warm", "electric", "bell"]),
    ("Stage EP",        "keys",   ["warm", "electric"]),
    ("Soft Pad",        "pad",    ["soft", "warm"]),
    ("Warm Pad Dly",    "pad",    ["warm", "delayed"]),
    ("Horror Pad",      "pad",    ["dark", "unsettling"]),
    ("JP-8 Haunting",   "pad",    ["dark", "cold", "jupiter"]),
    ("Shimmer Pad",     "atmos",  ["bright", "shimmer", "reverb"]),
    ("Heaven Pad 1",    "atmos",  ["bright", "lush"]),
    ("Tape Strings",    "pad",    ["strings", "tape", "mellotron"]),
    ("Strings4Film",    "pad",    ["strings", "cinematic", "swell"]),
    ("Marcato Str",     "pad",    ["strings", "bowed"]),
    ("Full Orchest",    "atmos",  ["orchestral", "big"]),
    ("Giant Sweep",     "atmos",  ["riser", "sweep"]),
    ("FM Sparkles",     "bell",   ["fm", "bright", "sparkle"]),
    ("Dreambell",       "bell",   ["soft", "bell"]),
    ("TR-909 Kit",      "drums",  ["house", "techno", "punchy"]),
    ("TR-808 Kit",      "drums",  ["hiphop", "boom", "sub"]),
    ("TR-606 Kit",      "drums",  ["thin", "dry", "electro"]),
    ("CR-78 Kit",       "drums",  ["vintage", "soft", "preset"]),
    ("Analog Kit",      "drums",  ["analog", "dry"]),
    ("Orchestra Kit",   "drums",  ["acoustic", "cinematic"]),
]

# --- factory tones VERIFIED IN USE (pulled from the 25 saved .mpj projects on
# the card -- these are the exact factory tones Adnan reaches for per aesthetic,
# so they carry real weight as suggestions/assignments). Names verbatim on-box.
_FACTORY_USED = [
    ("JD-800 Piano",    "keys",  ["piano", "jd800", "bright"]),
    ("Note Piano MC",   "keys",  ["piano", "soft"]),
    ("Synth Keys",      "keys",  ["synth", "warm"]),
    ("Reflective Keys", "keys",  ["soft", "reflective", "ambient"]),
    ("Juno P13 Str",    "pad",   ["juno", "strings", "warm"]),
    ("Soft Pad 2",      "pad",   ["soft", "warm", "simple"]),
    ("Stack Chord 2D",  "poly",  ["stacked", "chord", "wide"]),
    ("JUNO Stab 3",     "pluck", ["juno", "stab", "bright"]),
    ("Droplet",         "pluck", ["glassy", "bell", "short"]),
    ("AX Sync Lead",    "lead",  ["sync", "sharp", "solo"]),
    ("Unison Lead",     "lead",  ["unison", "fat", "solo"]),
    ("Trap Synth",      "bass",  ["trap", "sub", "modern"]),
    ("Vocal",           "vox",   ["vocal", "sustained"]),
    ("XV Spectre Vox G", "vox",  ["choir", "vintage", "xv"]),
    ("Trap Kit",        "drums", ["trap", "modern", "punchy"]),
    ("Over08 Kit",      "drums", ["overdrive", "gritty"]),
    # FX / one-shot tones used on aux tracks for risers, texture, punctuation
    ("Applause w",      "fx",    ["crowd", "swell", "texture"]),
    ("Step Slicer 5",   "fx",    ["gated", "rhythmic"]),
    ("Seq Sqr 1 Atk",   "fx",    ["sequence", "square"]),
    ("High Q",          "fx",    ["zap", "hit"]),
    ("Elec Slap",       "fx",    ["slap", "percussive"]),
    ("Scratch Push",    "fx",    ["scratch", "dj"]),
    ("Scratch Pull",    "fx",    ["scratch", "dj"]),
    ("Swish&Turn",      "fx",    ["sweep", "transition"]),
]

# --- Analog Dreams (50) ------------------------------------------------------
_ANALOG_DREAMS = [
    ("NK Poly Uni",      "poly",  ["analog", "unison", "warm"]),
    ("NK Brass",         "brass", ["analog", "brass"]),
    ("NK Uni String",    "pad",   ["analog", "strings", "unison"]),
    ("NK Jupiter Orbit", "poly",  ["jupiter", "wide", "lush"]),
    ("NK Landscape",     "pad",   ["evolving", "wide"]),
    ("NK Beauity vox",   "vox",   ["soft", "vocal", "airy"]),
    ("NK Phazed Slices", "pluck", ["phaser", "rhythmic"]),
    ("NK Whisper Tones", "vox",   ["breathy", "soft"]),
    ("NK Decay Bass",    "bass",  ["plucky", "decay", "analog"]),
    ("NK Funky Monkey",  "keys",  ["funky", "clav", "bright"]),
    ("NK Klauss Lead",   "lead",  ["berlin", "sequence", "analog"]),
    ("NK Glauss Lead",   "lead",  ["berlin", "sequence", "detuned"]),
    ("NK Funky Town",    "poly",  ["funky", "bright"]),
    ("NK Deep Bass",     "bass",  ["deep", "round", "sub"]),
    ("NK Acid Bass",     "bass",  ["acid", "303", "resonant"]),
    ("NK 106 Poly",      "poly",  ["juno", "chorus", "warm"]),
    ("NK Uni Bass",      "bass",  ["unison", "fat", "analog"]),
    ("NK Juno X",        "poly",  ["juno", "bright"]),
    ("NK Graal",         "poly",  ["evolving", "dark"]),
    ("NK Ivory",         "keys",  ["piano", "electric"]),
    ("NK VCO Pad",       "pad",   ["analog", "warm"]),
    ("NK Cyber",         "poly",  ["digital", "cold"]),
    ("NK Shnobel",       "poly",  ["quirky", "analog"]),
    ("NK Lead India",    "lead",  ["exotic", "solo"]),
    ("NK Lead Classic",  "lead",  ["classic", "analog", "solo"]),
    ("SR Golden Poly",   "poly",  ["warm", "lush", "80s"]),
    ("SR Legend 80",     "poly",  ["80s", "bright"]),
    ("SR Destiny",       "pad",   ["lush", "cinematic"]),
    ("SR Kingdom",       "pad",   ["wide", "epic"]),
    ("SR Softie",        "pad",   ["soft", "warm"]),
    ("SR Jupiter Dream", "poly",  ["jupiter", "dreamy"]),
    ("SR Retro Vibe",    "poly",  ["retro", "warm"]),
    ("SR Neon Light",    "pluck", ["bright", "80s", "neon"]),
    ("SR Red Planet",    "atmos", ["dark", "sci-fi"]),
    ("SR Snowfall",      "bell",  ["glassy", "soft"]),
    ("SR Crystal",       "bell",  ["glassy", "bright"]),
    ("SR Fly",           "lead",  ["soaring", "solo"]),
    ("SR 198X",          "poly",  ["80s", "retro"]),
    ("SR Flash Of Time", "pluck", ["arp", "bright"]),
    ("SR Anjuna",        "pluck", ["trance", "bright"]),
    ("SR Lunar",         "atmos", ["cold", "wide"]),
    ("SR Dreamer",       "pad",   ["dreamy", "soft"]),
    ("SR Zacepin",       "keys",  ["cinematic", "russian"]),
    ("SR Daft",          "lead",  ["french", "talkbox", "funky"]),
    ("SR Night City",    "poly",  ["neon", "80s", "moody"]),
    ("SR Deep",          "keys",  ["deep", "warm"]),
    ("SR Miami Vice",    "poly",  ["80s", "nostalgic"]),
    ("SR Angels Vox",    "vox",   ["choir", "soft"]),
    ("SR Juno Dream",    "poly",  ["juno", "dreamy", "chorus"]),
    ("SR Lazer",         "lead",  ["sharp", "sync", "bright"]),
]

# --- Cinematica (50) ---------------------------------------------------------
_CINEMATICA = [
    ("Cin Entrance",     "atmos", ["cinematic", "intro", "wide"]),
    ("Cin Far Way",      "atmos", ["distant", "reverb"]),
    ("Cin Monumental",   "atmos", ["epic", "big"]),
    ("Cin Early June",   "pad",   ["warm", "nostalgic"]),
    ("Cin Kingdom",      "pad",   ["epic", "wide"]),
    ("Cin Magica",       "pad",   ["magical", "shimmer"]),
    ("Cin Gravity",      "atmos", ["dark", "deep"]),
    ("Cin Fantasia",     "pad",   ["dreamy", "lush"]),
    ("Cin 2 Voice",      "vox",   ["choir", "duo"]),
    ("Cin Before Sunse", "pad",   ["warm", "cinematic"]),   # 'Sunset' truncated on-box
    ("Cin Obsession",    "pad",   ["dark", "tense"]),
    ("Cin Ghost Pluck",  "pluck", ["haunting", "delay"]),
    ("Cin Summer Lands", "pad",   ["warm", "bright"]),
    ("Cin Meta Pluck",   "pluck", ["rhythmic", "modern"]),
    ("Cin Modern XV",    "poly",  ["modern", "hybrid"]),
    ("Cin InRVoice",     "vox",   ["vocal", "processed"]),
    ("Cin Dream On",     "pad",   ["dreamy", "soft"]),
    ("Cin Voices",       "vox",   ["choir", "wide"]),
    ("Cin Crystal",      "bell",  ["glassy", "bright"]),
    ("Cin Oort Cloud",   "atmos", ["deep", "space", "drone"]),
    ("Cin Dramatic",     "atmos", ["tense", "cinematic"]),
    ("Cin Modern Vox",   "vox",   ["vocal", "modern"]),
    ("Cin Action Bass",  "bass",  ["driving", "cinematic"]),
    ("Cin Seq Holder",   "seq",   ["sequence", "rhythmic"]),
    ("Cin Hidden Voice", "vox",   ["breathy", "distant"]),
    ("Cin Oasis",        "pad",   ["warm", "shimmer"]),
    ("Cin Vibra",        "keys",  ["vibraphone", "mallet"]),
    ("Cin Desert Breat", "pad",   ["airy", "breath"]),      # 'Breath' truncated on-box
    ("Cin Northern Lig", "atmos", ["shimmer", "aurora"]),   # 'Lights' truncated on-box
    ("Cin Life Ways",    "pad",   ["evolving", "warm"]),
    ("Cin Signal Pad",   "pad",   ["evolving", "modern"]),
    ("Cin Memory",       "pad",   ["nostalgic", "soft"]),
    ("Cin Quasar",       "atmos", ["space", "bright"]),
    ("Cin Sanctuary",    "pad",   ["choir", "sacred", "wide"]),
    ("Cin Apocalyptic",  "atmos", ["dark", "tense", "big"]),
    ("Cin Mosaic",       "pluck", ["rhythmic", "arp"]),
    ("Cin Anubis",       "atmos", ["dark", "exotic"]),
    ("Cin Module 01",    "keys",  ["electric", "modern"]),
    ("Cin Milky Way",    "atmos", ["space", "shimmer"]),
    ("Cin Creatures Pd", "pad",   ["organic", "evolving"]),
    ("Cin Airy Keys",    "keys",  ["airy", "soft", "electric"]),
    ("Cin Desert Angel", "pad",   ["choir", "warm"]),
    ("Cin Saint Voice",  "vox",   ["choir", "sacred"]),
    ("Cin Strobe Light", "pluck", ["rhythmic", "bright"]),
    ("Cin Vangelico",    "pad",   ["vangelis", "80s", "epic"]),
    ("Cin Inerstellar",  "atmos", ["space", "epic"]),       # 'Interstellar' spelling on-box
    ("Cin Moonwalk",     "poly",  ["retro", "funky"]),
    ("Cin Oblivion",     "atmos", ["dark", "deep"]),
    ("Cin Mirage",       "pad",   ["shimmer", "distant"]),
    ("Cin Ice Desert",   "pad",   ["cold", "wide"]),
]

# --- assemble TONES ----------------------------------------------------------
# name -> {"pack", "role", "tags"}. Built once from the per-pack tables above.
TONES = {}


def _add(pack, table):
    for name, role, tags in table:
        assert role in ROLES or role == "seq", f"{name}: bad role {role!r}"
        if name in TONES:
            raise ValueError(f"duplicate tone name across packs: {name!r}")
        TONES[name] = {"pack": pack, "role": role, "tags": list(tags)}


_add("factory", _FACTORY)
_add("factory", _FACTORY_USED)
_add("analog_dreams", _ANALOG_DREAMS)
_add("cinematica", _CINEMATICA)
# lofi_throwback / future_pop: names are read from the box -- paste (name, role,
# tags) rows for the tones you actually use and call _add("lofi_throwback", ...).
# Until then, reference these packs by pack name in kitsounds.py (see fallback).


# --- helpers -----------------------------------------------------------------
def resolve(name):
    """Full entry for a tone name (exact, on-box spelling). KeyError if unknown."""
    return TONES[name]


def known(name):
    return name in TONES


def by_role(role, pack=None):
    """Every tone in a role, optionally limited to one pack. -> [names]."""
    return [n for n, e in TONES.items()
            if e["role"] == role and (pack is None or e["pack"] == pack)]


def by_pack(pack):
    return [n for n, e in TONES.items() if e["pack"] == pack]


def describe(name):
    """'NK Deep Bass  [analog_dreams · bass · deep/round/sub]' for cards/LAYOUT."""
    e = TONES[name]
    return f"{name}  [{e['pack']} · {e['role']} · {'/'.join(e['tags'])}]"


if __name__ == "__main__":
    from collections import Counter
    print(f"soundlib: {len(TONES)} tones across "
          f"{len(set(e['pack'] for e in TONES.values()))} installed packs "
          f"(+2 sdz packs pending box-read names)\n")
    for pack in PACKS:
        ns = by_pack(pack)
        if not ns and PACKS[pack]["names"] == "from_box":
            print(f"  {pack:<16} names read from box -- none registered yet")
            continue
        rc = Counter(TONES[n]["role"] for n in ns)
        roles = ", ".join(f"{r}:{c}" for r, c in sorted(rc.items()))
        print(f"  {pack:<16} {len(ns):>3} tones  ({roles})")
