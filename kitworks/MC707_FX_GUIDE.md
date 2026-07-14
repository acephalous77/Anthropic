# MC-707 setup guide — tones, knobs, filter/FX/compression

How to make the kits sound good and sound *different* on the 707. Every kit
ships a one-page `FX_SETUP.txt` card (in its `output/` folder and on the SD
card) with the concrete numbers; this is the manual behind them.

> **Verified vs. tuned.** The mechanics (one tempo per project, per-clip tones,
> pack/project folders, the CC map, signal flow) are researched and sourced.
> The *values* (cutoff points, MFX drive, ratios, sends) are musically
> defensible starting points — turn them to taste. MFX type names are real 707
> types; the exact on-screen wording may differ slightly by firmware.

## 0. The two things that made kits sound the same / wrong

1. **Tones.** An imported clip plays through its **track's assigned tone** — the
   707 ignores the SMF's program/channel bytes. So all 33 kits played through
   the same 8 tones. Fix: each kit's card has a **TONES** recipe (a distinct
   patch per track). The 707 can hold a **different tone per clip** on one track
   — set the track's tone scope to **CLP** (the TRK/CLP indicator, top-right of
   the tone edit screen), and each kit's clip keeps its own sound. So one
   project can carry all 33 kits, each sounding like itself.
2. **Tempo.** The 707 has **one global tempo per project** and does **not** read
   an imported clip's tempo. The "184 on every song" was your project's stored
   tempo, not a file bug (every clip file carries its correct tempo). **Set the
   project tempo per kit** (each card states it). Kits at different tempos that
   must play in one set belong in **separate projects** — there is no per-clip
   tempo.

## 1. Signal flow

```
tone → FILTER/MOD/FX/SOUND knob macros → insert MFX (per track) →
Delay send + Reverb send → Master → Total MFX → Total Comp → Total EQ → out
```

## 2. Fixed knob scheme (same on every track)

Bind under `[SHIFT]+[KNOB ASSIGN]`. Cutoff, coarse tune, release on **all**
tracks; only the 4th knob's target changes per part.

| Knob | Controls | CC | Start |
|---|---|---|---|
| **FILTER** | Cutoff | CC80 (or direct CC74) | 90 |
| **MOD** | Coarse Tune | CC81 (bind internally — no direct CC) | 64 (=0 st) |
| **FX** | MFX depth *or* a send (per part) | CC82 | 40 |
| **SOUND** | Release | CC83 (or direct CC72) | 64 |

The FX knob is MFX-depth on drums/bass, **delay send** on lead/counter/arp,
**reverb send** on chords — each card says which.

## 3. Per-track insert MFX / sends / EQ (tuned per feel)

Each card lists, per track, the specific **insert MFX** (with the thematic
distortion/delay/chorus and its params), **delay + reverb send** amounts, and an
**EQ tilt** — different for PUSHING / LAIDBACK / RITUAL. Highlights:

- **Bass** — Overdrive (acid bite) / Warm Saturator / Tone Fattener by feel.
- **Lead** — Stereo Delay (synced) / Tape Echo (dub) / Reverse Delay (cavern).
- **Chords** — JUNO Chorus → reverb wash, deeper and wetter as the feel darkens.
- **Drums** — Overdrive glue / Phonograph vinyl / Distortion grit.

## 4. Master bus (set once per feel)

`[SHIFT]+[MULTI]` → Comp / EQ / MFX tabs. Each card gives Total Comp
(ratio/attack/release/threshold/makeup), 3-band Total EQ, and a Total MFX
suggestion — punchy glue for pushing, transparent for laidback, slow weight for
ritual.

## 5. Motion (the arrangement's filter/reverb arc)

Automatable CCs only — **CC74 cutoff, CC91 reverb, CC11 expression**. Intro
filtered → opens to peak → slams shut + drenches in the break → settles on the
end. Two ways on: `usb_feed.py <clip> --fx --feel <feel>` streams it so a
live-record pass captures it as motion (fw 1.8), or ride the FILTER knob per
column. The song previews in `songs/` embed it so you can hear it in a DAW.
(SMF import may bring only notes, so motion = live-record or by hand.)

## 6. Loading your packs, samples, and projects (needs the SD card / your Mac)

Researched folder homes on the MC-707 SD card (function solid; exact casing
community-reported):

- **ZEN-Core sound packs** — buy/download in **Roland Cloud Manager**, copy the
  `.svz` / `.sdz` to the card's **`SOUND`** folder, then load in-unit via
  `[SOUND]` → sound-file browser. (`.sdz` packs are license-locked to your
  account.)
- **Samples / WAV packs** — `.wav` into the **`SAMPLE`** folder, import in-unit,
  assign to a looper track or drum-kit partials.
- **Projects (factory / purchased `.mpj`)** — drop the `.mpj` into the
  **`PROJECTS`** folder and it appears in the load list. The `.mpj` format is
  undocumented and **unwritable by tools**, so I can place/rename existing ones
  but cannot author new projects.

These live in your `/downloads` on your Mac — **this cloud session can't reach
them.** Run the session on your machine (`claude --teleport`) and I'll copy the
right files into the right SD folders and point each kit's TONES recipe at your
actual pack patches.

## 7. About the song files and the 8-track limit

The 707 has **exactly 8 tracks**, and SMF import is **one file → one clip**
(a multi-track SMF is flattened onto a single clip). So the multi-track files in
`songs/` are **DAW previews only** — do not import them into the 707 expecting
separate tracks. On the 707 you build a kit from its per-clip SD files
(`sd/.../T<n>_<PART>_<section>.MID`), one clip per track, ≤6 tracks per kit.
