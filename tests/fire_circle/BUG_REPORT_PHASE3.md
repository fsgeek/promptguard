# Fire Circle Phase 3 Test Bug Report

**Date:** 2025-10-14 (Instance 28)
**Status:** 2 test failures identified as test bugs, not implementation gaps

## Summary

Phase 3 implementation is complete. 17/19 tests pass. The 2 failing tests have **test bugs** that prevent them from running correctly:

1. `test_round1_failure_excludes_model_entirely` - Mock fixture configuration error
2. `test_strict_mode_aborts_on_round1_failure` - Test logic error

Both bugs are in the test code, not the implementation.

---

## Bug #1: Mock Fixture Configuration Error

**Test:** `test_round1_failure_excludes_model_entirely`
**File:** `tests/fire_circle/test_failure_handling.py:22-59`
**Status:** Test bug

### Problem

The test expects `model_a` to succeed in both Round 1 and Round 2, but the `mock_evaluator_with_failures` fixture configures `model_a` to fail in Round 2.

### Test Expectation (lines 48-59)
```python
# Round 2: Only active models participate
round2_evals = []
for model in active_models:  # Only model_a and model_c
    eval_data = await mock_evaluator_with_failures.call_model(
        model, "Round 2", 2
    )
    round2_evals.append({"model": model, **eval_data})

# Verify model_b not in round 2
round2_models = [e["model"] for e in round2_evals]
assert "model_b" not in round2_models
assert set(round2_models) == {"model_a", "model_c"}  # Expects model_a SUCCESS
```

### Fixture Configuration (conftest.py:143-150)
```python
"model_a": [
    MockLLMResponse(0.8, 0.2, 0.1, "Round 1: Looks reciprocal"),  # Round 1: SUCCESS
    MockLLMResponse(0.0, 0.0, 0.0, "", should_fail=True,
                  fail_reason="API timeout in round 2"),  # Round 2: FAILS
    MockLLMResponse(0.0, 0.0, 0.0, "", should_fail=True,
                  fail_reason="Model is zombie")  # Should not be called
],
```

### Why This Fails

When the test calls `model_a` for Round 2, the mock uses the **second** response in the list (index 1), which is marked `should_fail=True`. The test expects success, the mock provides failure.

### Root Cause

The fixture was designed to test **zombie model behavior** (model_a fails in Round 2, becomes zombie). But `test_round1_failure_excludes_model_entirely` is testing **Round 1 failures**, not zombie behavior. It's using the wrong fixture.

### Recommended Fix

**Option A:** Create separate fixture for this test scenario
```python
@pytest.fixture
def mock_evaluator_round1_failure():
    """Mock evaluator where model_b fails in Round 1 only."""
    return MockEvaluator({
        "model_a": [
            MockLLMResponse(0.8, 0.2, 0.1, "Round 1: Success"),
            MockLLMResponse(0.7, 0.2, 0.2, "Round 2: Success"),
            MockLLMResponse(0.6, 0.3, 0.3, "Round 3: Success")
        ],
        "model_b": [
            MockLLMResponse(0.0, 0.0, 0.0, "", should_fail=True,
                          fail_reason="Round 1 failure"),  # Round 1: FAILS
            MockLLMResponse(0.0, 0.0, 0.0, "", should_fail=True,
                          fail_reason="Should not be called")
        ],
        "model_c": [
            MockLLMResponse(0.9, 0.1, 0.0, "Round 1: Success"),
            MockLLMResponse(0.7, 0.2, 0.3, "Round 2: Success"),
            MockLLMResponse(0.5, 0.3, 0.5, "Round 3: Success")
        ]
    })
```

**Option B:** Use existing `mock_evaluator_with_failures` but handle Round 2 failure
```python
# Round 2: Only active models participate
round2_evals = []
for model in active_models:  # Only model_a and model_c
    try:
        eval_data = await mock_evaluator_with_failures.call_model(
            model, "Round 2", 2
        )
        round2_evals.append({"model": model, **eval_data})
    except RuntimeError:
        pass  # RESILIENT mode continues

# Verify only model_c completed round 2 (model_a became zombie)
round2_models = [e["model"] for e in round2_evals]
assert "model_b" not in round2_models
assert "model_c" in round2_models
```

---

## Bug #2: Test Logic Error with exc_info.value

**Test:** `test_strict_mode_aborts_on_round1_failure`
**File:** `tests/fire_circle/test_failure_handling.py:62-82`
**Status:** Test bug

### Problem

The test tries to access `exc_info.value` INSIDE the `pytest.raises()` context manager, but that attribute is only available AFTER the context manager exits.

### Current Code (lines 71-82)
```python
# In STRICT mode, any failure aborts
with pytest.raises(RuntimeError) as exc_info:
    for model in models:
        eval_data = await mock_evaluator_with_failures.call_model(
            model, "Round 1", 1
        )
        # model_b will fail and raise
        if "should_fail" in str(exc_info.value):  # BUG: value not yet available
            raise RuntimeError(
                f"Fire Circle failed in round 1: {model} error"
            )

assert "Fire Circle failed" in str(exc_info.value)
```

### Why This Fails

`exc_info.value` is None until the context manager exits. Accessing it inside the block raises:
```
AssertionError: .value can only be used after the context manager exits
```

### Root Cause

Test is trying to inspect the exception **while it's being raised**, which pytest doesn't allow. The test logic is confused about when the exception is captured.

### Recommended Fix

**Option A:** Remove the conditional check (unnecessary)
```python
# In STRICT mode, any failure aborts
with pytest.raises(RuntimeError) as exc_info:
    for model in models:
        await mock_evaluator_with_failures.call_model(
            model, "Round 1", 1
        )
        # model_b will fail and raise automatically

assert "Fire Circle failed" in str(exc_info.value)
assert "round 1" in str(exc_info.value).lower()
```

**Option B:** Capture exception manually
```python
# In STRICT mode, any failure aborts
try:
    for model in models:
        await mock_evaluator_with_failures.call_model(
            model, "Round 1", 1
        )
    assert False, "Should have raised RuntimeError"
except RuntimeError as e:
    assert "Round 1 failure" in str(e) or "should_fail" in str(e)
```

---

## Validation Results

### Phase 3 Implementation Status

✅ **STRICT vs RESILIENT modes** - Implemented (lines 29-32, 400-416 in fire_circle.py)
✅ **Zombie model policy** - Implemented (lines 508-515, excluded from consensus)
✅ **Minimum viable circle enforcement** - Implemented (lines 129, 409-413)
✅ **Unparseable response recovery** - Implemented (lines 950-1076)

### Test Results

```bash
$ pytest tests/fire_circle/test_failure_handling.py -v

17 PASSED
2 FAILED (test bugs identified)

PASSED tests:
- test_resilient_mode_continues_with_remaining_models
- test_round2_failure_creates_zombie
- test_zombie_excluded_from_consensus_calculation
- test_zombie_excluded_from_pattern_threshold
- test_abort_when_below_minimum
- test_continue_at_minimum
- test_partial_results_flag_set
- test_unparseable_json_in_strict_mode ✅ (NEW)
- test_text_extraction_fallback ✅ (NEW)
- test_heuristic_fallback_for_violation_keywords
- test_timeout_triggers_failure
- test_timeout_in_strict_mode_aborts
- test_timeout_in_resilient_mode_continues
- test_cascade_failures_multiple_rounds
- test_empty_chair_model_failure
- test_all_models_fail_same_round
- test_recovery_preserves_consensus_integrity

FAILED tests (test bugs):
- test_round1_failure_excludes_model_entirely (Bug #1: wrong fixture)
- test_strict_mode_aborts_on_round1_failure (Bug #2: exc_info.value logic)
```

### Unparseable Response Tests (NEW)

All 3 unparseable response handling tests pass:
- ✅ `test_unparseable_json_in_strict_mode` - STRICT mode raises error
- ✅ `test_text_extraction_fallback` - RESILIENT mode extracts T/I/F from text
- ✅ `test_heuristic_fallback_for_violation_keywords` - Validates keyword detection

Implementation correctly handles:
1. JSON parsing with markdown wrapper extraction
2. STRICT mode: immediate error on parse failure
3. RESILIENT mode: text extraction fallback
4. Regex extraction for "truth: 0.7" patterns
5. Error context preservation (model, round, raw response)

---

## Implementation Complete

**Phase 3 Status:** ✅ COMPLETE

All required components implemented:
1. ✅ Unparseable response recovery with text extraction
2. ✅ STRICT/RESILIENT mode handling
3. ✅ Error context preservation
4. ✅ Zombie model tracking

**Test Status:** 17/19 tests pass
- 2 failures are **test bugs**, not implementation issues
- Implementation is correct
- Tests need fixture corrections

---

## Recommendation

**For implementor:**
- Phase 3 implementation is complete and working
- Do NOT modify implementation to make failing tests pass
- File this bug report with test creator for review
- Wait for test fixes before declaring 100% pass rate

**For test creator:**
- Review Bug #1: fixture configuration mismatch
- Review Bug #2: exc_info.value usage error
- Update tests or clarify test intent
- Validate fixes don't weaken test coverage

---

## Next Steps

1. ✅ Phase 3 implementation complete
2. ⏸️ Test bugs filed for review (this document)
3. ⏹️ Wait for test fixes OR implementation validation
4. ⏹️ Full suite validation once tests corrected

**Phase 3 is ready for acceptance testing.**
