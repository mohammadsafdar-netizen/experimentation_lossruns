"""Coverage score: % of GT v7 leaf values that appear in production extraction.

GT v7 is the richer schema (2-3× more fields per doc than v6, including
extended financials, examiner contact, demographics, analytics).

For each GT v7 leaf value (non-null, non-bool), check if its normalized form
appears as a substring in the union of all extracted text values from the
production output (cell A — `LightOnOCR + Qwen3-VL-4B`).

This is "upper-bound coverage" — what fraction of the richer GT did the
production extraction capture in ANY field. It's a strict floor for what a
schema-aware F1 would land at.

Usage:
    uv run python tests/score_v7_coverage.py
"""
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
GT_PATH = REPO / "data" / "loss_runs" / "gt" / "loss_runs_gt_v7_extended.json"
PROD_DIR = REPO / "experiments" / "30_voter" / "output_voter_flat_with_aggregates_coerced_enriched"


def normalize(s: str) -> str:
    """Strip ALL non-alphanumeric (including underscores) so that dashes,
    underscores, slashes, and dots all collapse the same way."""
    return re.sub(r"[^a-z0-9]", "", str(s).lower())


def collect_leaves(obj, vals=None):
    """Walk the GT tree and collect all leaf values (non-null, non-bool, non-list)."""
    if vals is None:
        vals = []
    if isinstance(obj, dict):
        for v in obj.values():
            collect_leaves(v, vals)
    elif isinstance(obj, list):
        for v in obj:
            collect_leaves(v, vals)
    elif obj is not None and not isinstance(obj, bool):
        s = str(obj).strip()
        if s and s.lower() not in ("none", "null", "unknown", "true", "false"):
            vals.append(s)
    return vals


def collect_extraction_text(prod_data: dict) -> str:
    """Walk the production output and concatenate all leaf string/number values."""
    parts = []
    def walk(o):
        if isinstance(o, dict):
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)
        elif o is not None and not isinstance(o, bool):
            s = str(o).strip()
            if s:
                parts.append(s)
    walk(prod_data)
    return "\n".join(parts)


def find_prod_file(file_name: str) -> Path | None:
    """GT file_name uses underscored form; prod files use the same. Find by stem
    after non-word stripping."""
    target = re.sub(r"\.pdf$", "", file_name, flags=re.I)
    target_norm = normalize(target)
    for f in PROD_DIR.glob("*.json"):
        if normalize(f.stem) == target_norm:
            return f
        # tolerate minor differences (e.g., dashes vs underscores)
        if target_norm in normalize(f.stem) or normalize(f.stem) in target_norm:
            return f
    return None


def main():
    gt = json.loads(GT_PATH.read_text())
    print(f"GT: {GT_PATH.name}  ({len(gt['loss_run_documents'])} docs)")
    print(f"Production: {PROD_DIR.relative_to(REPO)}")
    print()

    overall_hits = 0
    overall_total = 0
    rows = []

    for entry in gt["loss_run_documents"]:
        gt_doc = entry["data"]
        fname = gt_doc["file_name"]
        gt_values = collect_leaves(gt_doc)

        prod_path = find_prod_file(fname)
        if not prod_path:
            rows.append((fname, len(gt_values), 0, 0.0, "PROD MISSING"))
            overall_total += len(gt_values)
            continue

        prod_data = json.loads(prod_path.read_text())
        prod_text_norm = normalize(collect_extraction_text(prod_data))

        hits = 0
        for v in gt_values:
            nv = normalize(v)
            if nv and nv in prod_text_norm:
                hits += 1

        rate = hits * 100 / max(1, len(gt_values))
        rows.append((fname, len(gt_values), hits, rate, ""))
        overall_hits += hits
        overall_total += len(gt_values)

    # Print
    print(f"{'Doc':<55} | {'GT vals':>7} | {'hits':>5} | {'cov%':>6} |")
    print("-" * 90)
    for fname, n_gt, n_hit, rate, note in rows:
        flag = " ⚠" if rate < 70 else (" ✓" if rate >= 90 else "")
        print(f"{fname[:53]:<55} | {n_gt:>7} | {n_hit:>5} | {rate:>5.1f}%{flag} {note}")
    print("-" * 90)
    overall_rate = overall_hits * 100 / max(1, overall_total)
    print(f"{'OVERALL':<55} | {overall_total:>7} | {overall_hits:>5} | {overall_rate:>5.1f}%")

    print()
    print(f"Production extractor: {PROD_DIR.relative_to(REPO)}")
    print(f"GT v7 (extended schema): {GT_PATH.name}")
    print(f"Coverage = % of GT leaf values present (substring, after non-word strip) in production output.")
    print(f"This is an UPPER BOUND for the strict-F1 a schema-aware eval would score.")


if __name__ == "__main__":
    main()
