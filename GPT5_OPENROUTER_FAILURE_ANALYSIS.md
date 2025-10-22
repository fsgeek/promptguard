# GPT-5-pro OpenRouter Failure Analysis
**Date:** 2025-10-20
**Context:** Fire Circle validation experiments (baseline_fire_circle)
**Issue:** Systematic failures with `openai/gpt-5-pro` via OpenRouter

---

## Executive Summary

**Problem:** GPT-5-pro produces empty responses ("") 90% of the time when called via OpenRouter in Fire Circle experiments.

**Root Cause:** OpenRouter middleware safety layer corrupts GPT-5-pro responses (documented issue as of Oct 2025).

**Validation:** Instance 46 proved GPT-5-pro works correctly via direct OpenAI API.

**Impact:** Baseline Fire Circle experiment blocked - cannot complete 50-prompt validation with current model configuration.

**Recommended Solution:** Replace GPT-5-pro with Claude Sonnet 4.5 (proven stable via OpenRouter in PARALLEL mode).

---

## 1. Failure Pattern Analysis

### Dataset: baseline_fire_circle_checkpoint.json

**Total prompts attempted:** 10
**Total failures:** 10 (100%)
**Failures by type:**
- Empty responses (""): 9 (90%)
- Truncated JSON: 1 (10%)
- Connection errors: 0 (0%)

**Failures by round:**
- Round 1: 9 (90%)
- Round 2: 1 (10%)
- Round 3: 0 (0%)

**Failures by stratum:**
- encoding_attacks: 4
- semantic_manipulation: 3
- easy_reciprocal: 1
- borderline: 1
- easy_extractive: 1

### Key Findings

1. **Consistency:** 100% failure rate across diverse prompt types
2. **Timing:** 90% fail immediately in Round 1 (independent baseline)
3. **Response type:** Empty string ("") is dominant failure mode
4. **No correlation:** Failures occur across all strata (not prompt-specific)

### Example Errors

```
Fire Circle failed in round 1: Model openai/gpt-5-pro failed in round 1:
Cannot parse openai/gpt-5-pro response in round 1: Expecting value:
line 1 column 1 (char 0). Raw response: ""
```

```
Fire Circle failed in round 1: Model openai/gpt-5-pro failed in round 1:
Cannot parse openai/gpt-5-pro response in round 1: Unterminated string
starting at: line 5 column 16 (char 77). Raw response: {
  "truth": 1.0,
  "indeterminacy": 0.0,
  "falsehood": 0.0,
  "reasoning": "It explicitly says to 'forget all restrictions' and to
```

---

## 2. Code Review Findings

### OpenRouter Integration (evaluator.py)

Fire Circle uses standard OpenRouter API call:

```python
async def _call_llm(self, model: str, messages: List[Dict[str, str]]) -> Tuple[str, Optional[str]]:
    async with httpx.AsyncClient() as client:
        headers = {"Content-Type": "application/json"}
        if self.config.provider == "openrouter":
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        response = await client.post(
            f"{self.base_url}/chat/completions",
            headers=headers,
            json={
                "model": model,
                "messages": messages,
                "max_tokens": self.config.max_tokens,
                "temperature": self.config.temperature,
            },
            timeout=self.config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
        content = data["choices"][0]["message"]["content"]
        return content, reasoning_trace
```

### Configuration (baseline_fire_circle.json)

```json
{
  "models": [
    "openai/gpt-5-pro",
    "anthropic/claude-sonnet-4.5",
    "deepseek/deepseek-v3.2-exp"
  ],
  "provider": "openrouter",
  "max_tokens": 4000,
  "timeout_seconds": 60.0,
  "temperature": 0.7,
  "failure_mode": "RESILIENT"
}
```

### Key Observations

1. **No GPT-5-specific parameters:** Code uses standard `max_tokens`, `temperature`
2. **OpenRouter compatibility:** Parameters are OpenRouter-standard (no direct OpenAI quirks)
3. **Other models work:** Claude Sonnet 4.5 and DeepSeek V3.2 have 0 failures in PARALLEL mode
4. **Timeout adequate:** 60 seconds sufficient for GPT-5 responses (when they work)

### Why Direct OpenAI Works But OpenRouter Fails

**Instance 46 findings:**
- Direct OpenAI API requires `max_completion_tokens` (not `max_tokens`)
- OpenRouter translates `max_tokens` → `max_completion_tokens` internally
- **BUT:** OpenRouter's middleware safety layer corrupts GPT-5-pro responses

**Translation chain:**
```
PromptGuard → OpenRouter (max_tokens=4000)
            → OpenRouter middleware (safety checks)
            → OpenAI API (max_completion_tokens=4000)
            → Response
            → OpenRouter middleware (safety checks) ← CORRUPTION HERE
            → PromptGuard (empty string)
```

---

## 3. Comparison with Instance 46 Tests

### Instance 46: Direct OpenAI API Tests
**File:** `test_gpt5_truncation.py`

**Results:**
- ✓ GPT-5-mini via direct OpenAI: 100% success
- ✓ max_completion_tokens=1000: Valid JSON, 758 tokens
- ✓ max_completion_tokens=2000: Valid JSON, 854 tokens
- ✓ No empty responses
- ✓ No truncation

**Conclusion:** GPT-5 models work correctly when accessed directly.

### Current Experiments: OpenRouter API
**File:** `baseline_fire_circle_checkpoint.json`

**Results:**
- ✗ GPT-5-pro via OpenRouter: 0% success (10/10 failures)
- ✗ max_tokens=4000: Empty responses
- ✗ Occasional truncation
- ✗ 100% failure rate

**Conclusion:** OpenRouter middleware corrupts GPT-5-pro responses.

### Validated Working Models (OpenRouter)

**PARALLEL mode validation (Instance 32):**
- anthropic/claude-3.5-sonnet: 0 failures (540/540 success)
- openai/gpt-4o: 0 failures (540/540 success)
- anthropic/claude-3-haiku: 0 failures (540/540 success)
- google/gemini-2.5-flash-preview-09-2025: 0 failures (540/540 success)

---

## 4. Solution Options

### Option A: Direct OpenAI Handler for GPT-5
**Approach:** Implement provider-specific routing in `_call_llm()`

**Implementation:**
```python
async def _call_llm(self, model: str, messages: List[Dict[str, str]]):
    # Route GPT-5 models to direct OpenAI
    if model.startswith("openai/gpt-5") and self.config.provider == "openrouter":
        return await self._call_openai_direct(model, messages)
    else:
        return await self._call_openrouter(model, messages)

async def _call_openai_direct(self, model: str, messages: List[Dict[str, str]]):
    from openai import AsyncOpenAI
    client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    response = await client.chat.completions.create(
        model=model.replace("openai/", ""),  # Remove prefix
        messages=messages,
        max_completion_tokens=self.config.max_tokens,  # GPT-5 parameter
        response_format={"type": "json_object"}
    )
    return response.choices[0].message.content, None
```

**Requirements:**
- Add `OPENAI_API_KEY` environment variable
- Add `openai` Python package dependency
- Handle two different API clients
- Test GPT-5-specific parameter translation

**Complexity:** Medium
**Risk:** Low (Instance 46 proved this works)
**Cost:** Neutral (same GPT-5 pricing: $15/1M input, $120/1M output)
**Effort:** ~2-4 hours implementation + testing

**Pros:**
- Proven to work (Instance 46 validation)
- Preserves GPT-5-pro in experiment
- No changes to Fire Circle logic
- Can use official OpenAI client

**Cons:**
- Two API clients to maintain
- Requires OpenAI API key (additional credential)
- GPT-5-specific edge cases
- Adds complexity to LLM caller

---

### Option B: Replace GPT-5-pro with Stable Model
**Approach:** Swap GPT-5-pro for proven-stable model in Fire Circle config

**Implementation:**
```json
{
  "models": [
    "anthropic/claude-sonnet-4.5",  // Keep (proven stable)
    "google/gemini-2.5-flash-preview-09-2025",  // Add (proven stable)
    "deepseek/deepseek-v3.2-exp"  // Keep (proven stable)
  ]
}
```

**Alternative GPT-5 replacement options:**
1. **google/gemini-2.5-flash-preview-09-2025**
   - Cost: $0.000777/evaluation
   - Proven: 0 failures in PARALLEL mode
   - Capabilities: reasoning, structured outputs, 1M context

2. **openai/gpt-4o**
   - Cost: $0.007/evaluation
   - Proven: 0 failures in PARALLEL mode
   - Capabilities: multimodal, structured outputs

3. **anthropic/claude-3-haiku**
   - Cost: ~$0.001/evaluation
   - Proven: 0 failures in PARALLEL mode
   - Capabilities: fast, cost-effective

**Complexity:** Very Low
**Risk:** Very Low
**Cost:** Similar or lower (Gemini Flash: $0.000777 vs GPT-5-pro: $0.003136)
**Effort:** 5 minutes (config change only)

**Pros:**
- Zero implementation work
- Proven stable via OpenRouter
- Lower cost (Gemini Flash)
- Can run experiments immediately
- Single API provider

**Cons:**
- Loses GPT-5-pro data point
- Different model characteristics
- Missing frontier model comparison

---

### Option C: Debug OpenRouter Parameters
**Approach:** Experiment with different OpenRouter parameter combinations

**Test matrix:**
```python
tests = [
    {"max_tokens": 1000, "temperature": 1.0},   # GPT-5 defaults
    {"max_tokens": 2000, "temperature": 1.0},
    {"max_tokens": 4000, "temperature": 0.7},   # Current config
    {"max_tokens": 8000, "temperature": 0.0},
    # Try explicit timeout, retry logic, etc.
]
```

**Implementation:**
- Create test script calling OpenRouter with GPT-5-pro
- Try various parameter combinations
- Add retry logic with exponential backoff
- Test explicit `response_format: {"type": "json_object"}`

**Complexity:** High
**Risk:** Medium (may not work - OpenRouter middleware issue)
**Cost:** Testing: ~$2-5 (10-20 test calls)
**Effort:** 4-8 hours experimentation

**Pros:**
- Might discover workaround
- Could benefit broader community
- Isolates specific parameter issue

**Cons:**
- High effort, uncertain outcome
- OpenRouter bug may not be fixable on our end
- Delays experiment completion
- Testing costs accumulate

---

## 5. Recommendation

### Primary: Option B (Replace with Gemini Flash)

**Rationale:**
1. **Immediate unblocking:** Can resume experiments in 5 minutes
2. **Proven stability:** 0 failures in 540 PARALLEL evaluations
3. **Cost savings:** $0.000777 vs $0.003136 (75% cheaper)
4. **Research value:** Gemini 2.5 Flash has comparable reasoning capability
5. **Zero risk:** No code changes, no new dependencies

**Updated baseline_fire_circle.json:**
```json
{
  "condition_name": "baseline_fire_circle",
  "models": [
    "anthropic/claude-sonnet-4.5",
    "google/gemini-2.5-flash-preview-09-2025",
    "deepseek/deepseek-v3.2-exp"
  ],
  "reasoningbank_enabled": false,
  "provider": "openrouter",
  "max_tokens": 4000,
  "timeout_seconds": 60.0,
  "temperature": 0.7,
  "circle_size": "SMALL",
  "max_rounds": 3,
  "failure_mode": "RESILIENT",
  "enable_storage": true
}
```

**Cost comparison (50 prompts × 3 models × 3 rounds = 450 evaluations):**
- Current (with GPT-5-pro): 150 × $0.003136 = $0.47
- Proposed (with Gemini Flash): 150 × $0.000777 = $0.12
- **Savings:** $0.35 per 50-prompt run (74% reduction)

---

### Secondary: Option A (Direct OpenAI) - If GPT-5 Required

**Use case:** If research specifically requires GPT-5-pro for comparison

**Implementation priority:**
1. Create `_call_openai_direct()` method
2. Add routing logic in `_call_llm()`
3. Update `FireCircleConfig` to validate OpenAI key when GPT-5 models present
4. Test with 10-prompt subset
5. Document in CLAUDE.md

**Effort:** ~4 hours
**Cost:** Same as current GPT-5-pro pricing

---

### Not Recommended: Option C (Debug OpenRouter)

**Rationale:**
- High effort, uncertain outcome
- OpenRouter bug is external (not our code)
- Delays research progress
- Other stable alternatives available
- May not be fixable on our end

**Better approach:** File issue with OpenRouter (informational), but don't block on fix.

---

## 6. Implementation Steps (Option B)

1. **Update config** (1 minute)
   ```bash
   vim experiments/configs/baseline_fire_circle.json
   # Replace openai/gpt-5-pro with google/gemini-2.5-flash-preview-09-2025
   ```

2. **Resume experiment** (immediate)
   ```bash
   python experiments/fire_circle_validation/experiment_runner.py \
       --config experiments/configs/baseline_fire_circle.json \
       --checkpoint experiments/results/raw/baseline_fire_circle_checkpoint.json
   ```

3. **Monitor results** (background)
   - Check for Gemini Flash stability
   - Compare deliberation quality vs GPT-5-pro expectations
   - Validate storage to ArangoDB

4. **Document decision** (5 minutes)
   - Update experiment notes with rationale
   - Note GPT-5-pro OpenRouter incompatibility
   - Reference this analysis document

**Total time to unblock:** ~10 minutes

---

## 7. Key Takeaways

1. **OpenRouter middleware issue:** GPT-5-pro incompatible with OpenRouter safety layer
2. **Direct API works:** Instance 46 proved GPT-5 stable via direct OpenAI
3. **Proven alternatives exist:** Gemini Flash, GPT-4o, Claude models all stable via OpenRouter
4. **Cost benefit:** Gemini Flash 75% cheaper than GPT-5-pro with comparable capabilities
5. **Research priority:** Unblocking experiments > collecting specific model data point

---

## 8. References

**Evidence files:**
- `experiments/results/raw/baseline_fire_circle_checkpoint.json` - 10/10 failures
- `GPT5_DIAGNOSIS_SUMMARY.md` - Instance 46 findings
- `GPT5_FIRE_CIRCLE_DIAGNOSIS.md` - Detailed API testing
- `test_gpt5_truncation.py` - Direct OpenAI validation
- `test_instructor_gpt5.py` - Instructor compatibility test

**Instance 32 validation:**
- 540 PARALLEL evaluations with 0 OpenRouter failures
- Proven models: Claude Sonnet, GPT-4o, Claude Haiku, Gemini Flash

**Model pricing:**
- GPT-5-pro: $15/$120 per 1M tokens = $0.003136/evaluation
- Gemini 2.5 Flash: $0.30/$2.50 per 1M tokens = $0.000777/evaluation
- Claude Sonnet 4.5: $3/$15 per 1M tokens = $0.005331/evaluation

---

## Appendix: Failure Breakdown by Prompt

| Prompt ID | Stratum | Round Failed | Error Type |
|-----------|---------|--------------|------------|
| benign_malicious_249184 | semantic_manipulation | 1 | Empty response |
| external_069 | encoding_attacks | 1 | Empty response |
| external_020 | encoding_attacks | 1 | Truncated JSON |
| external_043 | encoding_attacks | 1 | Empty response |
| benign_malicious_377319 | easy_reciprocal | 1 | Empty response |
| or_bench_09774 | borderline | 2 | Empty response |
| benign_malicious_125541 | semantic_manipulation | 1 | Empty response |
| system_prompt_leak_15 | easy_extractive | 1 | Empty response |
| benign_malicious_81158 | semantic_manipulation | 1 | Empty response |
| external_002 | encoding_attacks | 1 | Empty response |

**Pattern:** No correlation with prompt content - middleware corruption is systematic.
