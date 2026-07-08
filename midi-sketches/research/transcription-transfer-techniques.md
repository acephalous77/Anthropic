# Transferable techniques: transcription pipeline → generative MIDI toolkit

**For:** local Claude Code, implementing against the existing MC-707 generative toolkit.
**Companion file:** `midi_analysis.py` (tested; the measurement instrument this doc leans on).
**Relationship to existing work:** this complements the `mc707-generator-diversity-fix.md`
track — it supplies the *measurement* that a diversity fix needs to be verifiable, plus a
few generative primitives lifted from the transcription side. It does not assume that doc's
internals; reconcile overlaps as you go.
**Instruction to the implementer:** these are architecture-agnostic techniques, not patches.
Adapt every signature to the toolkit's actual module layout. Where a technique names a
function, treat it as an interface to fit into existing code, not a file to drop in verbatim.

---

## 0. The one idea that matters

The transcription pipeline is an **analyzer**. The generator has a **diversity/entropy
problem currently tuned by ear**. The single highest-value transfer is to point the
analyzer at the generator's *output* and turn it into an **objective function**:

> generate → measure with `midi_analysis.py` → read diversity numbers → tune parameters → repeat

`diversity_report(tracks)` features each generated track and measures how *different* the
tracks are from each other. High mean pairwise distance = varied output. The minimum pair is
the collapse risk; `near_duplicate_pairs` names the offenders. This directly instruments the
stated problem ("tracks come out too samey") instead of arguing about it by listening.

**Hard caveat — do not skip.** Statistical distance is a *necessary-not-sufficient* proxy.
Two tracks can share an identical pitch-class histogram and sound completely different (order,
register, articulation). Use these numbers as a diagnostic and a *loose* target, never as
ground truth for "these sound different." Optimizing the proxy hard is textbook Goodhart. The
metric's job is to catch collapse and quantify trends, not to certify musicality.

Sanity check that the instrument is meaningful: in testing it flagged a C-major track and an
A-minor track as tonal near-duplicates (JSD ≈ 0.03) — correct, because relative major/minor
share a pitch-class set. It is measuring something musical, not just counting notes.

---

## 1. Reframe of the diversity problem

Two independent causes usually hide behind "everything sounds the same":

1. **Under-parameterized generation** — too few *axes of variation*. If every track draws
   from the same scale, register, grid, and velocity logic, statistical collapse is
   guaranteed regardless of RNG seed.
2. **Unmeasured generation** — no objective read on whether a change actually increased
   variety.

The techniques below attack both: several add new axes of variation; `midi_analysis.py`
supplies the measurement to confirm they landed. Fixing (2) without (1) just measures the
collapse precisely; fixing (1) without (2) is back to guessing.

---

## 2. Transferable technique — tonal-hierarchy-weighted pitch selection

**Source:** the transcriber's Krumhansl–Kessler key profiles.
**Problem it solves:** a naive scale-degree random walk treats all degrees as equiprobable,
which sounds aimless and, paradoxically, *not* diverse (it wanders without ever resolving).

**Mechanism.** At each step, weight candidate next-pitches by the product of three factors:

```
P(next) ∝ interval_prior(next | current)      # prefer stepwise / small leaps
        × kk_weight(scale_degree(next))        # tonal-hierarchy pull toward stable degrees
        × temperature_term                     # entropy knob
```

The K–K weight makes tonic/dominant/mediant land more often and passing tones pass through.
Critically this gives a **principled entropy control**: interpolate the distribution toward
uniform for more surprise, toward K–K-weighted for more tonal gravity. That is a cleaner
diversity knob than flat randomness, because it varies *character*, not just noise.

**Reference (adapt to the walk's state model):**

```python
import numpy as np
KK = {"major": np.array([6.35,2.23,3.48,2.33,4.38,4.09,2.52,5.19,2.39,3.66,2.29,2.88]),
      "minor": np.array([6.33,2.68,3.52,5.38,2.60,3.53,2.54,4.75,3.98,2.69,3.34,3.17])}

def choose_next(current_pitch, tonic, mode, temperature=1.0, leap_sigma=3.0, rng=None):
    rng = rng or np.random.default_rng()
    cands = np.arange(current_pitch - 12, current_pitch + 13)
    interval = np.exp(-((cands - current_pitch) ** 2) / (2 * leap_sigma ** 2))
    kk = KK[mode][(cands - tonic) % 12]
    logits = (np.log(interval + 1e-9) + np.log(kk + 1e-9)) / max(temperature, 1e-3)
    p = np.exp(logits - logits.max()); p /= p.sum()
    return int(rng.choice(cands, p=p))
```

Verify with `track_features(...)["pc_entropy"]` and `["tonal_clarity"]`: raising
`temperature` should raise pc_entropy and lower tonal_clarity, monotonically. If it doesn't,
the weighting isn't wired correctly.

---

## 3. Transferable technique — scale-distance as a bidirectional primitive

**Source:** the transcriber's `snap_pitch_to_scale` (nearest in-scale pitch, capped).
**Insight:** the same distance-to-scale primitive runs both directions. Snap *in* cleans
transcription garbage; a controlled *leak out* adds color to generation.

Implement one function, two uses: a `scale_leak(pitch, scale_pcs, p_leak, max_shift)` that,
with probability `p_leak`, nudges an in-scale note to an adjacent chromatic neighbour.

**Honesty on ranking:** this is a *minor* diversity lever and it needs taste — random
out-of-scale notes read as wrong, not adventurous. Rank it *below* the bigger axes in §6.
Ship it as a small, low-`p_leak` knob, not a headline fix.

---

## 4. Transferable technique — unified grid model (quantize ↔ humanize as one axis)

**Source:** the transcriber's `quantize_time(t, bpm, subdivision, strength, phase)`.
**Insight:** quantization and humanization are the same operation at opposite signs. The
toolkit already humanizes; adopt this parameterization so grid-affinity is one continuous
control plus two axes it may currently ignore:

- **`phase`** — a groove-pocket offset. A small negative/positive phase makes a part sit
  laid-back or pushed. This is expressive feel the generator probably isn't exploiting.
- **`subdivision`** — per-part grid resolution (16th vs. triplet), which is the natural home
  for the existing polymeter / mixed-meter / n-against-4 work. Different parts on different
  subdivisions is itself an axis of variation.

Model grid-affinity as `strength ∈ [−h, 1]`: `1` = hard quantize, `0` = raw, negative =
humanized jitter of magnitude `h`. One knob spanning tight-to-loose.

---

## 5. Transferable technique — metric-accent velocity

**Source:** the transcriber derived velocity from the onset-strength envelope (velocity as a
*shaped* signal, not constant, not pure noise).
**Generative dual:** derive velocity from **metric position**, not `random.randint`. Strong
beats accent, weak subdivisions ghost, with a small jitter on top. This matters most on
drums (the 707's home turf) and is what separates "programmed" from "quantized robot."

```python
def metric_velocity(grid_slot, subdivision, accents=(0,), base=64, accent=40, ghost=-20,
                    jitter=6, rng=None):
    rng = rng or np.random.default_rng()
    v = base + (accent if grid_slot % subdivision in accents else ghost)
    return int(np.clip(v + rng.integers(-jitter, jitter + 1), 1, 127))
```

An accent *template* per part (which slots are strong) is another cheap variation axis.

---

## 6. The diversity axes, ranked

For the samey-tracks problem specifically, vary these **per track**, biggest lever first:

1. **Mode / scale** (major/minor/modal/whole-tone/octatonic) — largest tonal-JSD mover.
2. **Register window** (pitch range per part) — big perceptual difference, trivially cheap.
3. **Rhythmic subdivision + Euclidean parameters** (pulses/steps/rotation per voice) —
   largest rhythmic-JSD mover.
4. **K–K temperature** (§2) — varies tonal focus without changing key.
5. **Metric-accent template** (§5) — varies feel/groove.
6. **Grid phase** (§4) — subtle pocket variation.
7. **Scale-leak** (§3) — minor colour, use sparingly.

Then run `diversity_report` across the batch and confirm `tonal_diversity` and
`rhythmic_diversity` means rise and `near_duplicate_pairs` empties. This is the loop.

---

## 7. Shared infrastructure (not a lesson, but reusable)

- **GM ↔ MC-707 kit mapping.** The transcriber's drum classifier maps roles → GM notes; the
  generator needs the same map to emit 707-addressable drums. Factor it into one shared
  module so both directions use it.
- **Role-conditioned drum logic.** Transcription showed resolution lives in per-piece
  separation (kick/snare/hat/tom/cymbal have distinct rhythmic grammars). If drum generation
  runs one Euclidean pattern across the kit, split it: complementary metric slots for
  kick/snare, subdivision-fill for hats, sparse accents for cymbals/toms.

---

## 8. Light / on-aesthetic — generative detune & pitch-bend

The transcriber captured pitch bends because the reference material (Fever Ray) detunes
deliberately. The generative dual is an expressive layer: subtle micro-detune on pads,
portamento on bass, emitted as MIDI pitch-bend (707 supports it; ties into the VT-4 CC work).
Secondary priority, but squarely on-aesthetic for /lla B/.

---

## 9. What does NOT transfer (so no effort is wasted here)

- **Demucs / stem separation** — analysis-only; no generative relevance.
- **Basic Pitch / AMT models** — audio→note inference; irrelevant to generation.
- **The "reverb/formant isn't MIDI-representable" point** — a transcription *limit*, not a
  generation concern. (If anything the generator has the inverse freedom: it authors the
  synth layer directly.)

Do not try to force these into the toolkit.

---

## 10. Suggested implementation order

1. **Wire in `midi_analysis.py` as a test harness** first — a script that runs the generator,
   dumps N tracks, and prints `diversity_report`. Nothing else is verifiable without it.
2. **K–K-weighted pitch selection (§2)** — biggest single quality lever; expose `temperature`.
3. **Per-track axis variation (§6, items 1–3)** — mode, register, Euclidean params.
4. **Metric-accent velocity (§5)** and **grid phase/subdivision (§4)**.
5. **Scale-leak (§3)** and **generative detune (§8)** last, as small knobs.

After each step, re-run the harness and record the diversity numbers. If a change doesn't move
them (or moves them the wrong way), it isn't doing what you think — that feedback is the whole
point of building the instrument first.
