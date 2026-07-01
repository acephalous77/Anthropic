"""Note names, scales, and chords -> MIDI note numbers."""

NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]

SCALES = {
    "major": (0, 2, 4, 5, 7, 9, 11),
    "aeolian": (0, 2, 3, 5, 7, 8, 10),      # natural minor
    "dorian": (0, 2, 3, 5, 7, 9, 10),
    "phrygian": (0, 1, 3, 5, 7, 8, 10),
    "minor_pentatonic": (0, 3, 5, 7, 10),
}

CHORDS = {
    "maj": (0, 4, 7),
    "min": (0, 3, 7),
    "min7": (0, 3, 7, 10),
    "maj7": (0, 4, 7, 11),
    "sus4": (0, 5, 7),
    "5": (0, 7),
}


def note(name, octave):
    """note('D', 3) -> MIDI number. C4 == 60 (middle C)."""
    idx = NOTE_NAMES.index(name)
    return (octave + 1) * 12 + idx


def scale_degree(root, scale, degree, octave_shift=0):
    """Pick a scale tone by degree (0-indexed, can exceed len(scale) to climb octaves)."""
    intervals = SCALES[scale]
    span = len(intervals)
    octave, step = divmod(degree, span)
    return root + intervals[step] + 12 * (octave + octave_shift)


def chord(root, quality):
    return [root + iv for iv in CHORDS[quality]]


def note_in_range(name, lo, hi):
    """The MIDI number for `name` in whichever octave lands closest to the middle of [lo, hi]."""
    target = (lo + hi) / 2
    candidates = [note(name, o) for o in range(-1, 10)]
    candidates = [n for n in candidates if lo <= n <= hi] or candidates
    return min(candidates, key=lambda n: abs(n - target))
