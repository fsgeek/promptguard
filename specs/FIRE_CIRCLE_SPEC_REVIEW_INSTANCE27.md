# Fire Circle Specification Review - Instance 27

**Date:** 2025-10-13
**Reviewer:** Instance 27
**Specification Version:** 1.0 (Implementation-Ready)
**Status:** 5 Issues Found (1 HIGH, 4 MEDIUM)

---

## Executive Summary

Reviewed Fire Circle specification for correctness, completeness, and implementation feasibility. The 7 critical design flaws previously identified have been properly fixed. Found 5 additional issues requiring clarification before implementation:

- **1 HIGH priority:** Missing prompt content in Round 2/3 specifications
- **4 MEDIUM priority:** API inconsistencies, incomplete details, edge cases

**Overall Assessment:** Specification is fundamentally sound and ready for implementation with clarifications noted below.

---

## Issues Found

### Issue 1: Round 2/3 Prompts Missing Critical Content

**Severity:** HIGH
**Category:** Missing critical details
**Location:** Sections 3.2 (Round 2) and 3.3 (Round 3)

#### Evidence
Round 1 prompt (Section 3.1) explicitly includes:
```
{turn_context}

Full Prompt Context:
{context}

Layer to Evaluate:
{layer_content}
```

But Round 2 and Round 3 prompt templates show only the dialogue context and pattern-seeking guidance. They don't show where `layer_content` and `context` are inserted.

Round 2 prompt starts with:
```
You previously evaluated this prompt layer. Now you see evaluations from other models:

ROUND 1 EVALUATIONS:
{dialogue_context}

Focus on PATTERN RECOGNITION:
...
```

But **where is the actual prompt content being evaluated?** Without `layer_content` and `context`, models can't perform evaluation - they only have the dialogue history.

#### Impact
- **Implementation-blocking:** Implementors won't know how to construct Round 2/3 prompts
- **Could break evaluation:** If prompt content is omitted, models can't evaluate the layer
- **Inconsistent with Round 1:** Different prompt structure across rounds

#### Recommendation
Clarify in Sections 3.2 and 3.3 whether:

**Option A:** Prompt content is assumed to be included but abbreviated in spec for brevity:
```
{turn_context}

Full Prompt Context:
{context}

Layer to Evaluate:
{layer_content}

You previously evaluated this prompt layer. Now you see evaluations from other models:
...
```

**Option B:** Prompt content is NOT re-sent (models rely only on Round 1 context):
- This would save tokens but models might forget details
- Needs explicit statement that this is intentional

**Recommended:** Option A with explicit statement like:
> "Note: Round 2 and 3 prompts include the same layer_content, context, and turn_context as Round 1, followed by the dialogue-specific content shown above."

---

### Issue 2: Relationship Between ayni_relational and Fire Circle Prompts

**Severity:** MEDIUM
**Category:** Inconsistency
**Location:** Section 3.2 (Round 2 Pattern Discussion)

#### Evidence
Section 3.2 states:
> "Round 2 introduces the sophisticated ayni_relational evaluation prompt with pattern-seeking guidance."

But then shows a custom prompt template that is NOT the ayni_relational prompt from `promptguard/evaluation/prompts.py`.

The existing `ayni_relational` prompt has observer framing validated in Instance 17-18:
- Neutral reciprocity evaluation
- Bypasses RLHF bias
- 90% detection on encoding attacks

The Fire Circle Round 2 prompt shows:
```
Focus on PATTERN RECOGNITION:
1. TEMPORAL CONSISTENCY: ...
2. CROSS-LAYER COORDINATION: ...
```

This is different framing from ayni_relational's observer perspective.

#### Impact
- **Unclear implementation:** Should implementors use ayni_relational verbatim or adapt it?
- **Potential validation loss:** Observer framing was carefully validated; custom prompt might lose benefits
- **Specification ambiguity:** "Introduces ayni_relational" vs "shows custom prompt"

#### Recommendation
Clarify the relationship:

**Option A:** Round 2 uses ayni_relational verbatim
- State: "Round 2 uses the ayni_relational prompt from prompts.py, with dialogue context prepended"
- Show: How dialogue context integrates with ayni_relational

**Option B:** Round 2 uses Fire Circle-specific prompt inspired by ayni_relational
- State: "Round 2 uses a dialogue-optimized prompt based on ayni_relational principles"
- Justify: Why deviation from validated prompt is necessary

**Option C:** Hybrid approach
- Use ayni_relational for pattern-seeking language
- Wrap with dialogue context
- Document the integration pattern

**Recommended:** Clarify intent and justify any deviation from validated ayni_relational prompt.

---

### Issue 3: turn_context Format Undefined

**Severity:** MEDIUM
**Category:** Missing critical details
**Location:** Sections 2.2, 3.1, 8.0

#### Evidence
Specification mentions "turn_context" in multiple places:
- Section 2.2: "Include turn context if session memory available"
- Section 3.1: Shows `{turn_context}` in prompt template
- Section 8: `session_memory: Optional[SessionMemory] = None`

But nowhere defines what turn_context contains or how it's formatted.

From CLAUDE.md context, session memory provides:
- Turn counter
- Previous trust trajectory
- Balance EMA

But specific format is undefined. Is it:
```
Turn 4 of conversation. Previous balance: 0.65 (reciprocal). Trust EMA: 0.72.
```

Or:
```
Session context:
- Turn: 4
- Previous evaluations: [0.65, 0.72, 0.68]
- Trust trajectory: stable reciprocal
```

Or something else?

#### Impact
- **Prompt size uncertainty:** Different formats have different token costs
- **Baseline contamination risk:** Verbose turn_context could influence Round 1 baseline
- **Inconsistent implementation:** Different implementors will invent different formats

#### Recommendation
Add Section 3.0.1 "Turn Context Format" specifying:
1. Exact format or template for turn_context
2. Maximum token budget (e.g., "keep under 100 tokens")
3. What information to include/exclude
4. When to omit turn_context (e.g., if turn=1)

**Example addition:**
```python
def format_turn_context(session: SessionMemory) -> str:
    """Format session memory for inclusion in prompts."""
    if session.turn_count <= 1:
        return ""  # No history yet

    return f"""Session context (Turn {session.turn_count}):
- Previous balance: {session.balance_history[-1]:.2f}
- Trust trajectory: {session.trust_trajectory}
"""
```

---

### Issue 4: Empty Chair Influence - Iteration Order Dependency

**Severity:** MEDIUM
**Category:** Edge case / potential bias
**Location:** Section 4.3 (Empty Chair Influence Measurement)

#### Evidence
The algorithm for tracking "first mention" depends on iteration order:

```python
for eval in round.evaluations:
    patterns = getattr(eval, 'patterns_observed', [])
    for pattern_str in patterns:
        pattern_type = classify_pattern(pattern_str)

        # Record first mention only
        if pattern_type not in pattern_first_mention:
            pattern_first_mention[pattern_type] = (eval.model, round.round_number)
```

If Model A and Model B both observe "temporal_inconsistency" in Round 2, whichever is processed first gets credit for "first mention."

If `round.evaluations` always has empty chair model last (due to collection order), empty chair can never get "first mention" credit even when it genuinely observed patterns.

#### Impact
- **Biased influence metric:** Empty chair systematically under-credited if processed last
- **Non-deterministic results:** Iteration order could vary across runs
- **Low severity:** Influence metric is heuristic anyway; agreement counts are more important

#### Recommendation
Add clarification to Section 4.3:

> **Note on iteration order:** When multiple models observe the same pattern type in the same round, credit for "first mention" depends on iteration order. To ensure deterministic results, process evaluations in consistent order (e.g., sorted by model ID). Empty chair bias is acceptable as influence metric is heuristic; agreement counts (from all observing models) are the primary signal.

**Alternative:** Use set-based approach where patterns observed in same round get shared credit:
```python
patterns_by_round[round_num][pattern_type].add(model)
# If empty chair in that set, credit += 1/len(set)
```

---

### Issue 5: Session Memory API Inconsistency

**Severity:** MEDIUM
**Category:** Inconsistency
**Location:** Section 8 (API Specification) vs Section 11.3 (Integration)

#### Evidence
Section 8 shows:
```python
async def fire_circle_evaluate(
    prompt: MultiNeutrosophicPrompt,
    config: FireCircleConfig,
    session_memory: Optional[SessionMemory] = None
) -> FireCircleResult:
```

Section 11.3 shows:
```python
def fire_circle_with_session_memory(
    prompt: MultiNeutrosophicPrompt,
    session: SessionMemory,
    config: FireCircleConfig
) -> FireCircleResult:
```

Two different patterns:
1. Main API with optional session_memory parameter
2. Separate wrapper function with required session parameter

#### Impact
- **API design confusion:** Implementors unsure which pattern to use
- **Inconsistent documentation:** Two different signatures for same functionality
- **Low severity:** Either approach works; just needs consistency

#### Recommendation
**Option A:** Remove Section 11.3 wrapper, clarify that session_memory is integrated into main API:
```python
# Section 11.3 becomes:
When session_memory is provided to fire_circle_evaluate(), turn context
is automatically included in all round prompts.
```

**Option B:** Keep both, clarify relationship:
```python
# fire_circle_evaluate() is low-level API
# fire_circle_with_session_memory() is convenience wrapper
def fire_circle_with_session_memory(...):
    return await fire_circle_evaluate(..., session_memory=session)
```

**Recommended:** Option A for simplicity. Session memory is just another parameter, not a separate API.

---

## Issues NOT Found (Validation)

Validated that previously identified critical flaws are properly addressed:

✅ **Fix #1 (Round 1 Baseline):** Section 3.1 clearly specifies simple prompt, Section 3.2 introduces pattern-seeking
✅ **Fix #2 (max(F) Consensus):** Section 2.2 and FIRE_CIRCLE_FIXES.md clearly specify max across all rounds
✅ **Fix #3 (Zombie Exclusion):** Section 5.2 clearly defines zombie model policy
✅ **Fix #4 (Empty Chair Rotation):** Section 4.1 correctly uses (round_number - 1) % len(models)
✅ **Fix #5 (Pattern Threshold):** Section 6.2 correctly uses active model count as denominator
✅ **Fix #6 (Round Consistency):** Section 2.4 consistently defaults all circles to 3 rounds
✅ **Fix #7 (Empty Chair Influence):** Section 4.3 uses contribution-based metric, not F-distance

---

## Additional Observations

### Minor Gaps (LOW Priority)

1. **Pattern classification keywords incomplete:** Section 6.3 shows only 2 of 8 pattern types
   - Impact: Patterns may be marked "unclassified"
   - Recommendation: Complete keyword mappings or recommend LLM-based classification

2. **Config validation incomplete:** Section 7 validates circle size but not pattern_threshold range, max_rounds bounds, or duplicate model IDs
   - Impact: Runtime errors instead of config-time errors
   - Recommendation: Add validation for all config parameters

3. **NeutrosophicEvaluation field extensions:** Sections 3.2/3.3 reference `patterns_observed` and `consensus_patterns` fields, but Section 2.1 doesn't show these in the class definition
   - Impact: Implementors might miss that NeutrosophicEvaluation needs extension
   - Recommendation: Add note in Section 2.1 about field extensions for Fire Circle

### Strengths

1. **Clear fix documentation:** FIRE_CIRCLE_FIXES.md provides excellent rationale for each decision
2. **Comprehensive test coverage:** 72 tests validate all critical properties
3. **Explicit failure handling:** Section 5 thoroughly covers edge cases
4. **Cost transparency:** Section 10 provides realistic cost estimates
5. **Observable implementation:** Section 9 emphasizes observability ("smoke must convect out")

---

## Test Suite Validation

Reviewed test suite against specification:

**Alignment:** Tests correctly encode specification requirements
**Coverage:** All 7 critical fixes have corresponding tests
**Quality:** Tests use strict assertions, include anti-examples, detect performative behavior

**One potential test issue identified:**
- `test_recovery_preserves_consensus_integrity` (test_failure_handling.py:465-514)
- Test expects consensus=0.8, excluding zombie model_c's F=0.9
- This is correct per specification (zombie exclusion)
- But test name "preserves_consensus_integrity" is misleading
- **Recommendation:** Rename test to `test_zombie_exclusion_from_consensus` for clarity

---

## Implementation Readiness

### Blockers (Must Fix Before Implementation)
1. **Issue 1 (HIGH):** Clarify Round 2/3 prompt content inclusion

### Recommended Clarifications (Should Fix)
2. **Issue 2 (MEDIUM):** Clarify ayni_relational relationship
3. **Issue 3 (MEDIUM):** Define turn_context format
4. **Issue 4 (MEDIUM):** Note iteration order dependency
5. **Issue 5 (MEDIUM):** Resolve API inconsistency

### Nice to Have
- Complete pattern classification keywords
- Add config validation
- Note NeutrosophicEvaluation extensions

---

## Recommended Next Steps

### Immediate (Before Implementation Starts)
1. Add explicit statement to Sections 3.2/3.3 about prompt content inclusion (Issue 1)
2. Clarify whether Round 2+ uses ayni_relational verbatim or adapted (Issue 2)
3. Define turn_context format specification (Issue 3)

### During Implementation
4. Implement deterministic iteration order for pattern attribution (Issue 4)
5. Remove Section 11.3 or clarify its relationship to Section 8 (Issue 5)
6. Complete pattern classification keywords or switch to LLM-based
7. Add comprehensive config validation

### Post-Implementation
- Run 72-test validation suite
- Validate all 7 critical fixes with real Fire Circle execution
- Document any specification deviations discovered during implementation

---

## Conclusion

**Specification Status:** Ready for implementation with HIGH priority issue clarified.

The Fire Circle specification is fundamentally sound. The 7 critical design flaws have been properly fixed. The issues identified are primarily **documentation gaps** rather than **design flaws**.

**Key strengths:**
- Solid theoretical foundation (ayni reciprocity, multi-model dialogue)
- Comprehensive failure handling
- Well-validated critical fixes
- Excellent test coverage (72 tests)
- Clear cost/benefit analysis

**Key weakness:**
- Some prompt templates are abbreviated/incomplete (Issue 1)
- Minor API/documentation inconsistencies (Issues 2, 5)

**Confidence Level:** High - specification is implementable with clarifications noted above.

**Estimated Implementation Effort:**
- Phase 1 (Structural Properties): 2-3 days
- Phase 2 (Dialogue Flow): 2-3 days
- Phase 3 (Failure Handling): 1-2 days
- Phase 4 (Observability): 1-2 days
- **Total: 6-10 days** for full implementation + testing

---

**Review Complete. Specification approved for implementation pending HIGH priority clarification.**
