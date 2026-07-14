"""Diversity metrics for the generator -- is a batch of clips actually varied,
or the same bones with different paint?

The diagnostic (see IMPROVEMENT_PLAN / the track-diversity spec) found the two
real convergence risks are DRUMS (hardcoded per-archetype grids) and
MACRO-STRUCTURE (fixed section order/entry). Melody is already a fresh rng
scale-walk. So this harness measures each dimension SEPARATELY and reports mean
pairwise distance across a batch -- rising distance after a fix = the fix works,
and the same numbers double as a regression guard against silent re-convergence.

    python diversity.py                 # every archetype, N=16, table
    python diversity.py fever_ray 24    # one archetype, N=24
    python diversity.py --all 20        # all archetypes at N=20

Distances are in [0,1]; higher = more diverse. Each is a mean over all
unordered clip pairs in the batch.

  pc_js     pitch-class histogram Jensen-Shannon distance (melody+bass tonality)
  ioi_js    inter-onset-interval histogram JS distance (melody rhythm)
  ngram_jac melody pitch-interval trigram Jaccard distance (melodic shape)
  drum_jac  (voice, step-in-bar) Jaccard distance (the drum skeleton)
  struct    section-count / bar-length / bpm spread (macro-form variety)
"""

import math
import sys
from collections import Counter
from itertools import combinations

import generator
from arrange import STEP_TICKS

BAR_STEPS = 16  # compare drum skeletons on a 16th-note 4/4 grid (approx for odd meters)


def _js_distance(a, b):
    """Jensen-Shannon distance (sqrt of JS divergence, base 2) between two
    Counters treated as distributions. 0 = identical, 1 = disjoint."""
    keys = set(a) | set(b)
    na, nb = sum(a.values()) or 1, sum(b.values()) or 1
    m = {}
    pa = {k: a.get(k, 0) / na for k in keys}
    pb = {k: b.get(k, 0) / nb for k in keys}

    def kl(p, q):
        s = 0.0
        for k in keys:
            if p[k] > 0 and q[k] > 0:
                s += p[k] * math.log2(p[k] / q[k])
        return s

    mid = {k: (pa[k] + pb[k]) / 2 for k in keys}
    div = 0.5 * kl(pa, mid) + 0.5 * kl(pb, mid)
    return math.sqrt(max(0.0, min(1.0, div)))


def _jaccard_distance(a, b):
    a, b = set(a), set(b)
    if not a and not b:
        return 0.0
    return 1.0 - len(a & b) / len(a | b)


# ---- per-clip feature extraction from a generate() result -----------------
def _features(gen):
    r = gen["result"]
    mel = sorted(r["melody"], key=lambda e: e.start)
    bass = r["bass"]
    pitches = [e.note for e in mel]

    pc = Counter(e.note % 12 for e in mel + bass)

    onsets = sorted({e.start for e in mel})
    iois = [onsets[i] - onsets[i - 1] for i in range(1, len(onsets))]
    # bucket IOIs to the nearest 16th so tiny humanization jitter doesn't count
    ioi_hist = Counter(round(d / STEP_TICKS) for d in iois)

    intervals = [pitches[i] - pitches[i - 1] for i in range(1, len(pitches))]
    trigrams = {tuple(intervals[i:i + 3]) for i in range(len(intervals) - 2)}

    drum = {(e.note, round(e.start / STEP_TICKS) % BAR_STEPS) for e in r["drums"]}

    bounds = r.get("section_bounds", [])
    n_sections = len(bounds)
    total_ticks = bounds[-1]["end"] if bounds else 0
    # macro-form fingerprint, deliberately bpm/key-INDEPENDENT: how many
    # sections and how long the whole form runs (in bars, not seconds)
    struct = (n_sections, round(total_ticks / (STEP_TICKS * BAR_STEPS)))
    return {"pc": pc, "ioi": ioi_hist, "trig": trigrams, "drum": drum, "struct": struct}


def measure(archetype, n=16, seed_base=1000):
    feats = []
    for i in range(n):
        gen = generator.generate(seed=seed_base + i, archetype=archetype)
        feats.append(_features(gen))
    pairs = list(combinations(range(n), 2))

    def mean(fn):
        return sum(fn(feats[i], feats[j]) for i, j in pairs) / len(pairs)

    pc = mean(lambda x, y: _js_distance(x["pc"], y["pc"]))
    ioi = mean(lambda x, y: _js_distance(x["ioi"], y["ioi"]))
    ng = mean(lambda x, y: _jaccard_distance(x["trig"], y["trig"]))
    dr = mean(lambda x, y: _jaccard_distance(x["drum"], y["drum"]))
    # macro-form spread: section-count differs (weight .5) + form-length
    # differs by >1 bar (weight .5) -- bpm/key deliberately excluded
    def _struct(x, y):
        sx, sy = x["struct"], y["struct"]
        return 0.5 * (sx[0] != sy[0]) + 0.5 * (abs(sx[1] - sy[1]) > 1)
    struct = mean(_struct)
    return {"pc_js": pc, "ioi_js": ioi, "ngram_jac": ng, "drum_jac": dr, "struct": struct}


def _row(name, m):
    return (f"  {name:<18} pc={m['pc_js']:.3f}  ioi={m['ioi_js']:.3f}  "
            f"ngram={m['ngram_jac']:.3f}  drum={m['drum_jac']:.3f}  struct={m['struct']:.3f}")


def main(argv):
    args = [a for a in argv if a != "--all"]
    n = next((int(a) for a in args if a.isdigit()), 16)
    named = [a for a in args if not a.isdigit()]
    archetypes = named if named else list(generator.ARCHETYPES)

    print(f"diversity over N={n} clips per archetype "
          f"(higher = more diverse; drum & struct are the diagnosed weak spots)\n")
    agg = Counter()
    for a in archetypes:
        m = measure(a, n)
        print(_row(a, m))
        for k, v in m.items():
            agg[k] += v
    if len(archetypes) > 1:
        mean_m = {k: agg[k] / len(archetypes) for k in agg}
        print("  " + "-" * 68)
        print(_row("MEAN", mean_m))


if __name__ == "__main__":
    main(sys.argv[1:])
