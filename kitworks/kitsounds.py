#!/usr/bin/env python3
"""kitsounds.py -- per-kit SOUND + FX assignments (the sound-design layer).

Kit score files (kits/*.py) hold the NOTES; this file holds which TONE each
part plays and how it is shaped. Kept separate so the scores stay pure.

SEEDED from the 25 saved projects on the card: each kit takes the palette of
the project aesthetic it was written toward (FEVER/RADIO/PORTIS/KNIFE/FOLK/
KOSMIC/TECHNO/DRONE). These are Adnan's own proven tone choices, not guesses --
change any slot to any exact name in soundlib. sd_export.py prints them to
each kit LAYOUT.TXT. The two .sdz packs (LoFi Throwback, Future Pop) still need
their names read off the box; none of the projects used them.

FX: 'master' sets master-bus reverb/delay as (type, level 0-127). 'cc' shapes
per-part tones (cutoff74/res71/atk73/rel72/rev91/cho92) -- left open to dial by ear.
"""

SOUNDS = {
    'Nightpulse': dict(   # FEVER palette · Fm 68bpm · ritual
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Deep Bass'      ,  # analog_dreams · deep/round/sub
        lead    = 'Cin Ghost Pluck'   ,  # cinematica · haunting/delay
        counter = 'Cin Saint Voice'   ,  # cinematica · choir/sacred
        chords  = 'NK 106 Poly'       ,  # analog_dreams · juno/chorus/warm
        fx      = dict(cc={}, master={'reverb': ('Hall', 78)}),
    ),
    'Glasskid': dict(   # RADIO palette · Cm 120bpm · pushing
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Uni Bass'       ,  # analog_dreams · unison/fat/analog
        lead    = 'Note Piano MC'     ,  # factory · piano/soft
        counter = 'Vocal'             ,  # factory · vocal/sustained
        chords  = 'NK Landscape'      ,  # analog_dreams · evolving/wide
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 60), 'delay': ('Delay', 40)}),
    ),
    'Hillrunner': dict(   # RADIO palette · Am 108bpm · pushing
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Uni Bass'       ,  # analog_dreams · unison/fat/analog
        lead    = 'Note Piano MC'     ,  # factory · piano/soft
        counter = 'Vocal'             ,  # factory · vocal/sustained
        chords  = 'NK Landscape'      ,  # analog_dreams · evolving/wide
        arp     = 'Cin Meta Pluck'    ,  # cinematica · rhythmic/modern
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 60), 'delay': ('Delay', 40)}),
    ),
    'Lowgold': dict(   # PORTIS palette · Ddor 84bpm · laidback
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'Trap Synth'        ,  # factory · trap/sub/modern
        lead    = 'Note Piano MC'     ,  # factory · piano/soft
        counter = 'Cin Saint Voice'   ,  # cinematica · choir/sacred
        chords  = 'Juno P13 Str'      ,  # factory · juno/strings/warm
        fx      = dict(cc={}, master={'reverb': ('Hall', 66), 'delay': ('Delay', 46)}),
    ),
    'Seaglass': dict(   # PORTIS palette · Cmaj 92bpm · laidback
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'Trap Synth'        ,  # factory · trap/sub/modern
        lead    = 'Note Piano MC'     ,  # factory · piano/soft
        counter = 'Cin Saint Voice'   ,  # cinematica · choir/sacred
        chords  = 'Juno P13 Str'      ,  # factory · juno/strings/warm
        arp     = 'Cin Ghost Pluck'   ,  # cinematica · haunting/delay
        fx      = dict(cc={}, master={'reverb': ('Hall', 66), 'delay': ('Delay', 46)}),
    ),
    'Ironveil': dict(   # TECHNO palette · Am 126bpm · pushing
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Deep Bass'      ,  # analog_dreams · deep/round/sub
        lead    = 'Cin Ghost Pluck'   ,  # cinematica · haunting/delay
        counter = 'NK Whisper Tones'  ,  # analog_dreams · breathy/soft
        chords  = 'NK Poly Uni'       ,  # analog_dreams · analog/unison/warm
        fx      = dict(cc={}, master={'reverb': ('Hall', 44), 'delay': ('Delay', 40)}),
    ),
    'Holloway': dict(   # PORTIS palette · F#m 76bpm · laidback
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'Trap Synth'        ,  # factory · trap/sub/modern
        lead    = 'Note Piano MC'     ,  # factory · piano/soft
        counter = 'Cin Saint Voice'   ,  # cinematica · choir/sacred
        chords  = 'Juno P13 Str'      ,  # factory · juno/strings/warm
        fx      = dict(cc={}, master={'reverb': ('Hall', 66), 'delay': ('Delay', 46)}),
    ),
    'Morningvow': dict(   # FOLK palette · Gmaj 72bpm · laidback
        drums   = 'Orchestra Kit'     ,  # factory · acoustic/cinematic
        bass    = 'NK Uni Bass'       ,  # analog_dreams · unison/fat/analog
        lead    = 'NK Lead Classic'   ,  # analog_dreams · classic/analog/solo
        counter = 'Cin Voices'        ,  # cinematica · choir/wide
        chords  = 'NK 106 Poly'       ,  # analog_dreams · juno/chorus/warm
        arp     = 'Droplet'           ,  # factory · glassy/bell/short
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 72)}),
    ),
    'Duskwire': dict(   # RADIO palette · Em 100bpm · laidback
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Uni Bass'       ,  # analog_dreams · unison/fat/analog
        lead    = 'Note Piano MC'     ,  # factory · piano/soft
        counter = 'Vocal'             ,  # factory · vocal/sustained
        chords  = 'NK Landscape'      ,  # analog_dreams · evolving/wide
        arp     = 'Cin Meta Pluck'    ,  # cinematica · rhythmic/modern
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 60), 'delay': ('Delay', 40)}),
    ),
    'Autoglide': dict(   # KOSMIC palette · Cmix 120bpm · pushing
        drums   = 'TR-909 Kit'        ,  # factory · house/techno/punchy
        bass    = 'NK Uni Bass'       ,  # analog_dreams · unison/fat/analog
        lead    = 'SR Night City'     ,  # analog_dreams · neon/80s/moody
        counter = 'NK Uni String'     ,  # analog_dreams · analog/strings/unison
        chords  = 'NK Cyber'          ,  # analog_dreams · digital/cold
        fx      = dict(cc={}, master={'reverb': ('Hall', 58), 'delay': ('Delay', 52)}),
    ),
    'Veilfire': dict(   # KNIFE palette · Bm 112bpm · pushing
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Acid Bass'      ,  # analog_dreams · acid/303/resonant
        lead    = 'NK Lead India'     ,  # analog_dreams · exotic/solo
        counter = 'Soft Pad 2'        ,  # factory · soft/warm/simple
        chords  = 'NK Cyber'          ,  # analog_dreams · digital/cold
        fx      = dict(cc={}, master={'reverb': ('Hall', 50)}),
    ),
    'Palefen': dict(   # KNIFE palette · Dm 96bpm · laidback
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Acid Bass'      ,  # analog_dreams · acid/303/resonant
        lead    = 'NK Lead India'     ,  # analog_dreams · exotic/solo
        counter = 'Soft Pad 2'        ,  # factory · soft/warm/simple
        chords  = 'NK Cyber'          ,  # analog_dreams · digital/cold
        arp     = 'Cin Strobe Light'  ,  # cinematica · rhythmic/bright
        fx      = dict(cc={}, master={'reverb': ('Hall', 50)}),
    ),
    'Redloam': dict(   # DRONE palette · Em 54bpm · ritual
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Deep Bass'      ,  # analog_dreams · deep/round/sub
        lead    = 'Synth Keys'        ,  # factory · synth/warm
        counter = 'Cin Voices'        ,  # cinematica · choir/wide
        chords  = 'NK VCO Pad'        ,  # analog_dreams · analog/warm
        fx      = dict(cc={}, master={'reverb': ('Hall', 84)}),
    ),
    'Chromehall': dict(   # KOSMIC palette · Gm 100bpm · pushing
        drums   = 'TR-909 Kit'        ,  # factory · house/techno/punchy
        bass    = 'NK Uni Bass'       ,  # analog_dreams · unison/fat/analog
        lead    = 'SR Night City'     ,  # analog_dreams · neon/80s/moody
        counter = 'NK Uni String'     ,  # analog_dreams · analog/strings/unison
        chords  = 'NK Cyber'          ,  # analog_dreams · digital/cold
        fx      = dict(cc={}, master={'reverb': ('Hall', 58), 'delay': ('Delay', 52)}),
    ),
    'Thornfield': dict(   # DRONE palette · Ephr 92bpm · ritual
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Deep Bass'      ,  # analog_dreams · deep/round/sub
        lead    = 'Synth Keys'        ,  # factory · synth/warm
        counter = 'Cin Voices'        ,  # cinematica · choir/wide
        chords  = 'NK VCO Pad'        ,  # analog_dreams · analog/warm
        fx      = dict(cc={}, master={'reverb': ('Hall', 84)}),
    ),
    'Brightwork': dict(   # KOSMIC palette · Ador 116bpm · laidback
        drums   = 'TR-909 Kit'        ,  # factory · house/techno/punchy
        bass    = 'NK Uni Bass'       ,  # analog_dreams · unison/fat/analog
        lead    = 'SR Night City'     ,  # analog_dreams · neon/80s/moody
        counter = 'NK Uni String'     ,  # analog_dreams · analog/strings/unison
        chords  = 'NK Cyber'          ,  # analog_dreams · digital/cold
        fx      = dict(cc={}, master={'reverb': ('Hall', 58), 'delay': ('Delay', 52)}),
    ),
    'Saltcode': dict(   # TECHNO palette · F#m 132bpm · laidback
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Deep Bass'      ,  # analog_dreams · deep/round/sub
        lead    = 'Cin Ghost Pluck'   ,  # cinematica · haunting/delay
        counter = 'NK Whisper Tones'  ,  # analog_dreams · breathy/soft
        chords  = 'NK Poly Uni'       ,  # analog_dreams · analog/unison/warm
        fx      = dict(cc={}, master={'reverb': ('Hall', 44), 'delay': ('Delay', 40)}),
    ),
    'Mirrorlake': dict(   # KOSMIC palette · Fmaj 86bpm · laidback
        drums   = 'TR-909 Kit'        ,  # factory · house/techno/punchy
        bass    = 'NK Uni Bass'       ,  # analog_dreams · unison/fat/analog
        lead    = 'SR Night City'     ,  # analog_dreams · neon/80s/moody
        counter = 'NK Uni String'     ,  # analog_dreams · analog/strings/unison
        chords  = 'NK Cyber'          ,  # analog_dreams · digital/cold
        fx      = dict(cc={}, master={'reverb': ('Hall', 58), 'delay': ('Delay', 52)}),
    ),
    'Nightshift': dict(   # PORTIS palette · Am 60bpm · laidback
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'Trap Synth'        ,  # factory · trap/sub/modern
        lead    = 'Note Piano MC'     ,  # factory · piano/soft
        counter = 'Cin Saint Voice'   ,  # cinematica · choir/sacred
        chords  = 'Juno P13 Str'      ,  # factory · juno/strings/warm
        fx      = dict(cc={}, master={'reverb': ('Hall', 66), 'delay': ('Delay', 46)}),
    ),
    'Stonecircle': dict(   # FOLK palette · Ddor 78bpm · ritual
        drums   = 'Orchestra Kit'     ,  # factory · acoustic/cinematic
        bass    = 'NK Uni Bass'       ,  # analog_dreams · unison/fat/analog
        lead    = 'NK Lead Classic'   ,  # analog_dreams · classic/analog/solo
        counter = 'Cin Voices'        ,  # cinematica · choir/wide
        chords  = 'NK 106 Poly'       ,  # analog_dreams · juno/chorus/warm
        fx      = dict(cc={}, master={'reverb': ('Warm Hall', 72)}),
    ),
    'Acidbath': dict(   # TECHNO palette · Am 130bpm · pushing
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Deep Bass'      ,  # analog_dreams · deep/round/sub
        lead    = 'Cin Ghost Pluck'   ,  # cinematica · haunting/delay
        counter = 'NK Whisper Tones'  ,  # analog_dreams · breathy/soft
        chords  = 'NK Poly Uni'       ,  # analog_dreams · analog/unison/warm
        fx      = dict(cc={}, master={'reverb': ('Hall', 44), 'delay': ('Delay', 40)}),
    ),
    'Winterlight': dict(   # DRONE palette · Cmaj 76bpm · laidback
        drums   = 'Trap Kit'          ,  # factory · trap/modern/punchy
        bass    = 'NK Deep Bass'      ,  # analog_dreams · deep/round/sub
        lead    = 'Synth Keys'        ,  # factory · synth/warm
        counter = 'Cin Voices'        ,  # cinematica · choir/wide
        chords  = 'NK VCO Pad'        ,  # analog_dreams · analog/warm
        arp     = 'JUNO Stab 3'       ,  # factory · juno/stab/bright
        fx      = dict(cc={}, master={'reverb': ('Hall', 84)}),
    ),
}


def for_kit(name):
    """Assignments for a kit name, or an empty dict if none set."""
    return SOUNDS.get(name, {})

