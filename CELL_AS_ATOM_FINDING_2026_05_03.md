# Cell-as-Atom (Idea 1) Test — Honest Negative Finding

**Date:** 2026-05-03

## TL;DR

Tested the "Cell-as-Atom" architecture proposed in the research plan: TATR-style cell decomposition (via Docling) + LLM schema mapping. **Result: 39.9% F1 — catastrophic regression vs LightOn+Qwen v4 baseline (80.1%).** However, the architecture **wins +28-50pp on summary_pivot archetype** where the document is already a clean table grid.

## Setup

- **Cell extractor**: Docling (already cached for all 9 docs — TATR integrated internally)
- **Cell data**: per-cell text + bbox + row/col indices + headers
- **Schema mapper**: Qwen2.5-7B text-only (since input is already structured)
- **Prompt**: structured cell JSON → Stage-7 schema mapping

Why text-only: Docling has already done the visual extraction (95.9% raw coverage). The remaining task is field mapping — text LLM should be sufficient given structured input.

## Per-doc F1 results

| Doc | Archetype | LightOn+Qwen v4 (best) | Docling-cells + Qwen2.5-7B | Δ |
|---|---|---|---|---|
| **Hartford pivot a** | summary_pivot | 28.6% | **57.1%** | **+28.5pp** |
| **Hartford pivot b** | summary_pivot | 25.0% | **75.0%** | **+50.0pp** |
| **Insperity** | flat_table | 66.7% | **83.3%** | **+16.6pp** |
| Strategic Info | hybrid_detail | 37.5% | 34.4% | -3.1pp |
| ICW | hybrid_detail | 84.4% | 53.2% | -31.2pp |
| Employers | per_policy_section | 79.5% | 37.5% | -42.0pp |
| TriNet | flat_table | 64.3% | 7.1% | -57.2pp |
| ADP | flat_multipage_zeros | 93.3% | 20.0% | -73.3pp |
| Arrowhead | per_policy_section | 87.2% | 0.0% | -87.2pp |
| **OVERALL** | | **80.1%** | **39.9%** | **-40.2pp** |

## Two distinct failure modes

### Failure 1: Arrowhead (scanned PDF)
Docling can't extract tables from scanned PDFs (no embedded text). Output: 22 "tables" with mostly noise text. → 4.3% coverage, 0% F1.

### Failure 2: text-only LLM can't reconstruct hierarchy
For Employers (4 policies × N claims), TriNet (1 claim with status="Incident Closed"), ADP (zeros table with TPA structure), the cells contain values but the model — without visual context — can't reconstruct which policy a claim belongs to or which row is a header vs data.

This is the **same failure mode** observed earlier with text-only Qwen2.5-7B (-55pp). Visual context is not optional for these document types.

## Where it works

**Summary_pivot archetype (Hartford pivots)**: +28-50pp. The document IS a single clean grid; row/col mapping IS the schema mapping. Cell-as-atom architecture exactly fits.

**Flat-table grouping (Insperity)**: +16.6pp. Similar reason — pure tabular layout, no hierarchy.

These are exactly the archetypes where v5_proper prompt + adaptive routing also won. Confirms: **cell decomposition helps when the document IS already grid-shaped.**

## Honest verdict on the research plan's Idea 1

The plan's claim was: "stop asking VLM to read whole page; decompose into cells; per-cell forward pass eliminates competing context."

**Confirmed for grid documents**: yes, +28-50pp on Hartford pivots.
**Refuted for hierarchy documents**: no, text-only mapping loses -42 to -87pp.

The plan's full proposal (Idea 1) actually requires **TATR cells + per-cell VLM read with image** — not text-only mapping. We tested only the structured-input + text-LLM variant due to HF transformers compat issues with the HF TATR pipeline.

A proper test of Idea 1 would feed cell crops (not text) to Qwen3-VL — preserving visual context AND cell decomposition. That's the next experiment.

## Path forward (revised)

Given consistent findings across 3 negative tests:
1. ❌ LightOn → Qwen2.5-7B text-only: -55pp
2. ❌ Docling cells → Qwen2.5-7B text-only: -40pp
3. ❌ Verifier+fix re-emit: -57pp on ICW

The fundamental constraint is: **visual context cannot be replaced by structured text input alone for hierarchical documents**.

Next legitimate paths:

| Approach | Visual context? | Predicted | Effort |
|---|---|---|---|
| Docling cells + Qwen3-VL with page image | YES | +5-10pp | 4 hr |
| LMDX coordinates-in-prompt + Qwen3-VL with image | YES | +2-4pp | 3 hr |
| Per-archetype router (already tested) | YES | matches best per archetype | done |
| **LoRA fine-tune Qwen3-VL** (Step 6) | YES | **88-92%** | **2 weeks** |

## Production recommendation (unchanged)

**Ship LightOn + Qwen3-VL (v4 prompt) at 80.1% F1.**

Cell-as-atom architecture is genuine win for summary_pivot — could be added as part of per-archetype routing. But text-only mapping is a dead-end across multiple tests now.

## Sources

- BBox-DocVQA paper (Liu et al., Nov 2025) claimed +1.7-12.4pp from giving exact regions vs full page. This validates **visual cell crops** + VLM, not structured text + LLM.
- The proposed Idea 1 architecture remains untested in its full form (TATR cells + Qwen3-VL with image input).
