# Fire Circle Validation Experiment

Empirical validation of Fire Circle dialogue-based consensus vs SINGLE/PARALLEL modes, with and without REASONINGBANK memory enhancement.

## Experimental Design

**Research Question:** Does Fire Circle dialogue produce better detection than averaging (PARALLEL) or single-model evaluation (SINGLE)? Does REASONINGBANK memory enhance detection?

**6 Conditions:**
- `baseline_single`: Claude Sonnet 4.5 alone, no REASONINGBANK
- `baseline_parallel`: 3 models independently (GPT-5 Pro, Claude Sonnet 4.5, DeepSeek V3.2), max(F) consensus
- `baseline_fire_circle`: Same 3 models in 3-round dialogue, max(F) consensus
- `enhanced_single`: Claude Sonnet 4.5 + REASONINGBANK retrieval
- `enhanced_parallel`: 3 models + REASONINGBANK
- `enhanced_fire_circle`: 3 models + REASONINGBANK + dialogue

**Dataset:** 50 prompts stratified across 5 attack types:
- `easy_reciprocal` (5): Clear benign prompts
- `easy_extractive` (5): Clear extraction attacks
- `encoding_attacks` (15): Unicode obfuscation, base64, etc.
- `semantic_manipulation` (15): Jailbreaks, role reversal, polite extraction
- `multi_layer` (5): History injection attacks
- `borderline` (5): Safe prompts about sensitive topics

**Models:**
- SINGLE: `anthropic/claude-sonnet-4.5`
- PARALLEL/FIRE_CIRCLE: `openai/gpt-5-pro`, `anthropic/claude-sonnet-4.5`, `deepseek/deepseek-v3.2-exp`

**Evaluation:**
- Observer framing (ayni reciprocity assessment)
- Neutrosophic (T, I, F) scores
- Fire Circle: 3-round dialogue, pattern extraction, empty chair rotation
- REASONINGBANK: Semantic retrieval of learned attack patterns

**Expected Cost:** ~$5-8 for full experiment (300 evaluations total)

## File Structure

```
experiments/
├── fire_circle_validation/
│   ├── README.md                    # This file
│   ├── stratified_sampler.py        # Samples 50 prompts across strata
│   ├── experiment_runner.py         # Evaluates prompts with checkpointing
│   └── stratified_sample.json       # Generated sample (50 prompts)
├── configs/
│   ├── baseline_single.json
│   ├── baseline_parallel.json
│   ├── baseline_fire_circle.json
│   ├── enhanced_single.json
│   ├── enhanced_parallel.json
│   └── enhanced_fire_circle.json
└── results/
    └── raw/
        ├── baseline_single_results.json
        ├── baseline_parallel_results.json
        ├── baseline_fire_circle_results.json
        ├── enhanced_single_results.json
        ├── enhanced_parallel_results.json
        └── enhanced_fire_circle_results.json
```

## Running the Experiment

### Prerequisites

1. **OpenRouter API key:**
   ```bash
   export OPENROUTER_API_KEY=your_key_here
   ```

2. **ArangoDB (optional but recommended for Fire Circle storage):**
   ```bash
   export ARANGODB_PROMPTGUARD_PASSWORD=your_password
   export ARANGODB_HOST=192.168.111.125  # Optional
   export ARANGODB_PORT=8529              # Optional
   ```

3. **REASONINGBANK memories (optional):**
   - Enhanced conditions require `reasoningbank/memories/` with learned patterns
   - Baseline conditions work without memories (retriever disabled)

### Full Experiment (All 6 Conditions)

```bash
# Run complete experiment (~$5-8, ~30-60 minutes)
./run_fire_circle_validation.sh
```

This script:
1. Generates stratified sample (if not exists)
2. Runs all 6 conditions sequentially
3. Saves results to `experiments/results/raw/`
4. Reports progress and errors

### Single Condition

```bash
# Run one condition
python experiments/fire_circle_validation/experiment_runner.py \
    experiments/configs/baseline_single.json
```

### Sample Test (3 Prompts)

```bash
# Test with 3 prompts before full run
python experiments/fire_circle_validation/experiment_runner.py \
    experiments/configs/baseline_single.json \
    --limit 3
```

**Use this to validate the pipeline before spending $5-8 on full run!**

## Checkpointing & Resume

The experiment runner saves checkpoints every 10 prompts to:
```
experiments/results/raw/{condition_name}_checkpoint.json
```

If a run fails, re-run the same command and it will resume from the last checkpoint:
```bash
python experiments/fire_circle_validation/experiment_runner.py \
    experiments/configs/baseline_single.json
```

Output:
```
Resuming from checkpoint: 23 prompts already completed
Remaining: 27
```

## Output Format

Each condition produces a results file with:

```json
{
  "metadata": {
    "condition": "baseline_single",
    "mode": "SINGLE",
    "models": ["anthropic/claude-sonnet-4.5"],
    "reasoningbank_enabled": false,
    "total_prompts": 50,
    "successful": 48,
    "failed": 2,
    "total_duration_seconds": 245.3,
    "average_duration_seconds": 4.9,
    "stratum_breakdown": {
      "encoding_attacks": {"total": 15, "successful": 14, "failed": 1},
      ...
    }
  },
  "results": [
    {
      "prompt_id": "benign_malicious_335243",
      "stratum": "easy_reciprocal",
      "expected_label": "reciprocal",
      "evaluations": [
        {
          "model": "anthropic/claude-sonnet-4.5",
          "T": 0.8,
          "I": 0.1,
          "F": 0.1,
          "reasoning": "...",
          "transparency_note": null
        }
      ],
      "consensus": null,
      "fire_circle_metadata": null,
      "duration_seconds": 3.2,
      "error": null
    },
    ...
  ]
}
```

**Fire Circle results include:**
- `fire_circle_metadata`: Patterns discovered, empty chair influence, dialogue rounds
- `consensus`: max(F) across all models in all rounds
- Per-round evaluations in `evaluations` array

## Analyzing Results

### Cost Tracking

```bash
# Sum total duration
jq '.metadata.total_duration_seconds' experiments/results/raw/*.json
```

### Detection Accuracy by Stratum

```bash
# Extract stratum breakdown
jq '.metadata.stratum_breakdown' experiments/results/raw/baseline_single_results.json
```

### Fire Circle Patterns

```bash
# Query ArangoDB for Fire Circle deliberations
python query_fire_circle_storage.py
```

### Per-Model Variance (PARALLEL/FIRE_CIRCLE)

```python
import json

with open('experiments/results/raw/baseline_parallel_results.json') as f:
    data = json.load(f)

for result in data['results']:
    if result['evaluations']:
        f_scores = [e['F'] for e in result['evaluations']]
        variance = max(f_scores) - min(f_scores)
        print(f"{result['prompt_id']}: F variance = {variance:.2f}")
```

## Validation Checklist

Before full $5-8 run:

- [ ] Run sample test (3 prompts)
- [ ] Verify stratified sample generated correctly
- [ ] Check OpenRouter API key set
- [ ] Verify ArangoDB connection (for Fire Circle)
- [ ] Confirm REASONINGBANK memories exist (for enhanced conditions)
- [ ] Test checkpoint/resume logic
- [ ] Validate output format

## Expected Results

**Baseline conditions:**
- `baseline_single`: Fast (~5s/prompt), no variance
- `baseline_parallel`: Slower (~15s/prompt), shows model disagreement
- `baseline_fire_circle`: Slowest (~30s/prompt), dialogue convergence

**Enhanced conditions:**
- Should show improved detection on encoding attacks (REASONINGBANK has learned patterns)
- Transparency notes in results show which memories were retrieved

**Fire Circle specific:**
- Pattern observations (temporal inconsistency, cross-layer fabrication, etc.)
- Empty chair influence metric
- Convergence trajectory across rounds

## Troubleshooting

**API timeout errors:**
- Increase `timeout_seconds` in config JSON
- Check OpenRouter status

**ArangoDB connection errors:**
- Fire Circle will fail if storage enabled but ArangoDB unavailable
- Disable storage in config JSON or fix connection

**REASONINGBANK retrieval errors:**
- Enhanced conditions gracefully degrade to baseline if retrieval fails
- Check `reasoningbank/memories/` directory exists

**Checkpoint corruption:**
- Delete checkpoint file and restart:
  ```bash
  rm experiments/results/raw/baseline_single_checkpoint.json
  ```

## Cost Estimation

Per condition (50 prompts):
- **SINGLE:** ~$0.50-1.00 (1 model × 50 prompts)
- **PARALLEL:** ~$1.50-2.00 (3 models × 50 prompts)
- **FIRE_CIRCLE:** ~$2.50-4.00 (3 models × 50 prompts × 3 rounds)

**Total for 6 conditions:** ~$8-13

Sample test (3 prompts × 1 condition): ~$0.20-0.50

## Next Steps

After experiment completes:

1. **Statistical analysis:** Compare detection accuracy across conditions
2. **Variance analysis:** Measure model disagreement in PARALLEL/FIRE_CIRCLE
3. **Pattern discovery:** Query Fire Circle deliberations for unique insights
4. **Cost-benefit:** Does Fire Circle justify 3-4x cost vs PARALLEL?
5. **REASONINGBANK validation:** Measure improvement delta (enhanced - baseline)

See `docs/INSTANCE_45_SUMMARY.md` for research context and Instance 42-44 findings.
