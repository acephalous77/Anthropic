# Track-diversity diagnosis & fix

Ran the "generated tracks sound too similar" diagnostic against the actual
code. Five suspected causes; **three did not apply** (the architecture already
avoids them) and **two were real**. `diversity.py` measures each dimension as
mean pairwise distance across a batch (higher = more varied) and doubles as a
regression guard.

## Verdicts

| # | Suspected cause | Verdict | Evidence |
|---|---|---|---|
| 1 | RNG seeding | **By design** | Batch drivers pin seeds so the committed library is byte-stable; the CLI already draws fresh entropy with `--seed` omitted. Not a bug. |
| 2 | Mixture blending flattens to an average | **Not present** | No continuous weight-averaging exists. Styles are discrete archetypes; the blend archetypes already assign one parent per part/section. |
| 3 | Scorer converges to one centroid | **Not present** | `_qc()` is a pass/fail degeneracy filter (accepts first clean candidate), not an optimizer toward a target. |
| 4 | Macro-structure fixed per archetype | **CONFIRMED** | Section order/arc/entry hardcoded; `phases` was a fixed default, never randomized. |
| 5 | Small motif/rhythm pool | **CONFIRMED (drums only)** | Melody = fresh rng scale-walk (fine). Drums = hardcoded per-archetype grids; six archetypes rendered a byte-identical beat every seed. |

## Fixes

- **Drums (#5)** — `drumvary.py`: each clip draws its own drum signature from
  its rng (kick syncopation, ghost snares, ornamental rotation/thinning),
  applied consistently across the clip so it still grooves, perturbing only
  existing voices so the kit mapping and grid-length invariant hold. Wired into
  `generator.generate()`; same seed still renders identically.
- **Structure (#4)** — `generator.generate()` now randomizes `phases`
  (`[2,3,4]`) for archetypes that accept it when the caller doesn't pin it, so
  section count/length varies per seed.

## Before → after (mean pairwise distance, N=12 per archetype)

| dimension | before | after |
|---|---|---|
| drum_jac (drum skeleton) | **0.079** | **0.432** |
| struct (macro-form, bpm-independent) | **0.251** | **0.490** |
| pc_js (tonality) | 0.641 | 0.641 |
| ngram_jac (melodic shape) | 0.925 | 0.924 |

pc/ngram were already high (root/scale randomized, motifs freshly walked) and
are unchanged — the fixes touched only the two weak dimensions.

## Still intrinsically low (by archetype character, not a bug)

- `four_floor_glitch` drum/struct stay low — four-on-the-floor house is
  repetitive by genre.
- `fever_radiohead` ioi ~0 — its melody is a continuous 16th-note arpeggio, so
  inter-onset intervals are uniform by design.

Run `python diversity.py --all 20` to re-check; watch that drum_jac and struct
don't silently fall back toward zero.
