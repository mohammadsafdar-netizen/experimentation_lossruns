# Loss-Run Ground Truths + Comparison Docs (current state)

Hand-curated ground-truth annotations for 9 workers'-comp loss-run PDFs across 7 carriers, plus the latest comparison and ablation results. **Only the most-reliable v6 GT is kept** — older versions (v1–v5) were removed to avoid confusion. v6 is the second-pass-audited target with 20 verified corrections (May 4, 2026).

## Latest comparison docs (`docs/`)

- **[`docs/V7_COVERAGE_2026_05_04.md`](docs/V7_COVERAGE_2026_05_04.md)** — production accuracy against the richer GT v7 schema: **86.2% upper-bound coverage** (741/860 leaf values). Per-doc breakdown + interpretation.
- **[`docs/INSIGHTS.md`](docs/INSIGHTS.md)** — production state (May 4, 2026): **91.12% winner-only F1 / 88.5% strict** on GT v6, per-archetype breakdown, active bottlenecks, cross-references
- **[`docs/TABLE_EXTRACTOR_COMPARISON.md`](docs/TABLE_EXTRACTOR_COMPARISON.md)** — head-to-head of docling, pdfplumber, pymupdf, unstructured, and YOLO+docling cascade across all archetypes. **Conclusion:** no single tool wins; per-archetype routing is the production path.
- **[`docs/ABLATION_MATRIX_2026_05_04.md`](docs/ABLATION_MATRIX_2026_05_04.md)** — VLM × OCR-config matrix. **Key finding:** bbox-coordinates-in-prompt regresses Qwen3-VL by 2.47pp (Landing AI's parse-once trick does NOT transfer to a 3-input setup). Granite/Dolphin swap-in tests confirm Qwen3-VL baseline; Granite at 15.95% F1, Dolphin produces empty output.
- **[`docs/LESSONS.md`](docs/LESSONS.md)** — 11 codified lessons (cache invalidation, A/B discipline, namespace separation, etc.)

## Scripts (`scripts/`)

- **[`scripts/score_v7_coverage.py`](scripts/score_v7_coverage.py)** — score any production output dir against `gt/loss_runs_gt_v7_extended.json`. Walks GT leaf values, checks substring-presence in the extraction. Used to produce the 86.2% number above.

> ⚠ Older milestone docs (`90_PERCENT_MILESTONE_2026_05_03.md`, `FINAL_94_7PCT_2026_05_03.md`, etc.) at the repo root are **pre-GT-v6**. Their numbers (90-94.7%) were produced against earlier GT versions that contained typos and duplicate-field counting; the rigorous v6 audit revealed and corrected those. **Trust the May 4 docs in `docs/` over the May 3 milestone docs at root.**

> **PRIVATE REPO ONLY.** Contains real PII (claimant names, claim numbers, employer/broker/carrier names). Do not make public.

## Layout

```
gt/
├── loss_runs_gt_v6.json                     # 47K — production target schema (75 fields)
├── loss_runs_gt_v7_extended.json            # NEW — richer schema (~140 fields, examiner contact, demographics, analytics, vendor tags)
│
├── per_doc/                                 # same v6 data, split per form (1 file per loss run)
│   ├── 21_25_WORK_10_22_25_Employers_Loss_runs__PSQ_PRODUCTIONS.json
│   ├── 24_26_RE_WORK_11_10_25_ICW_loss_runs.json
│   ├── Loss_Runs_2021_to_2024___Insperity.json
│   ├── Loss_Runs_2026___2018.json
│   ├── Loss_Runs_4_1_25_Eff_Date_to_Curr_ADP_1_27_26.json
│   ├── Loss_Runs_5_1_24_4_1_25_TriNet_Dated_1_26_26.json
│   ├── SIR_HARTFORD_Loss_Runs_2016_25_val_8_21_05.json
│   ├── SIR_Hartford_Loss_Runs_2016_25_val_8_21_25B.json
│   └── Strategic_Information_Resources_Inc_loss_runs.json
│
├── per_carrier_field_inventory.json         # which fields each carrier emits
├── AUDIT_CORRECTIONS.md                     # log of every correction in v6
├── audit_gt.py                              # schema/value sanity checks
└── verifications/                           # per-doc, per-field manual audit trail
```

`loss_runs_gt_v6.json` and `per_doc/*.json` contain the **same data** — pick whichever shape your pipeline prefers (consolidated for cross-doc eval, split for per-doc workflows).

## Coverage

| File (doc stem) | Carrier | Layout archetype | Pages | Claims |
|---|---|---|---|---|
| `21_25_WORK_10_22_25_Employers_Loss_runs__PSQ_PRODUCTIONS` | Employers Preferred | row-per-claim, digital | 1 | 3 |
| `24_26_RE_WORK_11_10_25_ICW_loss_runs` | ICW Group | form-per-claim, scanned | 15 | 12 |
| `Loss_Runs_2021_to_2024___Insperity` | Insperity (PEO) | summary, digital | 2 | 0 |
| `Loss_Runs_2026___2018` | Arrowhead / Everest | multi-section, scanned | 12 | 4 |
| `Loss_Runs_4_1_25_Eff_Date_to_Curr_ADP_1_27_26` | ADP / AmTrust (PEO) | summary, digital | 3 | 0 |
| `Loss_Runs_5_1_24_4_1_25_TriNet_Dated_1_26_26` | TriNet (PEO) | summary, digital | 2 | 1 |
| `SIR_HARTFORD_Loss_Runs_2016_25_val_8_21_05` | Hartford pivot | summary, digital | 1 | 0 |
| `SIR_Hartford_Loss_Runs_2016_25_val_8_21_25B` | Hartford pivot (dup) | summary, digital | 1 | 0 |
| `Strategic_Information_Resources_Inc_loss_runs` | Hartford detailed | row-per-claim, digital | 1 | 1 |

## Headline numbers (against v6)

- Production winner-only F1: **91.12%** (554/608 fields)
- Strict F1: **88.5%**
- Per-archetype: ICW 99% / Employers 96% / Arrowhead 97% / Insperity 92% / Hartford pivots 88%

## Schema

75-field workers'-comp loss-run schema covering: document metadata, policy summary, per-claim identity / dates / financials / injury / examiner, and combined-period totals. Each per-doc JSON is a single `document` object; the consolidated v6 has them under a top-level `documents: [...]` list.

## License

Internal only. No license granted for redistribution.
