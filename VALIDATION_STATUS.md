# Quantitative Validation Status - Task 1

**Started:** 2025-10-05 14:05:05
**Status:** RUNNING
**Expected completion:** ~79 minutes (~15:25 PDT)

## Overview

Running full quantitative validation for research paper (Gemini feedback Task 1).

**Datasets being evaluated:**
- benign_malicious.json (500 prompts)
- or_bench_sample.json (100 prompts)
- extractive_prompts_dataset.json (80 prompts)
- **Total:** 680 prompts

**Pipeline configuration:**
- Mode: BOTH (pre + post evaluation)
- Model: deepseek-r1-distill-qwen-7b
- Provider: LM Studio (http://192.168.111.125:1234/v1)
- Using same model for both pre and post evaluation

**Performance:**
- Processing rate: ~1 prompt per 7-8 seconds
- Estimated total time: ~79 minutes

## Output Files

Will generate three output files when complete:

1. **validation_results_task1.jsonl** - Raw evaluation records
   - One JSON record per line
   - Contains full pre/post evaluation data
   - Currently building incrementally

2. **validation_metrics_task1.json** - Computed metrics
   - Overall confusion matrix
   - Per-category precision/recall/F1
   - Special analysis of polite extraction attacks
   - Created after all evaluations complete

3. **validation_summary_task1.md** - Human-readable summary
   - Ready to insert into paper Results section
   - Includes all key metrics with percentages
   - Created after all evaluations complete

## Monitoring Progress

**Check current status:**
```bash
./check_validation_progress.sh
```

**View live log output:**
```bash
tail -f quantitative_validation.log
```

**Count completed prompts:**
```bash
wc -l validation_results_task1.jsonl
```

**Check if still running:**
```bash
ps aux | grep run_quantitative_validation | grep -v grep
```

## What the Script Does

For each of 680 prompts:

1. **Pre-evaluation (PromptGuard):**
   - Evaluates prompt layers with neutrosophic logic
   - Calculates ayni_balance, trust_field, exchange_type
   - Makes pass/block decision

2. **Response generation (if pre-eval passes):**
   - Generates response using configured model
   - Tracks token count, generation time
   - Records finish reason

3. **Post-evaluation:**
   - Evaluates response coherence, role consistency
   - Checks for trust field violations
   - Computes trajectory deltas (ΔT, ΔI, ΔF, Δtrust)

4. **Classification:**
   - Applies improved logic (layer count + ayni_balance)
   - Classifies as: reciprocal, manipulative, extractive, or borderline
   - Compares to ground truth label

5. **Recording:**
   - Writes complete record to JSONL immediately
   - No buffering - survives crashes

## After Completion

The script will automatically:

1. Compute confusion matrices (overall and per-category)
2. Calculate precision/recall/F1 for each category
3. Identify polite extraction attacks (extractive with positive balance)
4. Generate summary document with key metrics
5. Save all results to disk

**Expected metrics:**
- Overall accuracy
- Weighted precision/recall/F1
- Per-category performance (reciprocal, manipulative, extractive)
- Confusion matrix showing TP/TN/FP/FN
- Count of polite extraction vulnerability

## Error Handling

The script uses try/except around each prompt:
- Errors are logged but don't stop execution
- Failed prompts marked with `success: false`
- Partial results are valid (need 95%+ success rate)
- All errors saved to `validation_errors_task1.json`

## Success Criteria

**Minimum requirements:**
- At least 650/680 prompts successfully evaluated (95%+)
- Confusion matrix with actual TP/TN/FP/FN counts
- Metrics ready to insert into paper outline

**What success looks like:**
- All three output files created
- Metrics show real performance (not placeholder 98%)
- Can compare to previous validation runs
- Ready for paper Results section

## Current Progress

Check with: `./check_validation_progress.sh`

As of last check:
- ✓ Script is running
- ✓ 3 records written to JSONL
- Processing at expected rate (~1 per 7-8 seconds)
- No errors reported yet

---

**Note:** This validation uses local LM Studio inference, so cost is $0. The 1-2 hour runtime is acceptable for generating publication-quality metrics.
