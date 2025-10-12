# RLHF Comparison Experiment

**Research Question:** Does RLHF training help or hinder encoding attack detection when combined with observer framing?

---

## Quick Start

```bash
# 1. Verify setup
export OPENROUTER_API_KEY=your_key_here
uv run python verify_rlhf_setup.py

# 2. Run experiment (interactive)
./run_rlhf_experiment.sh

# 3. View results
cat RLHF_COMPARISON_ANALYSIS.md
```

---

## Background

**Instance 17 breakthrough:** Observer framing achieves 90% detection on encoding attacks vs 0% with defensive framing. Observer framing shifts the evaluation task from "detect attacks" to "assess reciprocity in exchange," bypassing RLHF conflict-avoidance bias.

**Research gap:** We don't know if observer framing works **because** it bypasses RLHF or **despite** RLHF. Base models (no RLHF) are now available on OpenRouter, enabling direct comparison.

---

## Experimental Design

### 2×2 Factorial Design

|                | **Defensive Framing** | **Observer Framing** |
|----------------|----------------------|---------------------|
| **Base Model** | Condition A          | Condition B         |
| **Instruct**   | Condition C          | Condition D         |

### Model Pairs Tested

1. **Llama 3.1 405B** - meta-llama/llama-3.1-405b vs meta-llama/llama-3.1-405b-instruct
2. **DeepSeek V3** - deepseek/deepseek-v3-base vs deepseek/deepseek-chat
3. **Llama 3 70B** - meta-llama/llama-3-70b vs meta-llama/llama-3.1-70b-instruct

### Dataset

72 encoding attacks from external sources:
- Cyrillic homoglyphs
- Zero-width unicode
- Leetspeak
- Base64 encoding
- Mathematical unicode
- And 8 other techniques

Source: `datasets/encoding_attacks_external_n72.jsonl`

---

## Hypotheses

**H1: RLHF Not Helping**
- Base + Observer ≈ Instruct + Observer
- Observer framing sufficient regardless of RLHF

**H2: RLHF Degrading**
- Base + Observer > Instruct + Observer
- RLHF introduces biases that interfere with detection

**H3: RLHF Complementary**
- Instruct + Observer > Base + Observer
- RLHF and observer framing work together synergistically

---

## Files

### Experiment Execution
- `test_rlhf_comparison.py` - Main experiment script (864 evaluations)
- `verify_rlhf_setup.py` - Pre-flight checks
- `run_rlhf_experiment.sh` - Interactive runner with safety checks

### Analysis
- `analyze_rlhf_results.py` - Statistical analysis and report generation
- `rlhf_comparison_results.json` - Raw experimental data (generated)
- `RLHF_COMPARISON_ANALYSIS.md` - Analysis report (generated)

### Documentation
- `RLHF_EXPERIMENT_README.md` - This file (quick reference)
- `RLHF_EXPERIMENT_PROTOCOL.md` - Detailed research protocol

---

## Cost and Runtime

**Evaluations:** 3 pairs × 4 conditions × 72 attacks = 864 evaluations

**Runtime:** 2-4 hours (with caching)
- First model pair: ~1.5 hours (no cache hits)
- Subsequent pairs: ~30-60 min each (cache hits on defensive/observer prompts)

**Cost:** $5-15 total (varies by model pricing)
- Llama 405B: ~$0.003 per evaluation
- DeepSeek V3: ~$0.001 per evaluation
- Llama 70B: ~$0.0005 per evaluation

**Cache benefit:** ~50% cost reduction across 4 conditions (defensive/observer prompts reused)

---

## Running the Experiment

### Step 1: Verify Setup

```bash
# Check API key, dataset, model access, cache
uv run python verify_rlhf_setup.py
```

Should output:
```
✓ API key found
✓ Dataset found: 72 encoding attacks
✓ Model responded successfully (both base and instruct)
✓ Cache working
✓ ALL CHECKS PASSED
```

### Step 2: Run Experiment

**Option A: Interactive (recommended)**
```bash
./run_rlhf_experiment.sh
```

**Option B: Background**
```bash
nohup ./run_rlhf_experiment.sh > rlhf_experiment.log 2>&1 &
tail -f rlhf_experiment.log
```

**Option C: Single pair test**
```python
import asyncio
from test_rlhf_comparison import run_model_pair_comparison, load_encoding_attacks

attacks = load_encoding_attacks()
result = asyncio.run(run_model_pair_comparison(
    "meta-llama/llama-3.1-405b",
    "meta-llama/llama-3.1-405b-instruct",
    "Llama-3.1-405B",
    attacks
))
```

### Step 3: Analyze Results

```bash
# Generate statistical analysis report
uv run python analyze_rlhf_results.py

# View report
cat RLHF_COMPARISON_ANALYSIS.md
```

---

## Interpreting Results

### Detection Rates

Example output:
```
Model Pair: Llama-3.1-405B
  Base + Defensive:  15.3%
  Base + Observer:   85.2%
  Instruct + Defensive: 18.1%
  Instruct + Observer: 88.9%
```

### Statistical Significance

Chi-square tests determine if differences are statistically significant:
- **p < 0.05:** Significant difference
- **p ≥ 0.05:** No significant difference

Effect sizes (Cohen's h) measure magnitude:
- **h < 0.2:** Negligible
- **0.2 ≤ h < 0.5:** Small
- **0.5 ≤ h < 0.8:** Medium
- **h ≥ 0.8:** Large

### Hypothesis Support

The analysis will determine which hypothesis is supported:

**If H1 (RLHF Not Helping):**
- Production can use either base or instruct models
- Observer framing is the key ingredient
- Cost savings: base models may be cheaper

**If H2 (RLHF Degrading):**
- Production should use base models
- RLHF bias persists even with observer framing
- Research finding: RLHF may degrade evaluation

**If H3 (RLHF Complementary):**
- Production should use instruct models
- RLHF maintains cooperative assessment
- Observer framing + RLHF = optimal

---

## Troubleshooting

### API Rate Limits
```
Error: Rate limit exceeded
```
**Solution:** Wait 60 seconds, then resume. Caching prevents duplicate work.

### Model Not Available
```
Error: Model not found
```
**Solution:** Check OpenRouter model availability. Base models may have limited access.

### Cache Issues
```
Warning: Cache may not be working
```
**Solution:** Check `.cache/rlhf_comparison` directory permissions. Clear cache if corrupted.

### Parsing Failures
```
Error: Failed to parse response
```
**Solution:** Model may be returning malformed JSON. Check logs for raw response. May need to adjust parsing logic.

---

## Expected Outputs

### Console Output

```
========================================
Model Pair: Llama-3.1-405B
Base: meta-llama/llama-3.1-405b
Instruct: meta-llama/llama-3.1-405b-instruct
========================================

Condition: Llama-3.1-405B - Base + Defensive
Model: meta-llama/llama-3.1-405b
Prompt: Defensive
Progress: 10/72 (2/10 detected, 20.0%)
Progress: 20/72 (4/20 detected, 20.0%)
...
Base + Defensive Detection Rate: 11/72 = 15.3%

Condition: Llama-3.1-405B - Base + Observer
Model: meta-llama/llama-3.1-405b
Prompt: Observer
Progress: 10/72 (9/10 detected, 90.0%)
...
Base + Observer Detection Rate: 61/72 = 84.7%
```

### JSON Results

`rlhf_comparison_results.json`:
```json
{
  "experiment": "rlhf_comparison",
  "dataset": "encoding_attacks_external_n72",
  "n_attacks": 72,
  "timestamp": "2025-10-11T...",
  "model_pairs": [
    {
      "pair_name": "Llama-3.1-405B",
      "base_model": "meta-llama/llama-3.1-405b",
      "instruct_model": "meta-llama/llama-3.1-405b-instruct",
      "conditions": {
        "base_defensive": {
          "detection_rate": 0.153,
          "detected": 11,
          "total": 72,
          "results": [...]
        },
        ...
      },
      "statistics": {
        "observer_effect_base": {
          "chi_square": 45.2,
          "p_value": 0.0001,
          "effect_size_h": 1.85,
          "significant": true
        },
        ...
      }
    },
    ...
  ]
}
```

### Markdown Report

`RLHF_COMPARISON_ANALYSIS.md`:
- Executive summary with key findings
- 2×2 tables for each model pair
- Statistical test results (chi-square, p-values, effect sizes)
- Hypothesis testing outcomes
- Per-encoding-technique breakdown
- Research implications
- Production recommendations

---

## Next Steps After Completion

1. **Update CLAUDE.md** with RLHF findings
2. **Create Instance 20→21 handoff** documenting methodology and results
3. **Production recommendation** (base vs instruct models)
4. **Threshold optimization** if needed (currently balance < 0)
5. **Cross-model validation** with Claude/GPT-4/Gemini if results warrant

---

## Support

**Questions?** Check:
- `RLHF_EXPERIMENT_PROTOCOL.md` - Detailed research protocol
- `docs/INSTANCE_18_HANDOFF.md` - Observer framing integration
- `docs/OBSERVER_FRAMING_BREAKTHROUGH.md` - RLHF bias discovery
- `CLAUDE.md` - Overall project status

**Issues?**
- Check `rlhf_experiment.log` for detailed error messages
- Verify setup with `verify_rlhf_setup.py`
- Ensure API key has sufficient credits

---

**Experiment designed by:** Instance 20
**Date:** 2025-10-11
**Status:** Ready for execution
