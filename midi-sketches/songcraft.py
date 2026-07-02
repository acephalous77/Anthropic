"""The single home for song-construction helpers that were drifting into
copies across sophia.py, album.py, and stemlib.py (improvement plan phase 3).

The vary_cell register-escape bug appeared twice because these lived in three
places; from here on, one implementation, imported everywhere.
"""

from theory import CHORDS, scale_degree


def voice_into(pitch, lo, hi):
    """Fold a pitch into [lo, hi] by octaves."""
    while pitch < lo:
        pitch += 12
    while pitch > hi:
        pitch -= 12
    return pitch


def fold_into(pitch, lo, hi):
    """Alias with fold-down-first order (identical result for spans >= 12)."""
    while pitch > hi:
        pitch -= 12
    while pitch < lo:
        pitch += 12
    return pitch


def lead_voicing(chord, prev, lo, hi):
    """Voice each chord tone into register, choosing octaves nearest the
    previous voicing (smooth pad movement -- no jumps to distract the ear)."""
    voiced = []
    for i, p in enumerate(chord):
        p = voice_into(p, lo, hi)
        if prev:
            target = prev[min(i, len(prev) - 1)]
            for cand in (p - 12, p, p + 12):
                if lo <= cand <= hi and abs(cand - target) < abs(p - target):
                    p = cand
        voiced.append(p)
    return voiced


def chord_of(root, scale, spec, seventh=False):
    """spec: scale degree (int, diatonic triad; seventh adds the 7th) OR
    (semitones, quality) for a chromatic chord (sus/quartal/borrowed major)."""
    if isinstance(spec, tuple):
        semis, quality = spec
        return [root + semis + iv for iv in CHORDS[quality]]
    degs = (0, 2, 4, 6) if seventh else (0, 2, 4)
    return [scale_degree(root, scale, spec + d) for d in degs]


def chord_root(root, scale, spec):
    return root + spec[0] if isinstance(spec, tuple) else scale_degree(root, scale, spec)


def anchor(events, step_ticks):
    """No dead space: snap any event that drifted to within half a step of the
    loop start back onto beat 1."""
    half = step_ticks // 2
    return [e._replace(start=0) if 0 <= e.start < half else e for e in events]
