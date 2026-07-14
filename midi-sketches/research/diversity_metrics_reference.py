"""
diversity_metrics.py

Standalone diversity/similarity metrics for evaluating generated MIDI
tracks from the MC-707 generative toolkit. Architecture-agnostic — only
needs pitch and onset-time sequences, not the generator's internal
representations.

Usage:
    from diversity_metrics import diversity_report

    tracks = [
        {'notes': [60, 62, 64, 65, ...], 'onsets': [0.0, 0.5, 1.0, ...]},
        ...
    ]
    report = diversity_report(tracks)
    print(report)

Dependencies: numpy, scipy
"""

from itertools import combinations
import numpy as np
from scipy.spatial.distance import jensenshannon


# ---------------------------------------------------------------------------
# Pitch-class histogram distance
# ---------------------------------------------------------------------------

def pitch_class_histogram(notes):
    """notes: list/sequence of MIDI pitch integers. Returns a normalized
    12-bin pitch-class histogram (octave-invariant)."""
    hist = np.zeros(12)
    for pitch in notes:
        hist[int(pitch) % 12] += 1
    total = hist.sum()
    return hist / total if total > 0 else hist


def pitch_class_distance(notes_a, notes_b):
    """Jensen-Shannon divergence between two tracks' pitch-class
    distributions. 0 = identical distribution, larger = more different."""
    eps = 1e-10
    h_a = pitch_class_histogram(notes_a) + eps
    h_b = pitch_class_histogram(notes_b) + eps
    return float(jensenshannon(h_a, h_b))


# ---------------------------------------------------------------------------
# Inter-onset interval (IOI) distribution distance
# ---------------------------------------------------------------------------

def iois(onset_times):
    """onset_times: sequence of note onset times (beats or ticks, any
    consistent unit). Returns sorted inter-onset intervals."""
    times = np.sort(np.asarray(onset_times, dtype=float))
    return np.diff(times)


def ioi_histogram(onset_times, bin_range=(0.0, 4.0), n_bins=32):
    """Normalized IOI histogram. Default range covers up to a whole note
    at IOI=4 beats; widen bin_range if your generator uses longer gaps."""
    intervals = iois(onset_times)
    bins = np.linspace(bin_range[0], bin_range[1], n_bins + 1)
    hist, _ = np.histogram(intervals, bins=bins, density=False)
    total = hist.sum()
    return hist / total if total > 0 else hist


def ioi_distance(onsets_a, onsets_b, **hist_kwargs):
    """Jensen-Shannon divergence between two tracks' IOI distributions —
    captures rhythmic-skeleton similarity independent of humanization
    jitter (jitter perturbs individual onsets by a few ms/ticks, not
    which histogram bin they land in)."""
    eps = 1e-10
    h_a = ioi_histogram(onsets_a, **hist_kwargs) + eps
    h_b = ioi_histogram(onsets_b, **hist_kwargs) + eps
    return float(jensenshannon(h_a, h_b))


# ---------------------------------------------------------------------------
# Pitch-interval n-gram Jaccard overlap
# ---------------------------------------------------------------------------

def pitch_interval_ngrams(notes, n=3):
    """Transposition-invariant n-grams of melodic intervals (differences
    between consecutive pitches), so the same motif shape in a different
    key still counts as a match."""
    notes = list(notes)
    intervals = [b - a for a, b in zip(notes, notes[1:])]
    if len(intervals) < n:
        return set()
    return {tuple(intervals[i:i + n]) for i in range(len(intervals) - n + 1)}


def ngram_jaccard(notes_a, notes_b, n=3):
    """Jaccard similarity of interval n-gram sets. 0 = no shared motif
    shapes, 1 = identical sets. NOTE: unlike the two distance metrics
    above, HIGHER jaccard means MORE similar/LESS diverse — don't average
    it in the same direction as the others without flipping the sign."""
    set_a = pitch_interval_ngrams(notes_a, n)
    set_b = pitch_interval_ngrams(notes_b, n)
    if not set_a or not set_b:
        return 0.0
    return len(set_a & set_b) / len(set_a | set_b)


# ---------------------------------------------------------------------------
# Batch diversity report
# ---------------------------------------------------------------------------

def diversity_report(tracks, n_gram=3, ioi_hist_kwargs=None):
    """
    tracks: list of dicts, each with:
        'notes'  — list of MIDI pitch ints in performance order
        'onsets' — list of onset times, same length as 'notes'
    Computes all pairwise metrics across the batch and returns means.

    Read the result as: pitch_class and ioi distances should RISE after a
    fix; ngram_jaccard_overlap should FALL. If pitch_class/ioi distances
    stay near 0 or jaccard overlap stays near 1 after a fix you believed
    should help, the fix isn't reaching the part of the pipeline that
    actually varies between runs.
    """
    ioi_hist_kwargs = ioi_hist_kwargs or {}
    pc_dists, ioi_dists, jaccards = [], [], []

    for a, b in combinations(tracks, 2):
        pc_dists.append(pitch_class_distance(a['notes'], b['notes']))
        ioi_dists.append(ioi_distance(a['onsets'], b['onsets'], **ioi_hist_kwargs))
        jaccards.append(ngram_jaccard(a['notes'], b['notes'], n=n_gram))

    return {
        'n_tracks': len(tracks),
        'n_pairs': len(pc_dists),
        'mean_pitch_class_distance': float(np.mean(pc_dists)) if pc_dists else None,
        'mean_ioi_distance': float(np.mean(ioi_dists)) if ioi_dists else None,
        'mean_ngram_jaccard_overlap': float(np.mean(jaccards)) if jaccards else None,
    }


# ---------------------------------------------------------------------------
# Smoke test — run directly to sanity-check the metrics behave as expected
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    identical = {'notes': [60, 62, 64, 65, 67, 65, 64, 62],
                 'onsets': [0, 0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 3.5]}
    identical_copy = dict(identical)
    different = {'notes': [48, 55, 51, 58, 53, 60, 46, 57],
                 'onsets': [0, 0.75, 1.25, 1.6, 2.3, 2.9, 3.4, 3.9]}

    print("identical vs identical_copy (expect ~0 distance, ~1 jaccard):")
    print(diversity_report([identical, identical_copy]))

    print("\nidentical vs different (expect higher distance, lower jaccard):")
    print(diversity_report([identical, different]))
