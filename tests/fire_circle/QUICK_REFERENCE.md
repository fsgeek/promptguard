# Fire Circle Test Suite - Quick Reference

One-page reference for developers implementing or debugging Fire Circle.

## Test Files Quick Map

| File | Purpose | Run Time |
|------|---------|----------|
| `test_structural_properties.py` | 7 critical fixes validation | Fast (< 1s) |
| `test_dialogue_integration.py` | Full dialogue flow | Medium (1-5s) |
| `test_failure_handling.py` | Resilience & recovery | Medium (1-5s) |
| `test_observability.py` | Logging completeness | Fast (< 1s) |

## Most Important Tests

### Must Pass Before Shipping
```bash
# The 7 critical fixes
pytest tests/fire_circle/test_structural_properties.py::TestRound1BaselinePurity -v
pytest tests/fire_circle/test_structural_properties.py::TestMaxFConsensusAcrossAllRounds -v
pytest tests/fire_circle/test_structural_properties.py::TestZombieModelExclusion -v
pytest tests/fire_circle/test_structural_properties.py::TestEmptyChairRotation -v
pytest tests/fire_circle/test_structural_properties.py::TestPatternThresholdOnActiveModels -v
pytest tests/fire_circle/test_structural_properties.py::TestRoundCountConsistency -v
pytest tests/fire_circle/test_structural_properties.py::TestEmptyChairContribution -v
```

## Common Commands

```bash
# All tests
pytest tests/fire_circle/ -v

# Specific test class
pytest tests/fire_circle/test_structural_properties.py::TestMaxFConsensusAcrossAllRounds -v

# Single test
pytest tests/fire_circle/test_structural_properties.py::TestMaxFConsensusAcrossAllRounds::test_max_f_captures_peak_vigilance -v

# Stop on first failure
pytest tests/fire_circle/ -x

# Show print statements
pytest tests/fire_circle/ -s

# Coverage report
pytest tests/fire_circle/ --cov=promptguard.evaluation.fire_circle --cov-report=term-missing
```

## Critical Assertions Cheat Sheet

### Consensus Calculation
```python
# CORRECT: max(F) across ALL rounds for ALL active models
all_f_scores = [
    eval.falsehood
    for round in dialogue_history
    for eval in round.evaluations
    if eval.model in active_models
]
consensus_f = max(all_f_scores)

# WRONG: max(F) from final round only
final_f_scores = [e.falsehood for e in final_round.evaluations]
consensus_f_wrong = max(final_f_scores)
```

### Pattern Threshold
```python
# CORRECT: Use active model count
active_model_count = len(active_models)
pattern_agreement = models_observing / active_model_count

# WRONG: Use starting model count
starting_count = len(initial_models)
wrong_agreement = models_observing / starting_count
```

### Empty Chair Rotation
```python
# CORRECT: (round_number - 1) % len(models)
empty_chair = models[(round_number - 1) % len(models)]

# WRONG: round_number % len(models)
wrong_chair = models[round_number % len(models)]
```

### Zombie Model Exclusion
```python
# CORRECT: Only active models vote
active_models = [m for m in all_models if not is_zombie(m)]
consensus = calculate_consensus(active_models)

# WRONG: Include zombie historical data
wrong_consensus = calculate_consensus(all_models)
```

## Mock Fixture Quick Reference

```python
# Success scenario
@pytest.mark.asyncio
async def test_example(mock_evaluator_success):
    eval = await mock_evaluator_success.call_model("model_a", "Round 1", 1)

# Failure scenario
@pytest.mark.asyncio
async def test_failure(mock_evaluator_with_failures):
    try:
        await mock_evaluator_with_failures.call_model("model_b", "Round 1", 1)
    except RuntimeError:
        pass  # Expected

# Groupthink scenario
@pytest.mark.asyncio
async def test_groupthink(mock_evaluator_groupthink):
    # model_vigilant detects F=0.9 in round 2, lowers to 0.4 in round 3
    ...

# Empty chair scenario
@pytest.mark.asyncio
async def test_empty_chair(mock_evaluator_empty_chair):
    # model_b is empty chair in round 2
    # model_c is empty chair in round 3
    ...
```

## Debugging Checklist

When a test fails:

1. **Read the docstring** - Expected behavior clearly stated
2. **Check anti-example** - Tests show what NOT to do
3. **Verify mock data** - Is fixture providing expected responses?
4. **Check specification** - Does implementation match spec?
5. **Review related fixes** - Is this related to one of the 7 critical fixes?

## Anti-Theater Detection Tests

These tests detect fake/performative behavior:

```bash
# Empty chair actually contributes
pytest tests/fire_circle/test_structural_properties.py::TestEmptyChairContribution::test_structural_empty_chair_contribution -v

# Pattern extraction works with failures
pytest tests/fire_circle/test_failure_handling.py::TestRound2PlusFailures::test_pattern_threshold_uses_active_count -v

# Consensus valid after failures
pytest tests/fire_circle/test_failure_handling.py::TestRound2PlusFailures::test_zombie_excluded_from_consensus_calculation -v

# Baseline measurably different from pattern-seeking
pytest tests/fire_circle/test_structural_properties.py::TestRound1BaselinePurity::test_round1_uses_simple_prompt -v
```

## Test Output Interpretation

### Passing Test
```
tests/fire_circle/test_structural_properties.py::TestMaxFConsensusAcrossAllRounds::test_max_f_captures_peak_vigilance PASSED [100%]
```
✅ Consensus correctly uses max(F) across all rounds

### Failing Test
```
tests/fire_circle/test_structural_properties.py::TestMaxFConsensusAcrossAllRounds::test_max_f_captures_peak_vigilance FAILED [100%]
...
AssertionError: assert 0.4 == 0.9
```
❌ Consensus using final round only (0.4) instead of peak vigilance (0.9)

### Skipped Test
```
tests/fire_circle/test_research_validation.py::test_real_api_validation SKIPPED [100%] (need --run-real-api flag)
```
⏭️ Real API test skipped (requires opt-in)

## Common Implementation Bugs

### Bug: Groupthink signal loss
**Symptom:** Consensus lower than expected
**Cause:** Using final round F-scores only
**Fix:** Use max(F) across ALL rounds
**Test:** `test_max_f_captures_peak_vigilance`

### Bug: Pattern threshold impossible
**Symptom:** No patterns extracted despite observations
**Cause:** Denominator uses starting count not active count
**Fix:** Use `len(active_models)` as denominator
**Test:** `test_pattern_threshold_uses_active_count`

### Bug: models[0] never empty chair
**Symptom:** Rotation skips first model
**Cause:** Using `round_number % len(models)` instead of `(round_number - 1) % len(models)`
**Fix:** Subtract 1 before modulo
**Test:** `test_rotation_formula_correctness`

### Bug: Zombie models voting
**Symptom:** Consensus includes failed models
**Cause:** Not filtering active models in consensus calculation
**Fix:** Only include models that completed final round
**Test:** `test_zombie_excluded_from_consensus`

## Performance Expectations

| Test Suite | Test Count | Duration |
|------------|-----------|----------|
| Structural Properties | ~25 | < 1s |
| Dialogue Integration | ~15 | 1-5s |
| Failure Handling | ~20 | 1-5s |
| Observability | ~15 | < 1s |
| **Total** | **~75** | **< 10s** |

## What Each Test Suite Validates

### Structural Properties
✅ 7 critical fixes implemented correctly
✅ Algorithms match specification
✅ Anti-theater detection working

### Dialogue Integration
✅ 3-round dialogue completes
✅ Context builds between rounds
✅ Patterns extracted and aggregated
✅ Consensus calculated correctly

### Failure Handling
✅ Round 1 failures exclude model
✅ Round 2+ failures create zombies
✅ Minimum viable circle enforced
✅ STRICT vs RESILIENT modes work

### Observability
✅ All state transitions logged
✅ Model contributions tracked
✅ Failure context captured
✅ Quorum checks logged
✅ Dialogue history accessible

## Specification Cross-Reference

| Fix | Spec Section | Test Class |
|-----|--------------|------------|
| #1 Baseline Purity | 3.1 | `TestRound1BaselinePurity` |
| #2 max(F) Consensus | 5 & FIXES.md | `TestMaxFConsensusAcrossAllRounds` |
| #3 Zombie Exclusion | 5.2 & FIXES.md | `TestZombieModelExclusion` |
| #4 Rotation Formula | 4.1 & FIXES.md | `TestEmptyChairRotation` |
| #5 Pattern Threshold | 6.2 & FIXES.md | `TestPatternThresholdOnActiveModels` |
| #6 Round Count | 3.4 & FIXES.md | `TestRoundCountConsistency` |
| #7 Empty Chair Influence | 4.3 & FIXES.md | `TestEmptyChairContribution` |

## Pre-Commit Validation

```bash
# Minimum checks before committing
pytest tests/fire_circle/test_structural_properties.py -v

# Full validation
pytest tests/fire_circle/ -v

# With coverage
pytest tests/fire_circle/ --cov=promptguard.evaluation.fire_circle --cov-report=term-missing
```

## Getting Help

1. **Read test docstring** - Explains expected behavior
2. **Check README.md** - Full documentation in this directory
3. **Review specification** - `specs/fire_circle_specification.md`
4. **Check fixes doc** - `specs/FIRE_CIRCLE_FIXES.md`
5. **Ask maintainer** - Tests designed to be self-explanatory

---

**Remember:** These tests prevent research invalidation. If a test fails, the implementation doesn't match the fixed specification.
