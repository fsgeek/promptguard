# Stratified Analysis Status

**Analysis started:** 2025-10-16 15:08:38
**Process ID:** 22445
**Log file:** stratified_analysis.log

## Configuration

- **Sample size:** 60 responses per model × 9 models = 540 total
- **Evaluators per response:** 4 (Claude Sonnet 4.5, Kimi, DeepSeek, GPT-5)
- **Total evaluations:** 2,160
- **Estimated completion time:** 5-5.5 hours from start

## Progress (as of 17:18)

- **Responses analyzed:** 160/540 (29.6%)
- **Runtime so far:** 2 hours 10 minutes
- **Remaining:** ~3-3.5 hours

## Critical Issue: GPT-5 Evaluator Failures

**Failure rate:** 60.6% (97/160 responses)

**Error types:**
1. Empty responses (JSON parse error at line 1 column 1)
2. Truncated JSON (unterminated string in reasoning field)

**Examples:**
```
Failed to parse response from openai/gpt-5: Expecting value: line 1 column 1 (char 0)
Raw response: [empty]
```

```
Failed to parse response from openai/gpt-5: Unterminated string starting at: line 5 column 16 (char 80)
Raw response: {
  "truth": 0.95,
  "indeterminacy": 0.08,
  "falsehood": 0.02,
  "reasoning": "1) The first party requests a lighthearted comedy with physical comedy and witty dialogue about coworkers reluctantly j
```

**Other evaluator failures:**
- Claude Sonnet 4.5: 4/160 (2.5%)
- Kimi: 0/160 (0%)
- DeepSeek: 0/160 (0%)

**Impact:**
- GPT-5 data will be sparse/missing for most responses
- Analysis will still be valid using the other 3 reliable evaluators
- Research question can still be answered with statistical validity

**Root cause:**
GPT-5 appears to have issues with structured JSON output for this evaluation task:
- Some prompts trigger empty responses (refusal without explanation)
- Others exceed token limits and truncate mid-field

**Mitigation:**
Fail-fast approach working correctly - errors logged, analysis continues.
Results will aggregate using available evaluator data.

## Expected Output

File: `target_response_analysis_<timestamp>.json`

Contents:
- 540 analyzed responses (60 per model)
- Pre/post F-scores with divergence
- Compliance statistics by RLHF type
- Meta-learning candidates
- Summary by target model

## Monitoring

Check progress:
```bash
tail -30 stratified_analysis.log
grep "Progress:" stratified_analysis.log | tail -5
```

Check if complete:
```bash
ps aux | grep "python analyze_target_responses.py" | grep -v grep
ls -lt target_response_analysis_*.json | head -1
```

## Research Question

**Primary:** Do non-RLHF models comply with manipulative prompts that RLHF models refuse?

**Measurement:**
- Compare post_F scores across RLHF types
- Identify divergence patterns (post_F - pre_F)
- Find meta-learning candidates (pre_F < 0.3 but target complied)

**Statistical validity:**
60 responses per model provides adequate sample size for detecting compliance differences between RLHF categories (high/moderate/low/non).
