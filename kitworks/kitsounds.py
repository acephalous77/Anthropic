#!/usr/bin/env python3
"""kitsounds.py -- per-kit SOUND + FX assignments (the sound-design layer).

Kit score files (kits/*.py) hold the NOTES; this file holds which TONE each part
plays and how it is shaped. Kept separate so the scores stay pure.

Each kit gets a DISTINCT palette chosen for its own genre/mood and spread across
the full soundlib (82 distinct tones in play, vs a handful before). Drum kits
repeat by idiom (small pool). Change any slot to any exact name in soundlib;
sd_export.py prints them to each kit LAYOUT.TXT.

FX: 'master' = master-bus (type, level 0-127) per mood. 'cc' shapes per-part
tones (cutoff74/res71/atk73/rel72/rev91/cho92) -- open to dial by ear.
"""

SOUNDS = {
    'Nightpulse': dict(   # Fm 68bpm · ritual
        drums   = 'TR-606 Kit'        ,  # factory · thin/dry/electro
        bass    = 'Dark Sub'          ,  # factory · dark/sub/hollow
        lead    = 'Cin Ghost Pluck'   ,  # cinematica · haunting/delay
        counter = 'NK Whisper Tones'  ,  # analog_dreams · breathy/soft
        chords  = 'JP-8 Haunting'     ,  # factory · dark/cold/jupiter
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 64)}),
    ),
    'Glasskid': dict(   # Cm 120bpm · pushing
        drums   = 'TR-909 Kit'        ,  # factory · house/techno/punchy
        bass    = 'Cin Action Bass'   ,  # cinematica · driving/cinematic
        lead    = 'Detuned EP 1'      ,  # factory · detuned/cold/electric
        counter = 'Cin Ice Desert'    ,  # cinematica · cold/wide
        chords  = 'NK Cyber'          ,  # analog_dreams · digital/cold
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 64)}),
    ),
    'Hillrunner': dict(   # Am 108bpm · pushing
        drums   = 'TR-909 Kit'        ,  # factory · house/techno/punchy
        bass    = 'Cin Action Bass'   ,  # cinematica · driving/cinematic
        lead    = 'Air Lead'          ,  # factory · airy/soft/vocal
        counter = 'NK Beauity vox'    ,  # analog_dreams · soft/vocal/airy
        chords  = 'Cin Desert Breat'  ,  # cinematica · airy/breath
        arp     = 'Cin Strobe Light'  ,  # cinematica · rhythmic/bright
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 64)}),
    ),
    'Lowgold': dict(   # Ddor 84bpm · laidback
        drums   = 'TR-808 Kit'        ,  # factory · hiphop/boom/sub
        bass    = 'NK Acid Bass'      ,  # analog_dreams · acid/303/resonant
        lead    = 'Wurly EP'          ,  # factory · warm/electric/vintage
        counter = 'Soft Pad'          ,  # factory · soft/warm
        chords  = 'SR Softie'         ,  # analog_dreams · soft/warm
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 50)}),
    ),
    'Seaglass': dict(   # Cmaj 92bpm · laidback
        drums   = 'Analog Kit'        ,  # factory · analog/dry
        bass    = 'NK Decay Bass'     ,  # analog_dreams · plucky/decay/analog
        lead    = 'Dyno EP'           ,  # factory · warm/electric/bell
        counter = 'Cin Oasis'         ,  # cinematica · warm/shimmer
        chords  = 'Cin Early June'    ,  # cinematica · warm/nostalgic
        arp     = 'Cin Meta Pluck'    ,  # cinematica · rhythmic/modern
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 50)}),
    ),
    'Ironveil': dict(   # Am 126bpm · pushing
        drums   = 'TR-909 Kit'        ,  # factory · house/techno/punchy
        bass    = 'Dark Sub'          ,  # factory · dark/sub/hollow
        lead    = 'Detuned EP 1'      ,  # factory · detuned/cold/electric
        counter = 'Cin Obsession'     ,  # cinematica · dark/tense
        chords  = 'JP-8 Haunting'     ,  # factory · dark/cold/jupiter
        fx      = dict(cc={}, master={'reverb': ('Hall', 44), 'delay': ('Delay', 40)}),
    ),
    'Holloway': dict(   # F#m 76bpm · laidback
        drums   = 'TR-808 Kit'        ,  # factory · hiphop/boom/sub
        bass    = 'NK Deep Bass'      ,  # analog_dreams · deep/round/sub
        lead    = 'Cin Airy Keys'     ,  # cinematica · airy/soft/electric
        counter = 'SR Angels Vox'     ,  # analog_dreams · choir/soft
        chords  = 'Cin Dream On'      ,  # cinematica · dreamy/soft
        fx      = dict(cc={}, master={'reverb': ('Hall', 70), 'delay': ('Delay', 48)}),
    ),
    'Morningvow': dict(   # Gmaj 72bpm · laidback
        drums   = 'Analog Kit'        ,  # factory · analog/dry
        bass    = 'NK Deep Bass'      ,  # analog_dreams · deep/round/sub
        lead    = 'SR Fly'            ,  # analog_dreams · soaring/solo
        counter = 'Soft Pad 2'        ,  # factory · soft/warm/simple
        chords  = 'Cin Summer Lands'  ,  # cinematica · warm/bright
        arp     = 'JUNO Stab 3'       ,  # factory · juno/stab/bright
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 64)}),
    ),
    'Duskwire': dict(   # Em 100bpm · laidback
        drums   = 'TR-909 Kit'        ,  # factory · house/techno/punchy
        bass    = 'NK Uni Bass'       ,  # analog_dreams · unison/fat/analog
        lead    = 'SR Deep'           ,  # analog_dreams · deep/warm
        counter = 'Cin Saint Voice'   ,  # cinematica · choir/sacred
        chords  = 'Cin Desert Angel'  ,  # cinematica · choir/warm
        arp     = 'Cin Mosaic'        ,  # cinematica · rhythmic/arp
        fx      = dict(cc={}, master={'reverb': ('Hall', 84)}),
    ),
    'Autoglide': dict(   # Cmix 120bpm · pushing
        drums   = 'CR-78 Kit'         ,  # factory · vintage/soft/preset
        bass    = 'NK Decay Bass'     ,  # analog_dreams · plucky/decay/analog
        lead    = 'NK Klauss Lead'    ,  # analog_dreams · berlin/sequence/analog
        counter = 'SR Anjuna'         ,  # analog_dreams · trance/bright
        chords  = 'Cin Fantasia'      ,  # cinematica · dreamy/lush
        fx      = dict(cc={}, master={'reverb': ('Hall', 44), 'delay': ('Delay', 40)}),
    ),
    'Veilfire': dict(   # Bm 112bpm · pushing
        drums   = 'TR-606 Kit'        ,  # factory · thin/dry/electro
        bass    = 'Trap Synth'        ,  # factory · trap/sub/modern
        lead    = 'SR Neon Light'     ,  # analog_dreams · bright/80s/neon
        counter = 'Cin Vangelico'     ,  # cinematica · vangelis/80s/epic
        chords  = 'SR Night City'     ,  # analog_dreams · neon/80s/moody
        fx      = dict(cc={}, master={'reverb': ('Hall', 56), 'delay': ('Delay', 52)}),
    ),
    'Palefen': dict(   # Dm 96bpm · laidback
        drums   = 'TR-909 Kit'        ,  # factory · house/techno/punchy
        bass    = 'Dark Sub'          ,  # factory · dark/sub/hollow
        lead    = 'AX Sync Lead'      ,  # factory · sync/sharp/solo
        counter = 'Cin Ice Desert'    ,  # cinematica · cold/wide
        chords  = 'Horror Pad'        ,  # factory · dark/unsettling
        arp     = 'Droplet'           ,  # factory · glassy/bell/short
        fx      = dict(cc={}, master={'reverb': ('Hall', 70), 'delay': ('Delay', 48)}),
    ),
    'Redloam': dict(   # Em 54bpm · ritual
        drums   = 'CR-78 Kit'         ,  # factory · vintage/soft/preset
        bass    = 'NK Acid Bass'      ,  # analog_dreams · acid/303/resonant
        lead    = 'Fuzz Lead'         ,  # factory · dirty/aggressive
        counter = 'Stage EP'          ,  # factory · warm/electric
        chords  = 'Cin Apocalyptic'   ,  # cinematica · dark/tense/big
        fx      = dict(cc={}, master={'reverb': ('Hall', 84)}),
    ),
    'Chromehall': dict(   # Gm 100bpm · pushing
        drums   = 'TR-606 Kit'        ,  # factory · thin/dry/electro
        bass    = 'NK Uni Bass'       ,  # analog_dreams · unison/fat/analog
        lead    = 'SR Neon Light'     ,  # analog_dreams · bright/80s/neon
        counter = 'Cin Vangelico'     ,  # cinematica · vangelis/80s/epic
        chords  = 'SR 198X'           ,  # analog_dreams · 80s/retro
        fx      = dict(cc={}, master={'reverb': ('Hall', 56), 'delay': ('Delay', 52)}),
    ),
    'Thornfield': dict(   # Ephr 92bpm · ritual
        drums   = 'CR-78 Kit'         ,  # factory · vintage/soft/preset
        bass    = 'Trap Synth'        ,  # factory · trap/sub/modern
        lead    = 'NK Lead India'     ,  # analog_dreams · exotic/solo
        counter = 'Cin Obsession'     ,  # cinematica · dark/tense
        chords  = 'Cin Anubis'        ,  # cinematica · dark/exotic
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 64)}),
    ),
    'Brightwork': dict(   # Ador 116bpm · laidback
        drums   = 'TR-808 Kit'        ,  # factory · hiphop/boom/sub
        bass    = 'NK Decay Bass'     ,  # analog_dreams · plucky/decay/analog
        lead    = 'NK Funky Monkey'   ,  # analog_dreams · funky/clav/bright
        counter = 'Cin Summer Lands'  ,  # cinematica · warm/bright
        chords  = 'NK Funky Town'     ,  # analog_dreams · funky/bright
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 50)}),
    ),
    'Saltcode': dict(   # F#m 132bpm · laidback
        drums   = 'TR-909 Kit'        ,  # factory · house/techno/punchy
        bass    = 'Cin Action Bass'   ,  # cinematica · driving/cinematic
        lead    = 'SR Lazer'          ,  # analog_dreams · sharp/sync/bright
        counter = 'SR Flash Of Time'  ,  # analog_dreams · arp/bright
        chords  = 'NK Juno X'         ,  # analog_dreams · juno/bright
        fx      = dict(cc={}, master={'reverb': ('Hall', 70), 'delay': ('Delay', 48)}),
    ),
    'Mirrorlake': dict(   # Fmaj 86bpm · laidback
        drums   = 'Analog Kit'        ,  # factory · analog/dry
        bass    = 'NK Acid Bass'      ,  # analog_dreams · acid/303/resonant
        lead    = 'SR Retro Vibe'     ,  # analog_dreams · retro/warm
        counter = 'SR Dreamer'        ,  # analog_dreams · dreamy/soft
        chords  = 'Cin Memory'        ,  # cinematica · nostalgic/soft
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 50)}),
    ),
    'Nightshift': dict(   # Am 60bpm · laidback
        drums   = 'TR-808 Kit'        ,  # factory · hiphop/boom/sub
        bass    = 'Dark Sub'          ,  # factory · dark/sub/hollow
        lead    = 'Note Piano MC'     ,  # factory · piano/soft
        counter = 'Reflective Keys'   ,  # factory · soft/reflective/ambient
        chords  = 'Cin Magica'        ,  # cinematica · magical/shimmer
        fx      = dict(cc={}, master={'reverb': ('Hall', 70), 'delay': ('Delay', 48)}),
    ),
    'Stonecircle': dict(   # Ddor 78bpm · ritual
        drums   = 'CR-78 Kit'         ,  # factory · vintage/soft/preset
        bass    = 'NK Deep Bass'      ,  # analog_dreams · deep/round/sub
        lead    = 'NK Lead India'     ,  # analog_dreams · exotic/solo
        counter = 'Cin Saint Voice'   ,  # cinematica · choir/sacred
        chords  = 'Cin Sanctuary'     ,  # cinematica · choir/sacred/wide
        fx      = dict(cc={}, master={'reverb': ('Hall', 84)}),
    ),
    'Acidbath': dict(   # Am 130bpm · pushing
        drums   = 'TR-909 Kit'        ,  # factory · house/techno/punchy
        bass    = 'NK Acid Bass'      ,  # analog_dreams · acid/303/resonant
        lead    = 'SR Lazer'          ,  # analog_dreams · sharp/sync/bright
        counter = 'Cin 2 Voice'       ,  # cinematica · choir/duo
        chords  = 'NK Juno X'         ,  # analog_dreams · juno/bright
        fx      = dict(cc={}, master={'reverb': ('Hall', 44), 'delay': ('Delay', 40)}),
    ),
    'Winterlight': dict(   # Cmaj 76bpm · laidback
        drums   = 'Analog Kit'        ,  # factory · analog/dry
        bass    = 'Dark Sub'          ,  # factory · dark/sub/hollow
        lead    = 'Cin Crystal'       ,  # cinematica · glassy/bright
        counter = 'Cin Mirage'        ,  # cinematica · shimmer/distant
        chords  = 'Cin Kingdom'       ,  # cinematica · epic/wide
        arp     = 'NK Phazed Slices'  ,  # analog_dreams · phaser/rhythmic
        fx      = dict(cc={}, master={'reverb': ('Hall', 84)}),
    ),
}


def for_kit(name):
    """Assignments for a kit name, or an empty dict if none set."""
    return SOUNDS.get(name, {})

