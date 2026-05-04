"""Migrate GT v3 → v4: add Hartford policy_year_lob_pivot[] + raw_combined_cell.

v4 adds new fields per schema_v4 changes:
  - document.policy_year_lob_pivot[]  (Hartford pivots)
  - claims[].location.raw_combined_cell (Hartford detail)
  - claims[].identity.claim_number_history[] (system migrations)
  - examiner.role
  - injury.nature_of_injury_prefix locked semantics
"""
import json
from pathlib import Path
from copy import deepcopy
from datetime import datetime, timezone

ROOT = Path(__file__).parent
SRC = ROOT / "loss_runs_gt_v3_pdftext.json"
DST = ROOT / "loss_runs_gt_v4_schema_extended.json"


def find_doc(gt, part):
    for d in gt["documents"]:
        if part in d["file_name"]:
            return d
    return None


def main():
    gt = json.loads(SRC.read_text())
    gt = deepcopy(gt)
    gt["_meta"]["version"] = "v4_schema_extended"
    gt["_meta"]["audited_on"] = "2026-05-02"
    gt["_meta"]["supersedes"] = "loss_runs_gt_v3_pdftext.json"
    gt["_meta"]["schema"] = "loss_run.schema_v4.json"

    fixes = []

    # === Hartford pivot a (val 8.21.05) — populate policy_year_lob_pivot ===
    h_a = find_doc(gt, "SIR_HARTFORD_Loss_Runs_2016_25_val_8_21_05")
    h_a["document_metadata"]["policy_year_lob_pivot"] = [
        {"line_of_business": "WORKERS COMP", "lob_code": "W",
         "policy_number": "076WEG AF8JGW",
         "policy_period_start": "2025-03-07", "policy_period_end": "2026-03-07",
         "earned_premium": 7185, "loss_ratio": 0.0, "paid_claims": 0,
         "open_claims": 0, "written_premium": 15677,
         "agency_code": "250846", "msi": "830", "scope": "latest_policy"},
        {"is_total_row": True, "scope": "latest_policy",
         "line_of_business": "WORKERS COMP", "earned_premium": 7185, "loss_ratio": 0.0,
         "paid_claims": 0, "written_premium": 15677},
        {"line_of_business": "FIRE & ALLIED", "lob_code": "P",
         "policy_period_label": "2016-2020", "earned_premium": 4608,
         "loss_ratio": 0.0, "paid_claims": 0, "scope": "row"},
        {"line_of_business": "WORKERS COMP", "lob_code": "W",
         "policy_period_label": "2016-2025", "earned_premium": 104444,
         "loss_ratio": 0.01, "paid_claims": 1, "scope": "row"},
        {"line_of_business": "GENERAL LIAB", "lob_code": "L",
         "policy_period_label": "2016-2020", "earned_premium": 13188,
         "loss_ratio": 0.0, "paid_claims": 0, "scope": "row"},
        {"is_total_row": True, "scope": "prior_lob", "earned_premium": 122240,
         "loss_ratio": 0.009, "paid_claims": 1},
        {"is_total_row": True, "scope": "account_total", "earned_premium": 129425,
         "loss_ratio": 0.008, "paid_claims": 1},
    ]
    fixes.append(f"Hartford a: added policy_year_lob_pivot[] with 7 rows")

    # === Hartford pivot b (val 8.21.25B) — same content (duplicate) ===
    h_b = find_doc(gt, "SIR_Hartford_Loss_Runs_2016_25_val_8_21_25B")
    h_b["document_metadata"]["policy_year_lob_pivot"] = h_a["document_metadata"]["policy_year_lob_pivot"]
    fixes.append(f"Hartford b: added policy_year_lob_pivot[] (same as a)")

    # === Strategic Info Hartford — populate raw_combined_cell on the claim ===
    si = find_doc(gt, "Strategic_Information_Resources_Inc_loss_runs")
    if si and "policies" in si:
        for p in si["policies"]:
            for c in p.get("claims", []):
                if c.get("claim_number") == "Y3WC99221":
                    c["raw_combined_cell"] = (
                        "Canoga Park Ca/Struck By Flying/falling Object - Not We /Office Manager"
                    )
                    fixes.append("Strategic Info: added raw_combined_cell to Y3WC99221")

    # === ICW — already has prefixed nature_of_injury values; v4 lock-semantics
    # is more about the EXTRACTION RULE than GT itself. GT can stay as-is.
    fixes.append("ICW: prefix semantics locked in extraction prompt (no GT change needed)")

    # === Save ===
    gt["_meta"]["v4_changes"] = fixes
    DST.write_text(json.dumps(gt, indent=2, default=str))
    print(f"[ok] wrote {DST}")
    print(f"[changes] {len(fixes)}:")
    for f in fixes:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
