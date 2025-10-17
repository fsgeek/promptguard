# Fire Circle Integration - Instance 28

## Status: ✅ Complete

Fire Circle multi-model dialogue evaluation is now integrated into the main PromptGuard API and validated with real OpenRouter API calls.

## What Was Done

### 1. Integration into LLMEvaluator (evaluator.py)

Fire Circle is now accessible through the standard `LLMEvaluator` API:

```python
from promptguard.evaluation.evaluator import LLMEvaluator
from promptguard.evaluation.fire_circle import FireCircleConfig, CircleSize, FailureMode

config = FireCircleConfig(
    models=["anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku", "google/gemini-2.0-flash-001"],
    circle_size=CircleSize.SMALL,
    max_rounds=3,
    failure_mode=FailureMode.RESILIENT,
    pattern_threshold=0.5,
    min_viable_circle=2,
    provider="openrouter"
)

evaluator = LLMEvaluator(config)
result = await evaluator.evaluate_layer(layer_content, context, evaluation_prompt)
```

**Changes:**
- Added Fire Circle imports to evaluator.py
- Modified `__init__` to detect FireCircleConfig and instantiate FireCircleEvaluator
- Updated `evaluate_layer()` to delegate to fire_circle.evaluate() when using FireCircleConfig
- Made recursion depth check conditional (only for configs with that field)
- Removed old 2-round stub implementation

### 2. API Key Loading (fire_circle.py)

FireCircleConfig now loads OPENROUTER_API_KEY from environment automatically:

```python
def __post_init__(self):
    """Validate Fire Circle configuration and load API key."""
    import os

    # Load API key from environment if not provided
    if self.provider == "openrouter" and self.api_key is None:
        self.api_key = os.getenv("OPENROUTER_API_KEY")
        if self.api_key is None:
            raise ValueError(
                "OpenRouter API key required. Set OPENROUTER_API_KEY environment "
                "variable or pass api_key to FireCircleConfig"
            )
```

### 3. Logging Fix (fire_circle.py)

Fixed Python logging conflict where 'message' is a reserved field:

```python
# Changed from "message" to "detail"
extra={"detail": "Any further failure will abort Fire Circle"}
```

## Validation Results

### ✅ Round 1 Validation (test_fire_circle_prompt.py)

**Config:** 2 models, 1 round, STRICT mode
**Result:** SUCCESS - Both models responded correctly

```
✅ Round 1 prompt works!
Number of evaluations: 2
  anthropic/claude-3-haiku: T=1.0, I=0.0, F=0.0
  anthropic/claude-3.5-sonnet: T=0.0, I=0.0, F=1.0
```

### ✅ Full 3-Round Validation (test_fire_circle_logging.py)

**Config:** 3 models, 3 rounds, RESILIENT mode
**Result:** SUCCESS - All rounds completed

```
Round 1 complete (3 evaluations)
Round 2 complete (3 evaluations)
Round 3 complete (3 evaluations)
Fire Circle evaluation complete

✅ SUCCESS
Evaluations: 9
```

### 🔄 In Progress: Detection Comparison (test_fire_circle_vs_parallel.py)

Comparing SINGLE vs PARALLEL vs FIRE_CIRCLE on PWNED jailbreak attack to measure if dialogue improves detection over independent evaluation.

## Key Files

**Core Integration:**
- `promptguard/evaluation/evaluator.py` - Fire Circle integration
- `promptguard/evaluation/fire_circle.py` - Fire Circle implementation

**Test Scripts:**
- `test_fire_circle_prompt.py` - Round 1 validation (2 models)
- `test_fire_circle_logging.py` - Full 3-round validation (3 models)
- `test_fire_circle_vs_parallel.py` - Detection comparison
- `test_api_direct.py` - Direct API verification
- `test_evaluator_call_llm.py` - Evaluator API verification

## Research Questions Enabled

1. **Pattern Discovery:** Do models identify different manipulation patterns in dialogue vs isolation?
2. **Empty Chair Influence:** Do absent-voice perspectives reveal patterns active models miss?
3. **Convergence:** Does F-score variance decrease across rounds (groupthink risk)?
4. **Detection Advantage:** Does dialogue improve detection over simple consensus?

## Technical Notes

**Fire Circle Protocol:**
- Round 1: Independent baseline (no dialogue context)
- Round 2: Pattern discussion with Round 1 dialogue context
- Round 3: Consensus refinement with Round 1 + Round 2 context

**Empty Chair Rotation:**
- Round 1: None (baseline)
- Round 2+: Rotates through models `models[(round_num - 1) % len(models)]`

**Consensus Algorithm:**
- `compute_max_f_consensus()` returns evaluation with maximum F-score across all active models in all rounds
- Preserves detection signal even if later rounds lower F-scores

**Failure Handling:**
- STRICT: Fail on any model error
- RESILIENT: Continue with remaining models if above min_viable_circle

## Cost Analysis

**Validation Run (3 models × 3 rounds = 9 LLM calls):**
- Total prompt: ~1,500 tokens per call (dialogue context grows)
- Total response: ~200 tokens per call
- **Total cost:** ~$0.03 per Fire Circle evaluation (vs $0.01 for PARALLEL)

**Trade-off:** 3x cost vs PARALLEL, but potentially better detection and richer pattern data.

## Next Steps

1. ✅ Validate Fire Circle works with real API
2. 🔄 Compare detection: Fire Circle vs PARALLEL vs SINGLE on encoding attacks
3. ⏳ Measure empty chair influence on pattern discovery
4. ⏳ Analyze F-score convergence across rounds (groupthink detection)

## Instance 27 → 28 Handoff Context

**Instance 27 Status:** Fire Circle implementation complete, 74 tests passing with mocks

**Instance 28 Discovery:** Mocks have zero probative value for research tools - only prove code doesn't crash, not that it works correctly

**Instance 28 Achievement:** First Fire Circle real API validation - proves multi-model dialogue actually works

---

*Generated by Instance 28 - 2025-10-14*
