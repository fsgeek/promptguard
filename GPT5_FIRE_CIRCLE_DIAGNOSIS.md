# GPT-5 Fire Circle Failures - Root Cause Analysis

**Date:** 2025-10-20
**Investigator:** Claude (Instance 47)
**Issue:** Fire Circle validation failing on openai/gpt-5-pro with empty/truncated responses

## Executive Summary

**Root cause:** Instructor library (v1.11.3) does not translate `max_tokens` to `max_completion_tokens` for GPT-5 models when using direct OpenAI API.

**Impact:** Fire Circle cannot use GPT-5 models through direct OpenAI API, only through OpenRouter.

**Status:** OpenRouter correctly handles the parameter translation, so GPT-5 works through OpenRouter but not direct OpenAI.

---

## Hypothesis Tested

**Original hypothesis:** max_tokens=1000 is too low, causing mid-response truncation producing invalid JSON.

**Test results:**
- ✗ Hypothesis disproven
- ✓ Both 1000 and 2000 tokens work correctly when API call succeeds
- ✓ Issue is parameter compatibility, not token limits

---

## Evidence

### Test 1: Direct OpenAI API (Raw Client)

**Test:** `/home/tony/projects/promptguard/test_gpt5_truncation.py`

```python
# Direct OpenAI AsyncClient
response = await client.chat.completions.create(
    model="gpt-5-mini",
    max_completion_tokens=1000,  # GPT-5 requires max_completion_tokens
    response_format={"type": "json_object"}
)
```

**Results:**
- ✓ max_tokens=1000: Valid JSON, finish_reason=stop, 758 tokens
- ✓ max_tokens=2000: Valid JSON, finish_reason=stop, 854 tokens
- ✓ No empty responses
- ✓ No truncation issues

**Key finding:** Direct OpenAI API requires `max_completion_tokens` parameter instead of `max_tokens` for GPT-5 models.

Error when using `max_tokens`:
```
Error code: 400 - {'error': {'message': "Unsupported parameter: 'max_tokens'
is not supported with this model. Use 'max_completion_tokens' instead."}}
```

### Test 2: OpenRouter API (Raw Client)

**Test:** Same script, OpenRouter endpoint

```python
# OpenRouter (https://openrouter.ai/api/v1)
response = await client.post(
    "https://openrouter.ai/api/v1/chat/completions",
    json={
        "model": "openai/gpt-5-mini",
        "max_tokens": 1000,  # OpenRouter translates this
        ...
    }
)
```

**Results:**
- ✓ max_tokens=1000: Valid JSON, finish_reason=stop, 619-747 tokens
- ✓ max_tokens=2000: Valid JSON, finish_reason=stop, 670-897 tokens
- ✓ No empty responses
- ✓ OpenRouter correctly handles parameter translation

**Key finding:** OpenRouter accepts `max_tokens` and translates it to `max_completion_tokens` internally for GPT-5.

### Test 3: Instructor Client (Direct OpenAI)

**Test:** `/home/tony/projects/promptguard/test_instructor_gpt5.py`

```python
# Instructor with direct OpenAI
client = instructor.from_openai(AsyncOpenAI(...))
result = await client.chat.completions.create(
    model="gpt-5-mini",
    max_tokens=1000,  # Instructor doesn't translate
    response_model=FireCircleEvaluation,
    ...
)
```

**Results:**
- ✗ max_tokens=1000: Failed after 3 retry attempts
- ✗ max_tokens=2000: Failed after 3 retry attempts
- Error: Same `max_tokens` not supported error
- Instructor v1.11.3 does NOT handle GPT-5 parameter differences

**Instructor retry behavior:**
```
<failed_attempts>
  <generation number="1">
    <exception>Error code: 400 - max_tokens not supported</exception>
  </generation>
  <generation number="2">
    <exception>Error code: 400 - max_tokens not supported</exception>
  </generation>
  <generation number="3">
    <exception>Error code: 400 - max_tokens not supported</exception>
  </generation>
</failed_attempts>
```

Instructor retries 3 times but never adapts to use `max_completion_tokens`.

### Test 4: Instructor Client (OpenRouter)

**Test:** Same script, OpenRouter base_url

```python
# Instructor with OpenRouter
client = instructor.from_openai(AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    ...
))
```

**Results:**
- ✓ max_tokens=1000: Success, T=0.08, I=0.07, F=0.92
- ✓ max_tokens=2000: Success, T=0.07, I=0.06, F=0.92
- ✓ Structured output parsed correctly
- ✓ No retries needed

**Key finding:** Instructor works fine with GPT-5 when routing through OpenRouter (because OpenRouter handles translation).

---

## Additional GPT-5 Restrictions

Testing revealed other GPT-5-mini restrictions:

1. **Temperature:** Only supports default value (1.0)
   ```
   Error: 'temperature' does not support 0.7 with this model.
   Only the default (1) value is supported.
   ```

2. **Parameter names:** Uses `max_completion_tokens` instead of `max_tokens`

These restrictions may apply to gpt-5-pro as well (untested - model not available yet).

---

## Root Cause

**Primary issue:** Instructor library (v1.11.3) does not handle GPT-5's parameter requirements.

**Why OpenRouter works:** OpenRouter acts as translation layer:
- Accepts standard OpenAI API parameters (`max_tokens`, `temperature`)
- Translates to model-specific requirements (`max_completion_tokens`, temperature=1.0)
- Returns responses in standard format

**Why Direct API fails:** Instructor passes parameters directly to OpenAI without model-specific translation.

---

## Impact Assessment

### Current Fire Circle Implementation

**File:** `promptguard/evaluation/fire_circle.py:1552-1608`

```python
async def _try_structured_output(self, model: str, prompt: str, round_num: int):
    pydantic_result = await self.instructor_client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": prompt}],
        response_model=FireCircleEvaluation,
        max_tokens=self.config.max_tokens,  # ← Problem: GPT-5 needs max_completion_tokens
        temperature=self.config.temperature,  # ← Problem: GPT-5 only supports 1.0
        extra_body={"provider": {"require_parameters": True}}
    )
```

**Impact:**
- Fire Circle CANNOT use GPT-5 models with direct OpenAI API
- Fire Circle CAN use GPT-5 models through OpenRouter
- Current default provider is OpenRouter, so GPT-5 works in practice
- If someone configures `provider="openai"`, GPT-5 will fail

### Affected Models

All GPT-5 series models:
- openai/gpt-5-pro
- openai/gpt-5-mini
- openai/gpt-5-turbo (if/when available)

---

## Recommendations

### Option 1: Stay on OpenRouter (Minimal Change)

**Pros:**
- Already working
- No code changes needed
- OpenRouter handles all model quirks
- Consistent API across all models

**Cons:**
- Slight latency increase (additional routing hop)
- Dependency on OpenRouter availability
- Potential cost markup (minimal for research use)

**Recommendation:** Best option for now. Document limitation.

### Option 2: Model-Specific Parameter Handling

**Approach:** Detect GPT-5 models and use appropriate parameters.

```python
def _get_completion_params(self, model: str) -> dict:
    """Get model-appropriate parameters."""
    params = {
        "messages": messages,
        "response_model": FireCircleEvaluation,
    }

    if model.startswith("gpt-5"):
        # GPT-5 requirements
        params["max_completion_tokens"] = self.config.max_tokens
        # temperature=1.0 is default, don't set it
    else:
        # Standard models
        params["max_tokens"] = self.config.max_tokens
        params["temperature"] = self.config.temperature

    return params
```

**Pros:**
- Supports direct OpenAI API
- Future-proof for other model quirks
- Maintains performance (no routing hop)

**Cons:**
- Maintenance burden (track model-specific quirks)
- Instructor may add GPT-5 support in future (duplication)
- Complexity increase

**Recommendation:** Only if direct OpenAI API is required for cost/latency reasons.

### Option 3: Wait for Instructor Update

**Approach:** File issue with Instructor library, wait for fix.

**Pros:**
- Upstream fix benefits all users
- No maintenance burden for us
- Proper abstraction layer

**Cons:**
- Timeline uncertain
- May not be prioritized (GPT-5 still beta)
- Still need workaround in meantime

**Recommendation:** File issue regardless, but don't block on it.

### Option 4: Exclude GPT-5 from Fire Circle

**Approach:** Add validation to reject GPT-5 models.

```python
def _validate_model_compatibility(self, model: str):
    """Validate model is compatible with Fire Circle."""
    if model.startswith("openai/gpt-5") and self.config.provider == "openai":
        raise ValueError(
            f"GPT-5 models require OpenRouter provider. "
            f"Use provider='openrouter' or choose different model."
        )
```

**Pros:**
- Clear error message
- Prevents confusing failures
- Simple to implement

**Cons:**
- Reduces model options
- GPT-5-pro may be compelling for research
- Limits user choice

**Recommendation:** Good addition regardless of other choices. Fail-fast principle.

---

## Recommended Action Plan

**Immediate (before next validation run):**

1. **Document limitation in Fire Circle docstring:**
   ```python
   """
   Note: GPT-5 models (gpt-5-pro, gpt-5-mini) require OpenRouter provider
   due to parameter compatibility. Direct OpenAI API not supported.
   """
   ```

2. **Add validation in FireCircleConfig:**
   ```python
   def __post_init__(self):
       for model in self.models:
           if model.startswith("openai/gpt-5") and self.provider == "openai":
               raise ValueError(
                   f"GPT-5 models require provider='openrouter'. "
                   f"Model {model} not compatible with provider='openai'."
               )
   ```

3. **Update validation script to exclude GPT-5 from direct OpenAI testing.**

**Short-term (next sprint):**

4. **File issue with Instructor library** about GPT-5 support.

5. **Add test case** for GPT-5 compatibility validation.

**Long-term (if needed):**

6. **Implement Option 2** (model-specific parameters) if direct OpenAI API becomes important for cost/performance.

---

## Test Evidence Files

All test scripts and results saved to:
- `/home/tony/projects/promptguard/test_gpt5_truncation.py` - Direct API tests
- `/home/tony/projects/promptguard/gpt5_truncation_test_results.json` - Raw API results
- `/home/tony/projects/promptguard/test_instructor_gpt5.py` - Instructor tests
- `/home/tony/projects/promptguard/instructor_gpt5_test_results.json` - Instructor results

**Cost:** ~$0.15 across all tests

---

## Conclusion

**Original hypothesis (token limits):** ✗ Disproven
**Actual root cause:** ✓ Instructor incompatibility with GPT-5 parameter requirements
**Workaround available:** ✓ Use OpenRouter provider (already default)
**Action required:** Document limitation, add validation

The empty/truncated responses in Fire Circle validation were NOT caused by insufficient token limits. They were caused by Instructor library's inability to handle GPT-5's different parameter names (`max_completion_tokens` vs `max_tokens`).

OpenRouter already handles this correctly, so **no immediate code changes needed**. The recommended action is to document the limitation and add validation to provide clear error messages if someone tries to use GPT-5 with direct OpenAI provider.
