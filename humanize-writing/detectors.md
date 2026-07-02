# How AI Detectors Work — and How to Answer Them

The deep-dive behind [GUIDE.md](GUIDE.md) §5. Mechanisms first, because every practical answer follows from them. "Answer" here means three things, all legitimate: write prose whose human signal is real, keep evidence that proves your process, and know the due-process facts when a score is used against you. What it does not mean is evasion-for-disguise — §5 explains why that's now a losing move on technical grounds before ethics even enters.

---

## 1. The four detection families

### 1a. Statistical (zero-shot) methods: measuring surprise

**Perplexity** is how surprised a reference language model is by your next word — the exponentiated average negative log-probability of each token given its context. Low perplexity means every word is what an LM would have predicted. Crucial nuance: perplexity is always relative to a *specific* reference model (GPTZero's original used a fine-tuned GPT-2, with a rule of thumb that document perplexity above ~85 leaned human). There is no model-free "perplexity of a text."

**Burstiness**, as GPTZero defines it, is the standard deviation of per-sentence perplexity across the document — variance of surprise, not just sentence length. Humans spike and dip; models hold a flat line.

**DetectGPT** (Stanford, 2023) tests probability *curvature*: perturb the passage ~100 times with a mask-filling model and compare log-probabilities. Machine text sits at a local maximum of the generator's probability surface (perturbations score worse); human text doesn't. Accurate but expensive, and it degrades across models and under paraphrase. **Fast-DetectGPT** (ICLR 2024) gets ~340× speedup by sampling alternative tokens in one forward pass; **Glimpse** (ICLR 2025) extends these methods to proprietary APIs using top-k logprobs.

**Binoculars** (ICML 2024) scores the *ratio* of a text's perplexity under one model to its "cross-perplexity" against a paired model. The ratio fixes the "capybara problem" — a weird prompt produces surprising *content* that fools plain perplexity — by normalizing for how intrinsically odd the topic is. It hits >90% detection at 0.01% false positives, zero-shot. Its documented failure: **memorized text**. The US Constitution scores deep in the machine range because models know it by heart — which is also why famous quotes, boilerplate, and scripture false-positive across this whole family.

### 1b. Trained classifiers: the commercial tools

OpenAI's own fine-tuned classifier was retired in July 2023 after catching only 26% of AI text while false-flagging ~9% of human text — the canonical proof that naive classifiers don't generalize. What replaced that generation:

- **Turnitin** slides overlapping windows of a few hundred words across the document; each sentence gets a 0–1 score averaged across the windows containing it, and the headline percentage is roughly the share of qualifying prose sentences flagged. Engineering choices reveal the false-positive fear: scores of 1–19% get an asterisk and no highlights; lists, bullets, and short documents are excluded; their own analysis shows 54% of false-positive sentences sit adjacent to genuine AI text (mixed documents smear at the boundaries). Since August 2025 it has a **bypasser-detection layer trained on the output patterns of humanizer tools themselves**.
- **Pangram** publishes its method (arXiv 2402.14873), which is why its false-positive rate is the industry's lowest: every human training document gets a topic-and-length-matched AI "mirror" (so the classifier learns generation artifacts, not topics), plus iterative **hard-negative mining** — scanning tens of millions of provably-pre-2022 human documents for ones the model gets wrong, and retraining on them. Result: ~0 false positives in the independent Chicago Booth benchmark, including on ESL essays, where everyone else fails.
- **GPTZero** (acquired by Superhuman/Grammarly, June 2026) now runs a multi-layer deep model over its old statistical features. **Originality.ai** trains ELECTRA-style from scratch. All headline accuracy numbers are vendor-claimed; the one independent anchor is the Chicago Booth study (all three major tools under 1% FPR on clean benchmarks; only Pangram met a strict 0.5% cap without losing detection power).

What the classifiers actually key on: token-distribution statistics (low mean perplexity *and* low variance), the "aidiolect" vocabulary fingerprint (the Kobak excess-vocabulary list — delve, underscore, intricate, meticulous), syntax and discourse patterns (uniform paragraphs, triads, connective carpet, "not only X but Y"), and formatting artifacts — including em dashes, whose overuse is partly **tokenizer economics** (" —" is a single cheap token) reinforced by post-training.

### 1c. Watermarking and provenance: mostly absent

**SynthID-Text** (DeepMind, Nature 2024) is the only production text watermark. Mechanism: a hash of recent tokens plus a secret key seeds pseudo-random scoring functions; **tournament sampling** picks each emitted token from candidates the model actually proposed, biased toward high-scoring ones — a sampling-layer tweak that's statistically detectable *by the key holder* with negligible quality loss (validated on ~20M live Gemini users). Only Google can detect its own watermark. It survives light editing but degrades badly under diverse paraphrase, splicing, or back-translation, and embeds weakly in low-entropy text.

**OpenAI built a ~99.9%-effective text watermark and shelved it** (2024): surveys showed 69% of users feared false accusations, it was trivially defeated by cross-model rewording, and it disproportionately harmed non-native speakers. **C2PA content credentials don't survive copy-paste for plain text.** Practical upshot: there is no working provenance infrastructure for prose — all real-world text detection remains statistical guesswork, which is why false positives are structural, not a bug being fixed.

### 1d. Stylometry: the family that can work FOR you

Authorship verification measures whether a disputed text matches a specific person's stable, unconscious patterns — above all **function-word frequencies** (the, of, but, however), which are content-independent and hard to fake, plus sentence-length distributions and punctuation habits. Burrows' Delta (z-scored common-word frequencies) is still the workhorse; it helped unmask Rowling as Galbraith. For a writer, stylometric consistency with your prior verified corpus is *supporting* evidence that you wrote the disputed piece. No institution treats it as dispositive, and heavy LLM polishing erases your signal — one more reason to keep the machine's hands off your sentence-level voice.

---

## 2. Why legitimate writers get flagged

Every false-positive population shares specific measurable features with machine text:

- **Non-native English writers**: constrained vocabulary and conventionalized syntax → low perplexity under any reference model. The Stanford/Liang study: 61.3% average false-positive rate on TOEFL essays across seven detectors; 97.8% of essays flagged by at least one. The kicker experiment: asking GPT-4 to *enrich the vocabulary* of those human essays dropped the false-positive rate to ~12% — proof the detectors were reading lexical richness rather than authorship.
- **Polished professional prose**: editing removes burstiness. Uniform register, regularized syntax, and genre conventions (abstracts, cover letters, legal boilerplate) flatten the variance detectors read as human.
- **Neurodivergent writers**: consistent formal structure and low-idiom directness mimic machine regularity; autistic and ADHD students are documented high-risk groups.
- **Memorized and formulaic passages**: near-zero perplexity by definition.
- **AI-polished human drafts**: after a "just polish this" pass, the text literally is partially model-sampled — a Grammarly-rewritten human abstract measured 16% AI on Turnitin, and the emblematic Marley Stevens case began with school-recommended Grammarly.
- **Mixed documents**: scores smear across human/AI boundaries (Turnitin's own 54% figure), so your genuinely human paragraphs inherit suspicion from an AI-assisted one nearby.

And the base-rate math that makes all of this matter: even a true 1% false-positive rate across a university's ~75,000 papers a year is ~750 wrongly implicated students — Vanderbilt's stated reason for disabling Turnitin's detector entirely.

---

## 3. Answering them in the prose

Here's the structural alignment the whole toolkit rests on: **detectors measure distance from the statistical mean, and so do bored readers.** The craft passes ([GUIDE §3](GUIDE.md), [CHECKLIST](CHECKLIST.md)) raise the human signal *honestly*, because the features detectors read as human are the features of good writing:

| Craft move | What the detector sees |
|---|---|
| Specificity pass: real numbers, names, dates, lived detail | High-surprise tokens no model would predict — raised perplexity |
| Rhythm pass: a 30-word build, then a 5-word slam | Raised burstiness (variance of per-sentence surprise) |
| Diction pass: killing the aidiolect vocabulary and constructions | Removes the classifier's lexical and syntactic fingerprint features |
| Commitment: a verdict instead of both-sides hedging | Breaks the discourse-structure template classifiers key on |
| Typography pass: em-dash density, quote consistency, no markdown residue | Removes formatting artifacts |
| Your voice profile: protecting YOUR patterns | Preserves the stylometric signal that proves your authorship |

This is not "evasion that happens to be ethical." It's the causal arrow pointing the right way: writing that carries real information, stakes, and voice is far from the mean *because it's good*, and both the reader and the classifier register that distance.

## 4. Answering them in the process

Output-based arguments ("but a different detector scored it 3%") are weak. Process evidence is strong, and mostly free to keep:

1. **Version history — the decisive evidence.** Write anything high-stakes in Google Docs or Word with AutoSave: timestamped incremental edits are effectively unfakeable at scale, and a pasted-in-whole text is instantly visible as one block appearing at once. Draftback (Chrome) replays Docs keystroke-by-keystroke; Grammarly Authorship tags every span's origin (typed / pasted / AI-suggested) in real time; GPTZero's own Writing Reports do the same replay. The field is visibly shifting from output classification to process attestation — be on the right side of that shift by default.
2. **Draft archaeology.** Keep outlines, notes, annotated sources, and prior drafts. For AI-assisted work, keep the actual prompts and transcripts — they document what the machine did and didn't contribute.
3. **The oral defense.** Explaining your argument, your sources, and your word choices in conversation is what academic-integrity officers treat as most decisive.
4. **Stylometric consistency.** A corpus of your verified prior writing lets an expert show the disputed text matches you (§1d). One more reason the voice profile and the constrained-edit workflows matter: they keep your fingerprint in the text.
5. **Disclosure up front.** Where norms require it (GUIDE §5), disclose tool, task, and sections. A documented, disclosed process converts "did AI touch this?" from an accusation into a non-event.

## 5. Answering them in a dispute

The due-process facts, for when a score is waved at you or someone you're defending:

- **No detector output is proof.** Turnitin's own chief product officer calls the score "a signal to start a conversation." The MLA-CCCC joint task force position: detectors are unreliable and biased, and institutions should not treat scores as sole evidence.
- **The precedents cut against detector scores.** Vanderbilt and others disabled detection over false positives and opacity. The Minnesota expulsion survived appeal (Feb 2026) explicitly on *non-detector* evidence — grader judgment and citation anomalies — not the score. A 2026 Palo Alto civil-rights suit is testing whether score-based accusations violate due process.
- **The demand to make**: sentence-level findings (not one headline number), the tool and version used, its published false-positive rate for writers like you (ESL? neurodivergent? polished formal register?), and an opportunity to present process evidence. The Stanford enrichment experiment and the Booth benchmark are the two citations that end most "the detector said so" arguments.

## 6. Why evasion is the losing move

The temptation is to run flagged text through a "humanizer" until the score drops. Three reasons this fails on its own terms:

1. **The detectors now detect the humanizers.** Turnitin's bypasser layer (Aug 2025, refreshed 2026) and Pangram's DAMAGE research train directly on humanizer-tool outputs — the paraphrase-spinners leave their own statistical fingerprint, so laundering adds a signature instead of removing one.
2. **It destroys the prose.** Paraphrase-spinning injects perplexity by making word choices *worse* — 14 of 16 tools failed independent testing on quality grounds. You end up with text that beats yesterday's classifier and loses today's reader.
3. **It erases your authorship signal.** Spinning strips the stylometric fingerprint that is your best affirmative defense (§4.4), trading a weak accusation-answer for a strong one.

The durable answer to detectors is the same as the answer to readers: text whose specificity, stakes, and voice are real — plus a process trail that makes the question moot.

---

*Sources: the mechanism papers (DetectGPT arXiv 2301.11305; Fast-DetectGPT arXiv 2310.05130; Binoculars arXiv 2401.12070; SynthID Nature 10.1038/s41586-024-08025-4; Pangram arXiv 2402.14873, DAMAGE arXiv 2501.03437; Kobak excess vocabulary, Science Advances 2025); the false-positive literature (Liang et al., Patterns 2023; UChicago Booth BFI WP 2025-116; Turnitin's published FPR analyses); institutional guidance (MLA-CCCC working papers; Vanderbilt's 2023 statement; USD's instructor due-process guide); reporting on the OpenAI watermark decision (WSJ/TechCrunch, Aug 2024) and the GPTZero acquisition (TechCrunch, June 2026). Vendor accuracy claims are flagged as such throughout; Turnitin's internal architecture details come from vendor and vendor-adjacent documentation; no independent audit exists.*
