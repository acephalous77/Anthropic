# Research archive — cross-project reference

Four documents from sibling Claude Code conversations, kept here for
reference, each reconciled against what this repo actually implements. They
are **reference, not active code** — nothing here is imported.

## diversity-fix-spec.md
The diagnostic spec for the generator's "tracks sound too similar" problem.
**Status: executed.** See `../DIVERSITY_FINDINGS.md`. Three of five suspected
causes did not apply (no continuous mixture-averaging, the QC pass is a filter
not an optimizer, fixed batch seeds are deliberate). Two were real and fixed:
drum convergence (`../drumvary.py`) and macro-structure (`phases` randomized in
`generator.generate`). Measured drum-skeleton diversity 0.079 -> 0.432.

## diversity_metrics_reference.py
A numpy/scipy implementation of three pairwise metrics (pitch-class JS, IOI JS,
interval-ngram Jaccard). **Superseded here by `../diversity.py`**, which
implements the same three **dependency-free** and adds the two that actually
caught the bug — a drum-skeleton Jaccard and a bpm-independent macro-form
metric. We did not adopt the scipy dependency.

## transcription-transfer-techniques.md
Techniques lifted from a transcription pipeline. Reconciliation:
- **K-K tonal-hierarchy weighting (its headline §2)** targets a *key-aware*
  melodic walk. This toolkit's `palette.motif` walk is deliberately
  *scale-agnostic* (degree offsets rendered onto any key later), so K-K
  weighting does not drop into the melody path without restructuring. Where
  K-K *does* fit cleanly is analysis — see below.
- Metric-accent velocity (§5) and per-part register/Euclidean variation (§6):
  already present (hand-written drum velocities, `apply_accents_metered`,
  per-archetype roots/scales/bpm, and `drumvary`'s per-clip Euclidean-style
  drum variation).
- Demucs / Basic-Pitch / reverb-limits (§9): analysis-only, correctly flagged
  as non-transferable.

## midi_analysis_reference.py
A richer measurement instrument (K-K `tonal_clarity`, `near_duplicate_pairs`).
Reconciliation:
- `near_duplicate_pairs` is already covered by `../mine.py`'s farthest-point
  selection (it actively spreads the picked set, not just flags collapse).
- The K-K `tonal_clarity` idea *was* lifted: `../keycheck.py` reimplements K-K
  key-finding dependency-free and audits every kit — does it assert its labeled
  tonic, and stay in its scale? All 11 hand-composed kits (23-33) pass clean;
  the older kits it flags carry deliberate chromatic color (lydian #4, blue
  notes, harmonic-minor 7ths), which is exactly what the tool should surface.
