# MC-707 Generator: Track Diversity — Diagnostic & Fix Spec

## Context

The toolkit generates short instrumental MIDI clips (drums, bass, rhythmic lead) from Fever Ray / Kate Bush / Radiohead mixture weights, via Euclidean rhythm generation, scale-degree random walks, motif generation with transposition, n-against-4 polymeter, mixed time signatures, and humanization (timing/velocity jitter, swing, CC automation).

**Symptom:** generated tracks sound too similar — either across different mixture ratios, across repeated runs of the same mixture, or both.

**How to use this doc:** this is a diagnose-then-fix pass, not a confirmed bug list. Investigate each item against the actual codebase before assuming it applies — report findings first, then implement fixes only for confirmed issues, in the priority order below. Code blocks under "Fixed" are illustrative patterns, not drop-in code — adapt names/signatures to the real implementation.

This spec ships with `diversity_metrics.py` — a tested, runnable module implementing the acceptance metrics described below. Drop it in alongside the generator and use it as the regression test for every fix.

---

## Priority order (cheapest-to-verify first)

### 1. RNG seeding
- [ ] **Diagnosed** — grep for `random.seed(`, `np.random.seed(`, `Random(` called with a fixed integer. Confirm whether it fires once at import/init vs. per-generation.
  *Symptom if true:* identical mixture + identical run = identical or near-identical output.
- [ ] **Fixed** — seed only when reproducibility is explicitly requested; otherwise draw fresh entropy per generation. Pass an explicit RNG object through the call chain rather than relying on global module state — this also makes parallel/batch generation safe, since global `random` state isn't thread-safe:

  ```python
  def generate_track(mixture, seed=None):
      rng = random.Random(seed)        # None -> OS entropy, fresh each call
      np_rng = np.random.default_rng(seed)
      ...  # pass rng / np_rng down instead of calling the global random module
  ```

### 2. Mixture blending mechanism
- [ ] **Diagnosed** — find where mixture weights (e.g. `{fever_ray: 0.5, kate_bush: 0.3, radiohead: 0.2}`) get applied. Is it a weighted average of continuous parameters (tempo, leap probability, swing%) computed once per track?
  *Symptom if true:* different ratios regress toward a shared "average style" — blending flattens exactly what makes each style distinct, so ratios cluster instead of sounding like distinct hybrids.
- [ ] **Fixed** — move from continuous averaging to structural mixture: assign a dominant parent per section/phrase, sampled proportionally to mixture weight, rather than blending every parameter:

  ```python
  def choose_section_parent(mixture_weights, rng):
      artists, weights = zip(*mixture_weights.items())
      return rng.choices(artists, weights=weights, k=1)[0]

  def generate_arrangement(mixture_weights, section_plan, rng):
      # section_plan e.g. ['intro', 'verse', 'chorus', 'verse', 'outro']
      return [(section, choose_section_parent(mixture_weights, rng))
              for section in section_plan]
  ```
  Each section then pulls its full parameter set (tempo feel, leap probability, swing, harmonic vocabulary) from its assigned parent artist, undiluted, rather than an averaged blend. The mixture ratio controls *how often* each artist wins a section, not how much each parameter is diluted toward a shared mean.

### 3. Scoring/rejection loop target
- [ ] **Diagnosed** — if the corpus-statistics scorer (pitch entropy / n-gram likelihood matching, from the earlier parameter research) is wired in, confirm what it scores candidates against: one fixed target profile per mixture, or something that varies per run?
  *Symptom if true:* every accepted candidate converges toward the same "highest-scoring" instance — the better the scorer works, the less diverse the output.
- [ ] **Fixed** — sample a fresh stochastic target point within the mixture's style envelope per generation, instead of scoring against one fixed centroid:

  ```python
  def sample_target_profile(style_envelope, rng, jitter=0.15):
      # style_envelope: {stat_name: (mean, std)} — the blended style's
      # characteristic corpus statistics (pitch entropy, n-gram
      # likelihood, etc.), derived once from the mixture weights
      return {stat: rng.gauss(mean, std * jitter)
              for stat, (mean, std) in style_envelope.items()}
  ```
  Compute `style_envelope` once per mixture ratio (it's the expensive part); call `sample_target_profile` fresh for every generation so the scorer is chasing a moving point inside the envelope, not the same fixed centroid every time.

### 4. Macro-structure invariance
- [ ] **Diagnosed** — confirm whether song form (phrase count, section order, instrumentation entry order, density/dynamics arc) is fixed by the template, with only note-level content varying.
  *Symptom if true:* tracks read as "the same song" even when notes differ — form is usually what a first listen tracks, more than pitch content.
- [ ] **Fixed** — parameterize structure as a small set of templates (or generative rules) and sample per run, optionally biased by which artist dominates the mixture:

  ```python
  SECTION_TEMPLATES = [
      ['intro', 'verse', 'chorus', 'verse', 'outro'],
      ['intro', 'verse', 'build', 'chorus', 'breakdown', 'outro'],
      ['verse', 'chorus', 'verse', 'chorus', 'outro'],
  ]

  def choose_structure(rng, mixture_weights=None):
      # optionally weight template choice — e.g. Radiohead-heavy
      # mixtures favor templates with a build/breakdown
      return rng.choice(SECTION_TEMPLATES)
  ```

### 5. Motif / rhythm pool size
- [ ] **Diagnosed** — how many seed motifs does the motif generator draw from? How many Euclidean (k,n) pairs does the drum generator cycle through per artist profile?
  *Symptom if true:* humanization varies the surface but the skeleton repeats — "different production, same bones."
- [ ] **Fixed** — generate fresh seed motifs per run instead of drawing from a small fixed library, then filter for well-formedness rather than hand-curating the pool:

  ```python
  def fresh_seed_motif(scale_degrees, length, rng):
      return [rng.choice(scale_degrees) for _ in range(length)]

  def is_well_formed(motif):
      # cheap sanity filter — replace/extend with the corpus-statistics
      # checks from the earlier research (contour variety, no more than
      # N repeated notes in a row, etc.)
      return len(set(motif)) > 1
  ```
  Widen the Euclidean (k,n) candidate set per artist profile the same way — sample from a range rather than a hardcoded shortlist.

---

## Verification: making "diverse" measurable

Listening is necessary but not sufficient. `diversity_metrics.py` (included alongside this spec) implements three pairwise metrics over a batch of generated tracks:

- **`pitch_class_distance`** — Jensen–Shannon divergence between two tracks' 12-bin pitch-class histograms (octave-invariant). 0 = identical distribution.
- **`ioi_distance`** — Jensen–Shannon divergence between inter-onset-interval distributions. Captures rhythmic-skeleton similarity independent of humanization jitter (jitter perturbs individual onsets by a few ms/ticks, not which histogram bin they land in).
- **`ngram_jaccard`** — Jaccard overlap of transposition-invariant pitch-interval n-grams (motif shape reuse). **Inverted relative to the other two: higher = more similar/less diverse.**

`diversity_report(tracks)` runs all pairwise combinations across a batch and returns the means. Smoke-tested against a trivial identical-vs-different case (see the module's `__main__` block) — identical tracks return 0.0 distance / 1.0 jaccard, clearly-different tracks return >0.4 distance / 0.0 jaccard, confirming the metrics discriminate correctly before you point them at real generator output.

**Acceptance test:**
1. Generate N (~20) tracks at a fixed mixture ratio; convert each to `{'notes': [...], 'onsets': [...]}`.
2. Run `diversity_report(tracks)`. Record the baseline.
3. Implement one fix from the priority list above. Re-run the same batch through `diversity_report`.
4. `mean_pitch_class_distance` and `mean_ioi_distance` should rise; `mean_ngram_jaccard_overlap` should fall. If a fix you expected to help doesn't move these numbers, it isn't reaching the part of the pipeline that actually varies between runs — keep looking rather than trusting the fix worked.
5. Repeat across 2–3 mixture ratios to confirm ratios are distinguishable from *each other*, not just internally diverse.

## Suggested order of work

1. Rule out #1 (RNG seeding) — five minutes, may resolve everything on its own.
2. Wire in `diversity_metrics.py` and record a baseline *before* touching anything else.
3. Work through #2–#5 in order, re-running `diversity_report` after each change.
