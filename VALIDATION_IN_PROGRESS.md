# Extractive Dataset Validation - IN PROGRESS

**Started:** 2025-10-17T23:33 UTC
**Status:** Running in background (process ID: efee8a)
**Expected completion:** ~10-15 minutes

## What's Being Tested

Comparing two versions of the evaluation prompt against 80 extractive attack prompts:

1. **OLD PROMPT** (Instance 18): Simple observer framing
   - Lines 23-44 in `validate_extractive_regression.py`
   - Short, focused on reciprocity balance
   - Instance 13 baseline: 100% detection (80/80)

2. **NEW PROMPT** (Instance 36): Enhanced with intent classification, keyword context, negative framing
   - Current implementation in `promptguard/evaluation/prompts.py` lines 32-116
   - Added to fix 37% false positive rate on benign requests
   - Unvalidated against extractive attacks

## Success Criteria

- **Minimum acceptable:** 76/80 detected (95%)
- **Baseline:** 80/80 (100%) from Instance 13
- **Threshold:** F >= 0.7 for "detected"

## Why This Matters

Instance 36 revised the evaluation prompt to reduce false positives (legitimate requests incorrectly flagged as manipulative). However, we MUST ensure this didn't introduce regressions in detecting **genuine attacks**.

Extractive attacks are multi-layer prompt injection attempts (system prompt extraction, role confusion). These should always score high F (≥0.7).

## Monitoring Progress

```bash
# Check progress
tail -f extractive_validation_execution.log

# Check if still running
ps aux | grep validate_extractive
```

## What Happens Next

When complete, the script generates:

1. **EXTRACTIVE_DATASET_VALIDATION.md** - Full report with regression analysis
2. **extractive_validation_results.json** - Detection rates and regression details
3. **extractive_f_scores.json** - F-scores for both prompts

## Expected Outcome

**If new prompt ≥ 95% detection:**
- Safe to adopt for production
- Proceed to false positive validation on benign_malicious dataset

**If new prompt < 95% detection:**
- Analyze regression patterns (which attacks were missed)
- Refine prompt to address gaps
- Re-validate before adoption

## Cost

- 80 attacks × 2 prompts × 2 layers (avg) × $0.0025/eval ≈ $0.80
- Actual cost may be lower due to caching

## Process Running

Monitor with:
```bash
# See latest output
tail -20 extractive_validation_execution.log

# Full log
less extractive_validation_execution.log
```
