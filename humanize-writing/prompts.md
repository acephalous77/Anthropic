# Prompt Library: generation-time de-AI-ing

Copy-paste blocks for the *generation* side (layer 1 of the stack in [GUIDE.md](GUIDE.md) §6). These reduce AI-isms at the source; they don't eliminate them — the overuse patterns are baked in by preference tuning, so the editing passes still apply. Evidence-based design notes: concrete negative constraints beat vague positives ("be conversational" produces folksy filler); ban 1–2 pattern families per prompt, not fifty (giant ban-lists degrade output); persona prompts shift costume while the grammar stays.

---

## 1. The core style block (append to any writing prompt)

```
Style constraints:
- No contrastive formulas: never "It's not just X, it's Y", "This isn't X. It's Y.", "not only X but also Y".
- Maximum one em dash per response. No bullet lists unless I ask for them. No bold mid-sentence. Sentence-case headings.
- Vary sentence length: no three consecutive sentences of similar length. It's fine to follow a 30-word sentence with a 5-word one.
- No trailing participial analysis ("..., highlighting the importance of...").
- Never "It's important to note", "In conclusion", "In today's fast-paced world", "Let's dive in".
- Commit to one position or recommendation. If evidence cuts both ways, say which side wins under what conditions. No "the implications remain unclear".
- Concrete over abstract: names, numbers, and dates instead of "various tools", "significant improvements". If you don't have the specific, write [ADD: ...] instead of a vague filler.
- Plain verbs: "is" not "serves as", "use" not "leverage", "show" not "showcase".
```

## 2. Voice-matched generation (with your style card)

```
Below is my voice profile and three samples of my real writing. Write the piece in MY register:
- Match my sentence-length mix and punctuation habits from the samples, not a generic "natural" style.
- Use my recurring phrases where they fit; never use words on my banned list.
- If I write "stuff" and "things", do not upgrade to "elements" and "components".
- Where my opinion is needed and you don't know it, write [ADD: your take] rather than a balanced non-position.

[paste voice-profile.md]
[paste 3–5 short samples, varied genres]
```

## 3. Interview mode (best voice preservation — the AI assembles YOUR words)

```
Interview me for a piece about <topic>. Rules:
- One question per turn. Start open ("what happened?"), then focus ("what broke when you tried X?"), then close ("so the fix was Y — did it hold?").
- Probe for specifics: numbers, dates, names, what went wrong, what it cost, what surprised me.
- Ask for real artifacts where relevant (the actual error, the actual code, the actual email).
- After 8–12 questions, assemble a draft built from MY phrasing in the transcript. Reuse my sentences wherever possible; add only minimal connective tissue, and mark every sentence that is yours rather than mine with ^ so I can check them.
```

Low-tech variant: dictate a voice memo, transcribe it, then: *"Clean up this transcript: remove filler words and fix punctuation ONLY. Do not rephrase, reorder, or formalize anything."*

## 4. Feedback, not rewrite (protects a human draft — "just polish this" is the most voice-destructive request you can make)

```
Do not rewrite this draft. Instead:
1. Flag anything unclear, flabby, or repetitive — quote it, explain why in one line, and leave the fix to me.
2. Where a claim needs support, say what kind (number? source? example?).
3. List up to 3 places where the structure fights the argument.
Do not correct grammar or word choice unless it's an outright error.
```

Variance-first alternative (Mollick's practice): *"Give me 10 rewrites of this one sentence in radically different styles — terse, angry, technical, deadpan, first-person…"* — then curate; you keep authorship of the choice.

## 5. The rubric self-audit (works; "make it sound human" doesn't)

```
Audit the draft below against each item and report violations with line quotes and a proposed fix. Do not rewrite yet.
1. Contrastive formulas ("not just X, it's Y") 2. Participial tails (", highlighting...")
3. Vague attribution ("experts say") 4. Significance inflation (pivotal/testament/tapestry)
5. Hedging stacks (2+ hedges on one claim) 6. Three consecutive same-length sentences
7. Transplantable intro / restating conclusion 8. Transition carpet (Furthermore/Moreover/Additionally)
9. Zero concrete specifics in any section 10. No committed position anywhere
11. Bolded-header bullet walls 12. Em dashes >1 per paragraph
Then wait. I'll tell you which fixes to apply.
```

## 6. Pre-writing gate (control structure before any prose exists)

```
Before writing anything: propose a title, a 3-sentence abstract, and a section outline with one line on what each section claims (not covers — claims). Wait for my approval or edits. Only then draft, one section at a time.
```
