# Ablation Matrix — VLM × OCR-config (May 4, 2026)

> **Goal:** isolate the F1 contribution of (a) VLM choice and (b) OCR-input shape, so every delta is attributable to a single variable.

**Schema:** 3 VLMs × 3 OCR configs = 9 cells.
**Eval:** GT v6, winner-only F1, full pipeline (flatten → derive → coerce → enrich → score).

| | LightOnOCR (text) | LightOnOCR + bbox-grounded | Image only (no OCR) |
|---|---|---|---|
| **Qwen3-VL-4B** | A: **91.12%** ✓ baseline | B: **88.65%** ⚠ −2.47pp | E: not run |
| **Granite-4.0-3B-Vision** | C: **15.95%** ⚠⚠ −75.17pp | D: cancelled (cell C result decisive) | F: cancelled |
| **Dolphin-v2** | G: **0.00% (empty output)** ✗ | H: cancelled (same fault as G) | I: cancelled |

> **Granite update (May 4 ~11am):** Side venv with `transformers==4.57.6` resolved the import error. Granite loads cleanly (8.96GB VRAM), produces structurally valid JSON, but the F1 collapses to 15.95%. Cells D + F cancelled — see "Granite catastrophic regression" below.

## What we learned (from cells that ran)

### Cell A — production baseline ✓
- **91.12% (554/608)** F1 — confirmed at HEAD `242e2d8`
- Per-doc: ICW 95.6% / Arrowhead 92.6% / Strategic 91.2% / ADP 88.2% / Employers 82.0% / TriNet 82.4% / Insperity 83.3% / Hartford pivots 50.0% & 40.0%
- This is the number to beat.

### Cell B — Qwen3-VL + bbox-grounded ⚠ regressed −2.47pp
- **88.65% (539/608)** — lost 15 fields
- Per-doc deltas:

| Doc | A_F1 | B_F1 | Δ | hits Δ |
|---|---|---|---|---|
| Employers | 82.0% | 80.9% | −1.1pp | −1 |
| Hartford 8.21.05 | 50.0% | 50.0% | 0 | 0 |
| Hartford 8.21.25B | 40.0% | 40.0% | 0 | 0 |
| Strategic Hartford | 91.2% | 85.3% | **−5.9pp** | −2 |
| Insperity | 83.3% | 83.3% | 0 | 0 |
| TriNet | 82.4% | 64.7% | **−17.6pp** | −3 |
| ADP | 88.2% | 88.2% | 0 | 0 |
| ICW | 95.6% | 94.7% | −0.9pp | −3 |
| Arrowhead | 92.6% | 86.2% | **−6.4pp** | −6 |

- **Hypothesis falsified:** Landing AI's claim that bbox-text in the prompt lifts grounding (95.36% → 99.16% on DocVQA) does NOT transfer to our setup. Adding 100-300 bbox regions per page (≈ 3-10k extra prompt tokens) DEGRADES output, hardest hit on the larger / more table-dense docs (Arrowhead, TriNet).
- **Likely mechanism:** the model has to reconcile three sources (image + LightOnOCR text + bbox-grounded text). The reconciliation cost exceeds the spatial-prior gain. Their setup uses bbox-text as the SOLE text input to a downstream text-only LLM; ours adds it as a third channel alongside image + LightOnOCR text — different architecture, different result.
- **Cost penalty:** bbox-grounded variant is 5-9× SLOWER (Employers: 269s vs 30s baseline; Arrowhead: 530s vs ~120s).
- **Decision:** do NOT ship bbox-grounding to the VLM input prompt. The bbox cache remains useful for the verification UI overlays.

## What we learned (from cells that failed)

### Granite-4.0-3B-Vision — initial env error then catastrophic regression

**First failure (cells C/D/F initial run):** `ImportError: cannot import name 'HybridMambaAttentionDynamicCache'`. Granite 4.0 expects `transformers==4.57.6`; our main env has 5.7.0. **Resolved** by creating `.venv-granite/` with pinned deps (~30 min).

**Second result (cell C retried in side venv): 15.95% F1** — vs **91.12%** baseline. Per-doc:

| Doc | A (Qwen) | C (Granite) | Δ |
|---|---|---|---|
| ICW | 95.6% | **1.8%** | −93.8pp |
| Hartford 8.21.05 | 50.0% | 12.5% | −37.5pp |
| Hartford 8.21.25B | 40.0% | 20.0% | −20.0pp |
| Strategic Hartford | 91.2% | 41.2% | −50.0pp |
| Insperity | 83.3% | 33.3% | −50.0pp |
| TriNet | 82.4% | 52.9% | −29.5pp |
| ADP | 88.2% | 29.4% | −58.8pp |
| Arrowhead | 92.6% | 29.8% | −62.8pp |
| Employers | 82.0% | 34.8% | −47.2pp |

**Why it failed:** Granite's output is structurally valid JSON conforming to the V4 schema's shape, but values land in the wrong fields. Sample from Employers cell C:

- `"carrier": {"name": "WORLDWIDE FACILITIES LLC"}` — **wrong**: WWFAC is the broker; the carrier is "Employers Preferred Insurance Company"
- `"report_id": "EIG469077603"` — **wrong**: that's the policy number, not a report ID

Granite is a general-purpose KVP-extraction model. Without insurance-domain priors, it makes naive label→field guesses that misclassify common loss-run elements. It also adds extra top-level fields not in our schema (`verification`, `confidence`, `signals`, `extraction_notes`, `source_provenance`) suggesting it's drawing from its general-domain pretraining rather than our V4 prompt.

**Cells D + F cancelled** — same model + same prompt would produce the same field-misattribution pattern. No point spending another 30+ min of GPU time on it.

**Conclusion:** Granite 4.0 3B Vision is **not a drop-in replacement** for Qwen3-VL-4B at our schema. It would need either (a) explicit field-by-field schema fine-tuning on insurance docs, or (b) a different prompt format (Granite's native `<tables_json>` + custom JSON schema task) to be useful. Both paths are real engineering, not ablation tweaks. **Not pursuing.**

### Dolphin-v2 (cells G/H/I) — wrong prompt format ✗

- Model loads fine (~7.5GB VRAM), but produces **0 output tokens** for every chunk.
- Our prompt is the V4 system prompt + LightOnOCR text + image — same shape that works for Qwen3-VL.
- Dolphin v2's "heterogeneous anchor prompting" is a two-stage paradigm: Stage 1 = layout, Stage 2 = element-wise parse with task-specific prompts. Feeding it our "extract a 75-field JSON" prompt directly bypasses the design and produces nothing.
- **Plan:** invoke via Dolphin's Stage-1 → Stage-2 demo path (`demo_page.py`). That returns markdown / structured layout; map to our 75-field schema in a downstream step. ~1 day of engineering.

## What we did NOT learn (and why)

- **Granite vs Qwen on KVP extraction** — the test we most wanted (Granite is KVP-pretrained). Blocked on transformers upgrade.
- **Dolphin two-stage anchor benefit** — blocked on prompt-format port.
- **Image-only ablation (cells E/I)** — pipeline killed before reaching them.

## Concrete next-step priorities

1. **Fix Granite environment** (~30 min): pin `transformers==4.57.6` in a side venv, retry cell C. **High value** — Granite is KVP-pretrained, most likely candidate to beat Qwen on form-layout docs.
2. **Port Dolphin to its native two-stage interface** (~1 day): use `demo_page.py` as the integration template; layer our schema-mapping prompt on Stage-2 output.
3. **Investigate B's regression in detail** — is it specific to certain field types? Specific docs? Per-field deltas may reveal whether bbox-grounding helps for SOME categories (e.g., column-disambiguation in dense tables) even if hurts overall — could be selectively applied.
4. **Skip image-only cells (E, I)** until 1+2 done — those test a less promising hypothesis (current production already includes LightOnOCR for good reason).

## Lessons applied to LESSONS.md

- **New rule (proposed):** "Validate model-loads in a smoke test BEFORE running full ablation matrix. 30 min of upfront verification beats 2 hours of failed cells."
- **New rule (proposed):** "When porting an architectural insight from a paper, check whether the target paper's *full setup* is replicable. Landing AI's bbox-text gain came from a parse-once + text-only-QA architecture; we tried the bbox-text part WITHOUT the architecture, and got opposite signed result."
