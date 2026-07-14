#!/usr/bin/env python3
"""kitsounds.py -- per-kit SOUND + FX assignments (the sound-design layer).

Kit score files (kits/*.py) hold the NOTES; this file holds which TONE each
part plays and how it is shaped. Kept separate so the scores stay pure.

Every slot below is scaffolded to None with 2-3 SUGGESTIONS (mood-matched from
soundlib.py) in the trailing comment -- fill a slot with an EXACT tone name from
soundlib (on-box spelling) to lock it in. Leave None to keep the generic hint.
sd_export.py prints whatever is set into the kit LAYOUT.TXT.

FX per kit: 'cc' shapes the tones from the computer (documented CCs only:
cutoff 74, resonance 71, attack 73, release 72, reverb 91, chorus 92); 'master'
sets the master-bus reverb/delay as (type_name, level 0-127). All optional.

Names for the two .sdz packs (LoFi Throwback, Future Pop) aren't in the files --
read them off the box, add rows to soundlib._add(...), then use them here.
"""

SOUNDS = {
    'Nightpulse': dict(
        # Fm  68bpm  feel:ritual
        drums   = None,   # DRUM kit -- try: TR-808 Kit
        bass    = None,   # bass -- try: Dark Sub  |  NK Deep Bass  |  Cin Action Bass
        lead    = None,   # lead -- try: Detuned EP 1  |  SR Deep  |  Cin Airy Keys
        counter = None,   # 2nd voice -- try: Detuned EP 1  |  SR Deep  |  Cin 2 Voice
        chords  = None,   # pad/keys -- try: Cin Gravity  |  Cin Oblivion  |  JP-8 Haunting
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Glasskid': dict(
        # Cm  120bpm  feel:pushing
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Airy Keys  |  Detuned EP 1  |  NK 106 Poly
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Hillrunner': dict(
        # Am  108bpm  feel:pushing
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Airy Keys  |  Detuned EP 1  |  NK 106 Poly
        arp     = None,   # arp/pluck -- try: Cin Crystal  |  Dreambell  |  NK Phazed Slices
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Lowgold': dict(
        # Ddor  84bpm  feel:laidback
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Inerstellar  |  Cin Milky Way  |  Cin Oort Cloud
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Seaglass': dict(
        # Cmaj  92bpm  feel:laidback
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Dream On  |  Cin Fantasia  |  SR Dreamer
        arp     = None,   # arp/pluck -- try: Cin Crystal  |  Dreambell  |  NK Phazed Slices
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Ironveil': dict(
        # Am  126bpm  feel:pushing
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Dark Sub  |  Cin Action Bass  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Anubis  |  Cin Apocalyptic  |  Cin Gravity
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Holloway': dict(
        # F#m  76bpm  feel:laidback
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Airy Keys  |  Detuned EP 1  |  NK 106 Poly
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Morningvow': dict(
        # Gmaj  72bpm  feel:laidback
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Airy Keys  |  Detuned EP 1  |  NK 106 Poly
        arp     = None,   # arp/pluck -- try: Cin Crystal  |  Dreambell  |  NK Phazed Slices
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Duskwire': dict(
        # Em  100bpm  feel:laidback
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Cin Saint Voice  |  Cin 2 Voice  |  Cin Voices
        chords  = None,   # pad/keys -- try: Cin Sanctuary  |  Cin Desert Angel  |  Detuned EP 1
        arp     = None,   # arp/pluck -- try: Cin Crystal  |  Dreambell  |  NK Phazed Slices
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Autoglide': dict(
        # Cmix  120bpm  feel:pushing
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Airy Keys  |  Detuned EP 1  |  NK 106 Poly
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Veilfire': dict(
        # Bm  112bpm  feel:pushing
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Dark Sub  |  Cin Action Bass  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Anubis  |  Cin Apocalyptic  |  Cin Gravity
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Palefen': dict(
        # Dm  96bpm  feel:laidback
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Airy Keys  |  Detuned EP 1  |  NK 106 Poly
        arp     = None,   # arp/pluck -- try: Cin Crystal  |  Dreambell  |  NK Phazed Slices
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Redloam': dict(
        # Em  54bpm  feel:ritual
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Dark Sub  |  Cin Action Bass  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Anubis  |  Cin Apocalyptic  |  Cin Gravity
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Chromehall': dict(
        # Gm  100bpm  feel:pushing
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Airy Keys  |  Detuned EP 1  |  NK 106 Poly
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Thornfield': dict(
        # Ephr  92bpm  feel:ritual
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Dark Sub  |  Cin Action Bass  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Anubis  |  Cin Apocalyptic  |  Cin Gravity
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Brightwork': dict(
        # Ador  116bpm  feel:laidback
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Airy Keys  |  Detuned EP 1  |  NK 106 Poly
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Saltcode': dict(
        # F#m  132bpm  feel:laidback
        drums   = None,   # DRUM kit -- try: TR-808 Kit
        bass    = None,   # bass -- try: NK Deep Bass  |  Dark Sub  |  Cin Action Bass
        lead    = None,   # lead -- try: SR Deep  |  Air Lead  |  Cin Airy Keys
        counter = None,   # 2nd voice -- try: SR Deep  |  Air Lead  |  Cin 2 Voice
        chords  = None,   # pad/keys -- try: Cin Gravity  |  Cin Oblivion  |  Cin Oort Cloud
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Mirrorlake': dict(
        # Fmaj  86bpm  feel:laidback
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Airy Keys  |  Detuned EP 1  |  NK 106 Poly
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Nightshift': dict(
        # Am  60bpm  feel:laidback
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Dark Sub  |  Cin Action Bass  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Anubis  |  Cin Apocalyptic  |  Cin Gravity
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Stonecircle': dict(
        # Ddor  78bpm  feel:ritual
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Oort Cloud  |  Detuned EP 1  |  NK 106 Poly
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Acidbath': dict(
        # Am  130bpm  feel:pushing
        drums   = None,   # DRUM kit -- try: TR-808 Kit
        bass    = None,   # bass -- try: NK Deep Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: SR Deep  |  Air Lead  |  Cin Airy Keys
        counter = None,   # 2nd voice -- try: SR Deep  |  Air Lead  |  Cin 2 Voice
        chords  = None,   # pad/keys -- try: Cin Gravity  |  Cin Oblivion  |  Cin Oort Cloud
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
    'Winterlight': dict(
        # Cmaj  76bpm  feel:laidback
        drums   = None,   # DRUM kit -- try: Analog Kit
        bass    = None,   # bass -- try: Cin Action Bass  |  Dark Sub  |  NK Acid Bass
        lead    = None,   # lead -- try: Air Lead  |  Cin Airy Keys  |  NK Funky Monkey
        counter = None,   # 2nd voice -- try: Air Lead  |  Cin 2 Voice  |  NK Beauity vox
        chords  = None,   # pad/keys -- try: Cin Airy Keys  |  Detuned EP 1  |  NK 106 Poly
        arp     = None,   # arp/pluck -- try: Cin Crystal  |  Dreambell  |  NK Phazed Slices
        fx      = dict(
            cc     = {},                 # e.g. {"bass":{"cutoff":55,"reverb":30}}
            master = None,               # e.g. {"reverb":("Hall",70),"delay":("Delay",40)}
        ),
    ),
}


def for_kit(name):
    """Assignments for a kit name, or an empty dict if none set."""
    return SOUNDS.get(name, {})

