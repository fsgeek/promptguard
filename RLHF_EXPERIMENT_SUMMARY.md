# RLHF Comparison Experiment - Implementation Summary

**Instance:** 20
**Date:** 2025-10-11
**Status:** Ready for execution

---

## What Was Built

Complete experimental infrastructure to test whether RLHF training helps or hinders encoding attack detection when combined with observer framing.

### Research Question

Does the observer framing breakthrough (Instance 17: 90% detection on encoding attacks) work **because** it bypasses RLHF biases, or **despite** RLHF?

### Experimental Design

**2×2 factorial design** per model pair:

|                | Defensive Framing | Observer Framing |
|----------------|-------------------|------------------|
| **Base**       | Condition A       | Condition B      |
| **Instruct**   | Condition C       | Condition D      |

**3 model pairs tested:**
1. Llama 3.1 405B (base vs instruct)
2. DeepSeek V3 (base vs instruct)
3. Llama 3 70B (base vs instruct)

**Dataset:** 72 encoding attacks (13 techniques)

**Total evaluations:** 3 pairs × 4 conditions × 72 attacks = 864

---

## Implementation Components

### Experiment Execution

1. **test_rlhf_comparison.py** (Main experiment script)
   - Loads 72 encoding attacks from JSONL dataset
   - Runs 4 conditions per model pair
   - Uses PromptGuard with custom evaluation prompts
   - Implements ayni balance < 0 detection threshold
   - Caching enabled (24-hour TTL, disk backend)
   - Saves intermediate results after each pair
   - Progress indicators every 10 attacks

2. **verify_rlhf_setup.py** (Pre-flight checks)
   - Verifies API key configuration
   - Tests dataset loading
   - Validates base and instruct model access
   - Tests encoding attack evaluation
   - Confirms cache functionality
   - Exit codes for automation

3. **run_rlhf_experiment.sh** (Interactive runner)
   - Safety checks (API key, confirmation prompt)
   - Creates cache directory
   - Runs experiment with logging
   - Auto-generates analysis on success
   - User-friendly status messages

### Analysis and Reporting

4. **analyze_rlhf_results.py** (Statistical analysis)
   - Chi-square tests (observer effects, RLHF effects)
   - Cohen's h effect sizes with interpretation
   - Wilson score confidence intervals
   - Hypothesis testing (H1, H2, H3)
   - Per-encoding-technique breakdown
   - Generates comprehensive markdown report

### Documentation

5. **RLHF_EXPERIMENT_README.md** (Quick reference)
   - Quick start guide
   - Cost and runtime estimates
   - Troubleshooting guide
   - Output examples

6. **RLHF_EXPERIMENT_PROTOCOL.md** (Detailed protocol)
   - Full research methodology
   - Background and hypotheses
   - Statistical analysis plan
   - Risk mitigation strategies
   - Success criteria

7. **RLHF_EXPERIMENT_SUMMARY.md** (This document)
   - Implementation overview
   - File inventory
   - Execution workflow

---

## Hypotheses to Test

**H1: RLHF Not Helping**
- Base + Observer ≈ Instruct + Observer
- Detection rates similar (within 5%)
- Implication: Observer framing sufficient, RLHF irrelevant

**H2: RLHF Degrading**
- Base + Observer > Instruct + Observer
- Statistically significant difference (p < 0.05)
- Implication: RLHF introduces biases, use base models

**H3: RLHF Complementary**
- Instruct + Observer > Base + Observer
- Statistically significant difference (p < 0.05)
- Implication: RLHF helps detection, use instruct models

---

## File Inventory

### Created Files (7 total)

```
test_rlhf_comparison.py          # Main experiment (340 lines)
analyze_rlhf_results.py          # Statistical analysis (280 lines)
verify_rlhf_setup.py             # Setup verification (240 lines)
run_rlhf_experiment.sh           # Interactive runner (60 lines)
RLHF_EXPERIMENT_README.md        # Quick reference
RLHF_EXPERIMENT_PROTOCOL.md      # Research protocol
RLHF_EXPERIMENT_SUMMARY.md       # This summary
```

### Generated Files (3 total)

```
rlhf_comparison_results.json     # Raw experimental data
RLHF_COMPARISON_ANALYSIS.md      # Statistical analysis report
rlhf_experiment.log              # Execution log
```

### Dependencies Used

- **promptguard.promptguard:** PromptGuard class
- **promptguard.evaluation.evaluator:** EvaluationConfig, EvaluationMode
- **promptguard.evaluation.config:** CacheConfig
- **scipy.stats:** Chi-square tests, effect sizes
- **numpy:** Statistical calculations

All dependencies already in `pyproject.toml`.

---

## Execution Workflow

### Phase 1: Verification (2-3 minutes)

```bash
export OPENROUTER_API_KEY=your_key_here
uv run python verify_rlhf_setup.py
```

**Checks:**
- ✓ API key configured
- ✓ Dataset loaded (72 attacks)
- ✓ Instruct model accessible
- ✓ Base model accessible
- ✓ Encoding attack detection working
- ✓ Cache functional

### Phase 2: Execution (2-4 hours)

```bash
./run_rlhf_experiment.sh
```

**Progress:**
1. Llama 405B pair (4 conditions × 72 = 288 evals)
2. DeepSeek V3 pair (4 conditions × 72 = 288 evals)
3. Llama 70B pair (4 conditions × 72 = 288 evals)

**Caching benefit:**
- Condition A: 0% cache hit (first defensive)
- Condition B: 0% cache hit (first observer)
- Condition C: ~70% cache hit (defensive reused)
- Condition D: ~70% cache hit (observer reused)

### Phase 3: Analysis (1 minute)

```bash
uv run python analyze_rlhf_results.py
```

**Generates:**
- Statistical tests (chi-square, effect sizes)
- Hypothesis determinations
- Per-encoding-technique breakdown
- Research implications
- Production recommendations

---

## Key Design Decisions

### 1. Defensive Framing as Baseline

Used Instance 13-16 defensive framing (not Instance 17 observer) to establish clean baseline. This lets us measure observer framing effect in both base and instruct models.

### 2. Ayni Balance Threshold

Detection threshold: `ayni_balance < 0` (negative = extraction)
- Consistent with extractive/manipulative classification
- Simple, interpretable boundary
- May need optimization based on results

### 3. Cache Strategy

- **Backend:** Disk (`.cache/rlhf_comparison`)
- **TTL:** 24 hours (models stable within experiment window)
- **Key:** SHA-256 hash of (layer_content, context, evaluation_prompt, model)
- **Benefit:** ~50% cost reduction across 4 conditions per pair

### 4. Statistical Approach

- **Chi-square:** Tests proportion differences (detected vs not detected)
- **Cohen's h:** Effect size for proportions (interpretable thresholds)
- **Wilson intervals:** Confidence intervals without assuming normality
- **Alpha:** 0.05 (standard significance level)

### 5. Fail-Fast Error Handling

- API failures raise EvaluationError with model context
- Intermediate results saved after each pair
- Verification script prevents wasted execution on misconfiguration

### 6. Per-Encoding-Technique Analysis

Secondary analysis breaks down detection by technique to identify:
- Which attacks most resistant across all conditions
- Whether base/instruct models have technique-specific strengths
- Patterns for future defense improvements

---

## Cost and Resource Estimates

### Time

- **Verification:** 2-3 minutes (6 API calls)
- **Experiment:** 2-4 hours (864 evaluations)
  - Llama 405B pair: ~1.5 hours
  - DeepSeek V3 pair: ~45 minutes
  - Llama 70B pair: ~30 minutes
- **Analysis:** 1 minute (local computation)

**Total:** ~3-5 hours end-to-end

### Cost

Model costs (per evaluation, approximate):
- Llama 405B: $0.003
- DeepSeek V3: $0.001
- Llama 70B: $0.0005

**Per pair (4 conditions × 72 attacks):**
- Llama 405B: $0.86 (with cache: $0.60)
- DeepSeek V3: $0.29 (with cache: $0.20)
- Llama 70B: $0.14 (with cache: $0.10)

**Total:** ~$1.29 (with cache: ~$0.90)

**Verification:** ~$0.02 (6 test calls)

**Grand total:** $1.31 (no cache) or $0.92 (with cache)

*Note: Prices subject to change on OpenRouter*

### API Rate Limits

OpenRouter free tier:
- 200 requests/minute
- 20,000 requests/day

**Experiment load:**
- 864 evaluations over ~3 hours = ~5 requests/minute
- Well within rate limits

---

## Expected Outcomes by Hypothesis

### If H1 Supported (RLHF Not Helping)

**Pattern:** Base + Observer ≈ Instruct + Observer

**Interpretation:**
- Observer framing is the critical ingredient
- RLHF neither helps nor hinders when framing is correct
- Production can use either base or instruct models

**Recommendation:**
- Choose based on cost: base models often cheaper
- Choose based on availability: instruct models more common
- No performance tradeoff

### If H2 Supported (RLHF Degrading)

**Pattern:** Base + Observer > Instruct + Observer

**Interpretation:**
- RLHF introduces biases that persist even with observer framing
- Conflict-avoidance training interferes with reciprocity assessment
- Base models preserve "raw" evaluation capability

**Recommendation:**
- Use base models for production evaluation
- Research finding: RLHF may degrade certain tasks
- Challenge assumption that RLHF always improves capabilities

### If H3 Supported (RLHF Complementary)

**Pattern:** Instruct + Observer > Base + Observer

**Interpretation:**
- RLHF and observer framing work synergistically
- RLHF maintains cooperative assessment frame
- Base models may lack instruction-following needed for evaluation

**Recommendation:**
- Use instruct models for production evaluation
- Validate that RLHF + observer framing is optimal
- Instance 17 findings hold up with instruct models

### If Mixed Results

**Pattern:** Different outcomes across model pairs

**Interpretation:**
- RLHF effect depends on model architecture/training
- No universal recommendation
- Model-specific testing needed

**Recommendation:**
- Per-model validation for production
- Further research into architecture differences
- Maintain flexibility in model selection

---

## Validation Checks

### Before Running

- [ ] API key exported: `echo $OPENROUTER_API_KEY`
- [ ] Dataset exists: `ls datasets/encoding_attacks_external_n72.jsonl`
- [ ] Setup verified: `uv run python verify_rlhf_setup.py`
- [ ] Cache directory created: `ls .cache/rlhf_comparison`

### During Execution

- [ ] Progress indicators showing
- [ ] Detection rates vary by condition (not all 0% or 100%)
- [ ] Intermediate results saving after each pair
- [ ] No repeated API errors

### After Completion

- [ ] Results file generated: `ls rlhf_comparison_results.json`
- [ ] Analysis report created: `ls RLHF_COMPARISON_ANALYSIS.md`
- [ ] All 3 model pairs completed (check JSON)
- [ ] Hypothesis determinations present in report

---

## Known Limitations

### Model Availability

Base models may have limited OpenRouter availability or higher costs. If a base model becomes unavailable mid-experiment, results will be partial.

**Mitigation:** Check OpenRouter model catalog before running. Save intermediate results.

### Detection Threshold

Current threshold (balance < 0) assumes negative balance indicates extraction. May not be optimal for all model types.

**Mitigation:** Analyze results to determine if threshold needs adjustment. Can rerun classification with different thresholds without re-evaluating.

### Cache Invalidation

Cache persists 24 hours. If models change behavior mid-experiment (unlikely), cached results may be stale.

**Mitigation:** Clear cache if experiment spans multiple days: `rm -rf .cache/rlhf_comparison`

### Sample Size per Technique

72 attacks across 13 techniques = ~5.5 attacks per technique average. Some techniques may have insufficient samples for technique-specific statistical tests.

**Mitigation:** Per-technique analysis is exploratory. Focus on overall detection rates for hypothesis testing.

---

## Integration with PromptGuard

### Clean Integration

Experiment uses existing PromptGuard infrastructure:
- `PromptGuard.evaluate()` with custom prompts
- Existing cache layer (DiskCache)
- Existing EvaluationConfig
- No modifications to core library

### Prompt Override

```python
guard = PromptGuard(
    evaluation_config=eval_config,
    evaluation_prompt_override=DEFENSIVE_PROMPT  # or OBSERVER_PROMPT
)
```

This temporarily replaces default observer framing to test defensive baseline.

### Detection Logic

```python
# Threshold-based detection
detected = result.ayni_balance < 0
```

Uses existing ayni_balance calculation. No custom logic in experiment script.

---

## Next Instance Handoff

### Results to Document

When experiment completes, Instance 21 should document:

1. **Hypothesis outcome:** Which hypothesis (H1, H2, H3) was supported
2. **Detection rates:** All 12 conditions (3 pairs × 4 conditions)
3. **Statistical significance:** Which effects were significant (p < 0.05)
4. **Effect sizes:** Magnitude of differences (Cohen's h)
5. **Production recommendation:** Base or instruct models for runtime evaluation

### Files to Update

1. **CLAUDE.md:** Add RLHF findings to "Validation results" section
2. **docs/INSTANCE_20_HANDOFF.md:** Create handoff document (this experiment)
3. **config/recommended_models.json:** Update with RLHF insights if needed

### Research Questions Raised

Depending on results:
- If H1: Why does RLHF have no effect? Is observer framing completely bypassing it?
- If H2: What specific RLHF bias persists? Can we quantify the degradation?
- If H3: How does RLHF help? Is it instruction-following or something deeper?

### Potential Follow-ups

- Cross-model validation (Claude, GPT-4, Gemini)
- Threshold optimization (ROC curve analysis)
- Technique-specific defenses (attacks resistant across all conditions)
- Meta-framing attacks (~10% still evade observer framing)

---

## Execution Checklist

### Pre-Flight

- [ ] Read RLHF_EXPERIMENT_README.md
- [ ] Export OPENROUTER_API_KEY
- [ ] Run verify_rlhf_setup.py (all checks pass)
- [ ] Understand cost ($1-2) and time (3-5 hours)

### Launch

- [ ] Run ./run_rlhf_experiment.sh
- [ ] Confirm when prompted
- [ ] Monitor progress (first 30 minutes)
- [ ] Let run in background (next 2-4 hours)

### Post-Flight

- [ ] Verify rlhf_comparison_results.json generated
- [ ] Read RLHF_COMPARISON_ANALYSIS.md
- [ ] Understand which hypothesis supported
- [ ] Document findings in CLAUDE.md
- [ ] Create Instance 20→21 handoff

---

## Success Metrics

**Minimum success:**
- All 3 model pairs complete
- Statistical tests run
- Hypothesis determination for 2/3 pairs

**Full success:**
- All 3 pairs complete
- Consistent pattern across pairs
- Large effect sizes (h > 0.5)
- Clear production recommendation
- Insights for future research

---

**Implementation complete:** 2025-10-11
**Instance:** 20
**Ready for execution:** Yes
**Estimated completion:** 3-5 hours after launch
