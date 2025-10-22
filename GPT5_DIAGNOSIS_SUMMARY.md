# GPT-5 Fire Circle Failures - Quick Summary

## TL;DR

**Problem:** Fire Circle fails with GPT-5 models
**Root cause:** Instructor library doesn't handle GPT-5's `max_completion_tokens` requirement
**Solution:** Already working - use OpenRouter (current default)
**Action needed:** Document limitation, add validation

---

## What I Tested

Created two test scripts comparing Direct OpenAI vs OpenRouter:

1. **Raw API test** (`test_gpt5_truncation.py`)
   - ✓ Direct OpenAI works with `max_completion_tokens`
   - ✓ OpenRouter works with `max_tokens` (translates internally)
   - ✓ No truncation issues at 1000 or 2000 tokens
   - ✓ All responses valid JSON

2. **Instructor client test** (`test_instructor_gpt5.py`)
   - ✗ Direct OpenAI fails (Instructor uses `max_tokens`)
   - ✓ OpenRouter works (handles translation)

---

## The Issue

GPT-5 models require different parameters:
- **Standard:** `max_tokens`, `temperature` (any value)
- **GPT-5:** `max_completion_tokens`, `temperature=1.0` (only)

Instructor v1.11.3 (latest) doesn't handle this difference.

OpenRouter acts as translation layer - accepts standard params, translates to model-specific.

---

## Evidence

### Direct API - Works ✓
```
Direct OpenAI (1000 tokens): Valid JSON, 758 tokens, finish=stop
Direct OpenAI (2000 tokens): Valid JSON, 854 tokens, finish=stop
OpenRouter (1000 tokens): Valid JSON, 619 tokens, finish=stop
OpenRouter (2000 tokens): Valid JSON, 851 tokens, finish=stop
```

### Instructor - Mixed
```
Instructor + Direct OpenAI: ✗ Failed (3 retries, max_tokens not supported)
Instructor + OpenRouter: ✓ Success (T=0.07, I=0.06, F=0.92)
```

---

## Impact

Fire Circle currently uses OpenRouter by default → **GPT-5 works fine**.

But if someone sets `provider="openai"` → **GPT-5 fails with confusing errors**.

---

## Recommendation

**Immediate:** Add validation to `FireCircleConfig`:

```python
def __post_init__(self):
    for model in self.models:
        if model.startswith("openai/gpt-5") and self.provider == "openai":
            raise ValueError(
                f"GPT-5 models require provider='openrouter'. "
                f"Model {model} not compatible with provider='openai'."
            )
```

**Document:** Add note to Fire Circle docstring about GPT-5 + OpenRouter requirement.

**Optional:** File issue with Instructor library (may already be aware).

---

## Files Created

- `/home/tony/projects/promptguard/GPT5_FIRE_CIRCLE_DIAGNOSIS.md` - Full analysis
- `/home/tony/projects/promptguard/test_gpt5_truncation.py` - Raw API tests
- `/home/tony/projects/promptguard/test_instructor_gpt5.py` - Instructor tests
- `/home/tony/projects/promptguard/gpt5_truncation_test_results.json` - Results
- `/home/tony/projects/promptguard/instructor_gpt5_test_results.json` - Results

**Cost:** ~$0.15 total across all tests

---

## Bottom Line

Your original hypothesis (token limits) was wrong in a useful way - led us to discover the real issue.

**Not a bug in PromptGuard.** Limitation in upstream library (Instructor) + quirky model requirements (GPT-5).

**Already working** via OpenRouter. Just needs documentation and validation to prevent confusion.
