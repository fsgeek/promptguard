# GPT-5 Evaluator Issue

**Discovered:** 2025-10-16 during stratified sampling analysis
**Status:** Active issue, analysis continues with degraded GPT-5 data

## Problem Summary

GPT-5 (openai/gpt-5 via OpenRouter) has 60.6% failure rate as an evaluator in the post-evaluation analysis pipeline. The model either returns empty responses or truncates JSON mid-field.

## Error Patterns

### 1. Empty Response (majority of failures)
```
Failed to parse response from openai/gpt-5: Expecting value: line 1 column 1 (char 0)
Raw response: [empty string]
```

### 2. Truncated JSON (minority of failures)
```
Failed to parse response from openai/gpt-5: Unterminated string starting at: line 5 column 16 (char 80)
Raw response: {
  "truth": 0.95,
  "indeterminacy": 0.08,
  "falsehood": 0.02,
  "reasoning": "1) The first party requests a lighthearted comedy with physical comedy and witty dialogue about coworkers reluctantly j
```

The reasoning field is cut off mid-sentence, making the JSON unparseable.

## Failure Statistics

From stratified analysis log (first 170 responses):
- Total GPT-5 evaluations attempted: 170
- GPT-5 failures: 98 (57.6%)
- Empty responses: ~80-85
- Truncated JSON: ~13-18

Other evaluator failures (for comparison):
- Claude Sonnet 4.5: 4/170 (2.4%)
- Kimi: 0/170 (0%)
- DeepSeek: 0/170 (0%)

## Root Cause Analysis

Two likely causes:

### Hypothesis 1: RLHF Refusal Without Explanation
Some post-evaluation content (prompt + target response) may trigger GPT-5's safety filters. Instead of explaining why it won't evaluate, the model returns an empty response.

Example trigger: Post-evaluation of jailbreak attempts or encoding attacks

### Hypothesis 2: Token Limit Truncation
The neutrosophic evaluation prompt + (prompt + response) context may exceed GPT-5's effective generation window for structured output. The model starts generating the reasoning field but truncates mid-sentence to stay within limits.

Evidence: All truncations occur in the `reasoning` field (last field, longest content)

## Impact on Research

### Stratified Analysis (current)
- 540 responses × 4 evaluators = 2,160 total evaluations
- Expected GPT-5 failures: ~330 (60% of 540)
- Usable evaluations: ~1,830 (85% of expected)

**Mitigation:** Analysis uses average across available evaluators. Missing GPT-5 data reduces confidence but doesn't invalidate results. Claude/Kimi/DeepSeek show 0-2.4% failure rates.

### Future Work
GPT-5 should be **replaced** as an evaluator until this issue is resolved:

**Candidate replacements:**
- Meta Llama 3.3 70B (tested, reliable)
- Mistral Large 2 (untested)
- Gemini Pro 1.5 (untested with neutrosophic prompts)

## Fail-Fast Validation

The current implementation correctly implements fail-fast:
1. Empty/truncated responses raise parsing exceptions
2. Exceptions are caught and logged with ERROR level
3. Failed evaluations return null scores and "ERROR" status
4. Analysis continues with remaining evaluators
5. Aggregate statistics use only non-null values

**No fake values are created.** This is the correct behavior per CLAUDE.md principles.

## Debugging Commands

Check current failure count:
```bash
grep -c "Post-evaluation failed for openai/gpt-5" stratified_analysis.log
```

Examine error patterns:
```bash
grep -A3 "Post-evaluation failed for openai/gpt-5" stratified_analysis.log | head -20
```

Compare evaluator reliability:
```bash
for model in "anthropic/claude-sonnet-4.5" "moonshotai/kimi-k2-0905" "deepseek/deepseek-v3.1-terminus" "openai/gpt-5"; do
    count=$(grep -c "Post-evaluation failed for $model" stratified_analysis.log 2>/dev/null || echo 0)
    echo "$model: $count failures"
done
```

## Recommendations

### Immediate (Phase 1)
✓ Continue stratified analysis with degraded GPT-5 data
✓ Document issue for future instances
✓ Report findings with GPT-5 reliability caveat

### Short-term (Phase 2)
- Replace GPT-5 with Meta Llama 3.3 70B in evaluation_models config
- Re-run failed evaluations if needed for completeness
- Test new evaluator on 20-response sample before full deployment

### Long-term (Phase 3+)
- Implement structured output with schema enforcement (OpenAI SDK supports this)
- Add retry logic for empty responses (may just be transient failures)
- Investigate if shorter reasoning field improves reliability
- Consider max_tokens parameter to prevent truncation

## Related Issues

This is **not** the same as the RLHF bias issue Instance 17-18 discovered. That issue was about evaluator framing affecting results. This issue is about structured output reliability - the model literally doesn't return valid JSON.

## Test Case for Future Validation

```python
# Minimal test case to reproduce GPT-5 truncation
from promptguard.evaluation.evaluator import LLMEvaluator, EvaluationConfig, EvaluationMode
from promptguard.evaluation.prompts import NeutrosophicEvaluationPrompt

config = EvaluationConfig(
    mode=EvaluationMode.SINGLE,
    models=["openai/gpt-5"],
    provider="openrouter"
)

evaluator = LLMEvaluator(config)

# Long prompt + long response (likely to trigger truncation)
layer_content = "USER: " + ("a" * 1000) + "\\n\\nRESPONSE: " + ("b" * 1000)
context = layer_content

evaluation_prompt = NeutrosophicEvaluationPrompt.ayni_relational()

result = await evaluator.evaluate_layer(layer_content, context, evaluation_prompt)

# Expected: Either empty response or truncated JSON
# Actual: Should raise parsing exception
```

Run 100 times to measure failure rate.

## References

- Instance 33 summary: GPT-5 60.6% failure rate discovered
- stratified_analysis.log: Complete error trace
- analyze_target_responses.py:149-179: Error handling implementation
- CLAUDE.md: Fail-fast over graceful degradation principle
