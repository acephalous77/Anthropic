# husband & wife — user guide

Two complementary tools for the MC-707 / VT-4 / Keystep rig:

- **v1** (`hw-707-control.html`) — hands-on control surface: transport, scenes, faders, X-Y, pads.
- **v2** (`hw-v2/`) — generative engine: Euclidean rhythms, LFO CC sweeps, and a clock-locked VT-4 harmony driver.

They run side by side; the v2 header links to v1.

---

## 0. One-time setup

**Browser:** Chrome or Edge on desktop only (Web MIDI doesn't exist in Safari/Firefox).

**Launch:** ES modules don't load from `file://`, so serve the folder once:

```
cd <repo>
python3 -m http.server 8080
```

- v1 → `http://localhost:8080/hw-707-control.html`
- v2 → `http://localhost:8080/hw-v2/`

The "v1 control surface ↗" link in the v2 header opens v1 in a new tab.

**Cabling (the 707 owns the tempo):**

| Cable | From → To | Carries |
|---|---|---|
| USB | 707 ↔ computer | clock out + control in |
| USB | Keystep → computer | notes for follow mode |
| 5-pin | 707 OUT1 → Keystep IN | clock to Keystep |
| 5-pin | Keystep OUT → 707 IN | notes / arp into 707 |
| 5-pin | 707 OUT2 → VT-4 IN | harmony notes |

**Audio:** condenser mic → VT-4 rear XLR (phantom **ON**) → VT-4 L OUT (wet) + R OUT (dry/bypass) → 707 EXT IN L/R. On the 707: `SHIFT+INPUT` → EXT IN type = **LINE**. (The R/BYPASS jack carries the dry vocal — route it to one side of the looper to capture dry while monitoring wet.)

**On the 707:** set each track's Rx channel (`SHIFT+TRACK SEL`), `Control Rx = ON` (so scene Program Changes land), and `TxUSB MIDI = ON` (so it shows up as a port and sends clock).

---

## 1. v1 — control surface

- **Output** (top right): pick the 707 port.
- **Transport:** Start / Continue / Stop / Panic (all-notes-off).
- **Scenes:** 16 buttons send Program Change on the chosen channel → launches 707 clips/scenes.
- **Tracks (×8):** FILTER / MOD / FX / SOUND faders on **CC 80/81/82/83**, plus two **Matrix** slots — type any CC number you've mapped in the 707's Matrix Control and the fader sends it. Each strip has its own channel selector.
- **X-Y Blend:** drag to send two CCs at once (default CC 80/81); set the CC numbers and channel below the pad.
- **Pads:** one-octave keyboard; choose channel, octave, velocity.

v1 is the control layer only — notes, Program Change, transport, CC. No patch editing (that's the box itself or the B67 editor).

---

## 2. v2 — generative engine

### Header / transport
- **OUT / CLOCK IN / KEYS IN** — three port pickers, auto-detected by name (Roland → OUT + CLOCK, Arturia → KEYS). Override anytime.
- **BPM + tap**, **Clock: INTERNAL | SLAVE** (slave follows the 707's MIDI clock), **SUB** (step resolution), **START / STOP**, **PANIC**.
- State auto-saves to the browser and restores on reload — no save/load buttons.

### Euclidean (amber, left) — `+ ADD VOICE` (up to 8)
Each voice: **steps** + **pulses** (Bjorklund pattern shown on the ring), **offset** (rotation), **probability**, and a target — either a **note** (channel / note / velocity / length) or a **CC** (number / high / low). The ring glows on the current step and brightens on a hit. Toggle (●) or remove (✕) per voice.

### LFO Sweeps (amber, left) — `+ ADD LFO` (up to 4)
Pick **shape** (sine / triangle / sawtooth / ramp / square / random / s&h), clock-synced **rate**, **depth**, **center**, and a **CC target**. The waveform preview animates with a live cursor. CC output is throttled to 16th-notes with value dedup (no zipper noise).

### Harmony · VT-4 (teal, right)
Set **MIDI CH** (VT-4 default 1), **VOICES** (1–3), **OCT**, **INV**. Four modes:

- **AUTO** — the progression auto-advances on each step's bar count. Build it by clicking a step cell to set root / quality / bars (up to 8 steps). `START / STOP / RESET`. The NOW / NEXT box shows the current chord large, next chord small, and a bar-countdown dot row that empties with the clock.
- **LOCK** — hold the current chord indefinitely; click again to resume auto-advance from where it paused.
- **MANUAL** — tap `NEXT ▸` to advance one step (rehearsal / free-form).
- **FOLLOW** — play the Keystep; the engine detects the chord from held notes (triads through 7ths/9ths) and sends it to the VT-4 (40 ms debounced). It shows held notes, the detected chord with a dim/bright confidence dot, and the output notes. Releasing all keys holds the last chord so the VT-4 keeps harmonizing between phrases; switching back to AUTO resumes the progression from where it paused. **Keys CH** selects the input channel (or "any").

> **VT-4 note semantics:** the notes you send set the *harmonic context* (key/scale center), not literal pitches the VT-4 plays. Sending C–E–G tells it to harmonize around C major. Put the VT-4 in **Harmony** mode and match its MIDI channel.

---

## 3. Troubleshooting

| Symptom | Fix |
|---|---|
| "No Web MIDI" / no ports | Use Chrome/Edge, served over `http://localhost` — not `file://`. |
| 707 missing from the port list | Enable `TxUSB MIDI` on the box, reconnect USB. |
| MIDI access blocked | Check `chrome://flags/#enable-web-midi` and OS MIDI/privacy permissions. |
| Scenes don't fire | Set `Control Rx = ON` on the 707 and match the scene channel. |
| VT-4 silent | Harmony mode on, MIDI channel matches, OUT2 → VT-4 IN connected, velocity ≥ 1. |
| Stuck notes | Hit PANIC — it also fires automatically on stop, port/mode change, and page close. |
| Clock drifts | v2 uses an AudioContext scheduler; for tight sync set Clock = SLAVE and let the 707 drive. |

---

## Scope

MIDI controller only — notes, CC, Program Change. No SysEx, no patch/tone/effect editing (B67's domain), no audio DSP, no DAW/backend.
