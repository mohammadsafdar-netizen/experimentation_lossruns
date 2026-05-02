# Schema v4 — Rationale and Examples

**Built:** 2026-05-02
**Extends:** v2 (loss_run.schema.json, 462 paths)
**Strategy:** Extend universal schema (NOT per-carrier). Merge to canonical fields, preserve raw values.
**Decision authority:** Modified directly per session; one consolidated review at end.

---

## Why these 9 changes

Each addresses a real failure mode observed in the 9-doc reference corpus AND scales to N carriers (not single-carrier hacks). Together they unlock ~+30-50pp on the worst-performing archetypes (`summary_pivot`, `hybrid_detail`).

---

## CHANGE 1 — `document.policy_year_lob_pivot[]` ★ highest impact

**Failure mode:** Hartford summary_pivot archetype scores 27-45% F1. Schema lacked a structured field for the LOB×period pivot table that Hartford prints.

**Generalisation:** Multiple carriers print pivot summaries (BlueCross multi-LOB, Travelers account summary). Universal pivot field works for any of them.

**Example (Hartford, val 8.21.05):**

```text
PDF prints:
  LATEST POLICY INFORMATION
   W   076WEG AF8JGW   03/07/2025-03/07/2026   $7,185   0.0%   0   0   ...
  LATEST POLICY INFORMATION TOTAL              $7,185   0.0%   0   ...
  PRIOR LOB
   P   FIRE & ALLIED                            $4,608   0.0%   0   ...
   W   WORKERS COMP                            $104,444  1.0%   1   ...
   L   GENERAL LIAB                            $13,188   0.0%   0   ...
  PRIOR LOB TOTAL                              $122,240  0.9%   1   ...
  ACCOUNT TOTAL                                $129,425  0.8%   1   ...

Schema v4 fills:
{
  "document": {
    "policy_year_lob_pivot": [
      {"line_of_business":"WORKERS COMP","lob_code":"W",
       "policy_number":"076WEG AF8JGW","policy_period_start":"2025-03-07",
       "policy_period_end":"2026-03-07","earned_premium":7185,"loss_ratio":0,
       "paid_claims":0,"open_claims":0,"scope":"latest_policy"},
      {"line_of_business":"WORKERS COMP","lob_code":"W",
       "earned_premium":7185,"loss_ratio":0,"is_total_row":true,
       "scope":"latest_policy"},   // LATEST POLICY INFORMATION TOTAL
      {"line_of_business":"FIRE & ALLIED","lob_code":"P",
       "policy_period_start":"2016-03-07","policy_period_end":"2020-03-07",
       "earned_premium":4608,"loss_ratio":0,"paid_claims":0,"scope":"row"},
      ...
      {"is_total_row":true,"scope":"prior_lob",
       "earned_premium":122240,"loss_ratio":0.009,"paid_claims":1},
      {"is_total_row":true,"scope":"account_total",
       "earned_premium":129425,"loss_ratio":0.008,"paid_claims":1}
    ]
  }
}
```

**Distinct from existing fields:**
- `policies[]` — individual policy terms with claims (not pivot rows)
- `section_totals[]` — cross-policy rollup rows only
- `policy_year_lob_pivot[]` — full grid of LOB × period intersections

---

## CHANGE 2 — `document.report_platform`

**Failure mode:** TriNet/Insperity/Hartford detail use Origami Risk SaaS. The platform prints its own metadata (filters, run dates, options) which were going into `report_definition` without identifying the platform.

**Generalisation:** Risk-management platform is a separate dimension from carrier and TPA. Examples:
- Origami Risk → TriNet, Insperity loss runs
- Riskonnect → many enterprise insureds
- Marsh ClearSight → Marsh-managed accounts
- Ventiv → Ventiv-hosted carriers

**Example (TriNet):**
```json
{
  "document": {
    "report_platform": {
      "name": "Origami Risk",
      "logo_text": "ORIGAMI RISK"
    }
  }
}
```

---

## CHANGE 3 — `claims[].identity.claim_number_history[]`

**Failure mode:** AmTrust prints "Converted Claim #" for legacy migrated claims. v2 had `converted_claim_number` (single-valued) which doesn't generalise to carriers with multi-system histories.

**Generalisation:** Any carrier that has migrated systems (or insurers acquired by another) will have multiple historical claim numbers. Array form scales.

**Example (AmTrust ADP):**
```json
{
  "identity": {
    "claim_number": "QWC1446510-NEW-001",
    "claim_number_history": [
      {"claim_number": "OLD-12345", "source_system": "AmTrust pre-2020 ICM",
       "valid_from": "2018-04-15", "valid_to": "2020-12-31"}
    ]
  }
}
```

Backward-compat: `converted_claim_number` (single field) kept as alias.

---

## CHANGE 4 — `claims[].location.raw_combined_cell` (locked semantics)

**Failure mode:** Hartford detail combines location + cause + occupation in ONE cell. Doc-level F1 stuck at 11.5% because parsing fails on the boundaries.

**Generalisation:** Any combined-cell layout (Sedgwick TPA reports do similar). Field already existed in v2; v4 LOCKS it as REQUIRED for `hybrid_detail` archetype.

**Example (Strategic Info Hartford):**
```text
PDF cell content (one cell):
  "Canoga Park Ca/Struck By Flying-falling Object - Not We /Office Manager"

Schema v4 fills:
{
  "claims": [{
    "location": {
      "injury_location_city": "Canoga Park",
      "injury_location_state": "CA",
      "raw_combined_cell": "Canoga Park Ca/Struck By Flying-falling Object - Not We /Office Manager"
    },
    "injury": {
      "cause_of_injury": "Struck By Flying-falling Object - Not We"
    },
    "identity": {
      "claimant_occupation": "Office Manager"
    }
  }]
}
```

**Rule:** even when individually parsed, `raw_combined_cell` MUST be preserved when source was a combined cell. Audit trail for downstream verification.

---

## CHANGE 5 — Prefix semantics locked

**Failure mode:** ICW prints `Spc: Strain` / `Trunk: Low Back (Lmbr/Lmbo-Sac)`. v2 had both `nature_of_injury` and `nature_of_injury_prefix` but didn't lock who gets what.

**Locked rule:**
- `nature_of_injury_prefix` = the prefix string (`Spc`, `Occ`, `Mult`)
- `nature_of_injury` = stripped main value (`Strain`, NOT `Spc: Strain`)
- Same for `body_part_prefix` / `body_part`

**Example (ICW Eduardo Baird Alejandre):**
```json
{
  "injury": {
    "nature_of_injury": "Strain",
    "nature_of_injury_prefix": "Spc",
    "body_part": "Low Back (Lmbr/Lmbo-Sac)",
    "body_part_prefix": "Trunk"
  }
}
```

**Generalisation:** Any carrier using NCCI taxonomic prefixes (Sedgwick, BlueCross, large self-insured TPAs) follows similar pattern.

---

## CHANGE 6 — `examiner` shape lock

**Failure mode:** Some extractors emit `examiner.contact = {...}` (nested), some flat. Inconsistency hurts cross-carrier query.

**Locked shape:**
```json
{
  "examiner": {
    "name": "BREA PFANKUCH",
    "id": null,
    "phone": "(858) 350-2665",
    "email": "bpfankuch@icwgroup.com",
    "category": null,
    "role": "examiner"
  }
}
```

5 fields, all siblings, no nested wrapper. Added `role` enum for cross-carrier consistency.

---

## CHANGE 7 — `verification.reconciliation_summary`

**Failure mode:** Downstream consumers (ACORD form fillers, underwriting analytics) need a quick pass/fail summary without parsing every individual check.

**Example:**
```json
{
  "verification": {
    "reconciliation_summary": {
      "checks_run": 24,
      "checks_passed": 22,
      "checks_failed": 2,
      "overall_pass": false,
      "categories_failed": ["bucket_arithmetic", "policy_total"]
    },
    "checks": [...]   // detailed per-check entries (existing v2 field)
  }
}
```

**Generalisation:** Universal gating signal regardless of carrier specifics.

---

## CHANGE 8 — `document.currency`

**Failure mode:** None observed (US-only corpus). But: schema must be future-proof for international expansion (UK lossy runs, Canadian comp, etc.).

**Example:**
```json
{"document": {"currency": "USD"}}
```

Default = `USD`. Cheap field, prevents downstream ambiguity.

---

## CHANGE 9 — `claims[].cross_references[]`

**Failure mode:** v2's `related_claim_number` was single-valued, can't represent claims with multiple relationships (re-opening + linked litigation, or split claim).

**Generalisation:** Insurance claims commonly have N relationships:
- Re-openings of original claim
- Linked litigation (workers' comp + GL on same incident)
- Multi-policy claims (one event spanning two policies)
- Subrogation linked claims

**Example:**
```json
{
  "cross_references": [
    {"claim_number": "2023030615", "policy_id": "EIG469077602|2023-01-14",
     "relationship": "reopening_of",
     "note": "Original closed 7/16/2024, reopened 8/2/2024 due to surgical complication"}
  ]
}
```

Backward-compat: `related_claim_number` kept.

---

## What was NOT added (rejected for generalisability)

| Rejected idea | Why rejected |
|---|---|
| `policies[].carrier_specific_fields` (pass-through map) | Defeats universal schema; downstream can't query consistently |
| `injury.nature_code` (NCCI nature code int) | Not always printed; can be derived later if needed |
| `claims[].litigation_details` (case_number, court, etc.) | Not in observed corpus; YAGNI |
| `document.medicare_msa_required` (CMS flag) | Real concept but not yet observed in our 9 docs |
| `policies[].self_insured_retention` (SIR amount) | Excess policy concept; not in observed corpus |

These can be added later when actually observed in real loss runs (post-Phase 2 synthetic data).

---

## Migration impact

**On GT v3:** Hartford pivot docs (2 of 9) need new `policy_year_lob_pivot[]` populated. Other docs unchanged. ~30 new GT field values across 2 docs.

**On extraction prompts:** v4 prompt needs §6 schema example updated to show new fields with examples. ~+1KB to prompt.

**On evaluator:** `eval_vs_gt.py` field map needs entries for new GT fields. ~10 mapping additions.

**On downstream consumers:** Backward-compatible — all v2 fields preserved. New fields are additive. No breaking changes.

---

## Estimated F1 impact (vs current LightOn+Qwen 80.1% baseline)

| Change | Doc(s) affected | Expected gain |
|---|---|---|
| `policy_year_lob_pivot[]` | Hartford pivot a, b | **+9pp on summary_pivot archetype** |
| `raw_combined_cell` semantics | Strategic Info Hartford | **+30pp on hybrid_detail doc fields** (11.5% → 40%+) |
| `claim_number_history[]` | AmTrust ADP | +2pp |
| Prefix locks | ICW (276 claim fields) | +3pp on ICW |
| `report_platform` | TriNet, Insperity, Hartford detail | +1pp doc fields |
| Other locks (examiner, currency, etc.) | All | +1-2pp incremental |
| **Total expected** | | **+15-25pp F1 overall** (from 80.1% to ~95-105%, likely capping at ~92%) |

---

## Next steps

1. ✅ Schema v4 built at `data/loss_runs/schema/loss_run.schema_v4.json`
2. ✅ Rationale doc at `data/loss_runs/schema/SCHEMA_V4_RATIONALE.md`
3. ⏳ User reviews
4. ⏳ Update prompt v4 → v5 (proper) with new schema example
5. ⏳ Migrate GT v3 → v4 (Hartford pivot rows + locked semantics)
6. ⏳ Update eval mappings
7. ⏳ Re-run extraction on all 9 docs
8. ⏳ Compare results
