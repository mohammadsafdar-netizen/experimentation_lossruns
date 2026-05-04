# Project Insights — Document Extraction System

> **Living document.** Updated as experiments produce evidence.
> Latest update: 2026-05-04
> Hardware: NVIDIA RTX 3090 (24 GB), Python 3.11.14, PyTorch 2.11.0+cu130

This is the cross-task synthesis. For per-task details see `experiments/<n>_<name>/REPORT.md`.

---

## Loss-runs production state — May 4, 2026 (CURRENT)

> **What this section measures:** the loss-run sub-project against GT v6 (9 carrier docs, 75-field schema). This supersedes the Step-4 URF-builder numbers below as the current production benchmark for *this* sub-project. The URF-builder track is for ACORDs, a different corpus.

| Metric | Number |
|---|---|
| Production winner-only F1 vs GT v6 | **91.12%** (554/608) at HEAD `242e2d8` |
| Production strict F1 | 88.5% |
| Production extractor | LightOnOCR-2-1B (OCR pass) + Qwen3-VL-4B-Instruct (schema mapping). bf16, single 3090, ~10-30s/page baseline. |
| Schema | v5, 75 industry-standard fields covering doc metadata, policies, claims (identity / dates / financials / injury / examiner), combined-period totals. |
| Ground truth | v6 — second-pass-audited, 20 verified corrections. See `data/loss_runs/gt/AUDIT_CORRECTIONS.md`. |
| Bridge tests | 6/6 round-trip (date/money/status/ID/state/Jaccard). 5/5 derivation-boundary tests. |

### Per-archetype F1 (against GT v6)

| Archetype | F1 | Bottleneck |
|---|---|---|
| Form-per-claim scanned (ICW) | **95.6%** | label-value disambiguation in form cells |
| Multi-section scanned (Arrowhead) | **92.6%** | cross-section claim grouping |
| Detailed Hartford (Strategic) | **91.2%** | clean — high baseline |
| PEO summary (ADP) | 88.2% | multi-carrier disambiguation in PEO docs |
| PEO summary (Insperity) | 83.3% | 0 claims — only doc-level fields scored |
| PEO summary (TriNet) | 82.4% | multi-carrier disambiguation |
| Row-per-claim digital (Employers) | 82.0% | clean — high baseline |
| Hartford pivot summaries | **40-50%** | **carrier identity not on page** — unrecoverable |

### Findings from the May 4 ablation matrix (partial)

**Bbox-coordinates-in-prompt → REGRESSION** (`ABLATION_MATRIX_2026_05_04.md`, cell B). Adding 100-300 docling bbox regions per page to the Qwen3-VL prompt (per Landing AI's parse-once technique) DROPPED F1 from 91.12% → 88.65% (-2.47pp), and made inference 5-9× slower. Hardest hit: TriNet (-17.6pp), Arrowhead (-6.4pp), Strategic Hartford (-5.9pp). Hypothesis falsified for our setup — the model already gets spatial info from the image; piling bbox-text alongside image + LightOnOCR text creates reconciliation noise that exceeds the spatial-prior gain. **Not shipping.**

**Granite-4.0-3B-Vision and Dolphin-v2 swap-in tests:** blocked. Granite needs `transformers==4.57.6` (env upgrade required). Dolphin v2 produces empty output without its native two-stage prompt format. Both are ~30 min - 1 day of fix-up to retry. See `ABLATION_MATRIX_2026_05_04.md`.

### Table-extraction tooling comparison (`TABLE_EXTRACTOR_COMPARISON.md`)

Cell-level upper-bound recall against GT v6, by archetype:

| Tool | Digital row-per-claim (Employers) | Scanned multi-section (Arrowhead) | Scanned form-per-claim (ICW) |
|---|---|---|---|
| pdfplumber | **90.4% / 0.1s** ✓ | 0.0% (no text layer) | 52.8% |
| pymupdf | 90.4% / 0.3s | 0.0% (no text layer) | 35.4% |
| docling | 84.0% | 24.8% | **92.2%** ✓ |
| unstructured | 87.2% | **60.0%** ✓ | 80.9% |
| YOLO+docling cascade | 79.8% | 48.6% | 91.9% |

**No single tool wins.** Per-archetype routing (DocLayout-YOLO classifier → tool selection) is the suggested production path. **Note:** these are upper-bound numbers for a hypothetical perfect schema-mapper on top of each tool. The current production VLM pipeline ALREADY beats these for all-fields F1 because it also reads non-table content (headers, footers, free text).

### Active bottlenecks (May 4)

1. **Hartford pivot summaries (40-50% F1):** carrier identity is not on the page. No extractor or model can recover it. Architectural commitment is `_enriched.carrier.status = no_clean_match` with top-k Levenshtein candidates as diagnostic. Not a fix-able extraction failure — it's a bounded data limitation.
2. **PEO multi-carrier disambiguation:** TriNet/ADP/Insperity reference multiple carriers in body text. Domain-conversation pending (`PROMPT_AUDIT_FINDINGS_PENDING.md`); blocks 3 prompt-edit decisions.
3. **Form-layout label/value separation (ICW):** cells contain `"Claim Number: 2025901234"` (label and value combined). Production VLM handles this at 95.6% F1; structure-first table head (TATR) could push it higher.

### Cross-references

- `ABLATION_MATRIX_2026_05_04.md` — VLM × OCR-config matrix, including the bbox-grounding regression
- `TABLE_EXTRACTOR_COMPARISON.md` — docling/pymupdf/pdfplumber/unstructured/YOLO+docling head-to-head
- `LESSONS.md` — 11 codified lessons (cache invalidation, A/B discipline, namespace separation, etc.)
- `data/loss_runs/PROMPT_AUDIT_2026_05_03.md` + `PROMPT_AUDIT_FINDINGS_PENDING.md` — pending prompt edits
- `data/loss_runs/gt/AUDIT_CORRECTIONS.md` — GT v5 → v6 correction log
- `tests/winner_only_eval.py` — per-edit A/B eval (winner path bypasses voter)
- `tests/ablation_eval.py` — score any chunked output dir against GT v6
- Production extractor: `experiments/28_alt_extractors/run_lighton_qwen_hybrid.py`

---

## Bottom-line empirical state — REVISED (2nd time, post Step 4)

> **Latest update (2026-04-30, after Step 4 URF builder):** Added URF-builder-based extraction with multi-token regex span merger and fuzzy synonym matching. Engineering ceiling now matches what C5+C2 achieved earlier (~52%) but in the URF architecture.

> **Earlier correction (2026-04-30, mid-day):** The original "80%" number was an artifact of cherry-picked strict-format fields with n=10. **Credible methodology with n=84 tuning + n=42 holdout, balanced field types, bootstrap CIs, hold-out validation** gives a very different picture.

| Question | Answer (CREDIBLE, post Step 4) |
|---|---|
| Best engineering pipeline on real ACORDs | **URF builder + URF extractor** (Step 4) |
| Tuning split exact accuracy | **50.0%** (CI95: 39.3%–60.7%, n=84) |
| Held-out exact accuracy | **52.4%** (CI95: 38.1%–66.7%, n=42) — generalizes |
| Soft accuracy (Levenshtein) | 62.6% tuning, 65.8% holdout |
| Best per-type accuracy | **IDs 81.2%** (was 65% before span merger; multi-token assembly works) |
| Worst per-type accuracy | **Names 21.4% — no regex; needs learned NER (Step 6)** |
| Phone soft accuracy | **60-70%** — assembly works but exact format normalization fails |
| Path past 50% | Learned matcher (Step 6 LoRA on Qwen3-VL-4B) for names + format normalization |
| Earlier non-URF pipeline (C5+C2) | 52.4% on tuning — matches URF approach |

The earlier 80% number measured "format mask on strict-format fields where the right answer was *anywhere* in the candidate set." Once we test the realistic field mix (names, addresses, multiple-candidate dates), the engineering pipeline is **52%, not 80%**.

The architectural value-add of learned components is much larger than I previously claimed. Specifically:
- **Names (0% rule-based → would be 80%+ with NER)** account for 28 of 84 instances. Closing names alone = +27 pp.
- **Dates (50% → could be 90%+ with spatial label-locator)** account for 16 instances. Closing dates = +6 pp.
- Combined: rule-based 52% → with NER + spatial = **85% projected**.

---

## Validated component results — n=10 (early, NOW DEPRECATED)

The n=10 numbers in the earlier table were on a cherry-picked strict-format-only field set. **They overstate engineering capability. They are kept here for historical traceability only.**

```
n=10 (early): C1=70%, C2=80%, C3=80%, C4=50%, C5+C2=80%
```

## Validated component results — credible (n=84 tuning, n=42 holdout)

From `experiments/19_credible_eval/`. Balanced field set: 32 ID fields, 16 dates, 4 phones, 4 emails, 28 names. Bootstrap 95% CIs reported.

| Component | Tuning exact (CI95) | Holdout exact (CI95) | Best at | Weak at |
|---|---|---|---|---|
| C1 (WORD + mask) | 36.9% [27, 46] | — | IDs 66% | names 0%, phones 0% |
| C2 (LINE + mask) | 36.9% [27, 46] | — | IDs 66%, dates 50% | names 0%, phones 0% (different from n=10 — small sample bias) |
| C3 (sliding-window merge) | 41.7% [31, 52] | — | **phones 100%** | names 0% |
| C5 (Docling char-window) | 41.7% [31, 52] | — | precision 80% when answers | names 0%, 38 no-answer |
| C1+C5 (C1 first, C5 fallback) | 40.5% [31, 50] | — | — | — |
| C2+C5 (C2 first, C5 fallback) | 36.9% [27, 46] | — | — | — |
| **C5+C2 (Docling first, C2 fallback)** | **52.4%** [42, 63] | **52.4%** [38, 67] | **IDs 94%, phones 100%** | names 0%, dates 50% |

**Per-field-type breakdown of the winning C5+C2 combo:**

| Field type | Tuning | Holdout | Why |
|---|:---:|:---:|---|
| ID (NAIC, policy, ZIP, state) | **93.8%** | **93.8%** | Format mask + Docling table column → header |
| phone | 100% | 50% | Small n; one was likely a fax mismatch on holdout |
| email | 50% | 100% | Small n |
| date | 50% | 50% | Multiple dates per form, no spatial disambiguation yet |
| **name** | **0%** | **0%** | **No regex applies, no NER** |

**Empirical finding (corrected):** Label-locator-first ordering is *better* than expected when the locator is Docling-aware (C5). C5+C2 beat C2 alone by **+15.5 pp** on tuning, **+15.5 pp** on holdout. The earlier finding that "label-locator-first is harmful" applied only to the *naive synonym matcher* (C4), not to C5. Confidence calibration matters — C5 has 80% precision when it answers vs C4's lower precision; the layering only works when the leading component is more precise than the follower.

**The two persistent failures both have clear next-step solutions:**
- **Names (0%)**: needs a learned NER. Spatial ModernBERT's three-head classifier handles this directly.
- **Dates (50%)**: needs spatial label-locator that distinguishes "Form Completion Date" from "Effective Date" from "Signature Date". RE2's eGAT or a smaller geometric matcher handles this.

---

## What has been *empirically validated* (with measurements)

### Components that work as expected
- **Tesseract via tesserocr (no-sudo)** — 1.2 s/page on RTX 3090 CPU, word-level bboxes + confidence. Quality lower than ML OCRs on stylized text. (`experiments/03_tesseract/`)
- **Tesseract LINE-level (`RIL.TEXTLINE`)** — solves the phone-fragmentation problem (`(859) 555-1234` is one span, not two). Closed the phone field from 0% → 100%. (`experiments/17_harness/`)
- **Format mask** — 100% on strict-format fields (FEIN, NAIC, ZIP, email, policy number). The architectural anti-hallucination guarantee holds. (`experiments/09_format_mask/`)
- **GLM-OCR base model** — excellent text quality (~0.97 conf), 4.7 s load + 8.25 s/page inference, 3.15 GB peak VRAM. **No bbox output via transformers** path; needs SDK + self-hosted vLLM for bbox/layout. (`experiments/01_glm_ocr/`)
- **Nemotron ColEmbed VL 4B v2** — loads fine with bf16 + eager attention (8.88 GB VRAM), 0.95 s/query, 0.81 s/image. **Schema synonyms +1.89 over abbreviation** in MaxSim score, confirming synonyms in spec are essential. Page-level retrieval works; field-level localization does not (scores cluster within 0.4 between unrelated queries). (`experiments/05_nemotron_colembed/`)
- **Synthetic form generator** — Jinja + WeasyPrint + bbox extraction works end-to-end. Container-level bboxes; text-tight bboxes deferred. (`experiments/04_synthetic_data/`)
- **Docling on rasterized PNGs** — 4 s/page, structured markdown with tables ✓. Found `40544`, `20443`, `(859) 555-1234`, etc. all in their correct table-cell context. Reading order looks right. (`experiments/18_docling/`)

### Components that did NOT work as expected
- **Docling on PDF directly** — extracts the form template, not filled values. ACORD 125 PDF processed in 142 s, found 0 of our 4 test values in markdown. (`experiments/18_docling/run_docling.py`)
- **PaddleOCR on CPU** — 40 s/page, unacceptable for production. Bbox quality is good (106 blocks, conf ≥ 0.97). Need GPU paddle wheel matching CUDA 13. (`experiments/02_pp_doclayout/`)
- **Surya** — multiple `transformers 5.x` API breaks (`pad_token_id`, `ROPE_INIT_FUNCTIONS['default']`). Cannot install in shared env. Ported microservice would work. (`experiments/13_surya/`)
- **GeoLayoutLM** — Repo + 1.66 GB FUNSD-RE checkpoint downloadable, but `bros/__init__.py` imports `transformers.file_utils._LazyModule` (4.x API removed in 5.x). Multi-day port. (`experiments/06_geolayoutlm/`)
- **ROAP code** — GitHub repo (`KevinYuLei/ROAP`) created Dec 2025, never populated. Empty. (`experiments/07_roap_availability/`)
- **Naive label-locator (C4, C5)** — synonym-text matching alone confidently picks wrong matches. *Strictly worse* than not having a label-locator.

---

## Architectural insights

### 1. The engineering ceiling is ~52%, not 80%
- The earlier "80% on 8/10 fields" was n=10 cherry-picked strict-format fields. On a balanced credible corpus (n=84 tuning, n=42 holdout, mixed id/date/name/phone/email), rule-based tops out at **~50–52%**.
- Two independent rule-based pipelines (URF builder v1.2 with span merger; C5+C2 Docling-first synonym + format mask) converge to the same 52% — strong evidence this is the engineering ceiling.
- **Bottleneck #1: names (0–29% rule-based)** — no regex applies, needs NER.
- **Bottleneck #2: multi-date disambiguation (37–50%)** — multiple date-shaped values per form, needs spatial label-locator.
- Both bottlenecks are learned-component territory. Path past 52% requires Step 6 LoRA matcher.

### 2. The single-venv assumption was wrong
- Surya, GeoLayoutLM, Docling-on-PDF: all built on `transformers 4.x` APIs.
- Nemotron, GLM-OCR, our trainable components: need `transformers 5.x`.
- **Reality is multi-venv microservices.** Same pattern the prior project uses (Docling + EasyOCR + Ollama as separate processes).

### 3. Format mask is the strongest single mechanism
- 100% on strict-format fields (FEIN, NAIC, ZIP, email, policy number) IF the right candidate is in the candidate set.
- Makes the architecture's anti-hallucination guarantee load-bearing.

### 4. Synonyms in schema are *essential*, not optional
- Nemotron MaxSim showed `"Federal Employer Identification Number"` scoring **+1.89** over `"FEIN"` alone — a meaningful boost.
- Schema spec must include synonyms for matching quality.

### 5. Layered combination is order-sensitive
- High-confidence components MUST go first.
- Low-confidence components as fallback for nulls only.
- Putting a weak component (C4, C5) first pollutes the output with confidently-wrong picks.

### 6. The architecture's value comes from the LEARNED layer
- Engineering ceiling = ~52% (credible eval). Hidden upside in names (0% → 80%+ projected with NER) and dates (50% → 90%+ projected with spatial label-locator).
- Above 52% requires either better structural extraction (Docling-table-aware engineering) OR learned label-value matchers (LoRA on Qwen3-VL-4B, RE2 eGAT, GeoLayoutLM-style pair geometric head). Spatial ModernBERT was the original choice but skipped (paper-only).
- AlphaFold-style recycling + triangle attention only pays off above ~85% baseline (recycling refines locks; if the base has nothing solid to lock, recycling has nothing to do).

---

## The architecture (current state)

```
INPUT: (form_image, schema_json)
  ↓
[A] Layout fingerprint cache (deferred) — known templates → fast path
  ↓
[B] URF Construction (target representation):
   B.1 OCR + element typing (Tesseract today; Unstructured / Docling later)
   B.2 Layout regions + tables + checkboxes (Docling on PNG produces these)
   B.3 Initial pairing (rule-based for v1; learned for v2)
   B.4 Schema-as-prompt VLM pass for unfilled fields (deferred)
  ↓
[C] URF Refinement (deferred — recycling + triangle attention)
  ↓
[D] Schema → URF mapping (graph homomorphism; format mask + spatial coherence)
  ↓
[E] Verification (V1 re-OCR, V3 cross-field consistency)
       Confidence calibration (temperature scaling)
       Abstention router → HITL queue
  ↓
OUTPUT: ExtractedJSON + URF (cached for future)
```

**Current implementation reaches stage [D] with rule-based pairing only.** Stages [A], [B.4], [C] are deferred.

---

## Cross-domain ideas evaluated (Apr 30, 2026)

User shared 10 cross-domain papers + 2 honorable mentions. My evaluation:

### Strong fits (would change v1.5 / v2)

1. **Element grouping into semantic clusters** (UI Semantic Component Group Detection). Maps directly to URF.fields construction: KV pairs as UI component groups. **Adopt for the URF pairing module.**
2. **Subject–predicate–object as relation primitive** (Scene Graph Generation, SPADE 2025). Validates our graph-homomorphism formal model. **Already in plan via RE2.**
3. **Geometry + sequence dual-stream** (protein structure: SSRGNet — three edge types: sequential, spatially close, local environment). Maps perfectly to documents — reading-order edges, spatial-proximity edges, visual-block-membership edges. **Strong addition to URF graph.**
4. **Iterative cluster–tag–regroup loops** (fPLSA — EM-style alternation). Cheap, model-agnostic, post-hoc. **Direct slot in for v1.5 refinement; lighter than recycling.**

### Useful but lower priority

5. **Local neighborhood attention with adaptive radius** (Hierarchical Point Attention, DA-NAM). Useful when we train our own attention layers; not for v1 with Docling.
6. **Hierarchical multi-scale (octree over the page)** (OctFormer, Swin/Shunted). Architecturally interesting but premature — we don't have a learned model that needs hierarchical attention yet.
7. **Vectorized structural parsing (raster → graph)** (GLSP floor plans, junction-heatmap supervision). Strong for table-cell-corner detection if we train a layout module from scratch. v2 candidate.
8. **Code/program as structural intermediate** (ChartReasoner, VProChart). HTML/JSON/markdown DSL. Already implicit in URF design.

### Tangential or already-covered

9. **Viewpoint/orientation invariance** (VIZOR). Useful for rotated scans. Out of v1 scope (printed forms only).
10. **Inversion-guided spatial calibration** (SPADE diffusion inversion). Research-grade. Not v1.

### Of the prior batch's 10:
- **Spatial ModernBERT** + **RE2** + **ReLayout** + **D-REEL** still validated.

### Highest-leverage pick from this round
**The protein-structure analogy with three edge types is the cleanest add.** Make the URF graph carry three kinds of edges:
- Sequential (reading order)
- Spatial proximity (label-near-value)
- Block membership (same section / table / cell)

This mirrors SSRGNet's framing and gives the graph a richer prior than spatial-only adjacency. Drop-in for the eGAT layer's edge features.

---

## Decisions made / pending

| Decision | Status |
|---|---|
| Single venv for everything | ❌ Rejected — multi-venv microservices needed |
| Use 510 real ACORDs as primary training corpus | ✅ Locked — credible eval `corpus.json` defines GT for 18 forms (12 tuning + 6 holdout = 126 instances). 4 additional form directories exist on disk but have no GT entries and aren't evaluated. |
| URF as the central representation | ✅ Adopted |
| URF schema spec format | ✅ v1.0.1 locked (`docs/URF_SPEC.md` + `docs/urf.schema.json` + 10 regression tests) |
| Use Docling for structure | ✅ Adopted (PNG inputs only, not PDFs) |
| Use Spatial ModernBERT for token merging | ❌ Skipped (Step 3) — paper-only, no code/weights. Fallback if Step 6 needs it. |
| Use RE2 eGAT for matcher | ⏳ Phase 2 plan |
| Use AlphaFold recycling/triangle attention | ⏳ Phase 2 only if base hits 85%+ |
| Three-edge-type graph (SSRGNet pattern) | ⏳ Adopt for URF graph design |
| Skip Nemotron/GeoLayoutLM port for v1 | ✅ Adopted (use the IDEAS, not the legacy code) |

---

## Honest list of *remaining* unknowns (we don't know, until measured)

1. Does Docling-table-aware pairing actually break 52% (the rule-based ceiling)? Need to write a real markdown-table parser, not the C5 char-window hack.
2. Does Unstructured (untested) add value over Docling? Element-typing might disambiguate label vs value better.
3. (Skipped — Spatial ModernBERT is paper-only; deferred to fallback.)
4. Does RE2's eGAT reproduce its claimed +18.88% F1 on insurance forms specifically?
5. How does our pipeline perform on actual loss-run forms (not just notice forms)? We don't have any locally yet.
6. Will Step 6 LoRA on Qwen3-VL-4B push past 70% (≥+18pp over the 52% rule-based ceiling)? If not, the learned-component bet is in trouble.

---

## Files / artifacts produced (latest)

- ~30 commits on `dev`
- 18 experiment subdirectories under `experiments/`
- `experiments/FINAL_STACK.md` — locked component manifest
- `docs/superpowers/plans/2026-04-29-document-extraction-stack-validation.md` — original validation plan
- `docs/superpowers/specs/2026-04-30-document-extraction-design.md` — user-approved architecture design
- `docs/URF_SPEC.md` — URF v1.0.1 spec (LOCKED)
- `docs/urf.schema.json` — formal JSON Schema
- `docs/test_urf_schema.py` — regression suite (10/10 pass)
- `INSIGHTS.md` — this document (living)

## Implementation progress (Steps 1-4 of 11)

| Step | Status | Outcome |
|---|---|---|
| 1 — URF spec lock | ✅ DONE | URF v1.0.1, 11 audit fixes, JSON schema validates |
| 2 — Base VLM | ✅ DONE | Qwen3-VL-4B-Instruct (Apache 2.0); load 5.17s, inference 20s, VRAM 9.94 GB peak — all 4 GPU gates passed |
| 3 — Spatial ModernBERT | ⏭ SKIPPED | Paper-only, no code/weights publicly available; fallback noted |
| 4 — URF builder | ✅ DONE | Tuning 50.0%, holdout 52.4% (CI95 38-67); GATE passed |
| 5 — HITL UI + replay | ⏳ next | FastAPI + web canvas + bbox overlays + SQLite replay buffer |
| 6 — LoRA matcher (Qwen3-VL-4B) | ⏳ pending | Must lift ≥+18pp from 52% to 70%+ to validate architecture |
| 7-9 — Research tracks | ⏳ parallel after Step 6 | Triangle attn / foveated / recycling — keep ones that add ≥3pp |
| 10 — Verifiers | ⏳ pending | V1 re-OCR + V2 plausibility + V3 consistency + abstention router |
| 11 — Demo | ⏳ pending | End-to-end on 4 ACORDs + 3 loss-run carriers |

---

## Next concrete action

**Step 5: HITL UI + replay buffer.** FastAPI + web canvas + bbox overlays + SQLite. ~3 days. Builds the human-in-the-loop correction surface that feeds Step 6's training signal. Can be built in parallel with Step 6 prep.

**After Step 5: Step 6 LoRA matcher on Qwen3-VL-4B.** Target: lift the 52% rule-based ceiling to 70%+. If Step 6 doesn't move past ~52%, the architecture's investment in learned components isn't paying off and we fall back to a Docling-markdown-table-aware extractor (C6) experiment as Plan B.
