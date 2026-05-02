# Verifier+fix loop — HONEST NEGATIVE FINDING

**Date:** 2026-05-02

## TL;DR

Tested two verifier+fix variants on the per-archetype router output (78.2% F1 baseline). Both failed:
- **Lenient checks** (paid+reserve=incurred, required fields): found 0 issues across 8 of 9 docs. **No F1 change.**
- **Strict checks** (added policy_total_reconciliation, date ordering, class code, linkage): found 3 genuine failures on ICW. Model "fixed" by deleting claims. **ICW dropped 80.7% → 23.9% F1 (-57pp catastrophe).**

## Why the strict approach failed

The strict checks correctly identified ICW's `policy_total_reconciliation` failures (sum of claim totals ≠ printed policy total). But when re-prompted with "fix these failures and re-emit the full JSON," the model took the easiest path: **delete the claims** that didn't fit the totals.

Result: ICW lost ~70% of its claim data. The reconciliation constraint was now satisfied (3 → 0 failures), but the actual extraction was destroyed.

## Lessons learned

1. **"Fix by re-emit"** is dangerous — model can satisfy constraints by data deletion
2. **Reconciliation checks must distinguish** between "fix this value" vs "delete this data"
3. **Lenient checks** are useless (most outputs already pass simple bucket arithmetic)
4. **Strict checks** find real issues but fix-by-re-emit can't safely apply them

## What would actually work

| Approach | Why it'd help | Cost |
|---|---|---|
| **Targeted field patching** (extract specific values, patch deterministically) | Surgical edits, no destruction | Medium |
| **Constraint-only edits** (prompt: "only adjust totals, never delete claims") | Lower risk of data loss | Low |
| **Multi-pass with quotas** (cap output length growth at 5%, force preservation) | Mechanical guarantee | Low |
| **Constrained decoding** (force output to match schema with required fields populated) | Schema-level guarantee | Medium |

## Final F1 across all session experiments

| Pipeline | F1 |
|---|---|
| v4 baseline | 78.9% |
| **LightOn + Qwen3-VL v4** | **80.1% (production winner)** |
| LightOn + Qwen v5_proper | 72.1% |
| **Per-archetype router** | 78.2% |
| Router + verifier-fix (lenient) | 78.2% (no change) |
| Router + verifier-fix (strict) | 46.5% **(catastrophic regression — model deleted claims)** |
| Router + verifier-fix (strict) + safe merge | 78.2% (recovered) |

## Production recommendation (unchanged)

**LightOn + Qwen3-VL (v4 prompt) at 80.1% F1** remains the production winner.

For corpora with Hartford pivots, use **per-archetype router** at 78.2% (gains +28-50pp on those docs).

**DO NOT use "fix by re-emit" verifier loops.** They risk catastrophic data loss.

## Path to 90%+ F1 (revised)

1. ❌ ~~Verifier+fix loop with strict checks~~ — proven dangerous
2. ✅ **Constrained JSON decoding** (vLLM `guided_json` against schema v5) — eliminates parse failures, enforces required fields
3. ✅ **LoRA fine-tune Qwen3-VL-4B** on 21 GT + 10K synthetic — most promising
4. ✅ **Synthetic data for 100+ carriers** — true generalisation
5. ⚠ Verifier+fix with **targeted patching** (extract specific values, patch deterministically) — needs reimplementation
