# Table Extractor Comparison — Loss Runs (May 4, 2026)

> **What this measures:** for each PDF, how many ground-truth values appear (substring match after non-word stripping) in the extracted table cells. This is the **upper-bound** F1 a perfect schema-mapper could achieve on top of each tool's output. If a value isn't present in any cell, no downstream parser can recover it.

**Hardware:** RTX 3090 (CPU for all tools except docling's TableFormer). All tools run on the source PDF in `data/loss_runs/`.

**Source:** `experiments/26_verification_ui/compare_table_extractors.py`

---

## Per-tool × per-doc upper-bound

| Tool | Insperity (PEO summary, digital, 2pg, 12 GT) | Employers (digital, row-per-claim, 1pg, 94 GT) | Arrowhead (scanned, multi-section, 12pg, 105 GT) | ICW (scanned, form-per-claim, 15pg, 345 GT) |
|---|---|---|---|---|
| **docling** (TableFormer) | 8.3% / 5.3s | 84.0% / 7.1s | 24.8% / 17.8s | **92.2% / 20.8s** |
| **pymupdf** (find_tables) | 8.3% / 0.2s | **90.4% / 0.3s** | **0.0%** (no text layer) | 35.4% / 0.3s |
| **pdfplumber** (extract_tables) | 8.3% / 0.1s | **90.4% / 0.1s** | **0.0%** (no text layer) | 52.8% / 0.5s |
| **unstructured** (hi_res + detectron2) | 0.0% / 4.5s | 87.2% / 6.7s | **60.0% / 29.8s** | 80.9% / 30.5s |
| **yolo+docling** (DocLayout-YOLO crops → docling cell-OCR) | — | 79.8% / 21.2s | **48.6% / 49.6s** | 91.9% / 61.4s |
| paddleocr | (skipped — formula-recognition model auto-download stalled at 0%) | | | |

**Insperity ceiling = 8.3%** is intrinsic — the doc has 12 GT values and 11 of them are document metadata (file_name, carrier, archetype, broker) that never appear in tables. All four tools that find the one table cap there.

## Headline findings

### 1. No single tool wins everywhere

| Archetype | Best tool | Margin |
|---|---|---|
| Digital row-per-claim (Employers) | **pdfplumber** (90.4% in 0.1s) | +6pp vs docling, **70× faster** |
| Scanned form-per-claim (ICW) | **docling** (92.2%) | +11pp vs unstructured |
| Scanned multi-section (Arrowhead) | **unstructured** (60.0%) | +35pp vs docling, +∞ vs pymupdf/pdfplumber (which return 0) |
| PEO summary (Insperity) | tied at intrinsic ceiling | — |

**Implication for production:** the right architecture is **per-archetype routing**, not "pick one tool." A page-level layout classifier (DocLayout-YOLO or similar) selects the appropriate tool per region.

### 2. PDF text layer is a hard divider

| Has text layer? | Winner | Loser |
|---|---|---|
| ✅ Yes (Employers) | pdfplumber/pymupdf (read text directly) | docling (forced OCR loses chars) |
| ❌ No / scanned (Arrowhead) | unstructured (detectron2 layout + OCR) | pdfplumber/pymupdf (return 0 tables) |
| ⚠️ Partial (ICW) | docling (best at form layouts) | pymupdf (35%) — sees some text but misses form cells |

### 3. YOLO+docling cascade is half-decent on Arrowhead but loses elsewhere

DocLayout-YOLO finds table regions on a page → crop each region → docling does cell extraction on the crop. Result:

- **Arrowhead: 24.8% (docling alone) → 48.6% (YOLO + docling)** — almost 2× recall improvement
- **ICW: 92.2% → 91.9%** — break-even
- **Employers: 84.0% → 79.8%** — slight regression (YOLO sometimes splits the single Employers table into multiple wrong crops)

The cascade helps where docling alone misses tables (Arrowhead's section detection is poor), and hurts where docling's full-page OCR is already finding everything (Employers, ICW).

## Practical recommendations

### Per-archetype routing (probable production path)

```
page → DocLayout-YOLO layout classification
   ├── digital + row-per-claim   → pdfplumber  (0.1s, 90% recall)
   ├── digital + form-per-claim  → docling     (20s, 92% recall)
   ├── scanned + multi-section   → unstructured (30s, 60% recall)
   ├── scanned + form-per-claim  → docling     (20s, 92% recall)
   └── narrative / summary       → VLM only    (no table extraction needed)
```

Implemented this way, expected:
- **Speed:** 70-90% of pages route to fast paths (pdfplumber). Mean per-page cost drops vs all-docling.
- **Quality:** ceiling for each archetype = best-per-archetype number above

### What this comparison does NOT cover

- **Per-cell semantic mapping** to our 75-field schema. The "upper bound" measures whether the value is *somewhere* in the cells — it does not measure whether a downstream parser can attribute it to the right schema field.
- **Form-per-claim with label+value combined cells** (ICW): docling correctly extracts cells, but cells contain `"Claim Number: 2025901234"` (label and value in one cell). Schema mapping requires a second stage to split label from value — see Landing AI's "structure-first table head" technique in `INSIGHTS.md`.
- **paddleocr** — install needed but blocked on a 100MB formula-recognition model auto-download. Add when bandwidth allows.

## Cross-reference

- Source: `experiments/26_verification_ui/compare_table_extractors.py`
- Cached results JSON: `experiments/26_verification_ui/table_extractor_comparison.json`
- Per-doc bbox caches: `experiments/26_verification_ui/bbox_cache_docling/` (3,370 regions across 38 pages)
- Production extractor (current winner — uses LightOnOCR + Qwen3-VL-4B, not these table tools directly): `experiments/28_alt_extractors/run_lighton_qwen_hybrid.py`
