# Setup — get running on the laptop

Condensed first-run flow. For full usage see [`GUIDE.md`](GUIDE.md).

> **Browser:** Chrome or Edge on desktop only — Web MIDI doesn't exist in Safari/Firefox.

---

## 1. Get the project onto the laptop

**Quickest (no git, just run it):** from the GitHub repo, download two files —
`hw-v2-standalone.html` and `hw-707-control.html` — into the **same Desktop folder**.

**Full project:**

```
git clone https://github.com/acephalous77/Anthropic.git
cd Anthropic
```

## 2. Launch

- **Standalone:** double-click `hw-v2-standalone.html` (opens in your default
  browser — make sure that's Chrome/Edge). No server needed.
- **Modular:** `python3 -m http.server 8080` in the repo root, then open
  `http://localhost:8080/hw-v2/` (and `/hw-707-control.html` for v1).

App-like window with its own icon: in Chrome, open the file → ⋮ →
*Cast, save, and share* → **Create shortcut…** → tick **Open as window**.

## 3. Configure the MC-707

| Setting | Where | Why |
|---|---|---|
| `Control Rx = ON` | MIDI menu | Scene buttons fire via Program Change |
| Per-track **Rx channel** | `SHIFT + TRACK SEL` | match the app's channels (track 1 → ch 1, …) |
| `TxUSB MIDI = ON` | MIDI menu | box shows up as a port + can send clock |
| EXT IN type = **LINE** | `SHIFT + INPUT` | line-level audio from the VT-4 |

## 4. Wire the ports (in the app header)

- **OUT** → MC-707 (CC, Program Change, transport, harmony notes)
- **CLOCK IN** → MC-707 (only if you want the app to slave to the box's tempo)
- **KEYS IN** → Keystep (for harmony follow mode — later)

## 5. Sanity test

Open **v1** (`hw-707-control.html`), select the 707 as output, then fire a
**Scene** or drag a **FILTER** fader. The box should react and the activity dot
flashes on send.

- Dot flashes but box doesn't move → channel mismatch, or `Control Rx` still off.
- No ports listed → wrong browser, or opened over `file://` for the *modular*
  version (use the standalone, or serve over `http://localhost`).
- 707 missing from the list → enable `TxUSB MIDI`, reconnect USB.

## 6. First sounds (v2)

1. Set the clock (INTERNAL + a BPM, or SLAVE to follow the 707) and press START.
2. **Euclidean** → `+ ADD VOICE`: try steps 16 / pulses 4, point it at a drum
   note on the right channel.
3. **Harmony · VT-4** (AUTO): click step cells to enter a 4-chord progression,
   set bars per step, press START. Put the VT-4 in **Harmony** mode on a matching
   MIDI channel.

---

## Tool boundaries

- **v1** — control surface (transport, scenes, faders, X-Y, pads). Don't modify it.
- **v2** — generative engine (Euclidean, LFO, harmony driver).
- **B67 editor** — your ZEN-Core tone/patch/effects editor. Runs as its own app.
  This project never touches tones, effects, or SysEx, so the two don't collide:
  shape sounds in B67, perform and generate with v1/v2.
