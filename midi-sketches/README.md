# midi-sketches

Drums, bass, and rhythmic-melody MIDI clips pulling from Fever Ray, Kate Bush,
and Radiohead, in two flavours:

- **`pieces/`** — three fixed, hand-composed sketches (rendered by `render.py`).
- **`generator.py`** — a *generative* engine (rendered by `generate.py`) that
  builds a fresh, seeded clip on every run from the same stylistic vocabulary.

Independent of the `hw-v2` live-performance rig in this repo: these are
offline `.mid` files to drag into a DAW or play into your own gear, not part
of the Web MIDI control surface.

## Generating fresh clips

```
cd midi-sketches
pip install -r requirements.txt
python generate.py                              # one random clip, random seed
python generate.py --seed 42                     # reproducible -- same seed, same clip
python generate.py --seed 42 --archetype broken_meter
python generate.py --seed 42 --root D --scale dorian --bpm 90
python generate.py --count 6                     # a batch of 6 different clips
```

Each run writes `drums.mid` / `bass.mid` / `melody.mid` / `all.mid` to
`output/generated/seed<N>_<archetype>/` and prints a "spec card" (title, key,
tempo, section count/length) since there's no audio backend here to preview
with.

Four **archetypes** carry the composed pieces' techniques as generators
instead of fixed data — same rhythmic/harmonic vocabulary, different specific
choices (key, tempo, density, contour, section lengths) every time:

- `halftime_drone` (~ `undertow`) — half-time groove, drone bass, angular
  bassline, call-and-response melody.
- `broken_meter` (~ `static_orchard`) — alternating 4/4 + clipped 7/8 bars,
  broken-beat drums, a melodic cry that crosses the bar line.
- `four_floor_glitch` (~ `glass_repeater`) — four-on-the-floor pulse, glitchy
  hi-hats, an n-against-4 phased melodic cell (n is randomly 3, 5, or 7).
- `gated_drama` — Kate Bush's tom-heavy, no-hats/no-cymbals gated-reverb
  groove plus Fever Ray's static drone-bass harmony. See "workable blends"
  below for why this one is deliberately narrower than the other three.

### Workable blends, not an average

Averaging all three artists' traits into every clip risks incoherence — some
traits reinforce each other, some actively fight. `gated_drama` exists to
demonstrate picking a *coherent* subset instead of blending everything at
once:

- **Compatible:** Fever Ray's static/drone harmony pairs naturally with
  Radiohead's non-functional, pedal-point harmony (`halftime_drone` and
  `broken_meter` already lean on this) — both favor harmony that *sits*
  rather than progresses. Kate Bush's tom-and-gated-reverb groove pairs with
  Fever Ray's dark, static bass for the same reason (mood over motion).
- **In tension:** Kate Bush's signature groove drops hi-hats/cymbals entirely
  (toms carry the rhythm); Radiohead's IDM glitch is *built* from hi-hat
  detail. Layering both into one groove just cancels Bush's whole point, so
  `gated_drama` uses toms-only, no hats at all — the same reason
  `four_floor_glitch` doesn't reach for toms.
- **Sequenced, not layered:** Bush's dramatic, wide vocal-leap melodies and
  Fever Ray's narrow, chant-like repetition are close to opposite melodic
  philosophies. Rather than average them into a medium-wide, medium-repetitive
  mush, `gated_drama` keeps a narrow chant (`leap_prob=0.05`) through the
  verse and saves the wide leaps (`leap_prob=0.45`) for one structural bridge
  — in 3/2, with a relative-major lift (Bush's own device, e.g. "Cloudbusting")
  — so the drama reads as an *event* the arrangement builds to, not a
  constant clash with the verse.

**How the generation is constrained ("smart," not random noise):** `palette.py`
holds the actual generative logic, tuned against a research pass on melodic
random-walk design, groove/microtiming practice, and polyrhythm perception --

- `scale_walk` — a scale-degree random walk targeting ~65-80% stepwise
  motion; any leap triggers a forced *post-leap reversal* (a step back the
  other way next move, Narmour-style) instead of wandering; an occasional
  pull back to the starting degree keeps it from drifting off forever.
- `bass_phrase` / `duration_partition` — `scale_walk` over a lopsided
  rhythmic partition of the bar, strong on the downbeat.
- `motif` / `motif_scored` / `render_motif` — a short relative-degree idea,
  generated as several candidates and kept only if it has real melodic
  motion and a smooth `interval_score` (small steps/3rds reward, 7ths and
  leaps beyond an octave penalized) — never a frozen single-pitch motif.
- `motif_invert` / `motif_retrograde` / `motif_augment` / `motif_diminish` /
  `motif_fragment` — thematic-development operators so a repeated section
  (e.g. a "build") varies the motif (inversion, stretched durations, ...)
  instead of transposing the identical shape every bar.
- `resolve_consonance` — a lightweight two-voice filter: where a melody note
  lands on a strong beat against a sounding bass note, nudge it (staying
  in-scale) to the nearest consonant interval if the raw pitch clashes.
- `phase_melody` / `additive_phase_melody` — two ways to generalize
  `glass_repeater`'s fixed 5-step cell: tiling a random 3/5/7-step cell
  against the 16-step bar (drifts out of phase every repeat), or a
  Glass/Reich-style *additive process* where the cell grows by one note each
  repeat. Both respect `min_safe_chunk_steps`, which keeps the fastest
  implied onset spacing above ~100ms — finer than that crosses the
  documented cognitive limit for grouping and reads as texture, not groove.
- `kick_pattern` / `hats_pattern` — Euclidean-rhythm kicks (via `rhythm.py`'s
  Bjorklund implementation) and hi-hat density/glitch patterns, rather than
  fully free-form step-by-step coin flips. `rhythm.EUCLIDEAN_PRESETS` also
  ships named real-world patterns documented by Toussaint (2005) --
  tresillo, cinquillo, bossa nova, Ghanaian fume-fume, a Steve Reich
  signature rhythm -- and `halftime_drone` occasionally reaches for one
  instead of a fully random Euclidean roll.
- `scale_walk`'s stepwise/leap direction is no longer symmetric: small
  intervals are weighted toward *descending* motion and leaps toward
  *ascending* motion, per Vos & Troost's (1989) corpus finding that melodic
  steps tend to fall while leaps tend to rise.

**Groove/production details**, in `humanize.py` and `drums.py` -- revised
after a second research pass specifically on the experimental groove/timing
literature, which overturned an assumption from the first pass:

- **Timing deviation is now 1/f (pink) noise, not independent jitter.**
  Controlled studies (Frühauf/Kopiez/Platz 2013; Davies/Madison/Silva/Gouyon
  2013) found random microtiming does not reliably increase perceived groove
  and often reduces it, while listeners prefer long-range-*correlated*
  timing fluctuations (Hennig, Fleischmann & Geisel 2011, PLOS ONE
  6(10):e26457). `humanize.pink_jitter()` generates a Voss-McCartney 1/f
  series and applies it in time order (so nearby notes drift together,
  rather than scattering independently) with a target standard deviation of
  ~8-18ms depending on part/archetype. Velocity variation is left as
  independent jitter -- the groove finding was specifically about timing.
- **Swing is a tempo-dependent curve, not a fixed percentage.**
  `humanize.sixteenth_swing_pct(bpm)` gives a gentle 16th-note swing that
  loosens at slow tempos (~62%) and straightens toward 50% as tempo rises,
  which is the grid `humanize.swing()` actually shuffles. A separate
  `bur_swing_pct(bpm)` encodes Friberg & Sundström's (2002) *eighth*-note
  beat-upbeat ratio (~2.5-3.5:1 slow, toward 1:1 by ~250-300 BPM); the two
  are kept distinct on purpose -- feeding the eighth-note BUR straight into a
  sixteenth-note swing overstates the shuffle by a whole metric level (a
  regression that briefly slipped in and was caught in review).
- `drums.choke_hihats()` shortens a still-ringing open hi-hat when a later
  closed/pedal hit lands inside it — GM channel 10 doesn't voice-steal this
  automatically, so every rendered drum track gets choked before writing.
- Ghost-note velocities sit in the ~15-35 range (audible but clearly
  subordinate), not just "quieter."

**QC additions** (`analysis.py`): alongside the existing empty-part/
single-pitch/out-of-range checks, `generator._qc` now also rejects a part
whose melodic-interval Shannon entropy is near zero (dominated by one
interval, likely near-static) and every generated clip reports a **Zipf
rank-frequency slope** for its combined pitch content — aesthetically-typical
music tends to cluster near slope -1 on a log-log rank-frequency plot
(Manaris et al. 2005); this is printed informationally, not used to block
generation (the "necessary but not sufficient" caveat from that paper is
taken seriously here). A from-scratch Temperley-style probabilistic melody
model and an IDyOM-trained information-content gate are on the list for a
future pass but not implemented — both need either a training corpus or
more validation than fits in one iteration; treat the current interval
weighting/entropy checks as a lighter-weight approximation of that direction.

`generator.generate()` also runs a lightweight **QC pass** after rendering
(`generator._qc`) — checking for an empty part, a melody/bassline stuck on
one pitch, or a note outside the MIDI range — and regenerates from a derived
sub-seed (up to 5 attempts) if a roll comes out degenerate. The reported
`seed` is always for the attempt that actually shipped, so it's still
reproducible.

## Rendering the fixed pieces

```
cd midi-sketches
python render.py                  # renders all 3 pieces into output/
python render.py undertow         # or render a subset by name
```

Each piece writes four files to `output/<piece>/`:

- `drums.mid` — GM drum-kit channel (10), one track
- `bass.mid` — channel 1, program 38 (Synth Bass 1)
- `melody.mid` — channel 2, program 81 (Lead 2 / sawtooth)
- `all.mid` — all three combined, for quick preview/playback

Nothing here is randomized — the same source always renders the same notes.
To vary a piece, edit its module under `pieces/`.

## The pieces

**`undertow`** — 84 BPM, D aeolian, straight 4/4. A half-time groove
(backbeat on beat 3 instead of 2-and-4) with a syncopated, Radiohead-angular
bassline underneath a Fever Ray-style low drone. The melody answers in long
Kate Bush-ish phrases every other bar, then the whole thing intensifies
through a "build" section and drops back to the drone for the outro.

**`static_orchard`** — 100 BPM, E dorian. Alternates a 4/4 bar with a
clipped 7/8 bar throughout — the metre itself lilts, Kate-Bush style. Bass
sustains a drone through the 4/4 bar and answers with an angular, unresolved
phrase in the 7/8 bar; the melody's exclamation lands off the beat in the 7/8
bar and doesn't resolve until the next bar's downbeat — a phrase that
deliberately crosses the bar line. Snare/kick placement is broken-beat,
Radiohead-style, with glitchy hi-hat gaps in the intensified "build" bars.

**`glass_repeater`** — 122 BPM, F# phrygian. An insistent four-on-the-floor
pulse (Idioteque-ish) with stuttering, dropout hi-hats and a deep,
octave-jumping synth-bass pulse. The melody is a 5-step motif tiled
continuously against the 16-step (4/4) bar — since 16 isn't a multiple of 5,
it drifts a step out of phase with the beat every bar instead of looping in
place: a controlled 5-against-4 polymeter, in the spirit of Kate Bush's
obsessive melodic repetition.

## Production layer

Each piece's `pieces/<name>.py` defines an optional `produce(result, ...)`
hook — called by `render.py` after `arrange.render_piece()` — that shapes the
raw quantized events into something less machine-flat. What each piece does
is a deliberate, per-piece choice, not a blanket effect:

- **`undertow`** — drums stay machine-tight (the Fever Ray precision), but
  bass/melody get subtle timing + velocity jitter (`humanize.jitter`), plus
  a CC11 (expression) swell through the "build" section and a release back
  down through the outro.
- **`static_orchard`** — the hi-hats are swung (`humanize.swing`, delaying
  every other 16th step) for a lilting, not-quite-straight feel; bass/melody
  get the most rubato of the three (Bush-style push-pull); expression swells
  through the "build" pair.
- **`glass_repeater`** — nothing is humanized (the mechanical pulse and the
  exact 5-against-4 phase drift depend on precise tick placement); instead a
  CC74 (brightness/cutoff) sweep opens and closes across
  verse → break → verse2, the classic "the machine is breathing" move.

`undertow`'s verse also alternates a quiet ghost snare into the bars where
the melody rests, so the groove has something happening even during the
call-and-response silences.

## Visualizing without an audio backend

`visualize.py` prints an ASCII step-grid (drums) / event list (bass,
melody) for a piece so you can eyeball the arrangement — note density,
gaps, and whether a section looks like what it's supposed to be — without
needing a synth or DAW to hit play:

```
python visualize.py undertow --section verse --voice drums
python visualize.py glass_repeater
python visualize.py --generated --seed 7 --archetype broken_meter
```

It's a dev tool, not part of the render pipeline. Note: because it buckets
events into fixed 16th-note columns, a note that `humanize.jitter` nudged a
few ticks earlier than a section boundary can appear to spill into the
previous section's printout — that's a display rounding artifact, not an
error in the actual MIDI (the real tick position is unaffected).

## How it's built

- `theory.py` — note names → MIDI numbers, scale/mode tables (aeolian,
  dorian, phrygian, ...), simple chord builder.
- `rhythm.py` — a small Bjorklund/Euclidean rhythm implementation, plus
  `grid_from_hits`/`grid_to_events` to turn step-position sets like
  `{0, 6, 11}` into a 16-character grid string and then into MIDI events.
- `arrange.py` — stacks a piece's sections/bars (each with its own time
  signature and tempo) into absolute-tick event lists for drums/bass/melody.
  All patterns are authored on a fixed 16th-note grid, so a 4/4 bar is 16
  steps and a 7/8 bar is 14 steps.
- `drums.py` — GM percussion note-number constants.
- `midiwriter.py` — writes the resulting event lists out as standard MIDI
  files via `mido` (tempo/time-signature meta events, GM program changes,
  CC automation via `cc_ramp`).
- `humanize.py` — deterministic (seeded) timing/velocity jitter and 16th-note
  swing, used by the per-piece `produce()` hooks below.
- `pieces/*.py` — the fixed pieces' composed content: drum cells, basslines,
  and melodic phrases assembled into `build()`, plus an optional `produce()`
  for piece-specific humanization/CC automation.
- `palette.py` — the generative building blocks (bassline random walk, motif
  generator, phase-melody tiler, Euclidean kick/hat patterns) shared by:
- `generator.py` — the three archetypes (`halftime_drone`, `broken_meter`,
  `four_floor_glitch`), each a function `(rng, root, scale, bpm) -> spec`,
  plus `generate()`, which seeds an attempt, renders it, QCs it, and retries
  from a derived sub-seed if needed.
- `generate.py` / `render.py` — the two CLI entry points, writing `.mid`
  files and printing a summary; otherwise identical in what they produce.

## GM drum map reference (used in `drums.py`)

| Voice | Note | GM name |
|---|---|---|
| KICK | 36 | Bass Drum 1 |
| RIM | 37 | Side Stick |
| SNARE | 38 | Acoustic Snare |
| CLAP | 39 | Hand Clap |
| LTOM2 | 41 | Low Floor Tom |
| CHH | 42 | Closed Hi-Hat |
| LTOM | 43 | Low Tom |
| MTOM | 45 | Low-Mid Tom |
| OHH | 46 | Open Hi-Hat |
| MTOM2 | 47 | Hi-Mid Tom |
| HTOM | 48 | High Tom |
| CRASH | 49 | Crash Cymbal 1 |
| RIDE | 51 | Ride Cymbal 1 |
| COWBELL | 56 | Cowbell |
| SHAKER | 70 | Maracas (used here as shaker) |

## Scope

MIDI note data only — no audio rendering/soundfont playback here. Import
the `.mid` files into a DAW (or play them into hardware) to actually hear
them through your own instruments.
