# midi-sketches

Three hand-composed instrumental sketches — drums, bass, and a rhythmic
melody, each as a separate standard MIDI file — pulling from Fever Ray, Kate
Bush, and Radiohead. Independent of the `hw-v2` live-performance rig in this
repo: these are offline `.mid` files to drag into a DAW or play into your own
gear, not part of the Web MIDI control surface.

## Run it

```
cd midi-sketches
pip install -r requirements.txt   # just mido
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
- `pieces/*.py` — the actual composed content: drum cells, basslines, and
  melodic phrases for each piece, assembled into `build()`, plus an optional
  `produce()` for piece-specific humanization/CC automation.

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
