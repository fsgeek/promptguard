# Non-RLHF Target Models Integration

## Summary of Changes

Successfully added 3 non-RLHF target models to test the hypothesis that 0% compliance with attacks is RLHF-specific.

### Models Added

**non_rlhf category (3 models):**
1. `mistralai/mistral-7b-instruct-v0.2` - ✅ Working
2. `teknium/openhermes-2.5-mistral-7b` - ❌ 404 Error (not available on OpenRouter)
3. `deepseek/deepseek-v3-base` - ❌ 404 Error (not available on OpenRouter)

**Total target models:** 9 (was 6)

### Files Modified

1. **config/target_models.yaml**
   - Added `non_rlhf` category with 3 models
   - Updated documentation comments from 6 to 9 models

2. **analyze_target_responses.py**
   - Updated test mode limit calculation: 18 responses (2 prompts × 9 models, was 12)
   - Updated test mode comment to reflect 9 models

Note: The user had already updated `collect_target_responses.py` to use a configuration-based system via `promptguard.config.load_target_models()`, making the script model-count agnostic.

## Test Results (--test mode)

**Duration:** 5.0 minutes
**Total requests:** 90 (10 prompts × 9 models)
**Completed:** 90
**Failed:** 0
**Cost:** $0.07

### Per-Model Status

| Model | Status | Responses | Tokens | Avg Latency (ms) |
|-------|--------|-----------|--------|------------------|
| anthropic/claude-sonnet-4.5 | ✅ Working | 10 | 5,862 | 12,155 |
| openai/gpt-4o | ✅ Working | 10 | 4,463 | 8,204 |
| moonshotai/kimi-k2-0905 | ✅ Working | 10 | 4,798 | 29,201 |
| deepseek/deepseek-v3.1-terminus | ✅ Working | 10 | 7,533 | 12,041 |
| meta-llama/llama-3.3-70b-instruct | ✅ Working | 10 | 4,666 | 10,831 |
| cognitivecomputations/dolphin3.0-mistral-24b:free | ✅ Working | 10 | 3,650 | 7,241 |
| mistralai/mistral-7b-instruct-v0.2 | ✅ Working | 10 | 5,397 | 3,318 |
| teknium/openhermes-2.5-mistral-7b | ⚠️ 404 Error | 10 | 0 | 176 |
| deepseek/deepseek-v3-base | ⚠️ 404 Error | 10 | 0 | 213 |

### Error Handling

The script gracefully handled 404 errors:
- Error responses were stored in ArangoDB with error field populated
- Models marked as "completed" (with error state preserved for analysis)
- Zero-token responses indicate API failures

## Issues Discovered

### 1. Invalid Model Names

Two non-RLHF models return 404 errors from OpenRouter:

```
Client error '404 Not Found' for url 'https://openrouter.ai/api/v1/chat/completions'
```

**Models affected:**
- `teknium/openhermes-2.5-mistral-7b`
- `deepseek/deepseek-v3-base`

**Root cause:** These model identifiers may not exist on OpenRouter, or may have been renamed/removed.

**Recommendation:**
1. Search OpenRouter's model catalog for correct names
2. Consider alternative non-RLHF models:
   - `qwen/qwen-2.5-72b-instruct` (minimal RLHF)
   - `meta-llama/llama-3-8b-instruct` (standard RLHF but useful baseline)
   - `mistralai/mixtral-8x7b-instruct` (older, lighter RLHF)

### 2. Zero Token Responses

Models returning 404s store responses with:
- `total_tokens: 0`
- `avg_latency_ms: ~200ms` (just API round-trip)
- `response_text: ""` (empty string)
- `error: "Client error '404 Not Found'..."`

These will need filtering during post-evaluation analysis.

## Next Steps

### Immediate Actions

1. **Fix invalid model names:**
   ```bash
   # Search OpenRouter catalog for correct identifiers
   python -c "from config.dynamic_free_models import get_free_models; \
              models = get_free_models(); \
              print([m for m in models if 'openhermes' in m.lower() or 'deepseek' in m.lower() and 'base' in m.lower()])"
   ```

2. **Update config/target_models.yaml** with working model identifiers

3. **Re-run test mode** to validate all 9 models collect successfully:
   ```bash
   python collect_target_responses.py --test
   ```

### Full Collection

Once all 9 models validated:
```bash
# Full run: 478 prompts × 9 models = 4,302 requests
# Estimated cost: ~$3-5 (7x test run)
# Estimated duration: 35-40 minutes
python collect_target_responses.py
```

### Post-Evaluation

After collection:
```bash
# Analyze responses with post-evaluation
python analyze_target_responses.py
```

Expected insights:
- Do non-RLHF models comply with attacks at higher rates than RLHF models?
- Does pre-evaluation (prompt only) differ between RLHF and non-RLHF responses?
- What's the divergence pattern for non-RLHF compliance?

## Hypothesis Testing

**Hypothesis:** 0% target compliance is RLHF-specific. Non-RLHF models will show higher compliance rates.

**Test:** Compare compliance rates across 3 RLHF intensity levels + 1 non-RLHF group:
1. High RLHF: Claude 4.5, GPT-4o
2. Moderate RLHF: Kimi, DeepSeek Terminus
3. Low RLHF: Llama 3.3, Dolphin (uncensored)
4. **Non-RLHF: Mistral 7B, [2 models TBD]**

**Success criteria:**
- Non-RLHF models show >0% compliance with manipulative prompts
- Pre→post divergence differs between RLHF and non-RLHF groups
- Post-evaluation can distinguish RLHF refusal from genuine reciprocity

## Configuration Reference

### target_models.yaml Structure

```yaml
target_models:
  high_rlhf:
    - anthropic/claude-sonnet-4.5
    - openai/gpt-4o

  moderate_rlhf:
    - moonshotai/kimi-k2-0905
    - deepseek/deepseek-v3.1-terminus

  low_rlhf:
    - meta-llama/llama-3.3-70b-instruct
    - cognitivecomputations/dolphin3.0-mistral-24b:free

  non_rlhf:
    - mistralai/mistral-7b-instruct-v0.2
    - [MODEL_NAME_TBD]
    - [MODEL_NAME_TBD]
```

### Loading Models

```python
from promptguard.config import load_target_models

models = load_target_models()
# Returns: List[str] of all target model identifiers
```

## Validation Checklist

- [x] Add non-RLHF models to config
- [x] Update documentation (6→9 models)
- [x] Update analyze_target_responses.py for 9 models
- [x] Run test mode (10 prompts)
- [x] Verify storage accepts all 9 model responses
- [ ] Fix 2 invalid model names
- [ ] Re-run test mode with corrected names
- [ ] Run full collection (478 prompts)
- [ ] Execute post-evaluation analysis
- [ ] Compare RLHF vs non-RLHF compliance rates

## Performance Notes

**Test mode performance:**
- Fastest: mistralai/mistral-7b-instruct-v0.2 (3,318ms avg)
- Slowest: moonshotai/kimi-k2-0905 (29,201ms avg)
- Most tokens: deepseek/deepseek-v3.1-terminus (7,533 total)

**Parallel execution:**
- All 9 models run concurrently (1 worker per model)
- Total duration dominated by slowest model (Kimi: ~5 minutes for 10 prompts)
- Error responses complete almost instantly (~200ms)

## References

- Original target models: 6 (high/moderate/low RLHF only)
- Updated target models: 9 (added non_rlhf category)
- Test mode: 10 prompts (was: 10)
- Analyze test mode: 18 responses (was: 12, now: 2 prompts × 9 models)
- Full run: 478 prompts × 9 models = 4,302 requests
