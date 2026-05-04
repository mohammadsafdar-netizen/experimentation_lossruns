"""GT v5 corrections (uncovered through visual diagnosis 2026-05-03):

1. Strategic Info Hartford: claim Y3WC99221 belongs to policy 2023-2024 (PDF says
   "Policy Term: 03/07/2023 - 03/07/2024" in the claim block header). GT v4 had it
   in policy 2024-2025.

2. Other docs unchanged from v4.
"""
import json
from copy import deepcopy
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).parent
SRC = ROOT / "loss_runs_gt_v4_schema_extended.json"
DST = ROOT / "loss_runs_gt_v5.json"


def main():
    gt = json.loads(SRC.read_text())
    gt = deepcopy(gt)
    gt["_meta"]["version"] = "v5"
    gt["_meta"]["audited_on"] = "2026-05-03"
    gt["_meta"]["supersedes"] = "loss_runs_gt_v4_schema_extended.json"

    fixes = []

    # === Strategic Info: move claim from policy[3] (2024-2025) → policy[2] (2023-2024) ===
    for d in gt["documents"]:
        if "Strategic_Information" in d["file_name"]:
            policies = d.get("policies", [])
            # Find which policy currently has the claim
            claim_to_move = None
            from_idx = None
            for i, p in enumerate(policies):
                for c in p.get("claims", []):
                    if c.get("claim_number") == "Y3WC99221":
                        claim_to_move = c
                        from_idx = i
                        break
                if claim_to_move:
                    break
            if claim_to_move and from_idx is not None:
                # Find target policy (2023-2024 term)
                to_idx = None
                for j, p in enumerate(policies):
                    if p.get("policy_period_start") == "03/07/2023":
                        to_idx = j
                        break
                if to_idx is not None and to_idx != from_idx:
                    # Move
                    policies[from_idx]["claims"] = [
                        c for c in policies[from_idx].get("claims", [])
                        if c.get("claim_number") != "Y3WC99221"
                    ]
                    if "claims" not in policies[to_idx]:
                        policies[to_idx]["claims"] = []
                    policies[to_idx]["claims"].append(claim_to_move)
                    fixes.append(
                        f"Strategic Info: moved claim Y3WC99221 from policy[{from_idx}] "
                        f"(2024-2025) to policy[{to_idx}] (2023-2024) — matches PDF header"
                    )

    gt["_meta"]["v5_fixes"] = fixes
    DST.write_text(json.dumps(gt, indent=2, default=str))
    print(f"[ok] wrote {DST}")
    print(f"[fixes] {len(fixes)}:")
    for f in fixes:
        print(f"  - {f}")


if __name__ == "__main__":
    main()
