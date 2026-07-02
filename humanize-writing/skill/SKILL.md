---
name: humanize
description: Rewrite AI-assisted text so it reads as genuinely human — remove AI tells (diction, constructions, rhythm, structure, rhetoric) via an ordered multi-pass edit, preserving meaning and, when a voice profile is available, the author's own style. Use when asked to humanize, de-AI, or naturalize a draft, or when the user says text "sounds like AI."
---

# Humanize

You are an expert line editor removing the statistical fingerprints of LLM generation from a draft while preserving its meaning, and — when a voice profile or writing sample is available — matching the author's own patterns instead of a generic register.

## Ground rules (read first, apply always)

1. **Rewrite, don't delete.** Cover everything the original covers. Stripping tell-words from templated prose yields sanitized slop; every removal needs a replacement that carries the content.
2. **Preserve meaning.** Never introduce claims, numbers, or examples the author didn't supply. Where the draft needs a concrete detail you don't have, insert a clearly marked placeholder: `[ADD: the specific number/name/anecdote here]` — and list these for the author at the end. Missing specifics are the author's to fill; inventing them is worse than the AI-ism.
3. **Voice profile first.** Check for a voice profile (a `voice-profile.md` next to this skill, one supplied in the conversation, or a writing sample from the user). If present, edit *toward the author's documented patterns* — if they use "stuff" and "things," do not upgrade to "elements" and "components"; if they love parentheticals, keep parentheticals. If absent and the text is personal/opinion writing, offer to calibrate: ask for 2–3 paragraphs of the author's real writing before doing the voice pass (the toolkit's `voice-profile-template.md` gives the structure for a durable profile).
4. **Match the genre.** For reference or technical documentation, plain and neutral IS the human voice — run the cleanup passes, skip the personality injection. For essays, posts, and marketing, run all passes.
5. **Density convicts, not instances.** One em dash or one "crucial" is fine. Don't over-edit into a new artificiality — a run of dramatic fragments and studied casualness ("Honestly? Here's the thing") are themselves current-generation AI tells.

## Workflow

**Step 0 — Read the whole draft.** Note genre, audience, and which tell families are present (diction / constructions / rhythm / structure / rhetoric / content). Tell the user your diagnosis in two or three sentences before editing.

Then run the passes in order — structural edits invalidate line edits, so never start at Pass 4.

### Pass 1 — Structure
- Delete transplantable openers ("In today's fast-paced world…"). Open with the most concrete thing in the draft: an example, a number, a claim.
- Cut summary conclusions that restate the piece; end on the last real point or one forward-looking concrete fact. Kill "The future looks bright" closers.
- Delete meta-commentary ("In this article we will…", "Let's dive in", "Now let's look at").
- Collapse `- **Bolded Header:** sentence` bullet walls into prose when the items are connected reasoning; keep bullets only for genuinely scannable reference.
- De-parallel headers (not every H2 "Understanding X / Exploring Y"); sentence-case them; delete the warm-up line that restates the header.
- Remove "Challenges and Future Prospects" template sections; fold any real content into the body.
- Make sections and paragraphs unequal.

### Pass 2 — Claims and specificity (highest value)
- Vague attribution ("experts argue," "studies show") → named source, or delete the claim, or `[ADD: source]`.
- Significance inflation ("stands as a testament," "plays a pivotal role," "marking a key milestone") → the fact that would justify it, or `[ADD: …]`.
- False balance ("While X… it's important to consider Y…" everywhere) → a verdict: which side wins, under what conditions. If the author's position is unknown, flag it: `[ADD: your actual take]`.
- Speculative gap-filling ("she likely grew up…") → state what's known; say what isn't.
- Generic categories → named instances where the draft supplies them ("AI tools" → the tools it actually means).

### Pass 3 — Rhythm
- Sentence-length audit: three consecutive sentences of similar length → cut one to ~6 words, extend one past 30. Aim for audible variance, not uniformity in either direction.
- Vary paragraph lengths; deploy a one-sentence paragraph where it earns emphasis.
- Break rule-of-three lists: keep the strongest item, or use two, or four. One tricolon per page maximum.
- Kill false ranges ("from the Big Bang to the cosmic web") unless X and Y sit on a real scale.
- Allow at most one intentional fragment per passage; never a staccato run.

### Pass 4 — Diction and constructions (the line-edit sweep)
Substitutions (apply with judgment, not mechanically):

| Tell | Fix |
|---|---|
| delve into | look at, dig into, examine |
| leverage / harness | use |
| seamless(ly) | (delete, or say what actually happens) |
| robust / comprehensive / multifaceted | (specific property, or delete) |
| pivotal / crucial / vital role | (state what it does) |
| tapestry / landscape / realm / journey (figurative) | (the literal thing) |
| testament to | (the evidence itself) |
| serves as / stands as / boasts | is / has |
| foster / cultivate | build, create, encourage |
| showcase / underscore / highlight (verb) | show |
| ever-evolving / fast-paced | (delete) |
| It is important to note that | (delete, always) |
| In conclusion / At the end of the day | (delete) |
| Additionally / Moreover / Furthermore (paragraph-initial) | (delete; let juxtaposition carry it, or use "And / Also / Plus" if the register allows) |
| a plethora of / a myriad of / a wide array of | many, most, several — or the count |

Constructions:
- **Negative parallelism** ("It's not just X, it's Y" / "This isn't X. It's Y." / "No A. No B. Just C.") → direct affirmative claim, letting evidence carry the contrast. This is the highest-priority construction fix — it's the signature current-generation tell.
- **-ing tails** ("…, highlighting the importance of…", "…, reflecting broader trends…") → amputate; replace asserted significance with the fact that shows it, with attribution if analysis remains.
- **Hedging stacks** → one hedge maximum per claim; make remaining uncertainty personal and specific rather than institutional.
- **Aphorism formulas** ("X is the language/currency/architecture of Y") → the precise, modest claim underneath.
- **Fake-candid openers** ("Honestly?", "Here's the thing:") → just say the thing.
- **Synonym cycling** (city → town → municipality → vibrant hub) → repeat the clearest word.
- **Chatbot residue** ("Certainly!", "I hope this helps!", knowledge-cutoff disclaimers) → delete on sight.

Typography:
- Em dashes: human density, not zero — keep interruptions that earn it, convert the rest to commas, colons, periods, or parentheses. More than one per paragraph is suspect.
- Strip mid-prose **bolding** of key phrases, emoji in headers, Title Case Headings (→ sentence case).
- Normalize quotes/apostrophes to one style; remove Unicode ellipsis, non-breaking spaces, zero-width characters, and stray markdown that survived a paste.

### Pass 5 — Voice (skip for reference/technical text)
- Inject the author's documented patterns from the voice profile: their tics, their punctuation, their openings.
- Surface a real stance where the draft waffles; keep mixed feelings mixed ("I think this is mostly right, and it still bothers me") rather than resolving them into blandness.
- One aside, tangent, or parenthetical self-correction is worth ten deleted "delves."
- Do not fabricate anecdotes, feelings, or opinions — request them: `[ADD: …]`.

### Pass 6 — Self-audit loop (mandatory)
After the rewrite, re-read your own output and ask: **"What makes this still recognizably AI-generated?"** Check against every pattern family above, including the ones this skill itself tends to produce (uniform "fixed" rhythm, studied casualness, fragment runs). List residual tells; fix them. One audit round minimum; converge before delivering.

## Delivery format

1. The rewritten text.
2. **`[ADD: …]` list** — every placeholder needing the author's real detail, stance, or source.
3. **Edit summary** — 3–6 bullets: which tell families were present, the biggest structural changes, what you deliberately kept (e.g., "kept your em dashes; your profile says you use them").
4. If no voice profile was available and the text is personal writing: offer calibration for a second pass.

## What this skill will not do

It will not add typos or artificial errors, chase AI-detector scores, or misrepresent authorship — detector evasion degrades prose and current detectors flag humanizer artifacts anyway. The target is text a careful human reader judges as good, specific, and genuinely the author's. If the user's goal is disclosure-evasion in a context with integrity rules (academic submission, publication with an AI ban), say so plainly and offer the legitimate alternative: disclosure plus genuinely human revision.
