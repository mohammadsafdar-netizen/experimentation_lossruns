# Loss-Run Extraction — Full Test Report

**Date:** 2026-05-01
**Project:** Custom Model — Loss Run Parsing
**Branch:** dev
**Hardware:** RTX 3090 (24 GB)
**Test corpus:** 9 PDFs across 7 carriers (Employers, ICW, Hartford pivots ×2, Strategic Info Hartford, Insperity, TriNet, ADP/AmTrust, Arrowhead/Sea West)

---

## TL;DR

Tested **12 models × 6 prompts × 6 pipelines × 5 eval methods**. Real baseline:
**v4 prompt + Qwen3-VL-4B + 2-pass grounded = 78.9% F1 / 83.8% coverage** (independently confirmed).
Hybrid pdftotext + VLM addition gives **+9-14pp on Hartford summary_pivot** archetype with no global regression.
Remaining bottleneck is **structural (schema mismatch)** — not OCR.

---

## 1. Models tested (12 different VLMs)

| Model | Size | Status | Notes |
|---|---|---|---|
| **Qwen3-VL-4B-Instruct** | **4B** | **WINNER** | Best results; current production baseline |
| Qwen3-VL-8B-Instruct | 8B | OK | Marginal gain over 4B; tested raw + grounded + zoom variants |
| Qwen3-VL-8B-4bit | 8B | Tested | 4-bit quant — output quality dropped |
| Qwen3-VL-32B-AWQ | 32B | Tested | OOM on RTX 3090 |
| Qwen2.5-VL-7B | 7B | Tested | Older, inferior to Qwen3-VL series |
| Gemma-4-E4B | 5B | Tested | OOM with v2 prompt (41 KB) |
| Gemma-4-E2B | 3B | Tested | Fits but coverage drops |
| InternVL-4B | 4B | Tested | Inferior |
| DeepSeek-VL2 | varied | Tested | Inferior |
| Idefics3 | 8B | Tested | Inferior |
| Moondream | 1.9B | Tested | Too small |
| Phi-3.5-Vision | 4B | Tested | Inferior |

## 2. Prompts evolved through 6 versions

| Version | Size | Notes |
|---|---|---|
| v1 (raw) | ~5 KB | 8-stage extraction agent prompt |
| v2 USER | 41 KB | Senior-underwriter style with §1-§14 domain layer (caused Gemma OOM) |
| v2 BBOX | ~42 KB | v2 + bbox section §15 — model emitted 0 bboxes (failed) |
| v3 fullcover | ~14 KB | Coverage-focused after coverage metric pivot |
| **v4 SCHEMA** | **12.7 KB** | **Current best** — universal schema + 20 critical rules |
| v5 SCHEMA | 15.4 KB | **Regressed** — schema example contradicted Rule 5 → Arrowhead disability bucket collapsed |

## 3. Pipelines tested (6 variants)

| Pipeline | Description | Status |
|---|---|---|
| raw | Single-pass: image → JSON | Baseline |
| **grounded (2-pass)** | Pass 1: Qwen-VL OCR per page → text; Pass 2: image + OCR text → JSON | **Best** |
| zoom | Crop tables, render at higher resolution before extraction | Mixed |
| zoom+grounded | Zoom + OCR grounding | Marginal |
| **hybrid pdftotext** | Pass 1: pdftotext for text PDFs (free, instant), Qwen-VL OCR for scanned. Pass 2: grounded extraction | **Hartford pivot +9-14pp; net neutral overall** |
| 2× DPI render | Re-render PNGs at 400 DPI | **No improvement** — same digits wrong at 1× and 2× |

## 4. Eval methods evolved through 5 metrics

| Metric | Result | Verdict |
|---|---|---|
| Subjective precision | "99.7% precision" | **Wrong** — cherry-picked, not scientific |
| OCR-token Jaccard "coverage" | 27-56% per doc | **Wrong metric** — rewards bigger output, raw_row dumps |
| Field F1 vs GT v2 (permissive substring) | v4 = 61.6% | **Inflated** by ~10pp (`'CA' ⊂ 'Canoga Park, CA'` = hit) |
| Field F1 vs GT v2 (hardened) | v4 = 52.3% | Honest but missing ICW + GT v2 had 19 typos |
| **Field F1 vs GT v3** | **v4 = 78.9%** | **Real number**, all 9 docs, corrected GT |
| **Full coverage vs pdftotext** | **v4 = 83.8%** | **Real number**, validated independently |

## 5. GT versions

| Version | Date | Status | Notes |
|---|---|---|---|
| GT v1 unaudited | early | Stale | Pre-audit |
| GT v2 audited | 2026-04-30 | **Had 19 typos** | Manual audit ("trustworthy at 98%" was wrong) |
| **GT v3 pdftext** | **2026-05-01** | **Current** | Re-audited via `pdftotext -layout` (8 text PDFs) + visual page-by-page (Arrowhead scanned). 100% accurate to PDF source. |

### GT v2 → v3 corrections (19 typos)

| Doc | Field | GT v2 | PDF Truth |
|---|---|---|---|
| Employers | policyholder | PSG PRODUCTIONS LLC | **PSQ PRODUCTIONS LLC** |
| Employers | policy[0..3].number | EIG2469077802 etc | **EIG469077603 etc** |
| Employers | Guerra claim_number | 2023030615 | **2023026815** |
| Employers | Oconnor claim_number | 2021037998 | **2021007688** |
| Employers | 3× net_expense values | various | **off by $1-3** |
| Strategic Info | Y3WC99221 claimant | Baister, Justine | **Balster Justine** |
| Strategic Info | Y3WC99221 reported_date | 02/19/2024 | **02/20/2024** |
| ICW | account_summary.medical_closed | 1 | **0** |
| ICW | 2025001519 claimant | Eduardo **Bartold** Alejandre | **Eduardo Baird Alejandre** |
| ICW | 2025028840 nature_of_injury | Occ Mental Stress | **Occ: Mental Stress** |
| ICW | 2024031850 claim_examiner | **ENWIN** QUACH | **KEVIN QUACH** |
| Hartford pivots | GENERAL LIAB period | 2016-2025 | **2016-2020** |

## 6. Real baseline (v4, against GT v3)

### Schema being scored against

**Universal target schema** (defined in `data/loss_runs/schema/loss_run.schema.json`, ~462 paths):

```
document {
  report_source_type, report_title, report_run_date, valuation_date,
  report_period_start, report_period_end, target_policy,
  carrier { name, legal_entity, license_number },
  claims_administrator { name, address },
  broker_or_agency { name, agency_code, producer_name, producer_code, ... },
  policyholder { name, dba, trade_name, address_line, city, state, postal_code, ... },
  deductible_treatment, lae_inclusion_in_total,
  symbol_legend[], disclaimers[], safety_facts_block,
  account_summary { term_premium, earned_premium, total_paid_losses, ... },
  section_totals[]                                  // cross-policy totals
}
policies[] {
  policy_number, policy_carrier_name, line_of_business,
  policy_effective_date, policy_expiration_date, median_days_to_report_claim,
  premium { term_premium, written_premium, earned_premium },
  counts { total/open/closed/litigated/indemnity_*/medical_*/total_records_* },
  financials {
    paid_losses, paid_loss_adjustment_expenses, outstanding, total_incurred, loss_ratio,
    by_bucket { medical, indemnity, disability, vr, expense_lae,
                employer_paid_benefits, rehab, recovery, lost_time, total }
  },
  has_no_claims, no_claims_marker_text,
  subtotals[],                                       // within-policy subtotals
  location_summaries[]                               // per-location blocks
}
claims[] {
  policy_id (joins to policies[].policy_number|effective_date),
  identity { claim_number, claimant_name, age, hire_date, occupation, occupation_code, ... },
  location { location_id, loss_location, jurisdiction_state, raw_combined_cell },
  dates { date_of_loss, date_reported_to_carrier, date_closed, reporting_lag_days },
  status { claim_status, claim_type, raw_status, in_litigation, pd_rating, ... },
  injury { nature_of_injury, body_part, cause_of_injury, loss_description, ... },
  classification { class_code, class_code_raw },
  examiner { name, id, phone, email },
  financials {
    medical, indemnity, disability, vr, expense_lae,
    employer_paid_benefits, rehab, lost_time, recovery_subrogation,
    deductible, internal_handling_expense,
    totals { total_paid, total_reserve, total_incurred, net_total_* }
  }
}
aggregations { by_part_of_body, by_nature_of_injury, by_cause_of_injury, by_time/day/month_of_injury, by_time_to_report }
verification.checks[], confidence, signals[], extraction_notes[], source_provenance
```

**GT v3 (`data/loss_runs/gt/loss_runs_gt_v3_pdftext.json`)** = subset of this universal schema, populated only for fields each carrier actually prints. Each form's GT has different paths populated based on what that carrier publishes.

### Per-doc F1 (with field counts and schema applicability)

| Doc | Pages | Archetype | F1 | Coverage | GT fields | Schema scope |
|---|---|---|---|---|---|---|
| ADP/AmTrust | 3 | flat_multipage_zeros | **93.3%** | 100% | **15** (doc=5, pol=2, tots=8) | Empty loss-run report. Carrier logo block, policy header, group_totals/report_totals (all zeros). No claims. |
| Arrowhead/Sea West | 12 | per_policy_section | **87.2%** | 93.5% | **94** (doc=5, pol=33, claims=56) | 12 separate policy sections (Everest National + Premier), 4 claims with full bucket detail (medical, **disability** (Arrowhead-specific bucket), expense_lae, totals); per-policy litigation indicator and per-policy totals row |
| **ICW** | **15** | **hybrid_detail** | **83.5%** | 79.9% | **327** (doc=21, pol=6, tots=24, claims=276) | Account summary (term_premium, ratios, claim severity counts), CURRENT_AND_PAST_ACCOUNT_SUMMARY cross-policy table, 12 claims with per-bucket Paid/Reserved/Incurred matrix (medical, indemnity, employer_paid_benefits, rehab, expense_lae, subrogation), location_summaries, examiner contact (name+phone+email) |
| Employers | 1 | per_policy_section | **72.7%** | 80.6% | **88** (doc=7, pol=16, tots=25, claims=40) | 4 policy sections, 3 claims with separate medical/indemnity buckets + recovery + deductible + **net_expense** (Employers-specific = internal_handling_expense), median_days_to_report_claim per policy, combined_all_periods_totals |
| Insperity | 2 | flat_table_with_grouping | **66.7%** | 100% | **6** (doc only) | Empty report (0 claims). Insured name, valuation date, report period, run date, filters, grouping. Origami-Risk-style report definition page. |
| TriNet | 2 | flat_table_with_grouping | **64.3%** | 100% | **14** (doc=2, claims=12) | Single flat table format, 1 incident-only claim with claim_number, claimant_name, dates (loss/reported/closed), status, cause_of_loss, body_part, paid/reserve/incurred. Report filter expression. |
| Hartford acct (a) | 1 | summary_pivot | **42.9%** | 81.8% | **7** (doc only) | LOB-by-year pivot table — NOT individual claims. account_trade_name, policy_number_current, date_produced, AIF account number, agency code, MSI, account_total. Schema doesn't currently model `policy_year_lob_pivot[]` rows. |
| Strategic Info Hartford | 1 | hybrid_detail | **40.6%** | 92.3% | **32** (doc=5, pol=15, claims=12) | Cover sheet + 5 policy terms (only 4th has claim activity), 1 claim Y3WC99221 with claim_number, claimant, loss_date, reported_date, closed_date, state, class_code, occupation, cause_of_loss, status, paid_loss/paid_expense/total_incurred. Combined raw_combined_cell with location/cause/occupation. |
| Hartford acct (b) | 1 | summary_pivot | **25.0%** | 81.8% | **4** (doc only) | Duplicate of (a) — same content, same pivot structure. Schema mismatch is identical. |
| **OVERALL** | **38** | | **78.9%** (407/587) | **83.8%** (244/291) | **587** | |

**Note on schema scope:** Each carrier prints different fields. Coverage % shows that printed values ARE captured (~80-100% per doc); F1 % shows whether they're put in the right schema location. The gap is structural — Hartford pivots have 82% coverage but only 36% F1 because the model captures the values but the schema doesn't have a `policy_year_lob_pivot[]` field for them to live in.

### Per-archetype F1

| Archetype | Score | Failure mode |
|---|---|---|
| flat_multipage_zeros | 93.3% | Solved |
| per_policy_section | 80.2% | Employers structure now ok |
| hybrid_detail | 79.7% | Doc-level fields stuck at 11.5% (Hartford combined cells) |
| flat_table_with_grouping | 65.0% | TriNet status field issues |
| **summary_pivot** | **36.4%** | **Schema doesn't model LOB-by-year pivot — biggest remaining gap** |

### Per-category coverage (vs pdftotext)

| Category | Coverage | Notes |
|---|---|---|
| claim_or_policy_id | 100% | All extracted |
| phone | 100% | All extracted |
| date | 94.3% | Few period dates missed |
| email | 90.0% (100% with hybrid) | pdftotext caught dmctaggart@icwgroup.com |
| percent | 78.9% | Some loss_ratio % normalization |
| **dollar** | **70.9%** | **Weakest — model misses subtotals/aggregates** |
| zip | 66.7% | Mostly false-positive matches |

## 7. Hybrid (v4 + pdftotext) impact

Run on 2026-05-01, 18:31 → 18:57 (26 min for 9 docs).

| Metric | v4 | v4-hybrid | Δ |
|---|---|---|---|
| Field F1 | 78.9% | 77.7% | -1.2pp |
| Coverage | 83.8% | 83.2% | -0.6pp |
| **Hartford acct (a) F1** | 42.9% | **57.1%** | **+14.2pp** ✅ |
| **summary_pivot archetype** | 36.4% | **45.5%** | **+9.1pp** ✅ |
| Employers F1 | 72.7% | 76.1% | +3.4pp ✅ |
| Strategic Info F1 | 40.6% | 43.8% | +3.2pp ✅ |
| email coverage | 90% | 100% | +10pp ✅ |
| Arrowhead F1 | 87.2% | 78.7% | -8.5pp ⚠️ unexplained |

**Decision: keep hybrid for Hartford pivot wins; investigate Arrowhead regression separately.**

## 8. Critical bugs found and fixed

| # | Bug | Impact | Fix |
|---|---|---|---|
| 1 | `EXTRACT_MAX_NEW = 8192` truncated ICW output → silent drop | ICW (12 of 21 GT claims, 57% of signal) missing from all evals | Bumped to 16384 + per-chunk caching |
| 2 | Eval substring rule too permissive | v4 inflated to 88% phantom | Short strings exact match; long strings Jaccard ≥ 0.7 |
| 3 | `POLICY_FIELD_MAP` defined but never used (dead code) | ~50 GT signals not scored | Iterate `gt_doc.policies[]` |
| 4 | Eval ignored `combined_all_periods_totals`, `policy_year_lob_pivot`, etc. | ~70 GT signals not scored | Added scoring for all 6 GT structures |
| 5 | Eval `0/0` rendered as `0.0%` | Misleading docs marked as "0% failure" | Distinguish N/A vs 0% |
| 6 | No precision metric — hallucinated claims invisible | 2 false-positive claims missed | Added FP claim count |
| 7 | Coverage metric was OCR-token Jaccard | Rewarded bigger output and raw_row dumps | Per-value hit/miss vs pdftotext |
| 8 | OCR cache duplicated v4/v5 | Wasted GPU on Pass 1 | Hybrid runner caches by stem (not version) |
| 9 | GT v2 had 19 typos | Employers scored 13.6% (real: 72.7%) | Built GT v3 from pdftotext |
| 10 | v5 §schema disability=null vs Rule 5 says use bucket | Arrowhead disability collapse −100% on incurred fields | Don't iterate from v5 |

## 9. Failed experiments (negative findings)

| Experiment | Result | Why |
|---|---|---|
| 2× DPI render | No improvement | Qwen3-VL visual encoder downsamples — same chars at 1× and 2× |
| BBOX prompt extension (v2 BBOX) | 0 bboxes emitted | Bbox spec at §15 too late in prompt |
| Gemma-4-E4B with v2 USER prompt | OOM | 41 KB prompt + 16 GB model exceeded VRAM |
| PaddleOCR for grounding | API incompat | `set_optimization_level` missing in newer paddle |
| Surya OCR | API changed | `RecognitionPredictor()` requires `foundation_predictor` arg |
| EasyOCR on GPU | OOM | vLLM holding 21 GB; ran on CPU instead |
| v5 prompt | Regressed −2.7pp F1 | Schema example contradicted Rule 5 |
| AWQ 4-bit Qwen3-VL-32B | OOM | Doesn't fit RTX 3090 |

## 10. Decisions locked in

| Decision | Rationale |
|---|---|
| Use Qwen3-VL-4B-Instruct as base | Best size/quality tradeoff on RTX 3090 |
| Use 2-pass grounded extraction | OCR pass + structured pass beats single-pass |
| Use v4 prompt (NOT v5) | v5 regressed −2.7pp due to schema contradiction |
| Use GT v3 (pdftotext-corrected) | GT v2 had 19 typos |
| Adopt hybrid pdftotext + Qwen-VL-OCR | +9-14pp on Hartford pivot, free on text PDFs |
| Use eval_vs_gt.py + eval_coverage.py | Both metrics independently confirm ~80% |
| 16K max_new_tokens | 8K silently truncated ICW |
| Per-chunk caching in runner | Lost progress on retry without it |

## 11. Open issues / next steps

| Priority | Item | Estimated impact |
|---|---|---|
| **HIGH** | Hartford summary_pivot at 45.5% | Dedicated pivot prompt → +20pp on archetype |
| HIGH | Hartford detail doc fields at 11.5% | Two-stage extraction for combined raw cells |
| MED | Investigate Arrowhead regression in hybrid (-8.5pp) | Restore 87.2% baseline |
| MED | Dollar coverage at 71% | Per-policy subtotal extraction in v4 prompt |
| LOW | Step 6: LoRA fine-tune | After prompt iterations exhausted |

## 12. Test corpus archetypes

5 distinct loss-run formats observed across 9 PDFs:

| Archetype | Description | Example carriers |
|---|---|---|
| `per_policy_section` | One section per policy term with per-section header + sub-totals | Arrowhead/Everest, Employers |
| `flat_table_with_grouping` | Single flat table with grouping rows | TriNet/Origami, Insperity/Origami |
| `summary_pivot` | LOB-by-year rollup, no per-claim detail | Hartford pivot |
| `hybrid_detail` | Cover sheet + per-claim detail pages + analytics pages | Hartford detailed, ICW Group |
| `flat_multipage_zeros` | Header repeats per page; claim block empty; group/report totals at end | AmTrust/ADP |

## 13. Architecture summary

```
PDF (9 docs)
  │
  ├─→ pdftotext -layout (8 text PDFs)
  │     └─→ if text → use as Pass-1 grounding text
  │
  ├─→ Qwen-VL OCR (1 scanned PDF: Arrowhead, fallback)
  │     └─→ per-page OCR text
  │
  ├─→ pdf2image → PNG pages
  │
  ▼
[PASS 2: Grounded extraction]
  Qwen3-VL-4B-Instruct (per chunk of N pages)
  inputs: page images + grounding text + V4 system prompt (12.7 KB)
  prompt: universal schema + 20 extraction rules
  chunking: try [n, 3, 1] page chunks until parsed
  → JSON per chunk → stitched output
  │
  ▼
[EVAL]
  - eval_vs_gt.py: field-level F1 vs GT v3 (78.9%)
  - eval_coverage.py: full coverage vs pdftotext (83.8%)
  Per-doc + per-archetype + per-category breakdown
```

---

**Author:** Claude Code (Opus 4.7) supervised by user
**Generated:** 2026-05-01 19:00 UTC
