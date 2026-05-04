# Loss-runs project lessons

Each lesson ends with a **standing rule** that applies to future work, not just a
post-mortem of one mistake. Rules are operative; observations fade.

---

### Lesson 1 — The eval layer's verdict is a summary; the JSON is the truth.
**(2026-05-03, ICW chunk[2] cause-column investigation)**

Spent 4 hours treating "VLM emitted None for 5 cause fields" as a content-extraction
failure. The model had actually extracted all 5 values correctly under a non-canonical
key (`cause` instead of `cause_of_injury`). Misattribution traceable to reading the
eval's miss report without reading the raw extraction's parent dict.

**Standing rule**: every eval-side miss investigation begins by reading the raw
extraction's parent dict for sibling keys. The eval reporter now surfaces these
automatically via `unknown_sibling_keys`. Attribution to the model is only valid
after that check.

---

### Lesson 2 — Aliases are for notational synonyms only, never conceptual ones.
**(2026-05-03, loss_ratio_pct vs experience_modification investigation)**

Saw GT `loss_ratio_pct = 197` paired with extraction `2.24` and the parent dict
exposing `experience_modification` as a sibling. Strong pull toward adding
`loss_ratio_pct: [experience_modification]` to the alias map. Resisted the pull,
checked the PDF, found the model had: (a) converted `224%` → `2.24` (unit drift)
and (b) bound to the current-policy row instead of the Total row (row-binding
drift). Two distinct conceptual failures. Neither is the same field as
experience_modification.

**Standing rule**: `cause ≡ cause_of_injury` (same concept, different surface
name) — alias yes. `loss_ratio_pct ≡ experience_modification` (different
actuarial concepts) — alias never. The slope from "convenient" to "carrier-
disambiguation hardcoded answer key" is steep. The notational-vs-conceptual
distinction is codified in `experiments/30_voter/schema_coerce/schema_aliases.yaml`
header. Conceptual disambiguation belongs in the prompt; never the alias map.

---

### Lesson 3 — VLM normalization is a category, not a one-off.
**(2026-05-03, "Fall/Slp" → "Fall/Slip" + "224%" → "2.24")**

VLMs trained on web-scale text have a habit of "normalizing" what they see:
expanding abbreviations they recognize, decimal-izing percentages, fixing
perceived typos, regularizing case. Helpful 90% of the time and disastrous when
the abbreviation, percentage, or odd-case *is* the ground truth — which it
usually is in claims data (Slp, Lftng, Strn are NCCI shorthand; "224%" is the
correct format on a loss-run cover page).

**Standing rule**: every prompt that asks for cell-level extraction includes
"preserve all abbreviations, codes, and numeric formats verbatim — do not
expand, decimal-ize, or normalize." A verifier rule flags any extracted string
strictly longer than its source-text region as a candidate hallucination
(deferred until per-cell OCR bounding boxes are surfaced to the verifier).

---

### Lesson 4 — Eval changes need the same regression discipline as code changes.
**(2026-05-03, after audit found multiple eval-rule additions had inflated F1)**

Multiple eval rules added during one session (`NONE_AS_ZERO`, address 80%-prefix,
carrier first-word match) inflated F1 by ~4pp without anyone noticing because
eval rules landed without per-doc per-field regression checks. Code reviewer
caught it; the user caught the user-facing inflation.

**Standing rule**: every eval rule addition is feature-flagged behind a config
toggle until per-doc per-field deltas confirm zero regressions across the
benchmark. The rule lands on default-true only when every doc is ≥ current.
Documented in the gated-eval protocol; same shape as the chunk-context fix
protocol the reviewer suggested.

---

### Lesson 11 — Silent system/GT convention disagreements resolve in GT's favor every eval run, by default.
**(2026-05-04 evening, after section 12 audit produced a real architectural finding instead of an F1 delta)**

The deepest lesson of the week, and the one that explains why the previous
ten read the way they do.

When the system's encoded model of reality differs from the GT's encoded model
of reality on a field, every eval run resolves that disagreement — by scoring
the system against GT and crediting only the GT convention. The eval cannot
surface the disagreement because it doesn't know one exists. It just scores.

This means: until someone names a convention disagreement, the system is
being implicitly forced to encode the GT's convention, *whether or not anyone
deliberately decided that was the right convention.* Every prompt edit, every
schema-coercion alias, every enrichment match that "improves F1" against
unverified GT is potentially optimizing harder against a convention nobody
checked. The +1pp F1 lands; the convention question stays invisible.

The section 12 audit didn't fix anything. What it did was make a
previously-invisible decision visible: TriNet/Insperity belong in the carrier
slot per GT, in the claims_administrator slot per insurance reality. Until
today, the system was being silently forced to use GT's convention via the
F1 reward signal. Now it isn't — the disagreement is named, the question is
explicit, and someone with authority over the schema can answer it
deliberately.

**Standing rule**: every audit finding's first deliverable is making the
disagreement explicit. F1 movement is downstream of resolving the
disagreement, not upstream of it. An audit that produces a +1pp F1 delta
without surfacing what convention question was answered to get it should be
treated with suspicion — the F1 may be downstream of an unverified
convention choice that was made silently by whoever picked the eval rule.

**Operational implication**: audits produce *decisions-needed*, not
*defects-fixed*. The PROMPT_AUDIT_FINDINGS_PENDING.md file is where these
land. Findings stay there until someone with schema authority resolves the
convention question. *Then* the F1 work is grounded — every subsequent
optimization is against a convention someone deliberately chose.

**Why this is the deepest lesson of the week**: every previous lesson is
about preventing the system from gaming itself (eval rules, prompt edits,
post-processors, derivation layers, enrichment matchers). This one is about
preventing the *measurement* from silently encoding business decisions that
weren't made by anyone — including by the model, by the engineer, or by the
customer. The GT is just an artifact someone produced at some point under
some convention. The eval treats it as truth. Until an audit asks "is this
GT convention what we actually want?" the answer is whatever the GT happens
to encode.

**What this means for project-level health**: the headline F1 number is only
as defensible as the convention questions that produced its GT. As long as
audits keep producing convention-disagreement findings without a decision
channel for resolving them, the F1 number compounds against unverified
conventions. The bottleneck this creates is not a measurement problem — it's
an organizational problem. F1 moving isn't the goal; F1 moving against
conventions someone deliberately chose is the goal.

---

### Lesson 10 — Per-edit A/B tests at the layer where the change occurs, never through downstream merges.
**(2026-05-04 afternoon, section 12 prompt edit revert)**

Edited section 12 of the prompt. Structural correction was right: TriNet/Insperity
moved from PEO-duplicated-in-both-slots to PEO-only-in-claims-administrator with
honest carrier abstention. Tested through the full pipeline (voter → flatten →
derive → coerce → enrich → eval). TriNet doc F1 dropped 80% → 20%. Reverted
per the standing acceptance criterion.

Then realized the regression wasn't from the prompt edit at all. The voter
merges 4 sources (winner / v5_proper / router / cell_as_atom). Only the winner
source updates with a prompt edit. The other three were days old, still
showing the pre-edit wrong-slot extraction. The voter merged today's correct
extraction with yesterday's wrong extraction, producing hybrid outputs that
were worse than either alone. The test path itself was the confound.

The narrow framing ("voter sources need to be synchronized") is true but
misses the class. The broader rule:

**Standing rule**: *for any change, identify the smallest pipeline subset that
contains the change's effect, and test against that subset only.* Downstream
layers that exist between the change and the eval are confounds — pin them
to a fixed baseline or exclude them from the test path.

| Change at layer | Test path |
|---|---|
| Prompt edit (extraction layer) | extraction → flatten → eval (no voter, no downstream merges using non-fresh inputs) |
| Schema-coercion alias addition | post-extraction-from-fixed-snapshot → coerce → eval |
| Derivation rule (combined-totals etc.) | fixed-snapshot → derive → eval |
| Enrichment matcher change | fixed-snapshot → enrich → eval |
| Eval rule change | fixed extraction snapshot → existing pipeline → eval |

The voter belongs in **production** for the headline number (it's the
configuration that produces the best per-doc output). It belongs in the
**test path only when the test path's other inputs are also fresh**. For
per-prompt-edit testing, that condition almost never holds — the other
voter sources weren't run with the edited prompt.

**Operational discipline**: every layer in the pipeline is a candidate confound.
Schema-coerce, compute_combined_totals, carrier_enrich — same shape as the
voter. Before running an A/B for a change at layer L, list every layer
between L and the eval, decide for each whether it's pinned (using a fixed
input from before the change) or fresh (using the current change's output).
Mixing pinned + fresh non-deterministically is the worst-of-both-worlds case.

**Sub-rule (the strict-number measurement path)**: the strict F1 number must
be measured via `winner_only_eval.py` (fresh pipeline from
`output_lighton_qwen_hybrid` → flatten → derive → coerce → enrich → eval) with
soft eval rules disabled. NOT via `eval_vs_gt.py` directly pointed at
`output_voter_flat` — that path reads from a stale voter snapshot and produces
a measurement-path artifact that drifts over time without anyone editing the
extraction. 2026-05-04 reported "87.2% strict at eef3cfe"; 2026-05-05
discovered that path was stale and the proper strict at the same commit on
the fresh path is 88.5%. The two numbers aren't comparable; the second is
correct, the first was technically wrong (same shape as Lesson 10 applied to
my own measurements).

**Cost of skipping**: a structural correction that improves the system gets
reverted because the test path mixed live and stale data and reported a
spurious regression. Section 12 edit was reverted today on a -23.6pp signal
that turned out to be 100% measurement artifact, 0% prompt-edit effect.

**The headline F1 reporting discipline pairs with this**: paired strict +
system numbers stay in the headline. The system number uses the full pipeline
including the voter, which requires synchronized sources. If the voter
sources aren't synchronized at the time of measurement, the system number
isn't reportable until they are. That's a known-cost batch operation that
runs at release boundaries or when a prompt edit is expected to materially
change a voter source — not on every prompt edit.

---

### Lesson 9 — Recovery code targeting one doc or carrier is a hardcoded answer key, regardless of size.
**(2026-05-04 morning, Hartford pivot logo-classifier scope reframe)**

When investigating Hartford pivot extraction (carrier slot returns wrong value),
the third-time-this-week temptation surfaced: write a small `disambiguate_hartford_from_boilerplate()`
that detects the legal-boilerplate "guarantee of payment by The Hartford" string
in Strategic doc and overrides `document.carrier.name`. Different shape from
last week's deleted `carrier_disambiguation.py`, same essence.

The pattern to recognize: **any code that special-cases a single document, a
single carrier, or a single layout to recover a field that isn't generally
present in the data is gaming, regardless of how small or "obvious" the
special case looks.** The smaller the special case, the more tempting and the
harder to notice as gaming.

**Standing rule**: when the data isn't recoverably present in the document,
the correct system behavior is **abstention with diagnostic** (`null` value +
top-k logging + `status: no_clean_match`), not heuristic recovery code.
F1 cost is acceptable; gaming cost compounds.

**Sub-rule**: before adding any function whose name contains a specific carrier,
doc, or format identifier — `disambiguate_hartford_*`, `fix_insperity_*`,
`detect_arrowhead_layout` — stop. Ask: "would this function exist if the input
were a carrier I haven't seen yet?" If no, it's gaming. The right shape is a
generic mechanism (logo classifier with abstention, Levenshtein-vs-known-list,
schema-coercion alias) that *happens* to handle the specific case as one of
many, not a function targeted at the specific case.

**Cost of skipping**: Hartford-pivot F1 number rises by 3-5pp on the benchmark,
zero generalization to the next carrier with the same failure pattern (white-
label TPAs, redacted reports, internal copies with stripped branding), and the
codebase accumulates one more function that has to be ripped out next time
someone audits for hardcoded answer keys.

---

### Lesson 8 — F1 numbers compare only against matched state.
**(2026-05-03 evening, "92.5% same number" claim caught by clean A/B regression)**

Reported "92.5% same as old-prompt baseline" mid-session. The "92.5% old-prompt
baseline" had been generated under varying intermediate eval state — different
DOC_FIELD_MAP entries, different alias paths active, different intermediate
output dirs. When I ran a clean A/B with stable pipeline + locked eval against
both old-prompt and new-prompt extractions, the actual delta was 91.50% → 92.50%
(+1pp, +6 fields recovered). The earlier "no change" reading was correct only
against the *wrong* comparison.

This is a different shape from Lessons 1, 6, 7 (all about attribution). This
one is about **measurement comparability**: the same number, reported at two
different times against two different intermediate states, treated as if
comparing one thing.

**Standing rule**: any F1 number reported in this project must be paired with
the commit hashes for the eval pipeline state, the prompt state, and the
post-processor state at the time of measurement. Two numbers can only be
compared head-to-head if they share the same hashes for everything except the
variable under test.

**Format for any F1 claim going forward**:
> *"92.50% F1 (eval@`<hash>`, prompt@`<hash>`, post-processors@`<hash>`)"*

For an A/B comparison, both numbers carry the same hash for everything except
the variable: *"old-prompt 91.50% vs new-prompt 92.50% (eval@`<same-hash>`,
post-processors@`<same-hash>`)"*. If a hash is missing, the comparison isn't
defensible — re-measure with locked state before reporting.

**Cost of skipping**: a "no F1 change" claim that was true against a moving
target and false against a clean baseline. The +1pp gain almost went unreported.
Worse: the +1pp gain wouldn't be replicable later because the intermediate
states it was measured against don't have a hash to revert to.

---

### Lesson 7 — One prompt-caused incident is evidence of more.
**(2026-05-03 evening, A/B test confirms cause/cause_of_injury drift was prompt-caused)**

The third prompt-caused incident in three days. Two of them (loss_ratio `2.24`,
schema-key drift `cause`) traceable to the same line on `EXTRACTION_AGENT_PROMPT_V4_SCHEMA.md:202`.
The third (Fall/Slp expansion) was caused by *absence* of a verbatim-preservation
rule — different shape but same root: the prompt file wasn't reflecting how the
extraction-vs-GT contract should work.

When a prompt-caused incident is confirmed once, the rest of the file is suspect.
The temptation is to patch the offending line, run regression, claim victory.
That's the same mistake as patching one eval rule when the eval design is the
problem.

**Standing rule**: confirmed prompt-as-cause triggers a full audit pass on the
prompt file, not just a line patch. Each section of the prompt is inspected
for: (a) convention conflicts with GT, (b) implicit canonicalization where GT
preserves, (c) carried-over instructions from earlier versions without
reconciliation. Each audit finding becomes a separate commit with rationale,
gated by a regression eval. Skipping the audit lets the next incident surface
"by accident" months from now.

**Cost of skipping**: the same prompt edit appears as fixes to three different
"unrelated" failures over months, each fix done in isolation, none of them
catching the others. Compound investigation cost vs one focused half-day audit.

**Caveat (added during the same incident's writeup)**: the A/B test demonstrated
that the prompt edit *fixed* the cause/cause_of_injury schema-key drift. It did
NOT prove the original line 202 (decimal-conversion instruction) was the
*specific causal mechanism*. Possibilities: removing the line cleared attention
budget; the new verbatim-preserve rule primed canonical naming; the wording
change shifted the model's schema-attention in a way that's hard to localize.
The audit is warranted because of the prompt's other confirmed-causal incidents
(loss_ratio decimal, Fall/Slp expansion), not because line 202 has been proven
to be the unique cause of every observed drift. **Don't retrofit a "line 202
caused everything" narrative onto evidence that's actually "this region of
the prompt is brittle."** That distinction matters for the audit's scope.

**Major retraction (2026-05-03 evening, post production re-extraction)**: the
A/B test result was *confounded*. My harness's `build_user_content()` differed
from production's `extract()` in three places I missed: the wrapper opening
phrasing, an entire GROUNDING block (`"OCR is your source of truth for tokens;
the image gives you spatial/columnar layout."`), and a closing marker. Test B
removed *both* the decimal-conversion line *and* this wrapper material. Cannot
attribute the canonical result to the prompt edit alone. The full re-extraction
in production confirms: the prompt edit fixes loss_ratio (224 instead of 2.24)
but does NOT fix the cause-drift (chunk[2] still emits 5/5 `cause` instead of
`cause_of_injury`). The schema-coercion layer remains load-bearing.

This is itself another instance of Lesson 6: claimed "production-conformant"
without byte-for-byte diffing the wrapper text. The pre-experiment checklist
caught `max_tokens` and the OCR-text feed but missed three other differences.
**Sub-rule**: when the comparison is "harness vs production," diff the
literal byte content of every text component the model receives, including
wrapper/grounding/closing instruction text. The prompt file isn't the only
text the model sees.

---

### Lesson 6 — Read your own code before attributing failure to the model.
**(2026-05-03, evening — loss_ratio prompt-instruction discovery)**

Spent half a day building a defensible mental model: "VLMs trained on web-scale
text habitually normalize what they see; this is a category." Codified it as
Lesson 3, planned a prompt-level "preserve verbatim" mitigation. Then opened
the actual prompt to make the edit and found line 202 explicitly instructing
`224% → 2.24 (decimal)`. The model wasn't normalizing on instinct; it was
following a prompt instruction nobody had reconciled against GT. The "category"
hypothesis was clean, defensible, generalizable, and *wrong as applied to
loss_ratio*.

This is the same shape as Lesson 1 (eval verdict ≠ JSON truth): a *summary
view* (the lesson statement, the eval miss report) suggested a clean story; the
*underlying artifact* (the actual prompt text, the raw JSON's parent dict)
contained the truth. Twice in three days I reached for a model-behavior
explanation when the answer was sitting in my own code.

**Standing rule (investigation-order practice)**: when a failure pattern looks
like it could be model behavior, the first three things to check — in this
order — are the prompt, the eval rules, and the post-processors. The model is
the LAST hypothesis, not the first. The cost of yesterday and today wasn't
unsupported writeups; it was that investigation went down a wrong path before
anyone re-read the prompt file. Reach for prompt-inspection before model-
explanation by reflex.

**Standing rule (writeup discipline)**: any "model behavior" claim in a writeup
must cite the prompt section and code path that did NOT cause it. If you can't
cite, you haven't checked. The writeup discipline is the artifact that proves
the practice was followed.

**Standing rule (caveat calibration)**: before writing any caveat — including
"reconstruction may be imperfect" or "I'm not sure" — ask: *what specific
evidence would change my confidence here, and do I have it?* If grep-confirmed
verbatim text exists, the caveat is overcautious. If grep-confirmed evidence is
absent, the caveat is appropriate. Both over- and under-confident caveats are
calibration errors; the fix is the same — caveats proportional to actual
epistemic state. (Today's "reconstruction caveat" was under-confident; this
week's previous incidents were over-confident.)

**Standing rule (verify before reporting on long-running jobs)**: when a
long-running job claims completion, spot-check the underlying artifact for the
property the job was supposed to change BEFORE reporting results. Open one
output file, grep for the specific behavior you expected, confirm it landed.
The eval/pipeline summary number can match the *previous run's* expected output
even when the current run silently no-op'd via cache. Cost of skipping: a
half-hour of cache-replay reported as "re-extraction with new prompt." Same
shape as Lesson 1 (eval verdict ≠ JSON truth) but at the pipeline-job level
instead of the field level.

**Sub-rule (multi-layer cache discovery)**: pipelines often have multiple
cache layers — per-page, per-chunk, per-doc-output, per-eval-result. Clearing
one layer leaves the others to short-circuit re-execution. When invalidating
cache for a re-run, scan the script for ALL `if cache.exists(): continue` /
`if path.exists(): use_cached(...)` patterns first, then clear every layer
that would skip the model invocation. The log message that catches this:
`[doc] X — cached` (or equivalent) when you expected the model to run.
2026-05-04: caught this twice in two days — chunks_lighton_qwen layer
yesterday, output_lighton_qwen_hybrid layer today. Same lesson, different
cache layer. Adding to discipline going forward: any cache-invalidating
command operates at script-level, not at the surface I happen to be thinking
about.

**Cost of skipping**: a half-day prompt fix described as a generalizable
model-behavior law, plus verbatim-preserve instructions added to the prompt
that may now over-correct on cases where light normalization was actually
correct (dates `1/2/24` → `2024-01-02`, currency `$3,547.48` → numeric, status
`Closed - Settled` → `closed`). Mitigation queued as a Day 2 task: regression-
test the new prompt across all 9 docs against the prior prompt's extractions;
any field that lost ground is collateral and needs to be exempted or moved to
a derivation layer.

---

### Lesson 5 — Two distinct numbers, always paired.
**(2026-05-03, after public correction of inflated headlines)**

Reporting a single F1 number for "the system" obscures whether what's being
measured is what the model extracted vs what the pipeline produced. Mixing them
caused the inflation that took two rounds of review to surface.

**Standing rule**: every F1 claim ships as a pair: **strict** (raw VLM
extraction, no derivation, no soft eval rules) AND **system** (full pipeline
including derivation + generic eval normalizations). Both numbers, every time,
with the "what's included" note. Never just one.
