# Diversity Calibration Completion Checklist

**For Instance 29 or subsequent instance when calibration completes**

## Pre-Completion (Running Now)

- [x] Script launched: `run_diversity_calibration.py`
- [x] Real API calls verified (first 30 prompts show actual T/I/F scores)
- [x] Progress monitoring enabled
- [x] Status documented in `DIVERSITY_CALIBRATION_STATUS.md`

## Upon Completion

### 1. Verify Outputs Generated

Check these files exist:

```bash
ls -lh diversity_calibration_raw.json
ls -lh diversity_calibration_matrix.json
ls -lh diversity_calibration_report.md
ls -lh diversity_calibration_execution.log
```

### 2. Extract Key Findings

From `diversity_calibration_matrix.json`:

```bash
python3 <<EOF
import json
with open('diversity_calibration_matrix.json') as f:
    matrix = json.load(f)

metrics = matrix['diversity_metrics']
print("=== KEY METRICS ===")
print(f"Total attacks: {metrics['total_attacks_in_dataset']}")
print(f"Detected by any: {metrics['detected_by_any_model']}")
print(f"Detected by all: {metrics['detected_by_all_models']}")
print(f"Missed by all: {metrics['missed_by_all_models']}")
print(f"Overlap percentage: {metrics['overlap_percentage']}%")
print()

print("=== UNIQUE CONTRIBUTIONS ===")
for model, contrib in metrics['unique_contribution'].items():
    print(f"{model}: {contrib:.2f} unique detections per dollar")
print()

print("=== PER-MODEL STATS ===")
for model, stats in matrix['per_model_stats'].items():
    print(f"{model}:")
    print(f"  Total detected: {stats['total_detected']}")
    print(f"  Unique: {stats['unique_detections']}")
    print(f"  Cost: ${stats['total_cost']:.2f}")
    print()
EOF
```

### 3. Validate OpenRouter Billing

**CRITICAL:** Verify real costs incurred

1. Log into OpenRouter dashboard: https://openrouter.ai/activity
2. Filter by date: 2025-10-15
3. Look for charges from these models:
   - `anthropic/claude-sonnet-4.5`
   - `moonshotai/kimi-k2-0905`
   - `deepseek/deepseek-v3.1-terminus`
   - `openai/gpt-4o`
4. Document actual costs vs estimated ($12.91)
5. Screenshot or save billing details

### 4. Answer Research Questions

From the matrix and report, determine:

**A. Overlap Percentage (Key Metric)**
- <30% = Sufficient diversity, proceed with 4-model ensemble
- 30-50% = Moderate diversity, consider testing more models
- >50% = High redundancy, replace 1-2 models

**B. Cost-Benefit Winner**
- Which model provides best unique_detections / total_cost ratio?
- Is it worth keeping expensive models (Claude $7.17)?

**C. Detection Gaps**
- Which attacks did ALL models miss?
- Are there attack types that only 1 model catches?
- Is there a "must-have" model for comprehensive coverage?

**D. False Positive Patterns**
- Which models over-detect on reciprocal prompts?
- What's the precision/recall trade-off?

### 5. Top 3 Findings

Document in clear language:

1. **Finding 1:** [Overlap percentage and diversity assessment]
2. **Finding 2:** [Cost-benefit winner and recommendation]
3. **Finding 3:** [Critical gaps or unique capabilities]

### 6. Final Recommendation

Based on findings, answer:

**Do we have sufficient structural diversity with these 4 models?**

Options:
- **YES, sufficient:** Overlap <30%, complementary detection patterns
- **NEEDS IMPROVEMENT:** Overlap 30-50%, consider adding models with different architectures
- **INSUFFICIENT:** Overlap >50%, must replace redundant models

### 7. Document for Handoff

Create summary with:
- Total cost incurred (from OpenRouter)
- Overlap percentage
- Top 3 findings
- Recommendation (proceed with 4-model ensemble or adjust)
- Evidence of real API calls (log excerpts, billing screenshot)

## Quick Status Check

```bash
# Check if complete
./check_calibration_status.sh

# View report
cat diversity_calibration_report.md

# View raw data sample
head -100 diversity_calibration_raw.json
```

## Deliverables for Tony

1. `diversity_calibration_report.md` - Full report
2. Evidence of real API calls:
   - `diversity_calibration_execution.log` (with timestamps)
   - OpenRouter billing screenshot/export
3. Summary of top 3 findings
4. Clear recommendation: Sufficient diversity or need more models?
5. Cost breakdown: estimated vs actual

## If Calibration Failed

Check:
```bash
# Process status
ps aux | grep run_diversity_calibration.py

# Last errors
tail -50 diversity_calibration_execution.log

# Partial results
cat diversity_calibration_raw.json | python3 -m json.tool | head -50
```

Document failure mode and restart if needed.

---

**Note for Instance 30+:** If you're reading this and calibration is complete, follow the checklist above. All evidence is in the files listed. The key metrics are in `diversity_calibration_matrix.json` under `diversity_metrics.overlap_percentage`.
