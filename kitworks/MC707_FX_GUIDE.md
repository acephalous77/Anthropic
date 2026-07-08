# MC-707 filter / effects / compression guide

How to give the kits their sound on the 707 — the layer above the notes. Every
kit ships an `FX_SETUP.txt` card (in its `output/` and SD folder) with concrete
starting numbers; this explains the system behind them.

> **Verified vs. assumed.** The signal flow, the CC numbers, the macro-knob
> assignments, the send routing, and where Total Comp/EQ live are all from the
> 707 reference / the pasted cheat sheet (§1, §6, §8, §12). The *values*
> (cutoff points, ratios, send amounts, section curves) are my musical
> defaults — sensible starting points, meant to be turned. If the other
> conversation's filter/FX/comp work differs, treat its numbers as the
> authority and keep this as the plumbing.

## Signal flow (what sits where)

```
tone → FILTER/MOD/FX knob macros → insert MFX (per track) →
Delay send + Reverb send → Master → Total MFX → Total Comp → Total EQ → out
```

The kit's FX layer maps onto three tiers of that chain.

## Tier 1 — per-track voice (static, dial once)

Each `FX_SETUP.txt` lists, per track: a **cutoff** and **resonance** start
point, an **insert-MFX** suggestion, **delay/reverb send** amounts, and **pan**.
Dial them per track:

- **Cutoff / resonance** — the FILTER knob (a cutoff-type macro by default), or
  precisely via CC74 (cutoff) and CC71 (resonance).
- **Insert MFX** — pick the named type on the track's MFX slot
  (`[SHIFT]+[MULTI]` on the track; `[SHIFT]+[C2]` jumps MFX categories). Roles:
  bass wants a saturator/compressor, lead a tempo delay, pads a chorus→reverb
  wash, arp a ping-pong.
- **Sends** — delay on `[SEL]+C3`, reverb on `[SEL]+C4`.

The feel tilts the whole kit: **pushing** kits sit brighter and drier,
**ritual** darker and more cavernous, **laidback** warm and roomy.

## Tier 2 — motion (the arrangement's filter/reverb arc)

The dynamics live in three automatable CCs — **CC74 cutoff**, **CC91 reverb
send**, **CC11 expression** — shaped per section:

| section | filter | reverb | feel |
|---|---|---|---|
| intro | ~55% | washed | filtered, held back |
| main | full | dry-ish | the statement, open |
| lift | brighter | +wash | energy up |
| break | ~45% (closed) | drenched | the drop |
| peak | fully open | +wash | brightest, loudest |
| end | settling | long tail | closes down |

Across a full song the filter opens intro→peak, slams shut and drenches in the
break, then settles on the end. **Two ways to get it onto the 707:**

1. **Live-record it.** Arm the clip, then
   `python usb_feed.py <clip>.MID --fx --feel pushing` streams the notes **and**
   this CC motion; firmware 1.8 captures incoming CC as clip motion. One pass
   gets the part and its filter move.
2. **By hand.** Set each clip-column's FILTER knob to the section's level from
   the card (intro down, peak wide open). Slower, no computer.

> **Honest caveat:** SMF import's handling of CC/motion is unverified — import
> may bring only notes. So motion comes from live-record (verified) or the hand
> path, not from dropping the `.MID` in. The song previews in `songs/` embed the
> CC so you can *hear* the arc in a DAW.

## Tier 3 — master bus (Total Comp + EQ, set once)

`[SHIFT]+[MULTI]` → Comp / EQ tabs. Each card gives comp (ratio/attack/release/
threshold/makeup) and 3-band EQ per feel:

- **pushing** — firmer glue (4:1, fast attack), scooped-forward EQ. Punch.
- **laidback** — gentle glue (2.5:1, medium), a little air up top.
- **ritual** — slow, transparent (2:1), warm low, soft top. Space.

In Total Comp edit, `[SHIFT]+[↑/↓]` jumps the same parameter across the low/mid/
high bands.

## Quick start for one kit

1. Load the kit's `*_2MAIN` clips (see `LAYOUT.TXT`).
2. Open `FX_SETUP.txt`. Dial each track's cutoff/reso/MFX/sends.
3. Set Total Comp + EQ for the kit's feel (once).
4. For motion: `usb_feed.py <clip> --fx --feel <feel>` while recording each
   clip, or ride the FILTER knob by column.
