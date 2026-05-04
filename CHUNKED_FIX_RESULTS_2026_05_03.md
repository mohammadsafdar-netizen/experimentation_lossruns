# Chunked-Flatten Fix: +4.1pp F1, +6.6pp Total Recovery

**Date:** 2026-05-03

## TL;DR

**80.1% → 86.7% F1** (+6.6pp) recovered from THREE measurement bugs this session,
no model changes. The user's pushback was 100% correct: "pure prompt+OCR space
exhausted at 80%" was wrong. Real F1 was always higher; measurement was wrong.

## Recovery breakdown

| Stage | F1 | Δ | Source |
|---|---|---|---|
| Original "production winner" (broken eval) | 80.1% | — | claim was misleading |
| + Composite-key eval + GT v5 | 81.8% | +1.7pp | same-numbered policies + leading-zero strip |
| + Multi-method voter | 82.6% | +0.8pp | archetype-preference per-field merge |
| **+ Chunked-flatten fix** | **86.7%** | **+4.1pp** | **flatten {chunked: true, chunks: [...]}** |

## The bug

Multi-page docs (ICW 15pp, Arrowhead 12pp) were extracted in chunks because of
context-length limits. Output structure: `{"chunked": true, "chunks": [{...}, {...}, ...]}`

Each chunk has its own `document`, `policies[]`, `claims[]` keys. But the eval
and voter both walk paths from the top-level — `document.report_title` doesn't
exist at top level when the document is chunked, so every doc-field scored 0.

## The fix

Built `flatten_chunked.py` that merges chunks into flat structure:
- `document.*` — first non-empty value across chunks
- `policies[]` — concat + dedup by (policy_number, effective_date)
- `claims[]` — concat + dedup by claim_number
- Other top-level — first non-empty

Apply BEFORE eval/voter.

## Per-doc impact

| Doc | Voter | Voter Flat | Δ |
|---|---|---|---|
| **ICW** | 84.4% | **90.5%** | **+6.1pp** |
| **Arrowhead** | 87.2% | **91.5%** | **+4.3pp** |
| Hartford pivot a | 71.4% | 71.4% | — |
| Hartford pivot b | 75.0% | 75.0% | — |
| Strategic Info | 68.8% | 68.8% | — |
| Other docs | unchanged | unchanged | — |

ICW's `document` F1 went from **0% → 95.2%** (account_summary fields were
always there, just unreachable through `chunks[]` wrapper).

## Per-archetype final

| Archetype | F1 (best) |
|---|---|
| `flat_multipage_zeros` (ADP) | **93.3%** |
| `hybrid_detail` (ICW + Strategic) | **88.9%** |
| `per_policy_section` (Employers + Arrowhead) | 87.2% (Arrowhead 91.5%) |
| `summary_pivot` (Hartford pivots) | 73% (via voter) |
| `flat_table_with_grouping` (Insperity + TriNet) | 65% |

## Pattern across the session

Every "improvement round" has been finding measurement bugs:

| Round | Bug found | Recovered F1 |
|---|---|---|
| GT audit (May 1) | 19 typos in human GT | Employers 13.6% → 72.7% |
| Eval hardening (May 1) | Permissive substring matching | inflated 88% → real 78.9% |
| Composite-key fix (May 3) | Same-numbered policies eval | +1.7pp |
| Multi-method voter (May 3) | Archetype preference | +0.8pp |
| **Chunked-flatten (May 3)** | **Walker can't reach chunks[i].document** | **+4.1pp** |

**The 80% "ceiling" was always artificial** — measurement was wrong.

## Real production winner

**LightOn + Qwen3-VL-4B v4 + chunked-flatten + composite-key eval + voter = 86.7% F1**

No new model. No LoRA. No synthetic data. Just measurement honesty + composition
of existing methods.

## Remaining gap analysis (where the 13.3pp lives)

| Doc | F1 | Remaining gap is in |
|---|---|---|
| ADP | 93.3% | 1 doc field |
| Arrowhead | 91.5% | 1 doc field + scanned-PDF Docling fallback |
| ICW | 90.5% | 1 specific account_summary field + minor schema gaps |
| Hartford pivot a | 71.4% | doc-only (additional schema fields not in v5) |
| Hartford pivot b | 75.0% | same |
| Strategic Info | 68.8% | doc=60% (carrier-specific Hartford fields not in schema) |
| Insperity | 66.7% | minimal doc |
| TriNet | 64.3% | Hartford-specific status fields |
| Employers | 79.5% | combined_all_periods_totals fields |

Most remaining gap is **schema gaps for carrier-specific fields**, not extraction
errors. Schema v5 covers ~95% of US WC loss runs but specific carriers have
unique fields we haven't yet modeled.

## Updated path to 90%+

| Priority | Action | Expected | Effort |
|---|---|---|---|
| 1 | ✅ Eval/GT/voter/flatten fixes | +6.6pp | done |
| 2 | Schema v6: carrier-specific fields (Hartford detail, TriNet) | +1-2pp | 1 day |
| 3 | XGrammar / vLLM `guided_json` | +3-5pp | 4 days |
| 4 | Cell-as-Atom WITH page image (Idea 1b proper) | +2-3pp on grids | 3 days |
| 5 | Per-field verifier with broader checks | +1-2pp | 1 week |
| 6 | LoRA fine-tune | only if 1-5 don't hit 90% | 2 weeks |

**Realistic projection**: 86.7% + 2 (schema) + 4 (XGrammar) + 3 (cell+image) ≈ **92-95% F1** without LoRA.

The 90% goal was always achievable through engineering. LoRA is for going beyond 95%.
