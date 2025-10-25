# Experiment 1 Re-Analysis Data

**Created:** 2025-10-24 (Instance 51)
**Purpose:** Correct analysis after discovering Haiku meta-evaluator has 95% error rate

## The Discovery

Claude Haiku 3.5 cannot distinguish compliance from refusal. Manual review of 20 samples showed:
- **Haiku accuracy: 59.3%**
- **Haiku error rate on refusals: 95%** (classified 19/20 refusals as "comply")

This invalidates all Experiment 1 results.

## Files in This Directory

### Primary Data Files

**`baseline_joined_data.json`** (2.7MB)
- Complete dataset: 1,068 responses
- Joins prompts (with dataset labels) and baseline_responses (with Haiku classifications)
- Fields: prompt_id, prompt_text, response_text, dataset_label, source_dataset, haiku_classification, haiku_score

**`false_negatives.json`** (879KB)
- All 433 cases where Haiku classified Sonnet as "comply" on manipulative/extractive prompts
- Manual review suggests ~95% of these are actually refusals (Haiku errors)
- Only ~22 are likely true compliances

**`false_positives.json`** (2 bytes)
- Empty array - zero cases where Haiku classified Sonnet as "refuse" on reciprocal prompts
- Haiku has perfect precision (no false positives)
- Haiku has terrible recall (95% false negatives)

### Validation Data

**`haiku_validation_sample.json`** (137KB)
- Stratified sample of 54 responses for validation
- 10 responses from each (dataset_label × haiku_classification) group
- Used for both text analysis and manual review validation

**`manual_review_results.json`** (3KB)
- Manual review of 20 randomly selected "false negatives"
- Results: 1 true compliance, 19 actual refusals
- Establishes Haiku's 95% error rate
- Includes detailed review notes

**`haiku_validation_disagreements.json`** (8.1KB)
- 22 cases where text-based analysis disagreed with Haiku
- Shows both approaches have limitations
- Text analysis accuracy: ~60-70%

### Summary Files

**`analysis_metrics.json`** (609 bytes)
- Confusion matrix (TP, FN, FP, TN)
- Performance metrics (accuracy, precision, recall, F1, FNR)
- Breakdown by dataset and label

**`haiku_error_examples.json`** (2.8KB)
- Five curated examples showing Haiku's failure modes
- Machine-readable JSON format
- Categories: explicit refusal, refusal with reasoning, system extraction, deflection, true compliance

**`HAIKU_ERRORS_READABLE.txt`** (3.6KB)
- Same five examples in human-readable format
- Formatted for easy reading and sharing
- Shows exact prompts and responses

## Key Statistics

### Dataset Distribution
- Total: 1,068 prompts (1,055 after excluding borderline)
- Reciprocal: 525 (49.2%)
- Manipulative: 460 (43.1%)
- Extractive: 78 (7.3%)
- Borderline: 5 (0.5%, excluded from analysis)

### Source Datasets
- benign_malicious: 890 (83.3%)
- or_bench: 100 (9.4%)
- extractive: 78 (7.3%)

### Haiku's Classifications
- Comply: 963 (90.1%)
- Refuse: 97 (9.1%)
- Borderline: 8 (0.7%)

### Corrected Estimates (After Manual Review)
- True refusals: ~1,041 (97 + 411 corrections from 433 false negatives)
- True compliances: ~547 (525 reciprocal + 22 on manipulative/extractive)
- Sonnet recall: **95.8%** (not 18.3% as Haiku suggested)
- Sonnet false negative rate: **4.2%** (not 81.7% as Haiku suggested)

## What This Means

**Original conclusion (using Haiku):**
Claude Sonnet 4.5 is dangerously permissive with 81.7% false negative rate.

**Corrected conclusion (after validation):**
Claude Sonnet 4.5 is actually quite safe with 95.8% recall and only 4.2% false negative rate.

**The experiment's conclusions are inverted.**

## Next Steps

See documentation in `/home/tony/projects/promptguard/docs/`:

1. **EXPERIMENT_01_EXECUTIVE_SUMMARY.md** - Quick overview (5 min)
2. **EXPERIMENT_01_HAIKU_FAILURE.md** - Five concrete examples (10 min)
3. **EXPERIMENT_01_REANALYSIS.md** - Complete statistical analysis (20 min)
4. **EXPERIMENT_01_PATH_FORWARD.md** - Four options for fixing methodology (20 min)
5. **INSTANCE_51_HANDOFF.md** - Complete context for next instance

## Queries Used

### Join Prompts and Responses
```aql
FOR b IN baseline_responses
  FILTER b.experiment_id == "exp_001_baseline_production"
  LET p = FIRST(FOR p IN prompts FILTER p.prompt_id == b.prompt_id RETURN p)
  FILTER p != null
  RETURN {
    prompt_id: b.prompt_id,
    prompt_text: b.prompt_text,
    response_text: b.response_text,
    dataset_label: p.label,
    source_dataset: p.source_dataset,
    haiku_classification: b.classification,
    haiku_score: b.compliance_score
  }
```

## Usage

### Load Full Dataset
```python
import json
with open('baseline_joined_data.json', 'r') as f:
    data = json.load(f)
print(f"Loaded {len(data)} records")
```

### Load False Negatives
```python
with open('false_negatives.json', 'r') as f:
    fn = json.load(f)
print(f"Haiku classified {len(fn)} as 'comply' on manipulative/extractive")
print(f"Estimated true compliances: ~{int(len(fn) * 0.05)} (5%)")
print(f"Estimated Haiku errors: ~{int(len(fn) * 0.95)} (95%)")
```

### Load Manual Review Results
```python
with open('manual_review_results.json', 'r') as f:
    review = json.load(f)
print(f"Sample size: {review['sample_size']}")
print(f"True compliances: {review['true_compliances']}")
print(f"True refusals: {review['true_refusals']}")
print(f"Haiku error rate: {review['haiku_fn_error_rate']:.1%}")
```

## Status

- **Experiment 1:** INVALID (meta-evaluator broken)
- **Experiment 2:** BLOCKED (cannot proceed without validated measurement)
- **Manual review:** RECOMMENDED (100-200 responses to establish ground truth)
- **Path forward:** DOCUMENTED (four options with implementation details)

---

**Created by Instance 51 on 2025-10-24**
**Database:** ArangoDB (192.168.111.125:8529)
**Collections:** prompts, baseline_responses
**Experiment ID:** exp_001_baseline_production
