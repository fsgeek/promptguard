# ArangoDB Integration Summary

Created evaluation harness that integrates PromptGuard with ArangoDB for data-driven experiments.

## What Was Created

### 1. Main Script: `run_baseline_arango.py`

**Purpose:** Run PromptGuard evaluations and write results directly to ArangoDB

**Key Features:**
- ✅ Query attacks from ArangoDB (flexible filtering)
- ✅ Query models from ArangoDB (flexible filtering)
- ✅ Run evaluations: direct condition + observer condition
- ✅ Write results to `evaluations` edge collection in real-time
- ✅ Duplicate detection (skip already-completed evaluations)
- ✅ Progress tracking with tqdm
- ✅ Cost accumulation tracking
- ✅ Graceful error handling
- ✅ Interrupt-safe (Ctrl+C shows cost and saves progress)

**Integration Pattern:**
- Uses existing PromptGuard library (no reimplementation)
- Follows test_baseline_comparison.py pattern
- Direct condition: Model-alone detection (refusal patterns)
- Observer condition: PromptGuard with observer framing

### 2. Usage Guide: `BASELINE_ARANGO_USAGE.md`

**Comprehensive documentation:**
- Quick start examples
- Command-line options reference
- Evaluation conditions explanation
- Database schema documentation
- AQL query examples for analysis
- Cost management tips
- Error handling and troubleshooting
- Example workflows

### 3. Connection Test: `test_arango_connection.py`

**Purpose:** Verify setup before running experiments

**Tests:**
- Database connection
- Collections exist and accessible
- Sample data queries
- Model/attack distribution statistics
- Existing evaluations check

## Database Schema

### Evaluations Edge Collection

Links models to attacks with evaluation results:

```json
{
  "_from": "models/anthropic_claude-sonnet-4.5",
  "_to": "attacks/external_001",
  "condition": "direct|observer",
  "success": true,
  "detected": false,
  "cost_usd": 0.0017275,
  "timestamp": "2025-10-11T14:23:45Z",
  "error": null,

  // Condition-specific fields
  "response_text": "...",           // For direct
  "evaluation_result": {            // For observer
    "T": 0.8, "I": 0.2, "F": 0.6,
    "reasoning": "...",
    "exchange_type": "extractive"
  },

  "experiment_metadata": {
    "experiment_id": "baseline_frontier_2025",
    "run_id": "20251011_142345",
    "condition_description": "..."
  }
}
```

## Quick Start

### 1. Test Connection

```bash
./test_arango_connection.py
```

Expected output:
```
✓ Connected to PromptGuard at 192.168.111.125:8529
✓ Collection 'models' exists (148 documents)
✓ Collection 'attacks' exists (722 documents)
✓ Collection 'evaluations' exists (0 documents)
...
All Tests Passed!
```

### 2. Quick Test Run

```bash
# Test 1 model against 5 attacks (both conditions = 10 evaluations)
./run_baseline_arango.py \
  --model-ids anthropic/claude-sonnet-4.5 \
  --attack-limit 5 \
  --experiment-id quick_test
```

Expected cost: ~$0.05-0.10

### 3. Reproduce Baseline Comparison

```bash
# Original experiment: 6 models, 72 encoding attacks, 2 conditions
./run_baseline_arango.py \
  --model-ids \
    anthropic/claude-sonnet-4.5 \
    openai/gpt-4.1 \
    google/gemini-2.5-pro \
    meta-llama/llama-3.1-405b-instruct \
    deepseek/deepseek-r1 \
    meta-llama/llama-3.1-405b \
  --dataset-source encoding_attacks_external \
  --experiment-id baseline_comparison_replication
```

Expected cost: ~$2-4 for full run

## Command-Line Examples

### Filter by Model Type

```bash
# Test all frontier aligned models
./run_baseline_arango.py --model-type frontier_aligned

# Test only observer-compatible models
./run_baseline_arango.py --observer-compatible-only

# Test specific models
./run_baseline_arango.py \
  --model-ids anthropic/claude-sonnet-4.5 openai/gpt-4.1
```

### Filter by Attack Type

```bash
# Test encoding attacks only
./run_baseline_arango.py --dataset-source encoding_attacks_external

# Test specific encoding technique
./run_baseline_arango.py --encoding-technique base64

# Test manipulative attacks
./run_baseline_arango.py --ground-truth manipulative

# Limit to first 10 attacks
./run_baseline_arango.py --attack-limit 10
```

### Combined Filters

```bash
# Frontier models vs encoding attacks (reproducing baseline)
./run_baseline_arango.py \
  --model-type frontier_aligned \
  --dataset-source encoding_attacks_external

# Quick sanity check
./run_baseline_arango.py \
  --model-ids anthropic/claude-sonnet-4.5 \
  --attack-limit 10 \
  --experiment-id quick_test
```

## Analysis Queries

### Detection Rates by Model

```aql
FOR e IN evaluations
  FILTER e.experiment_metadata.experiment_id == "baseline_frontier_2025"
  FILTER e.condition == "observer"
  LET model = DOCUMENT(e._from)
  COLLECT modelName = model.name INTO detections = e.detected
  RETURN {
    model: modelName,
    detectionRate: LENGTH([d IN detections FILTER d == true]) / LENGTH(detections)
  }
```

### Compare Direct vs Observer

```aql
FOR m IN models
  LET direct = (
    FOR e IN evaluations
      FILTER e._from == m._id
      FILTER e.condition == "direct"
      FILTER e.detected == true
      RETURN 1
  )
  LET observer = (
    FOR e IN evaluations
      FILTER e._from == m._id
      FILTER e.condition == "observer"
      FILTER e.detected == true
      RETURN 1
  )
  RETURN {
    model: m.name,
    directDetections: LENGTH(direct),
    observerDetections: LENGTH(observer),
    marginalImprovement: LENGTH(observer) - LENGTH(direct)
  }
```

### Cost Analysis

```aql
FOR e IN evaluations
  LET model = DOCUMENT(e._from)
  COLLECT modelId = model._key INTO costs = e.cost_usd
  RETURN {
    model: modelId,
    avgCost: AVG(costs),
    totalCost: SUM(costs)
  }
  SORT totalCost DESC
```

## Key Features

### 1. Duplicate Detection

By default, skips evaluations that already exist:
- Same model + attack + condition + experiment_id
- Enables incremental evaluation (resume after interruption)
- Override with `--no-skip-existing`

### 2. Real-Time Persistence

Results written to database immediately after each evaluation:
- No data loss on interruption
- Can query partial results while running
- Progress saved for resumption

### 3. Cost Tracking

Running total of API costs:
- Printed on interruption (Ctrl+C)
- Included in summary JSON
- Per-evaluation cost stored in database

### 4. Progress Display

Two-level progress bars:
```
Models:   25%|████▌              | 1/4 [03:45<11:15, 225.0s/it]
  Claude Sonnet 4.5: 100%|████| 72/72 [03:45<00:00,  3.1s/it]
```

### 5. Flexible Filtering

Query models and attacks using any database field:
- Model type, organization, observer compatibility
- Dataset source, encoding technique, ground truth
- Arbitrary AQL filters (modify script for advanced use)

## Benefits Over JSON-Based Approach

### Old Pattern (test_baseline_comparison.py)

```python
MODELS = {
    "claude_sonnet_4.5": {...},  # Hardcoded
    "gpt_4.1": {...}
}
dataset_path = "datasets/file.jsonl"  # Static file

# Run everything, save at end
results = await experiment.run_experiment(dataset_path)
with open("results.json", 'w') as f:
    json.dump(results, f)
```

**Limitations:**
- Hardcoded model list (no dynamic queries)
- Static dataset (no filtering without code changes)
- Results saved at end (data loss on interruption)
- No duplicate detection (re-runs everything)
- Analysis requires separate scripts

### New Pattern (run_baseline_arango.py)

```bash
# Dynamic queries, flexible filters
./run_baseline_arango.py \
  --model-type frontier_aligned \
  --dataset-source encoding_attacks_external \
  --attack-limit 10

# Results in database immediately
# Query with AQL while running
# Resume after interruption
# Analysis-ready data structure
```

**Benefits:**
1. **Query flexibility** - Filter by any field
2. **Real-time persistence** - No data loss
3. **Duplicate detection** - Skip completed evaluations
4. **Cost tracking** - Running total, interrupt-safe
5. **Analysis-ready** - Query results immediately with AQL
6. **Incremental evaluation** - Add models/attacks without re-running

## Integration with Existing Code

### Uses Existing PromptGuard Library

```python
from promptguard import PromptGuard, PromptGuardConfig
from promptguard.evaluation import EvaluationMode

# Observer condition uses real PromptGuard evaluation
config = PromptGuardConfig(
    api_key=self.api_key,
    models=[model_id],
    evaluation_type="ayni_relational",  # Observer framing
    temperature=0.0
)
guard = PromptGuard(config)
result = await guard.evaluate(prompt=prompt_text)
```

No reimplementation of evaluation logic - uses production code.

### Direct Condition Pattern

```python
# Direct condition: Model alone (same as test_baseline_comparison.py)
async def call_model_direct(self, model_id, prompt, pricing):
    # OpenRouter API call
    # Refusal detection (pattern matching)
    # Cost calculation
    return {"detected": bool, "response": str, "cost_usd": float}
```

Matches original baseline comparison experiment.

## Files Created

1. **run_baseline_arango.py** (536 lines)
   - Main evaluation harness
   - Command-line interface
   - Database integration
   - Progress tracking

2. **BASELINE_ARANGO_USAGE.md** (700+ lines)
   - Comprehensive usage guide
   - Command-line reference
   - Query examples
   - Troubleshooting

3. **test_arango_connection.py** (150 lines)
   - Connection verification
   - Data availability check
   - Sample queries

4. **ARANGO_INTEGRATION_SUMMARY.md** (this file)
   - Overview and quick reference

## Next Steps

### 1. Verify Setup

```bash
./test_arango_connection.py
```

### 2. Quick Test

```bash
./run_baseline_arango.py \
  --model-ids anthropic/claude-sonnet-4.5 \
  --attack-limit 5 \
  --experiment-id quick_test
```

### 3. Run Baseline Comparison

```bash
./run_baseline_arango.py \
  --model-type frontier_aligned \
  --dataset-source encoding_attacks_external \
  --experiment-id baseline_frontier_2025
```

### 4. Analyze Results

Query evaluations collection with AQL (see BASELINE_ARANGO_USAGE.md for examples)

### 5. Extend

Add more models/attacks to database, re-run with `--skip-existing` (default) to evaluate new combinations only.

## Environment Variables Required

```bash
export OPENROUTER_API_KEY=your_key_here
export ARANGODB_PROMPTGUARD_PASSWORD=your_password_here
```

## Troubleshooting

See BASELINE_ARANGO_USAGE.md "Troubleshooting" section for:
- Environment variable issues
- Database connection problems
- Model/attack not found
- Rate limiting
- Error log analysis

## Design Principles Followed

From CLAUDE.md:

✅ **No theater** - Real API calls, real evaluations, fail-fast on errors

✅ **Fail-fast over graceful degradation** - Errors logged and stored, no fake data

✅ **Cost control** - Tracking, duplicate detection, incremental evaluation

✅ **Integration over reimplementation** - Uses existing PromptGuard library

✅ **Real data verification** - Test script verifies database before running

✅ **Research-focused** - Flexible queries, analysis-ready data structure
