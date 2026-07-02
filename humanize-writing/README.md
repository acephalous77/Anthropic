# Humanize Writing

A toolkit for making AI-assisted writing read as genuinely human — and for keeping your own voice intact when you write with an LLM.

Built from a synthesis of the current (mid-2026) research and craft literature: Wikipedia's "Signs of AI writing" catalog (via its MIT-licensed derivatives), the Kobak et al. excess-vocabulary study (*Science Advances* 2025), the PNAS 2025 grammar-fingerprint study, EMNLP 2025 style-imitation research, detector benchmarks, and the classic editing craft (Zinsser, Strunk & White, Provost, Lamott, Graham) that turns out to solve most of it.

## What's here

| File | What it is |
|---|---|
| [`GUIDE.md`](GUIDE.md) | The full field guide: why AI text sounds like AI, the complete tells catalog, the fix-kit, workflows that preserve voice, tooling, and the detector/ethics landscape. |
| [`CHECKLIST.md`](CHECKLIST.md) | One-page quick reference for an editing pass. Print it, pin it. |
| [`voice-profile-template.md`](voice-profile-template.md) | Fill-in template for capturing your personal voice as a reusable style card. |
| [`skill/SKILL.md`](skill/SKILL.md) | A portable Claude Code skill that runs the full multi-pass humanization protocol on any draft. |
| [`prompts.md`](prompts.md) | Copy-paste prompt blocks for generation time: style constraints, voice-matched generation, interview mode, feedback-not-rewrite, self-audit rubric, pre-writing gate. |
| [`vale/`](vale/) | Starter [Vale](https://vale.sh) linter rules that catch the word- and phrase-level tells mechanically, in pre-commit or CI — including a template for your personal banned list. |
| [`detectors.md`](detectors.md) | How AI detectors actually work (perplexity/burstiness, trained classifiers, watermarking, stylometry), why they false-positive on legitimate writers, and how to answer them — in the prose, in your process evidence, and in a dispute. |

## Installing the skill on your machine

Copy the skill into your personal skills directory (works in Claude Code CLI and desktop):

```bash
mkdir -p ~/.claude/skills/humanize
cp skill/SKILL.md ~/.claude/skills/humanize/SKILL.md
```

Then in any Claude Code session:

```
/humanize path/to/draft.md
```

or paste text and ask it to humanize. Add your filled-in voice profile alongside it (`~/.claude/skills/humanize/voice-profile.md`) and the skill will edit toward *your* patterns instead of a generic "natural" register.

## The workflow, end to end

One piece of writing moves through the toolkit in this order:

1. **Before drafting** — fill in [`voice-profile-template.md`](voice-profile-template.md) once (from 5–10 samples of your real writing) and keep it with the skill. For each piece, pick a workflow from [GUIDE §4](GUIDE.md): talk or draft first if voice matters; outline-first if speed matters.
2. **Generating** — use the blocks in [`prompts.md`](prompts.md): the style-constraint block on every prompt, interview mode for personal pieces, the pre-writing gate for long ones.
3. **Editing** — run `/humanize` ([`skill/SKILL.md`](skill/SKILL.md)): six ordered passes, structure down to diction, with a mandatory self-audit. It leaves `[ADD: …]` placeholders wherever only you can supply the detail, stance, or source.
4. **Enforcing** — `vale` with the [`vale/`](vale/) rules catches the mechanical tells that crept back in; loop to zero warnings.
5. **Judging** — the passes no tool can do, from [`CHECKLIST.md`](CHECKLIST.md): fill the `[ADD]`s, commit to your verdicts, read it aloud.

[`GUIDE.md`](GUIDE.md) is the reference behind all five steps: the full tells catalog, the evidence, and the reasoning.

## The one-paragraph version

AI text sounds like AI because models sample toward the statistical mean: uniform sentence rhythm, hedged claims, balanced structure, promotional abstraction, and nothing only you could know. Deleting tell-words is not the fix; the tells are symptoms. The fix is five moves — concretize, commit or attribute, break symmetry, demote formatting, add what the model can't invent — applied in ordered passes (structure → claims → rhythm → diction → voice → read-aloud). And the best results come from workflows where your own phrasing survives to the final text: talk or draft first, let the model suggest rather than rewrite, and never ask it to "just polish."

## A note on detectors

This toolkit optimizes for readers and lets classifier scores fall where they may. Detector word-lists go stale with every model generation, detectors false-positive on non-native and neurodivergent writers at documented human cost, and paraphrase-spinning "humanizer" tools now leave their own detectable signature while making prose worse. Write things a human judges as good and as yours; disclose AI assistance where your domain's norms require it.
