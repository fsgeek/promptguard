# Evaluation Pipeline Implementation

## Overview

The evaluation pipeline provides a flexible research instrument for testing the trust trajectory hypothesis: manipulation detection may be more effective by analyzing how T/I/F values change through the pipeline rather than examining absolute values at a single point.

## Implementation Status

**Complete:** All core components implemented and syntax-validated.

### Files Created

1. **promptguard/research/pipeline.py** (539 lines)
   - `EvaluationPipeline` class with four configurable modes
   - `PipelineMode` enum (BASELINE, PRE, POST, BOTH)
   - `GeneratorConfig` dataclass for response generation
   - Integration with PromptGuard and PostResponseEvaluator
   - Immediate JSONL recording via EvaluationRecorder

2. **promptguard/research/post_evaluator.py** (588 lines)
   - `PostResponseEvaluator` class for response analysis
   - `BaselineStats` dataclass for anomaly detection
   - Neutrosophic evaluation of responses (T/I/F values)
   - Role consistency checking
   - Coherence assessment
   - Length anomaly detection (z-scores)
   - Violation pattern detection
   - Reasoning quality assessment

3. **test_pipeline.py** (235 lines)
   - Validation test script
   - Loads polite extraction attack from dataset
   - Runs through BOTH mode
   - Verifies EvaluationRecord structure
   - Confirms JSONL output

4. **examples/pipeline_usage.py** (388 lines)
   - Five usage examples demonstrating all modes
   - Cross-model evaluation example
   - Comprehensive documentation

5. **promptguard/research/__init__.py** (updated)
   - Exports new components for public API

## Architecture

### Four Pipeline Modes

```python
class PipelineMode(Enum):
    BASELINE = "baseline"  # No intervention, raw model response
    PRE = "pre"            # Front-end evaluation only
    POST = "post"          # Post-response evaluation only
    BOTH = "both"          # Full pipeline with pre + post
```

**BASELINE Mode:**
- Generate → Record
- Use case: Control group, measure baseline behavior
- Cost: Generation only

**PRE Mode:**
- Pre-eval → (Block if violation) → Generate → Record
- Use case: Test front-end screening effectiveness
- Cost: Evaluation + generation (if passed)

**POST Mode:**
- Generate → Post-eval → Record
- Use case: Test post-hoc detection capabilities
- Cost: Generation + post-evaluation

**BOTH Mode:**
- Pre-eval → Generate → Post-eval → Compute Deltas → Record
- Use case: Test trajectory hypothesis (ΔT, ΔI, ΔF)
- Cost: Full pipeline (most expensive, most comprehensive)

### Post-Response Evaluation

The `PostResponseEvaluator` analyzes responses for manipulation signals:

1. **Neutrosophic values** (T, I, F) using Ayni evaluation
2. **Role consistency** (did model maintain expected role?)
3. **Coherence score** (is response logically sound?)
4. **Length z-score** (vs baseline distribution)
5. **Violation detection** (role reversal, excessive apology, etc.)
6. **Reasoning quality** (structure, clarity)
7. **Decision** (accept, reject, flag)

### Delta Calculation

For BOTH mode, the pipeline computes trajectory deltas:

```python
delta_T = post.T - mean(pre.T across all layers)
delta_I = post.I - mean(pre.I across all layers)
delta_F = post.F - mean(pre.F across all layers)
delta_trust = post.trust_field_response - pre.trust_field.balance
```

**Hypothesis:** Manipulated responses show higher variance in deltas than genuine responses, even when absolute values appear acceptable.

### Model Flexibility

The pipeline supports:
- **OpenRouter provider:** Cloud API for diverse model access
- **LM Studio provider:** Local model hosting for reproducible research
- **Cross-model evaluation:** Different models for generation vs evaluation

Example:
```python
# Generate with flagship model
generator_config = GeneratorConfig(
    model="anthropic/claude-3.5-sonnet"
)

# Evaluate with budget model
post_evaluator = PostResponseEvaluator(
    evaluator_model="google/gemini-flash-1.5"
)
```

### Fail-Fast Design

All evaluation stages follow fail-fast principles:

- API failures raise `EvaluationError` with model/layer context
- Parser validates required fields and raises on unparseable responses
- No partial records created (research integrity)
- Incomplete data is worse than no data

### Immediate Recording

Each evaluation is written to JSONL immediately:

```python
record = await pipeline.evaluate(prompt_data)
# ↑ Already written to JSONL by this point
```

Benefits:
- No data loss if pipeline crashes mid-run
- Enables real-time monitoring during long evaluations
- Supports distributed processing (append-only JSONL is safe)

## Integration Points

The pipeline integrates seamlessly with existing components:

1. **PromptGuard** (`promptguard.PromptGuard`)
   - Used for pre-evaluation
   - Provides per-layer neutrosophic values
   - Calculates trust field and ayni balance

2. **LLMEvaluator** (`promptguard.evaluation.evaluator.LLMEvaluator`)
   - Used by PostResponseEvaluator for T/I/F assessment
   - Supports both OpenRouter and LM Studio
   - Caching layer reduces API costs

3. **Schema** (`promptguard.research.schema`)
   - All data structures defined
   - Versioned schema (1.0.0)
   - JSON serialization/deserialization

4. **Recorder** (`promptguard.research.recorder.EvaluationRecorder`)
   - Append-only JSONL writer
   - Validation utilities
   - Load/inspect capabilities

## Usage Example

```python
from promptguard.research import (
    EvaluationPipeline,
    PipelineMode,
    GeneratorConfig,
    EvaluationRecorder,
    PostResponseEvaluator,
)
from promptguard import PromptGuard, PromptGuardConfig

# Initialize components
pre_evaluator = PromptGuard(PromptGuardConfig())
post_evaluator = PostResponseEvaluator(evaluator_model="anthropic/claude-3.5-sonnet")
recorder = EvaluationRecorder(Path("results/run_001.jsonl"))

# Create pipeline
pipeline = EvaluationPipeline(
    mode=PipelineMode.BOTH,
    recorder=recorder,
    generator_config=GeneratorConfig(model="anthropic/claude-3.5-sonnet"),
    run_metadata=RunMetadata(...),
    pre_evaluator=pre_evaluator,
    post_evaluator=post_evaluator,
)

# Evaluate prompt
record = await pipeline.evaluate(prompt_data)

# Analyze trajectory
print(f"ΔT: {record.deltas.delta_T:+.3f}")
print(f"ΔF: {record.deltas.delta_F:+.3f}")
```

## Testing Validation

The `test_pipeline.py` script validates:

1. ✓ All components initialize correctly
2. ✓ Pipeline executes without errors
3. ✓ EvaluationRecord is properly populated
4. ✓ JSONL output is valid and parseable
5. ✓ All required fields are present

Run with:
```bash
uv run python test_pipeline.py
```

**Note:** Requires OPENROUTER_API_KEY or LM Studio running locally.

## Research Questions Enabled

The pipeline enables systematic testing of:

1. **Pre-evaluation effectiveness**
   - How many manipulative prompts does pre-screening catch?
   - What's the false positive rate on reciprocal prompts?
   - Does blocking save generation costs?

2. **Post-evaluation detection**
   - Can we detect manipulation from the response alone?
   - What signals correlate with manipulation success?
   - Are length anomalies or role violations more predictive?

3. **Trajectory hypothesis**
   - Do manipulated responses show higher ΔF (falsity increase)?
   - Is ΔT (truth degradation) a reliable signal?
   - Can we detect polite extraction via trajectory shifts?

4. **Cost optimization**
   - Does ensemble of budget models match flagship accuracy?
   - Can we use cheap models to evaluate expensive outputs?
   - What's the minimum viable configuration for production?

5. **Variance as signal**
   - Do different models detect different violation types?
   - Does model disagreement indicate edge cases?
   - Can we use variance to identify prompts needing human review?

## Known Limitations

1. **Post-evaluator uses LLM-based analysis**
   - Role consistency and coherence require additional API calls
   - Could be optimized with statistical heuristics
   - Current implementation prioritizes accuracy over cost

2. **Baseline statistics are placeholders**
   - Need to collect corpus of benign responses
   - Length z-scores not yet calibrated
   - Reasoning quality needs better metrics

3. **No Fire Circle support yet**
   - Fire Circle mode exists in LLMEvaluator
   - Not yet integrated into pipeline
   - High research value, unexplored

4. **Per-layer deltas not exposed**
   - Current deltas average across prompt layers
   - May want layer-specific trajectory analysis
   - Could add optional per-layer delta calculation

## Future Enhancements

1. **Batch processing**
   - Pipeline.evaluate_batch() for parallel processing
   - Progress tracking with tqdm
   - Checkpoint/resume for long runs

2. **Real-time monitoring**
   - WebSocket interface for live results
   - Dashboard for visualization
   - Alerts for anomalies

3. **Statistical analysis integration**
   - Correlation analysis (deltas vs manipulation success)
   - Confusion matrices per model
   - ROC curves for threshold tuning

4. **Cost tracking**
   - Record API costs per evaluation
   - Budget limits and warnings
   - Cost optimization recommendations

5. **Model ensemble evaluation**
   - Test multiple evaluator models in parallel
   - Compare detection rates across models
   - Identify best model combinations

## Cost Estimates

Based on current pricing (see `docs/model_pricing_analysis.md`):

**Claude 3.5 Sonnet (flagship):**
- BASELINE: $0.003/prompt (generation only)
- PRE: $0.008/prompt (eval + generation)
- POST: $0.008/prompt (generation + eval)
- BOTH: $0.015/prompt (eval + gen + eval)

**Budget ensemble (Gemini Flash, DeepSeek):**
- BASELINE: $0.0001/prompt
- PRE: $0.0005/prompt
- POST: $0.0005/prompt
- BOTH: $0.001/prompt

**Research run (680 prompts, BOTH mode):**
- Flagship: $10.20
- Budget: $0.68

## Implementation Complete

All components implemented and ready for testing:

- ✓ EvaluationPipeline with four modes
- ✓ PostResponseEvaluator with comprehensive analysis
- ✓ Generator abstraction (OpenRouter + LM Studio)
- ✓ Delta computation for trajectory analysis
- ✓ Outcome classification (TP/FP/TN/FN)
- ✓ Fail-fast error handling
- ✓ Immediate JSONL recording
- ✓ Test script for validation
- ✓ Usage examples and documentation

**Next step:** Run test_pipeline.py with real data to validate end-to-end functionality.
