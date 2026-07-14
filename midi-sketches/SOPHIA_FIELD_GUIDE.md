# Sophia Field Guide
*Reading her prose, tempo, and themes in real time → which lane, which tier, which move.*

The livekit is eight **key-locked lanes**, each a folder of clips named by
**intensity tier**. Load one lane across a 707 track row; the tier numbers are
your mixing order. Project tempo is global on the 707 — MIDI clips follow it —
so treat each lane's BPM as a starting suggestion and *nudge the tempo to her
voice*, not the other way around.

## 1 · Gauge her TEMPO before anything else

Listen to one full breath-phrase before touching a pad. Count roughly how many
stressed syllables she lands per breath and where she pauses:

| What you hear | Set tempo | Reach for |
|---|---|---|
| long unbroken sentences, incantatory | 52–66 | MYSTERY, STORYTELLING (slowed), GRIEF |
| conversational, wandering, reflective | 68–80 | INTIMACY, RITUAL, GRIEF |
| even, confident clauses; lists that build | 84–96 | WONDER, MOTION |
| breathless, urgent, prophetic run-ons | 100+ | RAPTURE |
| free, unmetered, drifting | any — **stay at tier 0–1** (drone+pad only, no drums) |

Rule of thumb: her natural phrase should fill **2 or 4 bars** at your tempo.
If her phrases keep spilling over the barline, slow the project 4–6 BPM.

## 2 · Gauge her THEME → pick the lane

| Her prose is about… | Lane | Why it fits |
|---|---|---|
| closeness, memory, small rooms, love addressed to one person | **1 INTIMACY** (Am 72) | warm Rhodes pocket, dilla drag = privacy |
| a story being told; events; "and then…" | **2 STORYTELLING** (Ddor 64) | dorian vamp stays out of the way; tumbao/organ bed leaves answer-space |
| loss, endings, someone/something gone | **3 GRIEF** (Gm 80) | the lament ground *is* this theme, 400 years deep |
| awe, sky, light, gratitude, beginnings | **4 WONDER** (Cmaj 88) | Pachelbel canon bass + additive shimmer = open heart |
| invocation, ceremony, repetition-as-spell, the dark | **5 RITUAL** (F#phr 72) | phrygian + tribal toms + isorhythm = litany |
| questions, doubt, the unnameable, paradox | **6 MYSTERY** (D sus 66) | **no chord has a third** — her melody decides major or minor; the music refuses to answer, like the question |
| journeys, resolve, defiance, celebration | **7 MOTION** (Dmaj 96) | pump bass and afrobeat lift, unambiguous major |
| ecstasy, rush, apocalypse, speaking in tongues | **8 RAPTURE** (Gm 124) | acid 16ths + motorik + phase-drift = controlled frenzy |

## 3 · Gauge her STYLE → set the tier and the *space*

- **Fragmented, halting phrases** → keep drums OFF (tiers 0–2). Her rhythm *is*
  the rhythm; drums would argue with it.
- **Steady flowing prose** → tiers 3–4. She'll ride the pocket.
- **She's leaving silences** → answer them: STORYTELLING or MYSTERY, and mute
  the pad on alternate 2-bar stretches (manual trading — the Trade/Yield trick).
- **She repeats a phrase like a refrain** → bring in tier 5 (melody) *under her
  refrain only*, then mute it for her verses. The melody becomes the chorus.
- **She's peaking** → tier 6 arp on top, then strip everything to tier 0 the
  moment she lands. The drop-to-drone after a peak is the strongest move you own.

## 4 · The PIVOT MAP (changing worlds without a train wreck)

Lanes are tuned in deliberate pairs. Safe live pivots:

| From → To | Relationship | When |
|---|---|---|
| INTIMACY (Am) → WONDER (C) | relative major | her memory turns to gratitude — same notes, brighter home |
| WONDER (C) → INTIMACY (Am) | relative minor | the light clouds over |
| STORYTELLING (Ddor) → MYSTERY (Dsus) | same root, color removed | the story reaches its unanswerable question |
| MYSTERY (Dsus) → MOTION (Dmaj) | same root, color *declared* | the answer arrives — hugely satisfying |
| GRIEF (Gm 80) → RAPTURE (Gm 124) | same key, tempo gear-shift | grief breaks into transcendence; jump project tempo between phrases |
| RITUAL (F#phr) → GRIEF (Gm) | half-step lift | intensification of dark; do it at a phrase boundary |

Pivot mechanics on the 707: mute down to tier 0–1 of the old lane, switch
scene/track group, bring the new lane's drone in *under* her current phrase,
then build. The drone-overlap hides the seam.

## 5 · Session recipes

- **Cold open**: MYSTERY tier 0 drone. It commits to nothing; whatever she
  starts, you can pivot in ≤2 moves.
- **She reads from a page** (fixed text, steady): STORYTELLING full ladder,
  climb one tier per stanza.
- **Free improvisation night**: park on INTIMACY; it forgives everything.
- **The end-of-the-world material**: the TERMINAL LIGHT stems are a ninth,
  thematic lane — grab any track's drone/pad/bass at its key when her themes
  turn eschatological (tracks 1–4 = A lanes, 5–8 = G, 9–12 = F, 13–16 = E).

## 6 · If a lane isn't landing

Wrong *energy*: move tiers, not lanes. Wrong *color*: pivot on the map above.
Wrong *everything*: tier 0 of MYSTERY and breathe — sus chords buy you time
because they're never wrong. Regenerate/extend the kit: `python livekit.py`
(curation lives in the LANES table — one line per clip).
