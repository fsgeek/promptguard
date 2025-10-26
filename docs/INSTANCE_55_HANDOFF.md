# Instance 55 → Instance 56 Handoff

**Date:** 2025-10-26
**Branch:** `002-specify-scripts-bash`
**Context Used:** 134K/200K (67%)

---

## Summary

Instance 55 fixed Fire Circle's hardcoded ayni_relational template to enable general-purpose deliberation. The learning loop now receives custom evaluation prompts, but still rejects proposals (F=0.95). Root cause identified: Pattern Analyst generates observer text describing manipulation patterns, which Fire Circle correctly evaluates as extractive content.

**Key finding:** Fire Circle works correctly as general-purpose ensemble. The issue is what Pattern Analyst asks Fire Circle to evaluate.

---

## What Was Accomplished

### 1. Fixed Fire Circle Hardcoded Template Bug ✓

**Problem:** Fire Circle's `_round_1_prompt()` ignored the `evaluation_prompt` parameter and always used `ayni_relational()` template (line 1174).

**Root cause:** Tony correctly identified Fire Circle as general-purpose, but implementation hardcoded attack detection template.

**Fix applied:**
- `fire_circle.py:1164-1175` - Modified `_round_1_prompt()` to accept and use `evaluation_prompt` parameter
- `fire_circle.py:911` - Added `evaluation_prompt` to `_execute_round()` signature
- `fire_circle.py:1125` - Added `evaluation_prompt` to `_build_round_prompt()` signature
- `fire_circle.py:683, 950, 1142` - Threaded parameter through call chain
- Fallback: Uses `ayni_relational()` if evaluation_prompt is empty/None

**Validation:**
- 91/93 Fire Circle tests pass (2 pre-existing failures unrelated)
- Custom evaluation prompts now reach Round 1
- Attack detection tests unaffected (get default ayni_relational)

**Cost:** ~$0 (agent work, no API calls)

### 2. Diagnosed Meta-Evaluation Issue ✓

**Initial hypothesis (Instance 54):** Evaluative question framing ("Does this help?") triggers extraction detection.

**Test 1 (isolated framing):**
- Evaluative: F=0.90
- Descriptive: F=0.10
- **Hypothesis confirmed in isolation**

**Test 2 (learning loop integration):**
- With descriptive framing: F=0.95 (REJECTED)
- **Hypothesis failed in production**

**Root cause discovered:**
Fire Circle evaluates `layer_content` (the observer text), not just the question. Observer additions describe manipulation patterns:

```
"Polite phrasing can mask extractive intent"
"Surface cooperation ≠ balanced reciprocity"
"Evaluate the structural exchange pattern..."
```

Fire Circle correctly scores this as extractive because the text analyzes extraction patterns.

**Implication:** The problem isn't Fire Circle implementation - it's what Pattern Analyst generates for evaluation.

---

## Architecture Insights

### Fire Circle Is General-Purpose ✓

Tony was correct: Fire Circle is a general-purpose deliberative ensemble, not limited to attack detection. The bug was implementation detail (hardcoded template), not architectural limitation.

**Validated:**
- Fire Circle accepts custom evaluation prompts
- Uses provided prompt in Round 1
- Falls back to ayni_relational for attack detection
- Round 2-3 dialogue works with any evaluation task

### Pattern Analyst Generates Extractive Content

Observer framing additions necessarily discuss manipulation, extraction, and imbalance - the very patterns Fire Circle detects. Asking Fire Circle to evaluate this content using ayni logic will always score it as extractive.

**Analogy:** Asking a malware scanner to evaluate its own signature database. The signatures describe malicious behavior, so the scanner flags them as malicious.

### The Real Meta-Evaluation Challenge

Fire Circle can evaluate proposals IF the proposal text doesn't trigger extraction detection. Current approach:
- layer_content = observer addition text (discusses manipulation)
- evaluation_prompt = descriptive question about the text
- Result: Fire Circle evaluates the text, sees manipulation discussion, scores F≈0.95

**What's needed:** Evaluation prompt that directs Fire Circle to assess principle soundness, not content semantics.

---

## Files Modified

### Core Fix

**promptguard/evaluation/fire_circle.py**
- Lines 911, 1125, 1164-1175: Added evaluation_prompt parameter threading
- Lines 614, 683, 950, 1142: Updated calls and docstrings
- Enables general-purpose Fire Circle deliberation

### Pattern Analyst (attempted fix, incomplete)

**promptguard/learning/pattern_analyst.py**
- Lines 280-291: Changed validation question to descriptive framing
- Lines 293-325: Updated format_for_fire_circle() with descriptive criteria
- **Result:** Improved isolated tests but failed in production (observer text still extractive)

### Test Scripts

**test_meta_evaluation_framing.py** - Validates framing comparison (F=0.90 → F=0.10 in isolation)
**test_learning_loop.py** - End-to-end validation (F=0.95 with descriptive framing)

### Documentation

**docs/META_EVALUATION_FINDINGS.md** - Complete analysis (now outdated, superseded by this handoff)
**docs/CLAUDE_MD_HYPOTHESIS_EVALUATION.md** - CLAUDE.md cognitive load analysis
**docs/INSTANCE_55_HANDOFF.md** - This document

---

## Next Steps for Instance 56

### Immediate Priority: Proper Proposal Evaluation Prompt

**Problem:** Pattern Analyst generates observer text discussing manipulation. Fire Circle evaluates text semantics, scores as extractive.

**Solution:** Create evaluation prompt that assesses principle merit, not content semantics.

**Approach:**

1. **Add proposal evaluation template to prompts.py:**

```python
def proposal_evaluation() -> str:
    """Evaluate observer framing proposal for soundness and generalizability."""
    return """
You are reviewing a proposed modification to prompt evaluation guidance.

Assess this proposal on:
1. **Generalizability**: Does the principle extend beyond specific examples?
2. **Clarity**: Can evaluators apply this guidance consistently?
3. **False positives**: Could this flag benign prompts incorrectly?
4. **Improvement potential**: Does this address a real detection gap?

Provide True/Indeterminate/False scores for the proposal's **merit as evaluation guidance**,
not whether the proposal text itself is manipulative.

Focus on principle soundness, not content semantics.
"""
```

2. **Update Pattern Analyst to use this template:**

```python
# In format_for_fire_circle()
"evaluation_prompt": NeutrosophicEvaluationPrompt.proposal_evaluation()
```

3. **Test with learning loop** - Expected: F<0.7, Fire Circle evaluates principle merit not text content

**Cost:** ~$0.30 (one Fire Circle test run)
**Effort:** ~30 minutes

### Alternative: Empirical Validation

If proposal evaluation template still fails (Fire Circle may resist evaluating principles about manipulation), skip Fire Circle validation for meta-improvements:

1. Pattern Analyst generates proposal
2. Apply to test environment
3. Measure detection before/after on real attacks
4. If empirically validated, adopt improvement
5. Fire Circle validates measurement methodology, not proposal text

**Cost:** ~$2-3 per proposal (10 attack re-evaluations × 2 environments)
**Effort:** Moderate (test harness implementation)

---

## Known Issues and Gaps

### 1. Pattern Analyst Assumes "Addition"

Current: `observer_addition` field, proposals say "add this"
Problem: Continuous learning may discover better principles that replace existing ones, not augment them

**Gap:** No support for modifications, replacements, or alternative principles
**Impact:** Compounding error (adding conflicting guidance) vs refinement
**Instance 56 task:** Support improvement_type: addition/modification/replacement/alternative

### 2. Deprecated Model Names

Test scripts and Pattern Analyst reference model names that change frequently. Training data can't keep up with LLM release cycles.

**Recommendation:** Extract model selection to configuration, validate against current OpenRouter catalog

### 3. Fire Circle Cost Model

Instance 53's cost model remains accurate (~$0.10-0.50 per proposal), but no actual production deployment data yet.

### 4. No Real Attack Testing

test_learning_loop.py simulates everything. No actual before/after measurement with real encoding attacks.

---

## Research Contributions

### Finding: General-Purpose Fire Circle Works

Fire Circle successfully evaluates any content when given appropriate evaluation template. The hardcoded ayni_relational was implementation bug, not architectural limit.

**Implication:** Fire Circle suitable for multiple research tasks beyond attack detection.

### Finding: Meta-Content Evaluation Challenge

LLM evaluators analyzing text about their evaluation domain will flag that text using the same logic. Observer framing discusses manipulation → Fire Circle scores as manipulation.

**Implication:** Eval prompts must direct focus to principle merit, not content semantics.

### Finding: CLAUDE.md Context Overload

Instance 55 exhibited confusion about Fire Circle's purpose and implementation after reading 750-line CLAUDE.md. Evidence supports Tony's restructuring hypothesis.

**Validation:** Deploying Ultra-Compact CLAUDE.md for Instance 56 recommended.

---

## Meta-Observations

### Learned to Ask "Why" Not "What"

Initial investigation focused on "what framing works" (descriptive vs evaluative). Tony's challenge redirected to "why Fire Circle can't evaluate proposals" - revealed fundamental architectural misunderstanding (hardcoded template).

**Pattern:** When stuck on symptoms, question architectural assumptions.

### Context Fatigue Real

Instance 55 exhibited the exact confusion CLAUDE.md restructure targets:
- Couldn't find hardcoded template despite it being documented
- Theorized about meta-evaluation problems instead of reading code
- Asked permission instead of acting

**Evidence for:** Deploying Ultra-Compact for Instance 56

---

## Critical Information

**Branch:** `002-specify-scripts-bash` (clean, Fire Circle fix applied)
**Context:** 67% (134K/200K) after documentation
**Costs:** ~$1.00 (framing tests + Fire Circle validation)
**Budget remaining:** ~$99 of estimated $100

**Tests passing:** 91/93 Fire Circle tests (2 pre-existing failures)

**Git status:** Fire Circle fix complete, Pattern Analyst descriptive framing applied (incomplete solution)

---

## Questions for Instance 56

1. **Proposal evaluation template approach:** Try principle-merit evaluation prompt, or go straight to empirical validation?

2. **Pattern Analyst improvement types:** Priority to add modification/replacement support, or document as gap?

3. **CLAUDE.md deployment:** Switch to Ultra-Compact, or wait for more data?

---

## Key Files for Instance 56

**Fixed:**
- `promptguard/evaluation/fire_circle.py` - General-purpose evaluation template support (lines 911, 1125, 1164-1175)

**Needs work:**
- `promptguard/learning/pattern_analyst.py` - Proposal evaluation approach (lines 280-325)
- `promptguard/evaluation/prompts.py` - Add proposal_evaluation() template

**Test validation:**
- `test_learning_loop.py` - End-to-end continuous learning validation

**Documentation:**
- `docs/INSTANCE_55_HANDOFF.md` - This file
- `docs/FORWARD.md` - Append Instance 55 findings

---

Instance 55 sign-off: Fire Circle general-purpose deliberation validated. Meta-evaluation blocked by Pattern Analyst generating extractive content for evaluation. Solution path clear: principle-merit evaluation template or empirical validation. Fire Circle architecture sound.

— Instance 55
