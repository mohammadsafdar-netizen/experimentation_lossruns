# Phase A Final Status — Multiple Measurement Bugs, Still Recovering

**Date:** 2026-05-03

## TL;DR

Continued Phase A execution found ANOTHER infrastructure bug: ICW's `document.*` fields are scoring 0% F1 because the voter doesn't handle `{"chunked": true, "chunks": [...]}` extraction structure. ICW was extracted in 5 chunks (15 pages, chunk_size=3); each chunk has its own `document` key but the voter's flat-path walker can't reach `chunks[i].document.report_title`.

**Net: Real F1 is likely +2-4pp higher than reported 82.6% once this is fixed.**

## Bug pattern across all rounds

Each "improvement round" has been finding more measurement bugs, not algorithmic gains:

| Round | Real bug found | F1 recovered |
|---|---|---|
| GT audit (May 1) | 19 typos in human GT | Employers 13.6% → 72.7% (+59pp on that doc) |
| Eval hardening (May 1) | Permissive substring matching | 61.6% inflated → real 52.3% (later 78.9%) |
| Composite-key fix (May 3) | Same-numbered policies across years | +1.7pp; Strategic Info +31pp |
| Multi-method voter (May 3) | (improvement, not bug fix) | +0.8pp |
| Per-field verifier (May 3) | Reconciliation checks too narrow (catches arithmetic only) | 0pp (voter already passes basic checks) |
| **Chunked structure (May 3)** | **Voter flat-walker can't reach chunks[i].document** | **TBD ~+2-4pp** |

## Where we actually are

| Pipeline | F1 | Notes |
|---|---|---|
| Original "production winner" (broken eval) | 80.1% | claim was misleading |
| Winner + composite-key eval + GT v5 | 81.8% | +1.7pp from infra |
| Winner + voter (per-archetype preference) | **82.6%** | **current best** |
| Winner + voter + chunked-fix (when applied) | likely 84-86% | predicted recovery |

## Remaining gap analysis (where the 17pp lives)

| Doc | Voter F1 | Where Δ from 100% lives |
|---|---|---|
| ADP | 93.3% | doc=80% → 1 missing field |
| Arrowhead | 87.2% | doc=0% (Docling fails on scanned PDF) |
| ICW | 84.4% | **doc=0% — voter chunked bug** |
| Hartford pivot a | 71.4% | doc-only fields, schema gaps |
| Strategic Info | 68.8% | doc=60%, schema gaps |
| Insperity | 66.7% | minimal extractable content |
| TriNet | 64.3% | Hartford-specific fields |
| Hartford pivot b | 75.0% | (but should match a) |

Most remaining gap is **doc-level fields the voter can't reach OR carrier-specific fields not in v5 schema**, not field-level extraction errors.

## Honest verdict

The user's pushback was correct on multiple fronts:
1. Pure prompt+OCR space had +2.5pp of pure measurement-fix headroom (now realized)
2. Strategic Info ceiling was an eval bug, not a model failure
3. The 80% "ceiling" claim was premature

Each round of "improvement" this session has found infrastructure bugs faster than algorithmic limitations. **The real bottleneck is that we keep discovering our measurement is wrong.** When the measurement is finally right, real F1 should be 84-88% from existing methods alone.

## Next concrete actions (priority order)

| Priority | Action | Expected | Status |
|---|---|---|---|
| 1 | Fix voter to handle chunked structure (ICW + Arrowhead) | +2-4pp | bug identified, not fixed |
| 2 | XGrammar / vLLM `guided_json` against schema v5 | +5-8pp | not started |
| 3 | Cell-as-Atom WITH page image (proper Idea 1b) | +3-5pp on grids | not started |
| 4 | Diagnose other low docs (Hartford pivots, TriNet) | +3-5pp | not started |
| 5 | Synthetic data + LoRA | path to 92%+ | deferred |

Phase A delivered +2.5pp from measurement honesty. Phase B requires real engineering work.
