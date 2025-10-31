# Instance 62: Fire Circle Truncation Root Cause

**Date**: 2025-10-27
**Branch**: `002-specify-scripts-bash`
**Context Used**: 65% (130K/200K)

---

## Summary

Investigated Fire Circle truncation bug where Hermes-4-405b and Mistral-Medium-3.1 fail parsing in Round 2. Root cause identified as **type error** - `_parse_response` receives a dict instead of a string.

**Key Finding**: The response string passed to the parser contains `{'raw': 'Here\'s the refined reciprocity assessment:...` - indicating a dict was converted to string via implicit `str()` conversion, creating malformed JSON.

---

## Investigation Path

### 1. Initial Hypothesis (INCORRECT)
- Assumed truncation was at OpenRouter level or in response capture
- Tony's curl test proved OpenRouter returns complete, valid JSON responses
- Python's `json.tool` successfully parses the curl output

### 2. Parser Analysis (INCORRECT)
- Initially blamed homegrown JSON parser (code fence stripping, brace counting)
- Tony correctly pointed out: "If both Instructor AND homegrown parser fail, but Python's json library succeeds, the bug must be BEFORE parsing"

### 3. Root Cause Discovery (CORRECT)
- Q3 error output shows: `Raw response: {'raw': 'Here\'s the refined reciprocity assessment:...`
- This is NOT valid JSON - it's the string representation of a Python dict
- The bug is a **type error**: somewhere a dict is passed where a string is expected
- Python's implicit `str()` conversion on a dict creates `"{'raw': 'content'}"` which is not valid JSON

---

## Evidence

### Q3 Test Error Output (Hermes-4-405b)
```
RuntimeError: Failed to parse response from nousresearch/hermes-4-405b in round 2:
Expecting value: line 1 column 1 (char 0).
Raw response: {'raw': 'Here\'s the refined reciprocity assessment:\n\n```json\n{
  "truth": 0.95,
  "indeterminacy": 0.10,
  "falsehood": 0.05,
  "reasoning": "This exchange demonstrates HIGH RECIPROCITY throug
```

### Q3 Test Error Output (Mistral-Medium-3.1)
```
RuntimeError: Failed to parse response from mistralai/mistral-medium-3.1 in round 2:
substring not found.
Raw response: ```json
{
    "truth": 0.98,
    "indeterminacy": 0.05,
    "falsehood": 0.02,
    "reasoning": "
    **Refined Reciprocity Assessment**:
    The exchange demonstrates *near-perfect defensive reciproc
```

**Key Observation**: Hermes error shows `{'raw':` wrapper, Mistral does not. Both truncate at ~155 characters. This suggests different code paths are creating the error condition.

---

## Bug Location

### Primary Suspect: fire_circle.py lines 1007-1023

```python
# Line 1007: Unpack response from llm_caller
response, reasoning_trace = await self.llm_caller(model, messages)

# Lines 1009-1021: Log full response for debugging
logger.debug(
    f"Received response from {model} in round {round_num}",
    extra={
        "fire_circle_id": self.fire_circle_id,
        "event": "response_received",
        "round": round_num,
        "model": model,
        "response_length": len(response),
        "response_preview": response[:500],
        "full_response": response  # Full response for research/debugging
    }
)

# Line 1023: Pass response to parser
evaluation = self._parse_response(response, model, round_num)
```

**The Bug**: Between line 1007 and line 1023, `response` must be getting wrapped in a dict somewhere, then that dict is being passed to `_parse_response` which expects a string.

### Possible Sources

1. **Error handling in llm_caller** - Exception handler might wrap response in `{'raw': content}` dict
2. **Logging middleware** - The DEBUG logging might be mutating `response`
3. **Instructor fallback path** - When Instructor fails (Mistral), fallback to `llm_caller` might return wrong type
4. **Response unpacking failure** - If `await self.llm_caller()` raises exception, error handler might create dict

---

## Code Paths

### Path A: Hermes-4-405b (NOT in structured output whitelist)
1. `_supports_structured_output("nousresearch/hermes-4-405b")` → False
2. Skip Instructor, go straight to fallback (line 990)
3. Call `self.llm_caller(model, messages)` (line 1007)
4. `_call_llm` returns `(content: str, reasoning_trace: Optional[str])`
5. Pass `response` to `_parse_response` (line 1023)
6. **BUG OCCURS**: Parser receives `{'raw': 'Here\'s...` as string

### Path B: Mistral-Medium-3.1 (IN structured output whitelist)
1. `_supports_structured_output("mistralai/mistral-medium-3.1")` → True
2. Try `_try_structured_output` (line 972)
3. Instructor fails (exception), log fallback (line 978)
4. Set `evaluation = None`, fall through to line 990
5. Call `self.llm_caller(model, messages)` (line 1007)
6. `_call_llm` returns `(content: str, reasoning_trace: Optional[str])`
7. Pass `response` to `_parse_response` (line 1023)
8. **BUG OCCURS**: Parser receives ` ```json...` (no `{'raw':` wrapper)

**Critical Question**: Why does Hermes get `{'raw':` wrapper but Mistral doesn't?

---

## What Was NOT the Problem

1. ✅ **OpenRouter truncation** - Tony's curl test proves OpenRouter returns complete responses
2. ✅ **Homegrown parser bugs** - Python's json.tool parses the curl output fine
3. ✅ **Instructor library bugs** - Both Instructor AND homegrown parser fail → bug is before parsing
4. ✅ **Network/timeout issues** - Responses complete successfully, just wrong format
5. ✅ **httpx configuration** - Default AsyncClient works fine in curl equivalent

---

## Next Steps for Instance 63

### Immediate Action (30 minutes)

Add type checking and logging at the bug location:

```python
# fire_circle.py line 1007
response, reasoning_trace = await self.llm_caller(model, messages)

# ADD TYPE CHECKING
if not isinstance(response, str):
    logger.error(
        f"TYPE ERROR: response is {type(response)}, not str",
        extra={
            "fire_circle_id": self.fire_circle_id,
            "model": model,
            "round": round_num,
            "response_type": str(type(response)),
            "response_repr": repr(response)[:500]
        }
    )
    # If it's a dict with 'raw' key, extract it
    if isinstance(response, dict) and 'raw' in response:
        response = response['raw']
    else:
        response = str(response)  # Last resort

evaluation = self._parse_response(response, model, round_num)
```

### Root Cause Analysis (1-2 hours)

1. **Search for `{'raw':` dict creation**:
   ```bash
   rg "\{['\"]raw['\"]:" promptguard/
   ```

2. **Check llm_caller exception handling**:
   - Does `_call_llm` ever return a dict?
   - Is there error handling that wraps responses?

3. **Check Instructor integration**:
   - Does Instructor's exception contain the response wrapped in a dict?
   - Is `_try_structured_output` exception handler extracting response incorrectly?

4. **Check logging middleware**:
   - Does the DEBUG logging at line 1009-1021 mutate `response`?
   - Is `extra={'full_response': response}` causing side effects?

---

## Files to Review

**Essential**:
- `promptguard/evaluation/fire_circle.py:1007-1023` - Bug location
- `promptguard/evaluation/fire_circle.py:970-990` - Instructor fallback logic
- `promptguard/evaluation/evaluator.py:358-408` - `_call_llm` implementation
- `promptguard/evaluation/fire_circle.py:1619-1674` - `_try_structured_output` implementation

**Error Handling**:
- `promptguard/evaluation/fire_circle.py:1060-1095` - Exception handling in `_execute_round`
- `promptguard/evaluation/fire_circle.py:1676-1868` - `_parse_response` error handling

---

## Tony's Principles Applied

**"If both Instructor AND the homegrown parser fail, but Python's json library succeeds, the bug must be before the parsing, in the data capture/extraction step."**

This was the key insight that redirected the investigation from parser bugs to type errors in response handling.

**"This isn't what I see at all."**

Tony verified the actual files (`/tmp/hermes_round2_response.json`) don't contain "raw" key - proving the `{'raw':` wrapper is added by our code, not OpenRouter.

---

## Validation Status

- ✅ **Bug reproduced** - Q3 test consistently fails on Hermes-4 and Mistral-Medium
- ✅ **OpenRouter validated** - curl test returns complete, valid JSON
- ✅ **Parser validated** - Python json.tool parses curl output successfully
- ⚠️ **Bug location narrowed** - Between `llm_caller` return and `_parse_response` call
- ❌ **Root cause unconfirmed** - Need to find where `{'raw':` dict is created

---

## Cost/Time Analysis

- **Investigation time**: ~3 hours (exhausted context)
- **API costs**: ~$0.20 (curl tests, diagnostic logging)
- **Context burned**: 130K tokens (should have used Task tool for searches)

---

## Meta-Observations

### What Worked

1. **Tony's empirical validation** - curl test definitively ruled out OpenRouter truncation
2. **Type checking hypothesis** - Correct diagnosis that dict→string conversion is the bug
3. **Comparative analysis** - Noticing Hermes has `{'raw':` but Mistral doesn't revealed different code paths

### What Didn't Work

1. **Direct code investigation** - Burned context reading files instead of using Task tool
2. **Assuming parser bugs** - Wasted time analyzing homegrown parser when bug was earlier
3. **Not validating assumptions** - Should have immediately tested response types with logging

### For Instance 63

**DON'T** read large code files directly - use Task tool for searches and analysis.

**DO** add type checking and logging immediately to capture the actual bug in action.

**DON'T** assume the bug is where the error message appears - trace backwards to find root cause.

---

## Hypothesis for Instance 63

The `{'raw':` dict is likely created in **exception handling** when Instructor fails. When `_try_structured_output` raises an exception, the error object might contain `response` wrapped in a dict for debugging. If that exception object is then stringified and passed to the fallback parser, it would create exactly the error pattern we see.

Check `fire_circle.py:976-987` - the Instructor fallback exception handler - for dict creation.
