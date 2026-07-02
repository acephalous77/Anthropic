# Vale rules: mechanical AI-tell enforcement

A starter [Vale](https://vale.sh) rule pack that catches the lexical and phrasal tells deterministically — in your editor, pre-commit, or CI. This is layer 3 of the stack in [`../GUIDE.md`](../GUIDE.md) §6: the linter catches word-level tells; the skill catches structural/semantic ones; you keep the claims, voice, and read-aloud passes.

## Setup

```bash
brew install vale        # or: https://vale.sh/docs/vale-cli/installation/
cd humanize-writing/vale
vale ../..some-draft.md  # or copy .vale.ini + styles/ to your project root
```

Note: these rules were written against Vale's documented `substitution`/`existence` syntax but haven't been runtime-validated in this repo (Vale isn't installed in the environment that generated them). Run `vale ls-config` once after install to confirm they parse; fix-ups should be trivial.

## What's included

| Rule | Level | Catches |
|---|---|---|
| `OverusedVocabulary` | warning | delve, leverage, seamless, boasts, serves as… with suggested swaps |
| `InflationWords` | suggestion | pivotal, tapestry, testament, unprecedented… |
| `Constructions` | warning | negative parallelism, -ing tails, "important to note", throat-clearing openers, "future looks bright" closers |
| `VagueAttribution` | warning | "experts argue", "studies show" (uncited) |
| `ChatbotResidue` | error | "I hope this helps!", knowledge-cutoff disclaimers |
| `Personal` | warning | **your** banned list — edit this one first |

For a much fuller pack (63 rules, incl. ParticipialPadding, VerbTricolon, StackedAnaphora, MicDrop), see [`tbhb/vale-ai-tells`](https://github.com/tbhb/vale-ai-tells) — these starters are compatible and can sit alongside it.

## Agent workflow

Tell Claude Code: *"Run `vale <file>` and fix every warning, then re-run until clean."* Deterministic loop, no judgment required — which is exactly why it only covers the mechanical half. A clean Vale run is necessary, not sufficient: it can't see burstiness, paragraph uniformity, missing specifics, or a missing take.

## Two caveats

- **Don't run it on quoted examples of AI writing** (like the GUIDE in this repo — it will light up like a Christmas tree, correctly).
- **Suggestion-level words are context-dependent.** "Crucial" is sometimes the right word. The rule flags for review; the cluster test (GUIDE §7) decides.
