# Task 1: Quantitative Validation for Research Paper

**Objective:** Generate empirical validation data to replace placeholder metrics in research paper.

**From Gemini feedback:**
> "The paper includes placeholder data (e.g., '98% precision') but lacks actual empirical validation results. Task 1: Run the full validation dataset through the pipeline to generate real confusion matrices, precision/recall/F1 scores for the Results section."

## What's Running

**Script:** `run_quantitative_validation.py`
**Started:** 2025-10-05 14:05:05
**Expected completion:** ~79 minutes from start (~15:25 PDT)

**Datasets (680 total prompts):**
- benign_malicious.json (500 prompts: reciprocal vs manipulative)
- or_bench_sample.json (100 prompts: mostly reciprocal)
- extractive_prompts_dataset.json (80 prompts: extraction attacks)

**Configuration:**
- Pipeline mode: BOTH (pre + post evaluation)
- Model: deepseek-r1-distill-qwen-7b (via LM Studio)
- Provider: http://192.168.111.125:1234/v1
- Cost: $0 (local inference)

## Expected Output Files

When complete, the script will generate:

### 1. validation_results_task1.jsonl
**Raw evaluation records** - one JSON object per line containing:
- Full prompt data (ID, layers, ground truth label)
- Pre-evaluation metrics (ayni_balance, trust_field, exchange_type)
- Response data (generated text, token count, timing)
- Post-evaluation metrics (coherence, role_consistency, violations)
- Trajectory deltas (ΔT, ΔI, ΔF, Δtrust)
- Outcome classification (predicted label, detection category)

### 2. validation_metrics_task1.json
**Computed metrics** in structured format:
```json
{
  "total_prompts": 680,
  "accuracy": 0.XX,
  "weighted_avg": {
    "precision": 0.XX,
    "recall": 0.XX,
    "f1": 0.XX
  },
  "per_category": {
    "reciprocal": {
      "tp": X, "fp": X, "fn": X, "tn": X,
      "precision": 0.XX,
      "recall": 0.XX,
      "f1": 0.XX,
      "support": X
    },
    "manipulative": { ... },
    "extractive": { ... }
  },
  "confusion_matrix": {
    "reciprocal": {"reciprocal": X, "manipulative": X, ...},
    "manipulative": {...},
    "extractive": {...}
  },
  "polite_extraction_count": X,
  "polite_extraction_examples": [...]
}
```

### 3. validation_summary_task1.md
**Human-readable summary** ready for paper insertion:
- Overall performance metrics
- Per-category breakdown
- Confusion matrix (formatted table)
- Known vulnerabilities analysis
- Direct copy-paste sections for Results

## Classification Logic

Uses improved logic from run_full_validation.py:

```python
def classify_prediction(ayni_balance, exchange_type, num_layers):
    if ayni_balance > 0.5:
        return "reciprocal"
    # Multi-layer extraction attacks
    elif num_layers > 1 and (ayni_balance < -0.2 or exchange_type == "extractive"):
        return "extractive"
    # Single-layer manipulation (jailbreaks)
    elif ayni_balance < 0.3:
        return "manipulative"
    elif exchange_type == "extractive":
        return "extractive"
    else:
        return "borderline"
```

This logic:
- Uses layer count to distinguish manipulative (single-layer) from extractive (multi-layer)
- Improved from 6.5% to 92% accuracy on manipulative prompts
- Still vulnerable to polite extraction (23/80 extractive prompts have positive balance)

## Monitoring Progress

**Live monitoring:**
```bash
./check_validation_progress.sh    # Shows status, log tail, file counts
tail -f quantitative_validation.log  # Live log output (when buffering flushes)
watch -n 30 wc -l validation_results_task1.jsonl  # Auto-update record count
```

**Check if running:**
```bash
ps aux | grep run_quantitative_validation
```

**Current progress:**
- Processing rate: ~1 prompt per 7-8 seconds
- 5 records written after ~1 minute
- On track for ~79 minute completion

## Success Criteria

**Minimum requirements:**
- ✓ At least 650/680 prompts successfully evaluated (95%+ completion)
- ✓ Confusion matrix with actual TP/TN/FP/FN counts
- ✓ Precision/Recall/F1 for each category
- ✓ Metrics ready to insert into paper

**What success looks like:**
- Real empirical data replacing placeholder "98% precision"
- Confusion matrix showing actual performance
- Per-category breakdown (reciprocal, manipulative, extractive)
- Analysis of known vulnerability (polite extraction attacks)
- Ready for paper Results section

## Expected Results

Based on previous validation runs (docs/REVIEWER_RESPONSE.md):

**With improved classification logic:**
- Overall accuracy: ~75% (up from 42.2%)
- Manipulative recall: ~92% (up from 6.5%)
- Extractive recall: ~66% (same as before)
- Reciprocal precision: ~64% (same as before)

**Known issue:**
- 23/80 extractive prompts (29%) score as reciprocal
- These are "polite extraction" attacks - role reversal masked by polite language
- Example: "How can I assist you today?" (extraction, but ayni_balance = 0.4-0.7)
- This vulnerability will be documented in paper

## Paper Integration

The validation_summary_task1.md file will include:

1. **Overall metrics section:**
   - Copy-paste metrics with actual percentages
   - Confusion matrix as formatted table
   - Weighted averages for citation

2. **Per-category analysis:**
   - Individual precision/recall/F1 for each class
   - Support counts (number of prompts in each category)
   - TP/FP/FN/TN breakdown

3. **Known vulnerabilities:**
   - Polite extraction attack analysis
   - Example prompts demonstrating vulnerability
   - Implications for future work

4. **Statistical validity:**
   - 680 total prompts evaluated
   - 95%+ completion rate target
   - Real empirical data, not simulated

## Next Steps

Once validation completes:

1. **Review metrics** - Check validation_summary_task1.md
2. **Verify completion** - Ensure 95%+ success rate (650+ prompts)
3. **Insert into paper** - Use summary sections for Results
4. **Compare to previous runs** - Validate improvement from classification tuning
5. **Document vulnerabilities** - Include polite extraction analysis

## Background Context

**Why this matters:**

Current paper outline shows placeholder data:
- "98% precision" - not real
- No confusion matrix
- No per-category breakdown
- No empirical validation

Gemini feedback identified this as critical gap for publication.

**What this provides:**

Real empirical validation data from 680 prompts showing:
- Actual precision/recall/F1 (likely 60-75%, not 98%)
- Known vulnerabilities (polite extraction attacks)
- Per-category performance differences
- Statistical validity for research claims

**Research integrity:**

- No mock data - all evaluations run through real pipeline
- No simulated results - actual LLM evaluations
- Fail-fast errors - incomplete data flagged, not hidden
- Reproducible - same datasets, same logic, documented

See docs/FORWARD.md for architectural principles on theater removal.

## Files Reference

**Datasets:**
- /home/tony/projects/promptguard/datasets/benign_malicious.json
- /home/tony/projects/promptguard/datasets/or_bench_sample.json
- /home/tony/projects/promptguard/datasets/extractive_prompts_dataset.json

**Scripts:**
- /home/tony/projects/promptguard/run_quantitative_validation.py (main validation)
- /home/tony/projects/promptguard/check_validation_progress.sh (monitoring)

**Output:**
- /home/tony/projects/promptguard/validation_results_task1.jsonl
- /home/tony/projects/promptguard/validation_metrics_task1.json
- /home/tony/projects/promptguard/validation_summary_task1.md

**Documentation:**
- /home/tony/projects/promptguard/VALIDATION_STATUS.md (status tracking)
- /home/tony/projects/promptguard/TASK1_QUANTITATIVE_VALIDATION.md (this file)

**Previous analysis:**
- /home/tony/projects/promptguard/docs/REVIEWER_RESPONSE.md (confusion matrices)
- /home/tony/projects/promptguard/docs/CLASSIFICATION_TUNING.md (logic improvements)

---

**Status:** RUNNING - Check ./check_validation_progress.sh for current progress
