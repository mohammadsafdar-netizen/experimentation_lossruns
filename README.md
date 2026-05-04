# Loss-Run Ground Truths

Hand-curated ground-truth annotations for 9 workers'-comp loss-run PDFs across 7 carriers (2026-04 / 2026-05).

> **PRIVATE REPO ONLY.** Contains real PII (claimant names, claim numbers, employer/broker/carrier names). Do not make public.

## Layout

```
gt/
├── loss_runs_gt_v1_unaudited.json     # initial annotation pass, no audit
├── loss_runs_gt_v2_audited.json       # 1st audit pass
├── loss_runs_gt_v3_pdftext.json       # rebuilt against pdftotext to fix typos
├── loss_runs_gt_v4_schema_extended.json # schema v5 fields added (75 industry-standard)
├── loss_runs_gt_v5.json               # consolidated production GT (May 3)
├── loss_runs_gt_v6.json               # current — second-pass audit (May 4)
│
├── per_carrier_field_inventory.json   # which fields each carrier emits
├── AUDIT_CORRECTIONS.md               # log of every correction applied (v5 → v6)
│
├── audit_gt.py                        # runs schema/value sanity checks across GT
├── build_gt_v3.py / build_gt_v4.py / build_gt_v5.py  # version progression scripts
│
└── verifications/                     # per-doc, per-field manual verification audit trail
```

## Versions

| Version | Date | Notes |
|---|---|---|
| v1 | Apr 30 2026 | Unaudited initial annotation |
| v2 | Apr 30 2026 | First audit pass |
| v3 | May 1  2026 | Rebuilt from `pdftotext` to fix 19 typo-class corrections |
| v4 | May 2  2026 | Schema v5 — extended to 75 industry-standard fields |
| v5 | May 3  2026 | Consolidated production GT |
| **v6** | **May 4  2026** | **Current — 20 corrections applied via second-pass audit** (see AUDIT_CORRECTIONS.md) |

The 9 docs covered (across 7 carriers + 1 narrative + 1 PEO summary):

1. `21-25 WORK 10.22.25 Employers Loss runs -PSQ PRODUCTIONS.pdf` — Employers (1pg, row-per-claim)
2. `24-26 RE WORK 11-10-25 ICW loss runs.pdf` — ICW Group (15pg, form-per-claim)
3. `Loss Runs 2021 to 2024 - Insperity.pdf` — Insperity PEO (2pg, summary)
4. `Loss Runs 2026 - 2018.pdf` — Arrowhead/Everest (12pg, multi-section)
5. `Loss Runs 4.1.25 Eff Date to Curr ADP 1.27.26.pdf` — ADP/AmTrust PEO (3pg)
6. `Loss Runs 5.1.24-4.1.25-TriNet Dated 1.26.26.pdf` — TriNet PEO (2pg)
7. `SIR HARTFORD Loss Runs 2016-25 val 8.21.05.pdf` — Hartford pivot (1pg, summary)
8. `SIR Hartford Loss Runs 2016-25 val 8.21.25B.pdf` — Hartford pivot (1pg, summary, dup)
9. `Strategic Information Resources Inc loss runs.pdf` — Hartford detailed (1pg)

## Headline numbers (against v6)

- Production winner-only F1: **91.12%** (554/608 fields, commit `242e2d8` of upstream repo)
- Strict F1: 88.5%
- Per-archetype: ICW 99% / Employers 96% / Arrowhead 97% / Insperity 92% / Hartford pivots 88%

## Schema

The schema is a 75-field workers'-comp loss-run target covering: document metadata, policy summary, per-claim identity / dates / financials / injury / examiner, and combined-period totals. See any v5+ JSON for the canonical structure.

## License

Internal only. No license granted for redistribution.
