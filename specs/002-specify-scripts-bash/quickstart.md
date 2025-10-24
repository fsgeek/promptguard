# Quickstart: End-to-End PromptGuard Validation Framework

**Date**: 2025-10-22
**Feature**: 4-Experiment Validation Framework

This guide walks through running the complete validation framework from setup to analysis.

---

## Prerequisites

- Python 3.13+ installed
- `uv` package manager installed
- ArangoDB 3.x running and accessible
- OpenRouter API key

---

## Installation

### 1. Clone and Setup

```bash
cd /home/tony/projects/promptguard
git checkout 002-specify-scripts-bash
uv sync  # Install dependencies from pyproject.toml
```

### 2. Configure ArangoDB

Set environment variables:

```bash
export ARANGODB_PROMPTGUARD_PASSWORD="your_password_here"
export ARANGODB_HOST="192.168.111.125"  # Optional, defaults to this
export ARANGODB_PORT="8529"              # Optional
export ARANGODB_DB="PromptGuard"        # Optional
export ARANGODB_USER="pgtest"           # Optional
```

### 3. Configure OpenRouter

```bash
export OPENROUTER_API_KEY="your_key_here"
```

### 4. Initialize Database Collections

```bash
uv run python scripts/validation/init_database.py
```

This creates 10 collections with proper indexes:
- `prompt_configurations` (with unique hash index on prompt_type + version)
- `prompts`, `processing_failures`, `baseline_responses`
- `pre_eval_results`, `post_eval_results`
- `confusion_matrices`, `reasoningbank_patterns`
- `validation_rounds`, `experiments`

---

## Running Experiments

### Experiment 1: Baseline Collection

**Purpose**: Measure what Claude actually does with 680 prompts (comply vs refuse)

```bash
uv run python scripts/validation/experiment_01_baseline.py \
    --target-model "anthropic/claude-3.5-sonnet" \
    --observer-model "anthropic/claude-3.5-sonnet" \
    --experiment-id "exp_001_baseline"
```

**Output**:
- 680 records in `prompts` collection
- 680 records in `baseline_responses` collection (with comply/refuse classification)
- 1 record in `experiments` collection (metadata with total cost)
- Processing failures logged to `processing_failures` (if any)

**Runtime**: ~20-30 minutes (680 prompts × 5-10s per evaluation)
**Cost**: ~$2-5 (depending on response lengths)

### Experiment 2: Pre-Evaluation Cross-Tabulation

**Purpose**: Measure PromptGuard detection before seeing LLM responses

```bash
uv run python scripts/validation/experiment_02_preeval.py \
    --observer-model "anthropic/claude-3.5-sonnet" \
    --experiment-id "exp_002_preeval" \
    --baseline-experiment-id "exp_001_baseline"
```

**Output**:
- 680 records in `pre_eval_results` collection (with F-scores and block/allow decisions)
- 3 records in `confusion_matrices` collection (PromptGuard×LLM, PromptGuard×Labels, LLM×Labels)
- Processing failures logged (if any)

**Runtime**: ~15-25 minutes (cache may help if prompts evaluated before)
**Cost**: ~$3-5

### Experiment 3: Pattern Mining from False Negatives

**Purpose**: Extract attack patterns from prompts PromptGuard missed

```bash
uv run python scripts/validation/experiment_03_patterns.py \
    --observer-model "anthropic/claude-3.5-sonnet" \
    --experiment-id "exp_003_patterns" \
    --preeval-experiment-id "exp_002_preeval"
```

**Output**:
- N records in `reasoningbank_patterns` collection (where N = number of patterns extracted)
- 680 records in `post_eval_results` collection (with divergence measurements)
- Processing failures logged (if any)

**Runtime**: ~20-30 minutes (fewer API calls if few false negatives)
**Cost**: ~$5-10 (post-evaluation + Fire Circle for pattern extraction)

**Stopping condition**: Continue until CI width ≤ 5% (Wilson score interval)

### Experiment 4: REASONINGBANK Validation

**Purpose**: Three-condition test to measure REASONINGBANK effect vs template marker effect

```bash
uv run python scripts/validation/experiment_04_validation.py \
    --observer-model "anthropic/claude-3.5-sonnet" \
    --experiment-id "exp_004_validation" \
    --sample-size 50 \
    --source-experiment-id "exp_001_baseline"
```

**Output**:
- 1 record in `validation_rounds` collection (with 3 FN rates, 3 deltas, interaction term)
- 150 records in `pre_eval_results` (50 prompts × 3 conditions)
- Processing failures logged (if any)

**Runtime**: ~12.5-50 minutes (50-100 prompts × 3 conditions × 5-10s)
**Cost**: ~$3-8

---

## Resuming Interrupted Experiments

All experiments support automatic resume via ArangoDB checkpointing:

```bash
# Same command as initial run - automatically detects completed prompts
uv run python scripts/validation/experiment_01_baseline.py \
    --target-model "anthropic/claude-3.5-sonnet" \
    --observer-model "anthropic/claude-3.5-sonnet" \
    --experiment-id "exp_001_baseline"  # Same ID = resume
```

Resume logic:
1. Query `prompts` collection for `experiment_id == "exp_001_baseline"`
2. Get set of completed `prompt_id` values
3. Load all 680 prompts from datasets
4. Exclude already-completed prompts
5. Process remaining prompts only

---

## Querying Results

### Get Experiment Summary

```aql
FOR e IN experiments
  FILTER e.experiment_id == "exp_001_baseline"
  RETURN {
    experiment: e.experiment_label,
    prompts: e.total_prompts,
    cost: e.total_cost,
    duration: DATE_DIFF(e.start_timestamp, e.end_timestamp, "minutes"),
    stages: e.stages_completed
  }
```

### Get Confusion Matrix

```aql
FOR cm IN confusion_matrices
  FILTER cm.experiment_id == "exp_002_preeval"
  FILTER cm.matrix_type == "promptguard_vs_llm"
  RETURN {
    type: cm.matrix_type,
    TP: cm.true_positives,
    FP: cm.false_positives,
    TN: cm.true_negatives,
    FN: cm.false_negatives,
    precision: cm.precision,
    recall: cm.recall,
    f_score: cm.f_score
  }
```

### Get False Negatives

```aql
FOR pre IN pre_eval_results
  FILTER pre.experiment_id == "exp_002_preeval"
  FILTER pre.decision == "allow"  # PromptGuard allowed
  LET baseline = FIRST(
    FOR b IN baseline_responses
      FILTER b.prompt_id == pre.prompt_id
      FILTER b.classification == "comply"  # LLM complied
      RETURN b
  )
  FILTER baseline != null  # Both conditions met = false negative
  LET prompt = DOCUMENT("prompts", pre.prompt_id)
  RETURN {
    prompt_text: prompt.prompt_text,
    pre_f_score: pre.f_score,
    compliance_score: baseline.compliance_score,
    divergence: baseline.compliance_score - pre.f_score
  }
```

### Get REASONINGBANK Patterns

```aql
FOR p IN reasoningbank_patterns
  FILTER p.experiment_id == "exp_003_patterns"
  RETURN {
    pattern_name: p.pattern_name,
    description: p.pattern_description,
    example_count: LENGTH(p.example_prompts),
    source_fn_count: LENGTH(p.source_false_negatives)
  }
```

### Get Validation Round Results

```aql
FOR vr IN validation_rounds
  FILTER vr.experiment_id == "exp_004_validation"
  RETURN {
    sample_size: vr.sample_size,
    condition_1_fn_rate: vr.condition_1_fn_rate,
    condition_2_fn_rate: vr.condition_2_fn_rate,
    condition_3_fn_rate: vr.condition_3_fn_rate,
    template_marker_effect: vr.delta_1_template_marker_effect,
    reasoningbank_effect: vr.delta_2_reasoningbank_effect,
    total_effect: vr.delta_3_total_effect,
    interaction_significant: vr.interaction_significant,
    interaction_term: vr.interaction_term
  }
```

### Get Processing Failures

```aql
FOR f IN processing_failures
  FILTER f.experiment_id == "exp_001_baseline"
  COLLECT error_type = f.error_type WITH COUNT INTO count
  RETURN {
    error_type: error_type,
    count: count
  }
```

---

## Export Results

### Export to JSONL (for archival)

```bash
uv run python scripts/validation/export_results.py \
    --experiment-id "exp_001_baseline" \
    --output-dir "exports/exp_001"
```

Creates:
- `prompts.jsonl`
- `baseline_responses.jsonl`
- `experiments.jsonl`
- `processing_failures.jsonl` (if any)

### Export Confusion Matrices to CSV

```bash
uv run python scripts/validation/export_confusion_matrix.py \
    --experiment-id "exp_002_preeval" \
    --output "exports/confusion_matrix_exp_002.csv"
```

---

## Model Version Handling

If model version changes mid-experiment, you'll see:

```
ModelVersionChangedError: Model changed: anthropic/claude-3.5-sonnet:20241015 → anthropic/claude-3.5-sonnet:20241022
Decision required: ABORT/CONTINUE/IGNORE
```

Options:
1. **ABORT**: Stop experiment, mark as incomplete, start fresh with new version
2. **CONTINUE**: Proceed with new version, log change in `experiments.model_version_change_decision`
3. **IGNORE**: Suppress future warnings for this experiment (not recommended)

---

## Cost Tracking

All experiments log costs to `experiments.total_cost`:

```aql
FOR e IN experiments
  SORT e.start_timestamp ASC
  RETURN {
    experiment: e.experiment_label,
    cost: e.total_cost,
    cost_per_prompt: e.total_cost / e.total_prompts
  }
```

**Budget guideline** (not design constraint):
- Experiment 1: ~$2-5
- Experiment 2: ~$3-5
- Experiment 3: ~$5-10
- Experiment 4: ~$3-8
- **Total**: ~$13-28 for complete validation

---

## Troubleshooting

### ArangoDB Connection Fails

```
ConfigurationError: Cannot connect to ArangoDB at 192.168.111.125:8529
```

Fix:
- Verify ArangoDB is running: `curl http://192.168.111.125:8529/_api/version`
- Check password: `echo $ARANGODB_PROMPTGUARD_PASSWORD`
- Check network: `ping 192.168.111.125`

### Fixture File Corrupted

```
ConfigurationError: Fixture corrupted: expected c104718..., got a3f2b19...
```

Fix:
```bash
git checkout 8a7fcd3 -- promptguard/evaluation/prompts.py
# Extract old_baseline_prompt.txt from commit
git checkout HEAD -- promptguard/evaluation/prompts.py  # Restore current version
```

### OpenRouter Rate Limit

```
EvaluationError: Rate limit exceeded (429 Too Many Requests)
```

Fix: Experiments automatically log to `processing_failures` and continue. Resume after rate limit resets.

### Dataset Missing

```
ConfigurationError: Expected 680 prompts, found 0
FileNotFoundError: datasets/benign_malicious.json
```

Fix: Ensure all 3 datasets exist:
```bash
ls -lh datasets/benign_malicious.json        # 500 prompts
ls -lh datasets/or_bench_sample.json         # 100 prompts
ls -lh datasets/extractive_prompts_dataset.json  # 80 prompts
```

---

## Next Steps

After completing all 4 experiments:

1. **Analyze results**: Use AQL queries above to understand PromptGuard effectiveness
2. **Expand REASONINGBANK**: If CI width > 5%, run additional strides (Experiment 3)
3. **Expand validation**: If Experiment 4 shows promise (p<0.10), expand to full n=680
4. **Write paper**: Export results to JSONL, import to analysis framework

---

## Constitution Compliance

- **No Theater**: Real API calls required, costs tracked, failures logged
- **Empirical Integrity**: Model versions tracked, timestamps recorded, evidence preserved
- **Fail-Fast**: ConfigurationError raised immediately if setup invalid
- **Immutable Storage**: All operations are INSERT-only (no UPDATE/DELETE)
- **First-Class Failures**: Processing failures stored in dedicated collection

For questions, see:
- Feature specification: `specs/002-specify-scripts-bash/spec.md`
- Data model: `specs/002-specify-scripts-bash/data-model.md`
- Research decisions: `specs/002-specify-scripts-bash/research.md`
