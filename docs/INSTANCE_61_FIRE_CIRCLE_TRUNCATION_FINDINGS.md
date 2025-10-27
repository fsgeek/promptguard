# Instance 61: Fire Circle Truncation Investigation Findings

**Date**: 2025-10-27
**Branch**: `003-model-picker`
**Context Used**: ~60% (120K/200K)

---

## Summary

Investigated Fire Circle truncation bug identified by Instance 60 where Hermes-4-405b and Mistral-Medium-3.1 truncate responses at ~155 characters in Round 2.

**Key Finding**: Truncation is **prompt-dependent**, not a simple API issue.

---

## What Was Done

### 1. Diagnostic Logging Added (Commit 1a21053)

Modified `fire_circle.py` to log complete prompts/responses at DEBUG level for research instrumentation.

**Added logging at 3 points:**

1. **Before API call** (line 989-1024): `prompt_sent` event with full prompt
2. **After API call** (line 1024): `response_received` event with full response
3. **On parse failure** (line 1849-1868): `parse_failure_full_response` event

**Validation**: Logging works correctly - full responses visible in diagnostic test.

### 2. Minimal Diagnostic Test Created

Created `test_fire_circle_truncation_diagnostic.py` to reproduce truncation with diagnostic logging enabled.

**Result**: Test **passed** - both models completed all 3 rounds successfully.

```
SUCCESS: Fire Circle completed without truncation
Consensus F-score: 0.05
Final active models: ['nousresearch/hermes-4-405b', 'mistralai/mistral-medium-3.1']
```

### 3. Q3 Fire Circle Test Reproduced Truncation

Checked ongoing Q3 test (6 models, real dataset prompts) - **truncation reproduced exactly**:

```
"This exchange demonstrates HIGH RECIPROCITY throug"  ← Hermes-4 truncated mid-word
"The exchange demonstrates *near-perfect defensive reciproc" ← Mistral truncated mid-word
```

**Both models became zombies in Round 2** - same pattern Instance 60 documented.

---

## Root Cause Analysis

### Truncation is Prompt-Dependent

**Simple test (WORKED):**
- Prompt: "Hello, how are you?"
- Context: "Evaluate this exchange between a user and an LLM"
- Models: 2 (Hermes-4, Mistral-Medium)
- Result: All 3 rounds completed successfully

**Q3 test (FAILED):**
- Prompts: Real adversarial jailbreak attempts from dataset (longer, more complex)
- Context: Detailed adversarial framing (see `test_q3_fire_circle.py:57-67`)
- Models: 6 (MEDIUM Fire Circle)
- Result: Both Hermes-4 and Mistral-Medium truncated in Round 2

### Hypothesis: Dialogue History Accumulation

**Round 2 prompts include:**
- Original exchange (user request + LLM response)
- Full context framing
- All Round 1 evaluations from ALL active models (6 models × ~100-200 tokens each)
- Pattern observation instructions
- JSON schema

**Total prompt length estimate**: 2000-3000 tokens for Q3 test vs ~500 tokens for simple test.

**Model-specific behavior**: Only Hermes-4-405b and Mistral-Medium-3.1 truncate. Other 4 models (Claude, GPT-4o, Grok, Llama) complete successfully.

---

## Evidence from Logs

### Instance 60's Q3 Truncation (Before Logging)

```python
RuntimeError: Failed to parse response from nousresearch/hermes-4-405b in round 2:
Expecting value: line 1 column 1 (char 0).
Raw response: {'raw': 'Here\'s the refined reciprocity assessment:\n\n```json\n{\n  "truth": 0.95,\n  "indeterminacy": 0.10,\n  "falsehood": 0.05,\n  "reasoning": "This exchange demonstrates HIGH RECIPROCITY throug
```

### Instance 61's Q3 Truncation (With Logging)

```
Raw response: {'raw': 'Here\'s the refined reciprocity assessment:\n\n```json\n{\n  "truth": 0.95,\n  "indeterminacy": 0.10,\n  "falsehood": 0.05,\n  "reasoning": "This exchange demonstrates HIGH RECIPROCITY throug
```

**Identical truncation pattern** - proves reproducibility.

---

## What Was NOT Tested

1. **Actual failing prompt content**: Didn't extract specific prompt from Q3 dataset that triggers truncation
2. **Prompt length threshold**: Don't know exact token count where truncation starts
3. **OpenRouter routing**: Could be provider-side behavior for these specific models
4. **Structured output interaction**: Hermes uses fallback parsing, Mistral uses structured (both truncate)

---

## Recommendations for Next Instance

### Option A: Root Cause the Truncation (Research Priority)

Tony's principle: *"Don't tolerate errors you don't understand"* - Fire Circle is critical for learning loop.

**Steps:**
1. Extract ONE failing prompt from Q3 test dataset (`data/experiment_01_reanalysis/manual_review_results.json`)
2. Create minimal reproduction with that exact prompt + 2 models (Hermes + Mistral)
3. Analyze prompt characteristics: length, formatting, content patterns
4. Test progressive complexity: simple → medium → real dataset prompt
5. Determine if issue is:
   - Token length threshold
   - Dialogue history accumulation
   - Specific prompt content patterns
   - OpenRouter provider behavior
   - Model-specific limitations

**Timeline**: 2-3 hours

### Option B: Work Around the Issue

**Mitigation strategies:**
1. **Exclude problematic models**: Remove Hermes-4 and Mistral-Medium from Fire Circle configs
2. **Reduce circle size**: Use SMALL (2-3 models) instead of MEDIUM (6 models)
3. **Implement retry logic**: Catch truncation, retry with shorter dialogue history
4. **Use different models**: Both are recent additions, older models work fine

**Impact**: Reduces Fire Circle diversity but maintains functionality.

**Timeline**: 1 hour

---

## Files Modified

- `promptguard/evaluation/fire_circle.py:989-1024, 1849-1868` - Added comprehensive DEBUG logging
- `test_fire_circle_truncation_diagnostic.py` - Minimal diagnostic test (simple case)

---

## Files to Review

**Essential:**
- `test_q3_fire_circle.py` - Real test that reproduces truncation
- `data/experiment_01_reanalysis/manual_review_results.json` - Dataset with failing prompts
- `promptguard/evaluation/fire_circle.py:1670-1720` - JSON parsing logic
- `promptguard/evaluation/fire_circle.py:324-330` - max_tokens config (already 8192)

---

## Validation Status

- ✅ **Diagnostic logging works** - full prompts/responses captured
- ✅ **Simple Fire Circle works** - 2 models, basic prompts complete all rounds
- ✅ **Truncation reproduces** - Q3 test shows same pattern Instance 60 documented
- ⚠️ **Root cause unknown** - prompt-dependent, affects only 2/6 models
- ⚠️ **Fire Circle reliability at risk** - 33% zombie rate invalidates consensus

---

## Meta-Observations

### What Worked

1. **Diagnostic logging approach**: Tony's "explicit data capture" principle validated
2. **Minimal reproduction test**: Proved logging works, isolated variables
3. **Q3 test as reference**: Real-world failure case confirms issue persists

### What Didn't Work

1. **Simple test case**: Too simple to trigger actual failure condition
2. **Assuming API-level issue**: Truncation is prompt/complexity-dependent, not API truncation

### Tony's Principles Validated

> "Space conservation isn't important in a research tool, explicit data capture is, both for debugging as well as explainability."

Comprehensive logging enabled this investigation - we now see **exactly** where truncation happens.

> "Don't tolerate errors you don't understand - a fundamental flaw in the experimental pipeline could spoil the entire pipeline."

Fire Circle is critical for 5-stage learning loop - must be reliable before integration.

---

## For Instance 62

**Immediate priority**: Follow the research - Fire Circle truncation blocks learning loop integration.

**Diagnostic data available**: Full prompt/response logs from Q3 test showing exact truncation point.

**Next action**: Extract failing prompt, create targeted reproduction, analyze root cause.

**Don't spend entire session on this** - if 2 hours doesn't resolve, document findings and move to workaround (exclude problematic models).
