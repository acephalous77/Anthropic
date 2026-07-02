# The Field Guide to Humanizing AI-Assisted Writing

*Synthesized mid-2026 from the research and craft literature. Sources at the end of each section; full apparatus in [Sources](#sources).*

---

## 0. Framing: what "de-AI-ing" actually means

Three commitments shape everything below.

**The goal is reader perception and prose quality, not beating detectors.** Detector accuracy claims are benchmark theater (the same tool scores 99% in one study and 32% in another depending on text type and model vintage). Detectors false-positive on non-native English speakers at rates up to 61% (Stanford/Liang, *Patterns* 2023) and on neurodivergent writers, with documented human costs — lawsuits at Yale and Michigan, an expulsion at Minnesota, Vanderbilt disabling Turnitin's detector entirely. Meanwhile Turnitin now detects *humanizer-tool artifacts* specifically: paraphrase-spinning adds a signature while degrading the prose. Chasing classifiers is an arms race you can't audit and don't need to win. Human readers and editors key on cadence and hollowness, and those you can actually fix.

**Deletion isn't editing.** Stripping "delve" and "tapestry" from templated prose yields sanitized slop. The tell-words are symptoms of missing specificity, missing stakes, and missing voice. Every fix in this guide replaces, it doesn't just remove.

**Single tells prove nothing; density convicts.** Every pattern below is human-attested English — the models learned them from us. "Delve" is ordinary formal register in Nigerian English. Journalists love em dashes. One em dash means nothing; em dashes plus rule-of-three plus "vibrant tapestry" plus a "Conclusion" section is a confession. Diagnose in clusters, and don't over-edit human quirks out of your own writing for fear of being flagged.

---

## 1. Why AI text sounds like AI

LLMs guess the statistically likely next word, so output trends toward "the most statistically likely result that applies to the widest variety of cases." Genericity is the optimization target, not an accident. Every tell in this guide is a downstream symptom of sampling toward the mean.

Two measurable signatures:

- **Low perplexity** — word sequences are highly probable; no surprising vocabulary, no odd constructions, no creative detours.
- **Low burstiness** — little variance in sentence length and weight. Humans alternate a long rambling build-up with a short punch. AI settles into an even 15–25-word cadence. One skill's headline metric: AI text scores ~0.00 burstiness against ~+0.70 for humans. Multiple 2026 sources call cadence uniformity, not any particular word, "the single biggest AI tell."

Two structural causes worth knowing:

- **RLHF bakes the diction in.** The word-overuse fingerprint ("delve," "underscore," "meticulous") traces to preference tuning, not training data (arXiv 2508.01930; the COLING 2025 "Why Does ChatGPT Delve So Much?" paper). No prompt fully suppresses it, which is why editing passes remain necessary no matter how good your prompt is.
- **The grammar fingerprint persists across styles.** The PNAS 2025 Carnegie Mellon study found instruction-tuned models use present-participial clauses at 2–5× the human rate (GPT-4o: 5.3×), plus elevated nominalization, passive voice, and phrasal coordination — a noun-heavy register that survives *even when prompted to write informally*. Persona prompts shift the costume, not the skeleton.

And one moving target: the tells are **versioned by model generation**. "Delve" and "stands as a testament" now date a text to 2023–24 rather than flag current output. GPT-5.x-era prose is terser, blander, more hedged; its puffery is quieter ("meaningful," "notable") and hides in participial bolt-ons. Newer models trained away from uniform cadence now overcorrect into *engineered* burstiness — runs of dramatic fragments — which reads as equally synthetic. Word lists are snapshots; the durable tells are structural.

---

## 2. The tells catalog

### 2.1 Vocabulary (the versioned list)

The empirical anchor: Kobak et al. (*Science Advances* 2025) analyzed 15M PubMed abstracts and found the post-LLM "excess vocabulary" is overwhelmingly **style words** — verbs and adjectives — where pre-LLM excess words were content nouns. That shift *is* the statistical signature of LLM assistance. "Delve" rose up to 28× in academic prose; "underscore" +10,000% in one engineering corpus.

**Verbs (strongest class):** delve, underscore, showcase, boast, leverage, harness, foster, streamline, elevate, embark, navigate (metaphorical), unlock, unleash, empower, revolutionize, transform, garner, surpass, bolster, facilitate, enhance, illuminate, unveil, encompass, epitomize, spearhead, cultivate; scaffold verbs that defer the claim — "aims to," "seeks to," "serves as," "serves to."

**Adjectives:** pivotal, crucial, vital, meticulous, intricate, robust, seamless, vibrant, dynamic, comprehensive, multifaceted, nuanced, holistic, transformative, groundbreaking, cutting-edge, unparalleled, unprecedented, ever-evolving, fast-paced, notable, remarkable, profound, invaluable, commendable, nestled, picturesque, bustling, rich (figurative), enduring, burgeoning, myriad, game-changing.

**Nouns/abstractions:** tapestry, testament, landscape (figurative), realm, journey (figurative), beacon, symphony, treasure trove, cornerstone, linchpin, insights, synergy, paradigm (shift), ecosystem (figurative), roadmap, legacy, heritage, hub, hidden gem, "challenges and opportunities," "the intersection of X and Y."

**Adverbs/connectives:** Additionally / Moreover / Furthermore as paragraph glue; notably, primarily, strategically, seamlessly, meticulously, ultimately, "quietly" as a significance adverb ("quietly became one of the most important…").

**Generation drift, because the list is versioned:**
- 2023–early 2024: delve, tapestry, testament, boasts, vibrant — now these *date* a text.
- 2024–2025: vocabulary softened; structural tells rose instead (negative parallelism in Fortune 500 filings quadrupled 2023→2025).
- 2025–2026: terser, quieter inflation; model-specific "aidiolects" (Grok still overuses "underscore," "causal," "empirical"; Claude reads fluent/conversational; DeepSeek rambles).
- The feedback loop runs both ways: FSU found AI buzzwords rising in 22M+ words of unscripted *spoken* English. The human baseline is drifting toward the AI signature.

### 2.2 Formulaic constructions

**Negative parallelism — the signature 2026 tell.** "It's not just X, it's Y." / "This isn't about X. It's about Y." / "No guessing. No wasted motion. Just Z." Antithesis that corrects a misconception nobody had; a structural proxy for depth. It persists across model generations when the vocabulary tells have faded.

> Before: "This isn't just a productivity tool — it's a fundamental shift in how teams work."
> After: "Teams that adopted it cut standup meetings from five a week to one. That's the shift."

**Significance inflation.** "stands as a testament to," "plays a vital/pivotal role," "underscores its importance," "marks a pivotal moment," "cements its legacy," "rich cultural heritage." Promotional register even when neutral was requested.

> Before: "Established in 1989, marking a pivotal moment in the evolution of regional statistics."
> After: "Established in 1989 to collect regional statistics independently from Spain's national statistics office."

**Participial trailing clauses (-ing tails).** The PNAS #1 discriminator: unearned analysis bolted to the sentence end. "…, highlighting the importance of…," "…, reflecting broader trends in…," "…, ensuring that…"

> Before: "Attendance doubled in 2024, highlighting the festival's growing cultural significance."
> After: "Attendance doubled in 2024, to about 40,000 — the first year the town's hotels sold out."

**Copula avoidance.** "serves as," "stands as," "boasts," "features," "represents" where a human writes "is" or "has."

> Before: "Gallery 825 serves as LAAA's exhibition space and boasts over 3,000 square feet."
> After: "Gallery 825 is LAAA's exhibition space. It has four rooms totaling 3,000 square feet."

**Rule-of-three carpet.** "flexible, scalable, and easy to maintain" — a tricolon per paragraph, used to make thin analysis look comprehensive. One tricolon is elegant; three back-to-back is a pattern-recognition failure. Fix: keep the strongest item, or make it two, or four.

**False ranges.** "From bustling markets to serene temples…" — X and Y not on any real scale.

**Throat-clearing openers.** "In today's fast-paced world," "In the ever-evolving landscape of," "Since the dawn of time." The transplant test: if the first paragraph could top a different article with minor edits, cut it.

**Fake-candid openers (newer-generation tell).** "Honestly?", "Look,", "Here's the thing" as theatrical pause-and-reveal before a routine point. A person being honest just says the thing.

**Aphorism formulas.** "X is the language/currency/architecture of Y." Profundity-shaped sentences with no added precision.

**Vague attribution / weasel authority.** "Experts argue," "Studies show," "Industry reports suggest" — uncited. Name the source or cut the claim.

**Elegant variation (synonym cycling).** protagonist → main character → central figure → hero, driven by repetition penalties. Humans repeat the clearest word. Repeat the right word.

**Chatbot residue.** "Certainly! Here is…," "I hope this helps!", "As of my last knowledge update…," "Would you like me to expand on any section?" Instant giveaways.

### 2.3 Punctuation and typography

- **Em-dash clusters.** GPT-4.1 measured ~3.3× human frequency; the AI pattern is several per paragraph as an all-purpose hinge, often inside negative parallelisms ("It's not X — it's Y"). Post-Nov-2025 ChatGPT can suppress them on request, so the tell is decaying. Human fix is human *density*, not zero: keep the one that earns its interruption, convert the rest.
- **Curly/straight quote mixing** within one document — the pasted-AI-passage flag. Also non-breaking spaces, zero-width characters, Unicode ellipsis, stray markdown (`**bold**`, `##`) surviving a paste.
- **Mid-prose bolding** of key phrases; the signature list shape `- **Bolded Header:** sentence restating the header.`
- **Emoji-headed sections** (🚀 ✅ 💡) in business prose.
- **Title Case On Every Heading** where the venue's style is sentence case.
- **Machine-uniform serial commas and hyphenation** in casual registers — a weak corroborating signal only.

### 2.4 Structure and rhythm

- **Uniform sentence length** (the 15–25-word cadence) and uniform paragraph length (every paragraph 3–4 sentences, opening the same way).
- **The five-paragraph ghost:** rigid intro-thesis/body/conclusion symmetry regardless of content; header-per-section with parallel phrasing.
- **Signposting overkill:** "In this article we will…," "Let's dive in," "Now let's look at." Meta-commentary announcing the writing instead of doing it. Readers experience it as condescending.
- **Fragmented headers:** heading → one-line restatement of the heading → actual content.
- **The "Challenges and Future Prospects" template:** "Despite its X, [subject] faces several challenges… Despite these challenges, [subject] continues to thrive."
- **Summary conclusions** that restate everything, closing on "The future looks bright" or "Exciting times lie ahead."
- **Transition-word carpet:** Furthermore/Moreover/Additionally heading every paragraph. Individually fine; the unbroken presence is the tell.

### 2.5 Rhetoric and content

- **Relentless balance.** "While X offers advantages, it's important to consider Y." Every claim counterweighted; the conclusion always lands safely in the middle. RLHF measurably trains this in (~50% more sycophancy than humans in comparable tasks).
- **Hedging stacks.** "could potentially possibly," "it's important to note that," "arguably," "generally considered" — applied to claims needing no hedge.
- **No commitment.** Pros-and-cons with no verdict. "The implications remain unclear."
- **Surface comprehensiveness.** Everything covered thinly, nothing deeply — genericity as optimization target.
- **No concrete specifics.** No numbers, dates, prices, names, sensory detail. LLMs round off specifics; humans hoard them.
- **No lived experience.** No anecdote, no "I tested this and it broke," no mixed feelings, no detail only a practitioner would know (what went wrong, what it cost, what never makes the brochure).
- **Speculative gap-filling.** Where a human writes "I don't know," the model writes plausible filler ("she likely grew up in a middle-class household, which shaped her interest in…"). Say what isn't known. Full stop.
- **No surprise, humor, or edge.** Grammatically perfect, stylistically consistent, tonally dead. Reads like a press release.

---

## 3. The fix-kit

### 3.1 The five moves (priority order)

1. **Concretize.** Replace abstraction and inflation with a number, name, date, price, or example. One real, checkable detail per abstract claim; one only-you detail per section. The single highest-leverage edit.
2. **Commit or attribute.** Delete hedges you're willing to defend past. Pin "experts say" to a named source or cut it. Convert every pros-and-cons standoff into a conditional verdict: which side wins, under what conditions, and why you think so.
3. **Break symmetry.** Kill negative parallelisms, surplus triads, uniform sentence lengths, parallel headers, mirrored paragraphs. Follow a 30-word sentence with a 6-word one. Let one list item stand alone.
4. **Demote formatting.** Strip mid-prose bold, emoji headers, title case, bullet scaffolding on content that wanted to be paragraphs. Normalize dashes, quotes, and hidden characters to the document's native typography.
5. **Repeat the right word.** Undo synonym cycling. Humans repeat when the word is right.

### 3.2 The multi-pass protocol

Order matters: structural changes invalidate line edits, so go top-down.

**Pass 1 — Structure.** Delete the first paragraph (the most transplantable block in any AI draft) and start with a concrete example, claim, or datum. Cut the conclusion, or replace it with one forward-looking concrete fact. Kill every sentence that describes the article ("In this section we will…"). Collapse bullet walls into prose where the content is reasoning rather than reference. De-parallel the headers; sentence-case them. Let sections be unequal.

**Pass 2 — Claims and specificity.** The highest-value pass. Replace vague attribution with named sources or delete. Inject what the model cannot invent: your numbers, your dates, your named tools ("ChatGPT, Claude, Perplexity," not "AI tools"), your anecdote, your stated opinion, the thing that went wrong. Cut false balance. Verify anything that smells gap-filled. Interview yourself: what surprised you? what did it cost? what would the brochure never say?

**Pass 3 — Rhythm.** Audit sentence lengths mechanically: three consecutive sentences at 15–20 words means cut one to ~6 and stretch another past 30. Vary paragraph lengths, including a one-sentence paragraph. Break the tricolons. Allow one fragment for emphasis — but not a run of them (staccato drama is now its own tell).

**Pass 4 — Diction and constructions.** The mechanizable pass (a linter can do half of it — see §6). Sweep the banned vocabulary; amputate -ing tails and attribute the analysis; restore "is/has" for "serves as/boasts"; convert negative parallelisms to direct claims; one hedge maximum per claim; "It is important to note that" dies on sight; em-dash sweep, bold sweep, emoji sweep; fix quote-mark consistency; delete chatbot residue.

**Pass 5 — Voice.** Distinct from cleanup, because sterile-but-clean is as obvious as slop. Add the take you actually hold, the acknowledged uncertainty that's *personal* ("this bothers me and I can't fully explain why") rather than institutional ("the implications remain unclear"). A tangent, a parenthetical self-correction, a mixed feeling. Judiciously — for reference or technical text, neutral-and-plain *is* the human voice.

**Pass 6 — Read aloud.** Paul Graham: "I read it out loud and fix everything that doesn't sound like conversation." Monotone or running out of breath means rhythm has failed. Rescue move for hopeless passages: explain to a friend what you meant, then replace the passage with what you said.

**The audit loop.** After rewriting, ask: "What makes this still obviously AI-generated?" List the residual tells, do one more pass. Rubric-driven critique against an explicit tell-list demonstrably works where vague "make it sound human" self-audits don't.

### 3.3 The craft lineage (this is not new)

Every fix above is pre-AI editing craft aimed at a new target. Zinsser: "Clutter is the disease of American writing" — bracket every word not doing work (that's the -ing tails and the throat-clearing). Strunk & White Rule 17: omit needless words. Quiller-Couch, 1914: "Murder your darlings" — and the model's darlings are precisely its aphorisms, punchlines, and significance inflation; the sentences that sound best are the ones to cut. Provost: vary sentence length — "I write music." Lamott: the down draft, the up draft, the dental draft — and keep the down draft human (§4). Graham: complex sentences give the writer "the false impression that you're saying more than you actually are" — exactly the AI failure mode of ceremony without content.

---

## 4. Workflows: keeping your voice when writing with an LLM

### 4.1 The core finding

Voice = claims + idiolect + cadence. Prompting reliably transfers register, partially transfers diction, and barely transfers cadence or idiolect. EMNLP 2025 ("Catch Me If You Can? Not Yet," 40,000+ generations): state-of-the-art LLMs still cannot reproduce nuanced personal styles from samples, especially informal ones. So the workflows that win are the ones where **your own phrasing survives to the final text**.

The most dangerous step is the innocuous one: **"just polish this."** The 2026 "Voice Under Revision" study found even grammar-only LLM edits produce substantial drift toward formal, impersonal language and sharply reduce first-person expression — and a ChatGPT-polished human manuscript measurably raises its odds of being flagged as AI. When voice matters, have the model *suggest and explain*, never rewrite.

### 4.2 The four patterns, ranked for voice preservation

**(c) Interview / dictation mode — best.** The AI asks questions (one per turn, open → focused → closed), you answer, it assembles a draft from *your actual words*; or you dictate a voice memo and constrain the AI to filler-removal. Spoken language is naturally bursty and idiomatic, so the voice survives; the AI's role shifts from generation to arrangement. An interview also "unlocks parts of your knowledge that wouldn't have made it into the article." Weakness: the assembly step still imposes LLM connective tissue — the voice pass stays mandatory.

**(a) Human draft → constrained AI feedback — close second.** Your diction, claims, and rhythm exist from the start; AI serves the up/dental drafts. Mitigate the polish hazard: ask for flagged suggestions with reasons, not rewrites; or use it variance-first (Mollick's practice: "give me 15 radically different rewrites of this bullet," then curate).

**(d) Human outline → AI prose → real voice pass — workable.** You own claims and structure, but every sentence is machine-born, so the voice pass fights the full grammar fingerprint sentence-by-sentence and in practice degrades to spot-editing.

**(b) AI draft → human edit — worst for voice.** The AI sets structure, framing, and claim inventory; anchoring keeps the human rewrite lighter than intended; the cadence survives. Acceptable for commodity how-to content — in a 500-blog-post blind test, readers identified AI how-to content at only 62% (coin flip) — but personal essays were caught at 89%. The reader quote that summarizes it: "The AI version is technically good, but it feels like you on autopilot."

### 4.3 Capturing your voice as a style card

Fine-tuning is fragile for individuals (needs hundreds of samples, freezes your voice at training time, introduces its own tics). The 2026 consensus: **style card + 4–5 varied few-shot samples in the system prompt**, refreshed as your writing evolves. Few-shot plateaus after ~4–5 examples, and five samples of the same structure teach a template, not a voice — vary the genres.

What to extract from 5–10 samples of your real writing (see `voice-profile-template.md`):

- Sentence-length pattern (short/punchy, long/flowing, mixed how?)
- Register and diction; recurring phrases and verbal tics
- How paragraphs start (jump in vs. set context)
- Punctuation habits (dashes? parentheticals? semicolons?)
- Transition handling (explicit connectors vs. just starting the next point)
- Opinions and standing stances; what you'd never say
- **The banned list — the negative space does more work than the tone adjectives.** If you say "stuff" and "things," an editor upgrading you to "elements" and "components" is destroying your voice, not improving it.

### 4.4 Prompting that actually reduces AI-isms

What works:

- **Banned-word and banned-construction lists** in the system prompt — the single most-endorsed technique. Removing the option to reach for "pivotal" forces specific phrasing. Keep it focused: banning 1–2 pattern families per prompt works; giant ban-lists degrade output.
- **Concrete negative constraints beat vague positives.** "No lists; no contrastive 'not X but Y' formulas; no three consecutive sentences of similar length" outperforms "be conversational" (which models interpret as folksy filler).
- **Demand opinion and specificity.** Instruct it to take a stance, commit to one recommendation, include numbers/names/dates, skip both-sides hedging.
- **Pre-writing gates.** Approve title/abstract/outline before any prose exists — human judgment upstream, where it's cheap.
- **Rubric-driven self-audit.** "Check this against the following 20 patterns and report each violation with a fix" works; models are demonstrably bad at finding their own faults without a rubric.

Folklore:

- "Write like a human" / "avoid AI detection" as bare instructions — produces caricatured casualness.
- Temperature advice in chat interfaces (consumer ChatGPT/Claude use fixed temperature; and higher temperature adds variance, not voice).
- Persona prompts ("you are a Pulitzer-winning essayist") — shifts costume, not the PNAS grammar skeleton.
- Adding typos/slang — 14 of 16 commercial humanizers failed independent testing doing exactly this.

---

## 5. Detectors and ethics (know the terrain, don't fight on it)

**The landscape, mid-2026:** GPTZero (acquired by Superhuman/Grammarly, June 2026) claims 99% but flagged 15% of human essays in one real-world university test. Turnitin claims <1% false positives; its own CPO conceded ~4% — at a 67,000-student university, ~2,700 false accusations — and since Aug 2025 it specifically detects humanizer-tool artifacts. Pangram is the outlier: near-zero measured false positives (~0.01%, and no significant elevation for ESL writers) in the UChicago Booth benchmark. Watermarking (SynthID) is a provenance layer for participating models' media, not a text-detection solution; OpenAI's text watermark remains shelved.

**The false-positive reality:** 61% of TOEFL essays by non-native speakers flagged (Stanford); elevated flags for neurodivergent writers; merely *polishing* human text with ChatGPT raises its flag rate. Institutions are retreating to "signal, never proof."

**Disclosure norms by domain:** ~70% of academic journals require disclosure (LLMs can never be authors; *Science* bans AI text outright; the useful emerging distinction is assistive AI — refining your own work, no disclosure — vs. generative AI, which must be disclosed). AP treats generative output as unvetted source material, never publishable content. Amazon KDP requires an AI-*generated* checkbox but exempts AI-*assisted*. Google doesn't penalize AI content per se but its March 2026 core update cut scaled unedited-AI sites 50–80%; E-E-A-T's first E is Experience — the thing generic AI text definitionally lacks. Literary short-fiction markets (Clarkesworld) ban AI involvement entirely.

**The ethical frame every serious source converges on:** de-AI-ing is legitimate as *craft* — making assisted writing good and genuinely yours, with domain-appropriate disclosure. It's illegitimate as *disguise* — misrepresenting authorship to evade detection. And the disguise route is now both self-defeating (bypasser detection) and prose-degrading. Editors like Neil Clarke don't use detectors anyway; they pattern-read: "I can tell on the first page."

---

## 6. Tooling: the recommended stack

Four layers, each catching what the previous can't:

1. **Generation:** style card + few-shot samples + focused banned-construction list in the system prompt (§4.3–4.4). Reduces but never eliminates — the overuse is RLHF-baked.
2. **LLM edit pass:** a humanizer-protocol skill (this repo's `skill/SKILL.md`; see also `blader/humanizer` and `Aboudjem/humanizer-skill` on GitHub, both built on Wikipedia's Signs-of-AI-writing catalog) with your voice profile loaded. Catches structural and semantic tells.
3. **Mechanical enforcement:** [Vale](https://vale.sh) with the [`tbhb/vale-ai-tells`](https://github.com/tbhb/vale-ai-tells) rule pack — 63 prose rules covering the lexical and phrasal tells deterministically (OverusedVocabulary, ContrastiveFormulas, ParticipialPadding, VagueAttributions, MicDrop, WrapUpHeadings…). Add your personal banned list as Vale `substitution` rules; run in pre-commit or CI; tell your agent "run vale and fix warnings" and loop to zero. Vale's own stated limits: it can't detect burstiness, paragraph patterns, or semantics — that's layers 2 and 4.
4. **Human judgment:** the claims pass, the voice pass, and the read-aloud pass (§3.2). No tool adds your pear, your Fish Guy, your opinion. It doesn't know them.

**Avoid commercial "humanizers."** In independent testing, 14 of 16 were glorified paraphrasers that swapped fancy words or added typos; aggressive paraphrase changes meaning, drifts facts, and produces rambling purple prose — while now also carrying its own detector signature. A paraphraser changes words; humanizing changes the character of the writing, and voice, specificity, and accountability are things no tool reliably adds by itself.

---

## 7. Quick diagnosis: the cluster test

Reading a suspect text (yours or anyone's), count families, not instances:

| Family | Flag |
|---|---|
| Diction | ≥3 canon words per page ("delve," "tapestry," "pivotal," "seamless"…) |
| Constructions | any negative parallelism + any -ing tail + any "serves as" |
| Rhythm | three consecutive sentences within ±3 words of each other, twice per page |
| Structure | transplantable intro, restating conclusion, transition carpet, bolded-header bullets |
| Rhetoric | every claim hedged or balanced; zero commitments |
| Content | zero numbers/names/dates; zero only-the-author-would-know details |

One family: noise. Three or more: AI-shaped, whoever wrote it — and the fix-kit (§3) applies either way, because these are just failures of good prose.

---

## Sources

Primary research: Kobak et al., *Science Advances* 2025 (arXiv 2406.07016) · PNAS 2025 "Do LLMs write like humans?" (10.1073/pnas.2422455122) · EMNLP 2025 Findings arXiv 2509.14543 · "Voice Under Revision" arXiv 2604.22142 · RLHF word-overuse arXiv 2508.01930 · COLING 2025 arXiv 2412.11385 · Liang et al., *Patterns* 2023 (TOEFL false positives) · FSU spoken-drift arXiv 2508.00238 · Pangram aidiolects arXiv 2506.21817.

Catalogs and craft: Wikipedia, *Signs of AI writing* (WikiProject AI Cleanup) and its MIT-licensed derivatives `blader/humanizer` and `conorbronsdon/avoid-ai-writing` · `tbhb/vale-ai-tells` · Pangram "Most common AI phrases" · Blake Stockton's "Don't Write Like AI" series · Colin Gorrie, Dead Language Society · Gary Provost, *100 Ways to Improve Your Writing* · Zinsser, *On Writing Well* · Strunk & White · Lamott, *Bird by Bird* · Paul Graham, "Write Like You Talk."

Workflows and industry: Ethan Mollick, *Co-Intelligence* and One Useful Thing · Elio Struyf (interview mode) · Every.to "Writing With AI is Harder Than You Think" (2026) · Forte Labs AI style guide · Product Upfront 500-post blind test · technology.org editorial workflow (2026) · Neil Clarke / Clarkesworld · detector benchmarks: UChicago Booth 2026, eyesift, gradpilot · Vanderbilt Turnitin statement · Google Search guidance on AI content.
