"""Build loss_runs_gt_v3_pdftext.json from loss_runs_gt_v2_audited.json by applying
19 typo corrections discovered via page-by-page audit (pdftotext + visual review).

Source of truth: PDF embedded text (pdftotext -layout) for 8 text-PDFs;
visual page-by-page verification for 1 scanned PDF (Arrowhead).

See AUDIT_CORRECTIONS.md for per-typo evidence.
"""
import json
from pathlib import Path
from copy import deepcopy

ROOT = Path(__file__).parent
SRC = ROOT / "loss_runs_gt_v2_audited.json"
DST = ROOT / "loss_runs_gt_v3_pdftext.json"


def find_doc(gt: dict, name_part: str) -> dict:
    for d in gt["documents"]:
        if name_part in d["file_name"]:
            return d
    raise KeyError(name_part)


def find_claim(doc: dict, claim_number: str) -> dict | None:
    for p in doc.get("policies") or []:
        for c in p.get("claims") or []:
            if c.get("claim_number") == claim_number:
                return c
    for c in doc.get("claims") or []:
        if c.get("claim_number") == claim_number:
            return c
    return None


def main():
    gt = json.loads(SRC.read_text())
    gt = deepcopy(gt)
    gt["_meta"]["version"] = "v3_pdftext"
    gt["_meta"]["audited_on"] = "2026-05-01"
    gt["_meta"]["auditor"] = "pdftotext-grounded re-audit (8/9 PDFs) + visual page-by-page (Arrowhead scanned)"
    gt["_meta"]["supersedes"] = "loss_runs_gt_v2_audited.json"
    gt["_meta"]["audit_corrections_count"] = 19

    fixes = []

    # === EMPLOYERS (10 fixes) ===
    emp = find_doc(gt, "Employers")
    # Policyholder name typo
    emp["document_metadata"]["policyholder"] = "PSQ PRODUCTIONS LLC"
    fixes.append("Employers/policyholder: PSG → PSQ")

    # Policy numbers (auditor inserted phantom 2/6 digit + wrong final digit)
    pol_corrections = [
        ("EIG2469077802", "EIG469077603"),
        ("EIG2469077801", "EIG469077602"),
        ("EIG2469077800", "EIG469077601"),
        ("EIG6469077800", "EIG469077600"),
    ]
    for p, (old, new) in zip(emp["policies"], pol_corrections):
        assert p["policy_number"] == old, f"expected {old}, got {p['policy_number']}"
        p["policy_number"] = new
        fixes.append(f"Employers/policy_number: {old} → {new}")

    # Claim numbers (Guerra and Oconnor)
    guerra = find_claim(emp, "2023030615")
    assert guerra is not None
    guerra["claim_number"] = "2023026815"
    fixes.append("Employers/Guerra claim_number: 2023030615 → 2023026815")
    # Guerra net_expense penny rounding
    guerra["net_expense"] = 3547.48
    fixes.append("Employers/Guerra net_expense: 3547.46 → 3547.48")

    # Update parent policy_period_totals to match the corrected claim
    emp["policies"][1]["policy_period_totals"]["net_expense"] = 3547.48
    fixes.append("Employers/policies[1].policy_period_totals.net_expense: 3547.46 → 3547.48")

    oconnor = find_claim(emp, "2021037998")
    assert oconnor is not None
    oconnor["claim_number"] = "2021007688"
    fixes.append("Employers/Oconnor claim_number: 2021037998 → 2021007688")

    # policies[3].policy_period_totals.net_expense
    emp["policies"][3]["policy_period_totals"]["net_expense"] = 157.35
    fixes.append("Employers/policies[3].policy_period_totals.net_expense: 158.35 → 157.35")

    # combined_all_periods_totals.net_expense
    emp["combined_all_periods_totals"]["net_expense"] = 3704.83
    fixes.append("Employers/combined_all_periods_totals.net_expense: 3706.81 → 3704.83")

    # === STRATEGIC INFO HARTFORD (2 fixes) ===
    strategic = find_doc(gt, "Strategic_Information_Resources")
    bal = find_claim(strategic, "Y3WC99221")
    assert bal is not None
    bal["claimant_name"] = "Balster, Justine"
    fixes.append("StrategicInfo/Y3WC99221 claimant_name: Baister → Balster")
    bal["reported_date"] = "02/20/2024"
    fixes.append("StrategicInfo/Y3WC99221 reported_date: 02/19/2024 → 02/20/2024")

    # === ICW (5 fixes) ===
    icw = find_doc(gt, "ICW")
    icw["current_account_summary"]["medical_closed"] = 0
    fixes.append("ICW/current_account_summary.medical_closed: 1 → 0")

    # Claim 2025001519 — Eduardo "Bartold" → "Baird"
    eduardo = find_claim(icw, "2025001519")
    assert eduardo is not None
    eduardo["claimant_name"] = "Eduardo Baird Alejandre"
    fixes.append("ICW/2025001519 claimant_name: Bartold → Baird")
    eduardo["cause"] = "Fall/Slip: Fall/Slip/Trip, Noc"
    fixes.append("ICW/2025001519 cause: Fall/Slp → Fall/Slip")

    # Claim 2025028840 — nature missing colon
    rebecca = find_claim(icw, "2025028840")
    assert rebecca is not None
    rebecca["nature_of_injury"] = "Occ: Mental Stress"
    fixes.append("ICW/2025028840 nature_of_injury: 'Occ Mental Stress' → 'Occ: Mental Stress'")

    # Claim 2024031850 — examiner "ENWIN QUACH" → "KEVIN QUACH"
    melvin = find_claim(icw, "2024031850")
    assert melvin is not None
    melvin["claim_examiner"] = "KEVIN QUACH"
    fixes.append("ICW/2024031850 claim_examiner: ENWIN QUACH → KEVIN QUACH")

    # === HARTFORD PIVOTS (2 fixes — both copies) ===
    for hartford_name in ("SIR_HARTFORD", "SIR_Hartford"):
        h = find_doc(gt, hartford_name)
        for entry in h.get("policy_year_lob_pivot") or []:
            if entry.get("policy_period_lob") == "GENERAL LIAB 2016-2025":
                entry["policy_period_lob"] = "GENERAL LIAB 2016-2020"
                fixes.append(f"{hartford_name}/GENERAL LIAB period: 2025 → 2020")

    # Save
    gt["_meta"]["audit_corrections"] = fixes
    DST.write_text(json.dumps(gt, indent=2))

    print(f"[ok] wrote {DST}")
    print(f"[fixes] {len(fixes)} corrections applied:\n")
    for f in fixes:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
