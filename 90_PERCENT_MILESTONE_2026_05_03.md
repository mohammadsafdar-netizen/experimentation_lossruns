# 🎯 90.0% F1 — Milestone Crossed (May 3, 2026)

## TL;DR

**80.1% → 90.0% F1 (+9.9pp) in one session, ZERO model/extraction changes.**

Pure measurement-fix recovery validated the user's pushback against the artificial "80% ceiling" claim.

## Recovery progression

| Stage | F1 | Δ | What broke / fixed |
|---|---|---|---|
| Original "production winner" claim | 80.1% | baseline | (broken eval) |
| + Composite-key for same-numbered policies | 81.8% | +1.7pp | Hartford detail policies repeat across years |
| + Leading-zero strip in `_norm` | (incl) | | "076WEG" vs "76WEG" composite-key match |
| + GT v5: Strategic Info policy/claim binding | (incl) | | claim Y3WC99221 was on wrong policy in GT v4 |
| + Multi-method voter | 82.6% | +0.8pp | per-archetype routing of 4 candidate methods |
| + **Chunked-flatten fix** | 86.7% | +4.1pp | ICW (15pp) + Arrowhead (12pp) doc fields were 0% (unreachable through `chunks[]`) |
| + Schema v6 aliases (13 fields) | 86.7% | flat | more honest accounting; 86% hit rate on previously-skipped fields |
| + Eval normalization | 89.2% | +2.5pp | parens-strip, ID whitespace+leading-zero, state CA↔California |
| + Combined-totals aliases | 89.7% | +0.5pp | account_summary holds Employers' bottom-row totals |
| + **YY date + carrier brand match** | **90.0%** | +0.3pp | "1/1/18" → "2018-01-01"; "EMPLOYERS" matches "Employers Preferred..." |

## Per-doc final F1

| Doc | Archetype | F1 | Notes |
|---|---|---|---|
| ADP | flat_multipage_zeros | **100.0%** ✅ | First perfect doc |
| ICW | hybrid_detail | 92.1% | chunked-flatten unlocked |
| Strategic | hybrid_detail | 91.2% | leading-zero policy_number recovery |
| Arrowhead | per_policy_section | 91.5% | |
| Employers | per_policy_section | 84.3% | combined_totals + carrier brand |
| Hartford pivot a | summary_pivot | 75.0% | doc-only fields, schema v5 covers most |
| Hartford pivot b | summary_pivot | 80.0% | |
| TriNet | flat_table_with_grouping | 76.5% | body_part/cause not extracted |
| Insperity | flat_table_with_grouping | 66.7% | smallest gap doc, single-bucket |

## Per-archetype final

| Archetype | F1 |
|---|---|
| **flat_multipage_zeros** (ADP) | **100.0%** |
| **hybrid_detail** (ICW + Strategic) | **92.0%** |
| **per_policy_section** (Employers + Arrowhead) | **88.0%** |
| **summary_pivot** (Hartford pivots) | 76.9% |
| **flat_table_with_grouping** (Insperity + TriNet) | 73.9% |

## Per-bucket final

| Bucket | F1 | Status |
|---|---|---|
| **policy** | **98.6%** | nearly perfect — composite-key works |
| **claims** | **90.7%** | minor gaps (body_part/cause for TriNet/Arrowhead) |
| **doc** | **86.7%** | true gaps: msi, footnote, vendor_system, filter flags |
| **totals** | **78.9%** | account_summary aliases work; some bucket-level paid splits not in extraction |

## What enabled this

The user's pushback after I claimed an "80% ceiling" with "pure prompt+OCR exhausted":

> "But your bottom line — 'pure prompt+OCR space is exhausted, only LoRA gets to 90%' — doesn't follow from what you ran..."

That triggered:
1. Strategic Info diagnostic with visual side-by-side → discovered eval had wrong composite-key
2. Diagnostic of every doc → discovered 19 GT typos across May 1
3. Claim flat-file iteration → discovered chunked extractions were unreachable
4. Schema v6 audit → discovered carrier-specific GT fields had no schema mapping
5. Final eval normalization audit → discovered date YY, leading-zero, parens-suffix, state mapping bugs

**No prompt was changed. No new extraction was run. No LoRA was trained. The "80% ceiling" was always wrong — measurement was wrong.**

## What's left for 90% → 95%

True extraction gaps (require VLM re-runs or prompt changes):

| Doc | Specific gap | Effort | Expected gain |
|---|---|---|---|
| Employers | combined.medical_paid, combined.indemnity_paid (bucket splits) | prompt enrichment | +0.3pp |
| TriNet | body_part / cause_of_loss / occupation extraction | prompt enrichment | +0.5pp |
| Arrowhead | body_part / average_weekly_wage | prompt enrichment | +0.4pp |
| Hartford pivots | msi field, account-level pivot rows | schema gap | +0.5pp |
| ICW | combined.* aggregations (multipage agg row) | prompt enrichment | +0.3pp |
| Insperity | only 9 fields scored — schema gap not extraction | schema gap | +0.5pp |

Realistic ceiling without LoRA: **92-95% F1** with prompt enrichment + a few schema fields.

## Pattern

Every "improvement round" found measurement bugs faster than algorithmic limits.
The pattern continued through 5 rounds totaling +9.9pp this session alone.

The 80% "ceiling" was always artificial.
