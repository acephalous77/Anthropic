# Vale rules: mechanical AI-tell enforcement

A starter [Vale](https://vale.sh) rule pack that catches the lexical and phrasal tells deterministically — in your editor, pre-commit, or CI. This is layer 3 of the stack in [`../GUIDE.md`](../GUIDE.md) §6: the linter catches word-level tells; the skill catches structural/semantic ones; you keep the claims, voice, and read-aloud passes.

## Setup

```bash
brew install vale        # or: https://vale.sh/docs/vale-cli/installation/
cd humanize-writing/vale
vale ../../some-draft.md  # or copy .vale.ini + styles/ to your project root
```

Note: every rule file YAML-parses, and the regexes compile and pass a 40+-case behavior battery (hits on every negative-parallelism variant and word order, -ing tails, "important to note", etc.; no hits on ordinary negation like "the dog is not just outside" or "we could not reproduce the crash"). The Vale binary itself wasn't runnable in the environment that generated these, so run `vale ls-config` once after install to confirm end-to-end.

## What's included

| Rule | Level | Catches |
|---|---|---|
| `NegativeParallelism` | **error** | the #1 tell, all variants: "it's not X, it's Y", "X is not Y — it's Z", "not X but Y", "not only/so much/merely", "less about X than Y", "more than just X", trailing "Y, not X.", "No A. No B. Just C." |
| `OverusedVocabulary` | warning | delve, leverage, seamless, boasts, serves as… with suggested swaps |
| `InflationWords` | suggestion | pivotal, tapestry, testament, unprecedented… |
| `Constructions` | warning | -ing tails, "important to note", throat-clearing openers, "future looks bright" closers |
| `VagueAttribution` | warning | "experts argue", "studies show" (uncited) |
| `ChatbotResidue` | error | "I hope this helps!", knowledge-cutoff disclaimers |
| `Personal` | warning | **your** banned list — edit this one first |

For a much fuller pack (63 rules, incl. ParticipialPadding, VerbTricolon, StackedAnaphora, MicDrop), see [`tbhb/vale-ai-tells`](https://github.com/tbhb/vale-ai-tells) — these starters are compatible and can sit alongside it.

## Agent workflow

Tell Claude Code: *"Run `vale <file>` and fix every warning, then re-run until clean."* Deterministic loop, no judgment required — which is exactly why it only covers the mechanical half. A clean Vale run is necessary, not sufficient: it can't see burstiness, paragraph uniformity, missing specifics, or a missing take.

## Two caveats

- **Don't run it on quoted examples of AI writing** (like the GUIDE in this repo — it will light up like a Christmas tree, correctly).
- **Suggestion-level words are context-dependent.** "Crucial" is sometimes the right word. The rule flags for review; the cluster test (GUIDE §7) decides.
