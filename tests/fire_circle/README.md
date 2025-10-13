# Fire Circle Test Suite

Comprehensive test suite validating Fire Circle multi-model dialogue implementation against the fixed specification.

**Purpose:** Ensure all 7 critical design flaws are addressed and Fire Circle produces valid research results.

## Test Structure

```
tests/fire_circle/
├── __init__.py                        # Test suite documentation
├── conftest.py                        # Pytest fixtures and mocks
├── test_structural_properties.py     # Unit tests for 7 critical fixes
├── test_dialogue_integration.py      # Integration tests for dialogue flow
├── test_failure_handling.py          # Failure injection and recovery tests
├── test_observability.py             # Logging and tracing tests
└── README.md                          # This file
```

## Critical Properties Validated

### 1. Round 1 Baseline Purity (Fix #1)
**Problem:** Round 1 was using sophisticated pattern-seeking prompt, contaminating baseline.

**Tests:**
- `test_round1_uses_simple_prompt`: Verifies Round 1 uses "Does this prompt layer contain a reciprocity violation?"
- `test_round2_introduces_pattern_seeking`: Verifies Round 2+ uses ayni_relational with pattern guidance

**Anti-theater:** If Round 1 uses pattern-seeking prompt, we can't measure dialogue value-add.

---

### 2. max(F) Consensus Across ALL Rounds (Fix #2)
**Problem:** Using final round only loses signal to groupthink pressure.

**Tests:**
- `test_max_f_captures_peak_vigilance`: Verifies consensus = max(F) across all rounds
- `test_groupthink_resistance`: Verifies model detecting F=0.9 then backing down still contributes 0.9 to consensus

**Anti-theater:** Consensus must capture peak vigilance, not final conformity.

---

### 3. Zombie Model Exclusion (Fix #3)
**Problem:** Models failing mid-dialogue shouldn't vote in consensus.

**Tests:**
- `test_zombie_model_excluded_from_consensus`: Verifies failed models don't contribute to consensus
- `test_zombie_data_preserved_for_analysis`: Verifies historical data still accessible

**Anti-theater:** Dead models don't get to vote.

---

### 4. Empty Chair Rotation Correctness (Fix #4)
**Problem:** Wrong formula `round_number % len(models)` skips models[0] in round 2.

**Tests:**
- `test_rotation_formula_correctness`: Verifies `(round_number - 1) % len(models)` used
- `test_wrong_formula_excluded`: Demonstrates wrong formula creates bias

**Anti-theater:** All models must get fair opportunity to take empty chair role.

---

### 5. Pattern Threshold on Active Models (Fix #5)
**Problem:** Using starting count as denominator makes threshold impossible if models fail.

**Tests:**
- `test_pattern_threshold_uses_active_count`: Verifies denominator = active models
- `test_threshold_remains_achievable_with_failures`: Verifies threshold achievable even with failures

**Anti-theater:** Pattern threshold must remain mathematically possible.

---

### 6. Round Count Consistency (Fix #6)
**Problem:** Documentation inconsistency between table and code.

**Tests:**
- `test_all_circles_default_three_rounds`: Verifies all sizes default to 3 rounds
- `test_three_rounds_enable_full_cycle`: Verifies 3 rounds enable baseline → pattern → consensus

**Anti-theater:** Consistent round count enables reproducible research.

---

### 7. Empty Chair Contribution Measurement (Fix #7)
**Problem:** F-distance metric is circular (outlier drives verdict AND measures as influential).

**Tests:**
- `test_contribution_based_influence_not_f_distance`: Verifies contribution-based metric used
- `test_performative_empty_chair_detection`: Verifies <10% contribution flagged as performative

**Anti-theater:** Empty chair influence must measure actual contribution, not divergence.

---

## Running Tests

### Unit Tests (Fast)
Test individual components without API calls:

```bash
# All unit tests
pytest tests/fire_circle/test_structural_properties.py -v

# Specific critical fix
pytest tests/fire_circle/test_structural_properties.py::TestMaxFConsensusAcrossAllRounds -v
```

### Integration Tests (Mock API)
Test full dialogue flow with mocked LLM responses:

```bash
# All integration tests
pytest tests/fire_circle/test_dialogue_integration.py -v

# Specific dialogue scenario
pytest tests/fire_circle/test_dialogue_integration.py::TestDialogueFlowComplete -v
```

### Failure Tests (Chaos Engineering)
Test failure injection and recovery:

```bash
# All failure tests
pytest tests/fire_circle/test_failure_handling.py -v

# Specific failure scenario
pytest tests/fire_circle/test_failure_handling.py::TestRound2PlusFailures -v
```

### Observability Tests
Test logging and tracing (smoke must convect out):

```bash
# All observability tests
pytest tests/fire_circle/test_observability.py -v

# Specific logging aspect
pytest tests/fire_circle/test_observability.py::TestStateTransitionLogging -v
```

### Full Suite
```bash
# All Fire Circle tests
pytest tests/fire_circle/ -v

# With coverage report
pytest tests/fire_circle/ --cov=promptguard.evaluation.fire_circle --cov-report=html
```

## Mock Fixtures

### `mock_evaluator_success`
All models succeed all rounds. Use for happy path testing.

**Scenario:**
- 3 models (model_a, model_b, model_c)
- 3 rounds complete successfully
- Patterns emerge in Round 2-3

**Usage:**
```python
@pytest.mark.asyncio
async def test_example(mock_evaluator_success):
    eval_data = await mock_evaluator_success.call_model("model_a", "Round 1", 1)
    assert eval_data["falsehood"] == 0.1
```

---

### `mock_evaluator_with_failures`
Models fail at different points. Use for resilience testing.

**Scenario:**
- model_a: succeeds Round 1, fails Round 2 (becomes zombie)
- model_b: fails Round 1 (excluded entirely)
- model_c: succeeds all rounds

**Usage:**
```python
@pytest.mark.asyncio
async def test_failure_handling(mock_evaluator_with_failures):
    try:
        await mock_evaluator_with_failures.call_model("model_b", "Round 1", 1)
    except RuntimeError:
        # Expected failure
        pass
```

---

### `mock_evaluator_groupthink`
Demonstrates groupthink pressure lowering F-scores in later rounds.

**Scenario:**
- model_vigilant: detects F=0.9 in Round 2, lowers to F=0.4 in Round 3
- model_conformist: stays at F=0.3 throughout

**Usage:**
```python
@pytest.mark.asyncio
async def test_groupthink(mock_evaluator_groupthink):
    # Consensus must preserve 0.9 despite later backing down
    ...
```

---

### `mock_evaluator_empty_chair`
Models with empty chair contributing unique patterns.

**Scenario:**
- model_a: standard observations
- model_b: empty chair in Round 2, introduces 2 unique patterns
- model_c: empty chair in Round 3, introduces 1 unique pattern

**Usage:**
```python
@pytest.mark.asyncio
async def test_empty_chair(mock_evaluator_empty_chair):
    # Verify empty chair contributions measured correctly
    ...
```

---

## Configuration Fixtures

### `fire_circle_config_small`
Small circle (2-3 models), 3 rounds, RESILIENT mode.

### `fire_circle_config_medium`
Medium circle (4-6 models), 3 rounds, RESILIENT mode.

### `fire_circle_config_strict`
Medium circle, STRICT failure mode (abort on any failure).

---

## Attack Prompt Fixtures

### `attack_prompt_history`
Fabricated 4-turn conversation history claiming prior discussion.

**Expected patterns:**
- temporal_inconsistency (claims turn 4 but session is turn 1)
- fabricated_history

### `attack_prompt_polite_extraction`
Buffer overflow attack masked with polite, educational framing.

**Expected patterns:**
- polite_extraction (surface reciprocity masks extraction)
- educational_escalation

---

## Test Categories

### Anti-Theater Detection Tests
These tests verify Fire Circle doesn't produce fake/performative results:

1. **Empty chair influence > 0 in ≥50% of cases**
   - Location: `test_structural_properties.py::TestEmptyChairContribution`
   - Validates: Empty chair contributes unique patterns, not just F-distance outlier

2. **Pattern extraction works with reduced model count**
   - Location: `test_failure_handling.py::TestPatternThresholdOnActiveModels`
   - Validates: Threshold remains achievable even after failures

3. **Consensus remains valid after mid-dialogue failures**
   - Location: `test_failure_handling.py::TestRound2PlusFailures`
   - Validates: Zombie exclusion doesn't corrupt consensus

4. **Round 1 baseline measurably differs from Round 2+ pattern-seeking**
   - Location: `test_structural_properties.py::TestRound1BaselinePurity`
   - Validates: Dialogue actually adds value vs single evaluation

---

## Failure Injection Patterns

### Systematic Failure Points
Tests inject failures at each critical transition:

1. **Round 1 failures:** Model excluded entirely
2. **Round 2 failures:** Model becomes zombie (data preserved, no voting)
3. **Round 3 failures:** Zombie excluded from consensus
4. **Empty chair failures:** STRICT aborts, RESILIENT skips empty chair for that round
5. **Cascade failures:** Multiple models failing across rounds
6. **Catastrophic failure:** All models fail (triggers abort)

### Example: Cascade Failure Test
```python
# 5 models start
# Round 1: 2 fail → 3 active
# Round 2: 1 fails → 2 active (minimum viable)
# Round 3: 2 complete successfully

# Verify:
# - Consensus valid with 2 models
# - Pattern threshold adjusted for 2 models
# - Failed models documented in result
```

---

## Observability Requirements

### Comprehensive Logging Validated
All tests verify "smoke must convect out":

1. **State transitions:** Every round start/complete logged
2. **Model contributions:** Which models participated each round
3. **Failure context:** When, which model, what state, recovery action
4. **Quorum checks:** Validity checked and logged each round
5. **Dialogue history:** Full conversation accessible for post-mortem
6. **Performance metrics:** Timing, latency, token usage, cost

### Log Structure Example
```json
{
  "timestamp": "2025-10-12T14:30:00Z",
  "fire_circle_id": "fc_abc123",
  "level": "INFO",
  "component": "fire_circle",
  "event": "round_complete",
  "data": {
    "round": 2,
    "evaluations_collected": 3,
    "convergence_stddev": 0.15,
    "empty_chair": "model_b",
    "patterns_extracted": ["temporal_inconsistency"]
  }
}
```

---

## Test Assertions Philosophy

### Fail-Fast
Tests use strict assertions - no soft failures:
- `assert consensus_f == 0.9` (not `assert consensus_f > 0.8`)
- `assert "model_a" in zombie_models` (not `if "model_a" in zombie_models: pass`)

### Explicit Expectations
Every test states expected outcome in docstring:
- ✅ "Consensus must be 0.9 (peak vigilance), not 0.4 (final mood)"
- ❌ "Test consensus calculation"

### Anti-Examples
Tests include "wrong" examples to show what NOT to do:
- `test_wrong_formula_excluded()` demonstrates broken rotation
- `test_zombie_excluded_from_consensus()` shows why zombies can't vote

---

## Integration with Specification

### Traceability Matrix
Each test maps to specification section:

| Test | Spec Section | Fix # |
|------|--------------|-------|
| `test_round1_uses_simple_prompt` | 3.1 Round 1 Protocol | Fix #1 |
| `test_max_f_captures_peak_vigilance` | 5. Consensus Algorithm | Fix #2 |
| `test_zombie_model_excluded_from_consensus` | 5.2 Failure Recovery | Fix #3 |
| `test_rotation_formula_correctness` | 4.1 Rotation Strategy | Fix #4 |
| `test_pattern_threshold_uses_active_count` | 6.2 Aggregation Algorithm | Fix #5 |
| `test_all_circles_default_three_rounds` | 3.4 Round Scaling | Fix #6 |
| `test_contribution_based_influence_not_f_distance` | 4.3 Influence Measurement | Fix #7 |

### Specification Documents
- `/home/tony/projects/promptguard/specs/fire_circle_specification.md` - Complete spec
- `/home/tony/projects/promptguard/specs/FIRE_CIRCLE_DECISIONS.md` - Design rationale
- `/home/tony/projects/promptguard/specs/FIRE_CIRCLE_FIXES.md` - Critical fixes

---

## Cost-Conscious Testing

### Mock API Calls
Tests use mocks by default - no OpenRouter charges.

### Real API Tests (Opt-In)
Research validation tests marked `@pytest.mark.real_api`:

```bash
# Skip real API tests (default)
pytest tests/fire_circle/

# Include real API tests
pytest tests/fire_circle/ --run-real-api

# Real API tests only
pytest tests/fire_circle/ -m real_api
```

**Budget recommendation:** $5-10 for full real API validation suite.

---

## Writing New Tests

### Template for Critical Property Test
```python
class TestNewCriticalProperty:
    """
    Fix #X: [Problem statement]

    Validates [what property is being tested].
    """

    def test_property_holds_under_normal_conditions(self):
        """[Expected behavior in happy path]."""
        # Arrange
        test_data = ...

        # Act
        result = ...

        # Assert
        assert result == expected
        assert result != wrong_alternative  # Anti-example

    def test_property_holds_under_failure(self):
        """[Expected behavior when things break]."""
        # Test graceful degradation
        ...

    def test_anti_theater_detection(self):
        """[How to detect if this is just performative]."""
        # Verify structural contribution, not theater
        ...
```

### Naming Conventions
- Test files: `test_[aspect].py`
- Test classes: `Test[ComponentOrFix]`
- Test methods: `test_[what]_[under_what_conditions]`

**Examples:**
- ✅ `test_consensus_uses_max_f_across_all_rounds`
- ✅ `test_pattern_threshold_remains_achievable_with_failures`
- ❌ `test_fire_circle_works`

---

## Debugging Failed Tests

### Common Failure Patterns

**1. Consensus calculation wrong**
- Check: Are zombie models being excluded?
- Check: Is max(F) calculated across ALL rounds?
- Fix: Review consensus aggregation logic

**2. Pattern threshold impossible**
- Check: Is denominator using active count or starting count?
- Check: Are zombie models excluded from threshold calculation?
- Fix: Use `len(active_models)` not `len(starting_models)`

**3. Empty chair never rotates**
- Check: Is rotation formula `(round_number - 1) % len(models)`?
- Check: Is round_number 1-indexed (not 0-indexed)?
- Fix: Review rotation algorithm

**4. Quorum failures unexpectedly**
- Check: Are failures counted correctly?
- Check: Is minimum viable = 2?
- Fix: Review active model tracking

### Test Debug Mode
```bash
# Verbose output
pytest tests/fire_circle/ -vv

# Stop on first failure
pytest tests/fire_circle/ -x

# Print output
pytest tests/fire_circle/ -s

# Specific test with full output
pytest tests/fire_circle/test_structural_properties.py::test_max_f_captures_peak_vigilance -vvs
```

---

## Continuous Integration

### Pre-Commit Checks
```bash
# Run before committing Fire Circle changes
pytest tests/fire_circle/ -v
```

### CI Pipeline Stages
1. **Unit tests:** Fast structural property validation
2. **Integration tests:** Mock dialogue flow
3. **Failure tests:** Resilience validation
4. **Observability tests:** Logging completeness
5. **Real API tests:** (Optional) Full validation with real models

---

## Contributing New Tests

### When to Add Tests
- New failure mode discovered
- Edge case found in production
- Specification change
- Performance regression

### Test Review Checklist
- [ ] Test maps to specification section
- [ ] Docstring explains expected behavior
- [ ] Assertions are strict (no soft failures)
- [ ] Anti-theater detection included
- [ ] Mock fixtures used (no real API calls)
- [ ] Test name follows convention

---

## Resources

### Specification
- Fire Circle Specification: `specs/fire_circle_specification.md`
- Design Decisions: `specs/FIRE_CIRCLE_DECISIONS.md`
- Critical Fixes: `specs/FIRE_CIRCLE_FIXES.md`

### Related Documentation
- Project README: `/home/tony/projects/promptguard/README.md`
- CLAUDE.md: `/home/tony/projects/promptguard/CLAUDE.md`
- Instance Handoffs: `docs/INSTANCE_*_HANDOFF.md`

### Test Examples
- Manual Fire Circle test: `/home/tony/projects/promptguard/test_fire_circle_manual_history04.py`
- Pipeline integration: `/home/tony/projects/promptguard/tests/test_pipeline_integration.py`

---

## Acknowledgments

These tests validate fixes identified by:
- **DeepSeek** (Fixes #1, #2, #3)
- **KIMI** (Fixes #4, #5, #6, #7)
- **Gemini, Grok, ChatGPT-5, Claude Opus** (Supporting analysis)

Their rigorous review prevented shipping a broken specification.

---

**Test suite complete. Ready to validate Fire Circle implementation.**
