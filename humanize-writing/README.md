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

## The one-paragraph version

AI text sounds like AI because models sample toward the statistical mean: uniform sentence rhythm, hedged claims, balanced structure, promotional abstraction, and nothing only you could know. Deleting tell-words is not the fix; the tells are symptoms. The fix is five moves — concretize, commit or attribute, break symmetry, demote formatting, add what the model can't invent — applied in ordered passes (structure → claims → rhythm → diction → voice → read-aloud). And the best results come from workflows where your own phrasing survives to the final text: talk or draft first, let the model suggest rather than rewrite, and never ask it to "just polish."

## A note on detectors

This toolkit optimizes for readers, not classifiers. Detector word-lists go stale with every model generation, detectors false-positive on non-native and neurodivergent writers at documented human cost, and paraphrase-spinning "humanizer" tools now leave their own detectable signature while making prose worse. Write things a human judges as good and as yours; disclose AI assistance where your domain's norms require it.
