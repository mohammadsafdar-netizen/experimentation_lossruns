# GT Audit Corrections — page-by-page review

**Audited 2026-05-01.** Method: `pdftotext -layout` for 8 text-based PDFs (authoritative — extracts embedded PDF text). Visual page-by-page review for the 1 scanned PDF (Arrowhead).

**Conclusion: `loss_runs_gt_v2_audited.json` has 15+ typos across 4 of 9 docs.** The previous "GT trustworthy at 98%" claim (task #37) was wrong.

---

## 1. Employers (`21-25_WORK_10_22_25_Employers_Loss_runs__PSQ_PRODUCTIONS.pdf`)

**Severity: WORST.** 9 typos.

| Field | GT v2 | PDF truth | Notes |
|---|---|---|---|
| `policyholder` | `PSG PRODUCTIONS LLC` | **`PSQ PRODUCTIONS LLC`** | G→Q typo |
| `policies[0].policy_number` | `EIG2469077802` | **`EIG469077603`** | extra "2", wrong digits |
| `policies[1].policy_number` | `EIG2469077801` | **`EIG469077602`** | extra "2", wrong digits |
| `policies[2].policy_number` | `EIG2469077800` | **`EIG469077601`** | extra "2", wrong digits |
| `policies[3].policy_number` | `EIG6469077800` | **`EIG469077600`** | extra "6", wrong digits |
| Guerra `claim_number` | `2023030615` | **`2023026815`** | wrong digits |
| Oconnor `claim_number` | `2021037998` | **`2021007688`** | wrong digits |
| Guerra `net_expense` | `3547.46` | **`3547.48`** | rounding |
| pol[3] `net_expense` total | `158.35` | **`157.35`** | wrong |
| Combined `net_expense` | `3706.81` | **`3704.83`** | wrong |

**Where model was right vs GT:** all 4 policy numbers, 2 of 3 claim numbers, policyholder name. **Where model was wrong:** "Alejandre" → "Alejandro" (model hallucinated last char).

---

## 2. Strategic Info Hartford (`Strategic_Information_Resources_Inc_loss_runs.pdf`)

**Severity: 2 typos.**

| Field | GT v2 | PDF truth | Notes |
|---|---|---|---|
| Claim `claimant_name` | `Baister, Justine` | **`Balster Justine`** | i→l (font ambiguity) |
| Claim `reported_date` | `02/19/2024` | **`02/20/2024`** | day-after-loss |

---

## 3. ICW (`24-26_RE-WORK_11_10_25_ICW_loss_runs.pdf`)

**Severity: 3+ typos in claim 2025001519 alone.**

| Field | GT v2 | PDF truth | Notes |
|---|---|---|---|
| `current_account_summary.medical_closed` | `1` | **`0`** | wrong count |
| Claim 2025001519 `claimant_name` | `Eduardo Bartold Alejandre` | **`Eduardo Baird Alejandre`** | "Bartold" → "Baird" |
| Claim 2025028840 `nature_of_injury` | `Occ Mental Stress` | **`Occ: Mental Stress`** | missing colon |
| Claim 2025001519 `cause` | `Fall/Slp: Fall/Slp/Trip, Noc` | **`Fall/Slip: Fall/Slip/Trip, Noc`** | abbreviated wrong |

The 12-claim ICW detail rows on pages 4-12 not yet exhaustively re-verified — likely additional typos.

---

## 4. Hartford Pivots (`SIR_HARTFORD_*.pdf`, both copies)

**Severity: 1 typo (each).**

| Field | GT v2 | PDF truth | Notes |
|---|---|---|---|
| `policy_year_lob_pivot[3].policy_period_lob` | `GENERAL LIAB 2016-2025` | **`GENERAL LIAB 2016-2020`** | wrong period |

GT label says GL covers 2016-2025; PDF clearly shows 03/07/2016-03/07/2020.

---

## 5. Insperity, TriNet, ADP — GT correct

Verified against pdftotext extraction. Minor formatting differences only (missing comma in "PARTNERS IN LEADERSHIP, LLC" → "PARTNERS IN LEADERSHIP LLC"). Field values correct.

---

## 6. Arrowhead / Sea West — GT correct (visual page-by-page audit)

12 pages verified. All 4 claims (Albert Nystrom 173008376, Juan Villanueva 173007214, Cody Walker 173005795, Albert Nystrom II 173006141) and all 12 policy numbers match GT. Empty-policy markers match.

**Finding:** Arrowhead PDF is scanned (`pdftotext` returns 0 lines). Visual-only reference.

---

## Impact on extraction scoring

The eval at `eval_vs_gt.py` was scoring extraction against this typo-laden GT. For Employers:
- 4 wrong GT policy numbers → all 4 GT policies fail to match extracted policies → policy_F1 = 0/N
- 2 wrong GT claim numbers → 2 of 3 GT claims fail to match extracted claims → claim_F1 punished
- Wrong GT financial totals → arithmetic checks fail

**Estimated scoring inflation correction once GT is fixed:** Employers should jump from 13.6% to ~70%+. ICW slight bump. Strategic Info slight bump. Overall likely **v4 from 69.3% → ~78-82%**.

---

## Recommended action

1. Build corrected GT v3 by:
   - Auto-extracting authoritative fields from pdftotext output for 8 text PDFs.
   - Visual-confirmed Arrowhead retained as-is.
2. Update `loss_runs_gt_v2_audited.json` → `loss_runs_gt_v3_pdftext.json`.
3. Re-run eval against v3 GT.
4. Update task #37 ("GT trustworthy at 98%") with the correction.
