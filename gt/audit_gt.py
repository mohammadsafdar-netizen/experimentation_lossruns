"""Audit user-provided AI-generated GT against actual PDFs via Tesseract OCR.

Strategy: for each document, pick 5-10 high-stakes values from GT.
Check each appears in OCR text (substring or normalized match).
Report per-document match rate. <90% = fix GT. >95% = trust.
"""
import os
import re
from pathlib import Path

os.environ["TESSDATA_PREFIX"] = str(Path.home() / "tessdata")

from PIL import Image
import tesserocr

PNG_DIR = Path(__file__).parent.parent / "png"


def ocr_full_doc(form_dir: Path) -> str:
    """OCR all pages of a form, return concatenated text."""
    text_parts = []
    with tesserocr.PyTessBaseAPI(lang="eng") as api:
        for png in sorted(form_dir.glob("page*.png")):
            api.SetImage(Image.open(png).convert("RGB"))
            text_parts.append(api.GetUTF8Text())
    return "\n".join(text_parts)


def normalize(s: str) -> str:
    """Strip non-word chars, lowercase. For comparison only."""
    return re.sub(r"[^\w@.]", "", str(s).lower())


def found(needle: str, haystack: str, fuzzy: bool = False) -> bool:
    """Check if needle appears in haystack."""
    if needle is None or needle == "":
        return False
    h = haystack.lower()
    n = str(needle).lower()
    if n in h:
        return True
    if fuzzy:
        return normalize(needle) in normalize(haystack)
    return False


def audit():
    """Run audit on each document."""
    # Map filename → list of high-stakes (label, value, fuzzy?) tuples to check
    audits = {
        "21_25_WORK_10_22_25_Employers_Loss_runs__PSQ_PRODUCTIONS": [
            ("carrier", "Employers", False),
            ("policyholder", "PSQ PRODUCTIONS", False),
            ("agency", "WORLDWIDE FACILITIES", False),
            ("data_as_of", "10/22/2025", False),
            ("policy_EIG469077602", "EIG469077602", False),
            ("policy_EIG469077600", "EIG469077600", False),
            ("claim_Guerra", "Guerra", False),
            ("claim_2023026815", "2023026815", False),
            ("Guerra_amount_21300", "21,300", False),
            ("Guerra_total_21530", "21,530", False),
            ("Alejandre", "Alejandre", False),
            ("Alejandre_amount_504", "504.92", False),
            ("Oconnor", "Oconnor", False),
            ("Oconnor_amount_1184", "1,184.72", False),
            ("combined_total_23219", "23,219.64", False),
            ("median_days_2", "2", True),  # too generic; fuzzy
        ],
        "24_26_RE_WORK_11_10_25_ICW_loss_runs": [
            ("carrier_ICW", "ICW", False),
            ("insured_PSQ", "PSQ PRODUCTIONS", False),
            ("agent_Arroyo", "ARROYO INSURANCE", False),
            ("agency_code", "0004569", False),
            ("address", "TECHNOLOGY DR", False),
            ("address_city", "IRVINE", False),
            ("zip", "92618", False),
            ("policy_WVE5075514_01", "WVE 5075514 01", False),
            ("policy_WVE5075514_00", "WVE 5075514 00", False),
            ("term_premium_63524", "63,524", False),
            ("loss_ratio_224", "224", False),
            ("claim_Rebecca", "Rebecca Duchsherer", False),
            ("claim_Eduardo", "Eduardo Baird", False),
            ("examiner_Danya", "DANYA DILBECK", False),
            ("examiner_Brea", "BREA PFANKUCH", False),
            ("amount_117100", "117,100", False),
            ("amount_40649", "40,649", False),
        ],
        "Loss_Runs_4_1_25_Eff_Date_to_Curr_ADP_1_27_26": [
            ("carrier_AmTrust", "AmTrust", False),
            ("insured_Partners", "Partners in Leadership", False),
            ("policy_QWC1446510", "QWC1446510", False),
            ("eff_date", "04/01/2025", False),
            ("no_claims", "No Claimants", True),  # fuzzy: case-insensitive
            ("zero_total", "0.00", False),
        ],
        "Loss_Runs_5_1_24_4_1_25_TriNet_Dated_1_26_26": [
            ("carrier_TRINET", "TRINET", False),
            ("location_Partners", "Partners In Leadership", False),
            ("location_code", "TIII24M6", False),
            ("claim_Kriegel", "KRIEGEL", False),
            ("claim_Jessica", "JESSICA", False),
            ("claim_M377969", "M377969", False),
            ("loss_date", "9/18/2024", False),
            ("description_slip", "SLIP AND FALL", False),
        ],
        "Loss_Runs_2021_to_2024___Insperity": [
            ("carrier_Insperity", "INSPERITY", False),
            ("client_Partners", "PARTNERS IN LEADERSHIP", False),
            ("origami", "ORIGAMI", False),
            ("zero_claims", "0", True),
        ],
        "Loss_Runs_2026___2018": [
            ("carrier_Everest", "Everest", False),
            ("broker_Arrowhead", "ARROWHEAD", False),
            ("admin_American", "American Claims Management", False),
            ("insured_Sea_West", "Sea West Enterprises", False),
            ("target_policy", "7600018496251", False),
            ("claim_173008376", "173008376", False),
            ("claim_Albert_Nystrom", "Albert", False),  # split surname/first
            ("loss_date_911", "9/11/2025", False),
            ("amount_626_86", "626.86", False),
            ("claim_173007214", "173007214", False),
            ("claim_Juan", "Juan", False),
            ("claim_Villanueva", "Villanueva", False),
            ("amount_72630", "72,630", False),
            ("claim_173005795", "173005795", False),
            ("claim_Cody_Walker", "Cody, Walker", True),  # fuzzy: punctuation
            ("amount_721_10", "721.10", False),
            ("claim_173006141", "173006141", False),
            ("claim_Albert_Nystrom_II", "Albert, Nystrom II", True),
            ("amount_721_94", "721.94", False),
        ],
        "SIR_HARTFORD_Loss_Runs_2016_25_val_8_21_05": [
            ("account_SIR", "Strategic Information Resources", False),
            ("policy_076WEG", "076WEG", False),
            ("aif_account", "1045104368", False),
            ("address", "Independence Ave", False),
            ("city", "Canoga Park", False),
            ("zip", "91303", False),
            ("date_produced", "08/21/2025", False),
            ("amount_7185", "7,185", False),
            ("amount_104444", "104,444", False),
            ("amount_122240", "122,240", False),
            ("amount_129425", "129,425", False),
        ],
        "SIR_Hartford_Loss_Runs_2016_25_val_8_21_25B": [
            # Same as above per GT (marked as duplicate)
            ("account_SIR", "Strategic Information Resources", False),
            ("policy_076WEG", "076WEG", False),
            ("aif_account", "1045104368", False),
            ("amount_7185", "7,185", False),
            ("amount_129425", "129,425", False),
        ],
        "Strategic_Information_Resources_Inc_loss_runs": [
            ("carrier_Hartford", "Hartford", False),
            ("insured_SIR", "Strategic Information Resources", False),
            ("city_Canoga", "Canoga Park", False),
            ("policy_076WEG", "076WEG", False),
            ("producer_Ap_Intego", "Ap Intego", False),
            ("producer_Fairport", "Fairport", False),
            ("producer_code", "250846", False),
            ("date_produced", "08/21/2025", False),
            ("claim_Y3WC99221", "Y3WC99221", False),
            ("claim_Balster", "Balster", False),
            ("amount_1056", "1,056", False),
            ("amount_75", "75", True),  # fuzzy, generic
        ],
    }

    print("=" * 70)
    print("GT AUDIT vs Tesseract OCR")
    print("=" * 70)

    results = {}
    for form_id, checks in audits.items():
        form_dir = PNG_DIR / form_id
        if not form_dir.exists():
            print(f"\n⚠️  {form_id}: NOT FOUND")
            continue
        ocr_text = ocr_full_doc(form_dir)
        passes, fails = 0, 0
        fail_list = []
        for label, value, fuzzy in checks:
            if found(value, ocr_text, fuzzy=fuzzy):
                passes += 1
            else:
                fails += 1
                fail_list.append((label, value))
        total = passes + fails
        rate = passes / total if total else 0
        verdict = "✓ TRUSTED" if rate >= 0.90 else ("⚠️ AUDIT" if rate >= 0.70 else "✗ FIX")
        print(f"\n{form_id}: {passes}/{total} ({rate:.0%}) {verdict}")
        for label, val in fail_list:
            print(f"    ✗ {label!r}: GT says {val!r} — NOT FOUND in OCR")
        results[form_id] = {"passes": passes, "fails": fails, "rate": rate, "fail_list": fail_list}

    print("\n" + "=" * 70)
    print("OVERALL")
    print("=" * 70)
    total_passes = sum(r["passes"] for r in results.values())
    total_total = sum(r["passes"] + r["fails"] for r in results.values())
    print(f"Total: {total_passes}/{total_total} ({total_passes/max(1,total_total):.0%})")
    if total_passes / max(1, total_total) >= 0.95:
        print("✓ GT TRUSTWORTHY (>95% match)")
    elif total_passes / max(1, total_total) >= 0.85:
        print("⚠️ GT MOSTLY OK BUT NEEDS FIXES (85-95% match)")
    else:
        print("✗ GT HAS SIGNIFICANT ERRORS (<85% match)")


if __name__ == "__main__":
    audit()
