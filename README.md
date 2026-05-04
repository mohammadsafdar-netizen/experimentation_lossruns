# Loss-Run Ground Truths (current production)

Hand-curated ground-truth annotations for 9 workers'-comp loss-run PDFs across 7 carriers. **Only the most-reliable v6 GT is kept** — older versions (v1–v5) were removed to avoid confusion. v6 is the second-pass-audited target with 20 verified corrections (May 4, 2026).

> **PRIVATE REPO ONLY.** Contains real PII (claimant names, claim numbers, employer/broker/carrier names). Do not make public.

## Layout

```
gt/
├── loss_runs_gt_v6.json                     # 47K — consolidated v6 (all 9 docs in one file)
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
