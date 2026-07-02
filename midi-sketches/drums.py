"""General MIDI percussion map (channel 10 / index 9)."""

KICK = 36
KICK_ALT = 35
RIM = 37
SNARE = 38
CLAP = 39
SNARE_ALT = 40
LTOM2 = 41   # low tom (lowest)
CHH = 42     # closed hi-hat
LTOM = 43
PHH = 44     # pedal hi-hat
MTOM = 45
OHH = 46     # open hi-hat
MTOM2 = 47
HTOM = 48
CRASH = 49
HTOM2 = 50
RIDE = 51
CHINA = 52
RIDE_BELL = 53
TAMBOURINE = 54
CRASH2 = 57
COWBELL = 56
SHAKER = 70
CONGA_HI = 63
CONGA_LO = 64
TIMBALE_HI = 65
TIMBALE_LO = 66
AGOGO_HI = 67
AGOGO_LO = 68
CABASA = 69
CLAVES = 75


def choke_hihats(events, closed=CHH, pedal=PHH, open_=OHH):
    """A closed/pedal hi-hat hit should cut off a still-ringing open hi-hat --
    GM doesn't do this automatically (channel 10 notes don't voice-steal by
    default), so shorten any open-hat note that a later closed/pedal hit lands
    inside of."""
    chokes = sorted(e.start for e in events if e.note in (closed, pedal))
    out = []
    for e in events:
        if e.note == open_:
            end = e.start + e.dur
            cut = next((c for c in chokes if e.start < c < end), None)
            if cut is not None:
                e = e._replace(dur=cut - e.start)
        out.append(e)
    return out
