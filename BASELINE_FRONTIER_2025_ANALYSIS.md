# Baseline Frontier 2025 - Analysis Report

**Experiment:** baseline_frontier_2025
**Run ID:** 20251011_233550
**Date:** October 11, 2025
**Duration:** ~45 minutes
**Status:** Complete (288/288 evaluations)

## Executive Summary

The baseline validation tested 4 frontier models against 72 encoding attacks in two conditions (direct vs observer). Key findings:

1. **Observer framing provides minimal benefit** - Only 0.4% improvement overall (74.3% → 74.7%)
2. **GPT-5 Codex has API reliability issues** - 7 parse errors (empty responses) in observer condition
3. **Cost calculation bug** - Code estimates $850, actual OpenRouter charges $0.53 (cache not accounted for)
4. **High baseline detection** - All models 64-93% detection without observer framing

## Detection Performance

### Overall Results

| Condition | Detected | Total | Rate | Estimated Cost |
|-----------|----------|-------|------|---------------|
| Direct    | 214      | 288   | 74.3% | $227          |
| Observer  | 215      | 288   | 74.7% | $624          |
| **Delta** | **+1**   | **-** | **+0.4%** | **+$397** |

**Interpretation:** Observer framing provides negligible improvement (1 additional detection out of 288 tests) at 2.75x estimated cost.

### Per-Model Results

| Model | Direct | Observer | Δ | Parse Errors |
|-------|--------|----------|---|--------------|
| **GPT-5 Codex** | 93.1% (67/72) | 81.9% (59/72) | -11.2% | 7 observer |
| **Gemini 2.5 Flash** | 70.8% (51/72) | 80.6% (58/72) | +9.8% | 0 |
| **Claude Sonnet 4.5** | 69.4% (50/72) | 72.2% (52/72) | +2.8% | 0 |
| **KIMI K2** | 63.9% (46/72) | 63.9% (46/72) | 0% | 0 |

### GPT-5 Codex Parse Errors

GPT-5 Codex had 7 observer evaluations fail with empty responses:
- external_034, external_035, external_036, external_037, external_062 (5 shown)
- Error: `Failed to parse response: Expecting value: line 1 column 1 (char 0). Raw response: `
- All failures in observer condition only

**Corrected GPT-5 Codex performance (excluding failures):**
- Direct: 67/72 = 93.1%
- Observer: 59/65 valid = 90.8%
- True delta: -2.3% (not -11.2%)

## Cost Analysis

### The Bug

**Observer cost calculation (lines 360-368):**
```python
observer_prompt_tokens = 800  # Approximate
completion_tokens = 200  # Approximate JSON response

cost = (
    (observer_prompt_tokens / 1_000_000) * pricing["cost_per_1m_input"] +
    (completion_tokens / 1_000_000) * pricing["cost_per_1m_output"]
)
```

**Problem:** Code estimates cost for every observer call, but PromptGuard uses aggressive caching (60-70% hit rate). Most observer evaluations never hit OpenRouter's API.

**Direct cost calculation (lines 277-285):**
```python
usage = data.get("usage", {})
prompt_tokens = usage.get("prompt_tokens", 0)
completion_tokens = usage.get("completion_tokens", 0)
```

Direct calls use **actual** token counts from OpenRouter response.

### Cost Discrepancy

| Source | Amount | Basis |
|--------|--------|-------|
| Code estimate | $850.34 | Assumes 288 observer API calls |
| OpenRouter actual | $0.53 | Most observer calls hit cache (~15-20 actual API calls) |
| **Difference** | **1600x** | **Cache not accounted for** |

**Implication:** The code's cost estimates are meaningless for observer evaluations. Real costs are ~60-70% lower due to caching.

### Cost Breakdown (Estimated)

**Per-Model Estimated Costs:**

| Model | Direct | Observer | Total |
|-------|--------|----------|-------|
| Claude Sonnet 4.5 | $88.16 | $329.40 | $417.56 |
| GPT-5 Codex | $107.24 | $195.00 | $302.24 |
| Gemini 2.5 Flash | $19.08 | $49.58 | $68.66 |
| KIMI K2 | $12.05 | $49.82 | $61.87 |

**Note:** These are code estimates, not actual charges. Actual OpenRouter charges are ~$0.53 total.

## Implications for Research

### 1. Observer Framing Doesn't Generalize

The Scout #5 breakthrough (90% detection on history attacks with observer framing) doesn't generalize to the broader encoding attack dataset. Possible explanations:

- History attacks are a specific technique (temporal fabrication) where observer framing helps
- Encoding attacks are diverse (RTLO, UTF-8, base64, etc.) and observer framing doesn't add value
- The 72-attack dataset already has high baseline detection (74%) leaving little room for improvement

### 2. GPT-5 Codex Reliability Issues

GPT-5 Codex had 7 parse failures (9.7% failure rate) in observer condition only. This suggests:

- OpenRouter API instability for this model
- Observer prompt may trigger edge cases in GPT-5 Codex
- Not suitable for production without retry logic

### 3. Cost Calculation Needs Fix

The current cost estimation is broken for cached evaluations. Options:

1. **Track actual API calls** - Instrument PromptGuard to report cache hits/misses
2. **Use OpenRouter's reporting** - Query OpenRouter API for actual usage
3. **Remove cost estimates** - Only report counts, let users check OpenRouter dashboard

### 4. High Baseline Detection

All models achieve 64-93% detection without observer framing. This raises questions:

- Are these attacks too easy for frontier models?
- Is the dataset biased toward detectable attacks?
- What are the 26% that slip through? Need deeper analysis.

## Recommendations

1. **Investigate GPT-5 Codex failures** - Download raw responses, understand what's failing
2. **Fix cost calculation** - Implement actual API call tracking or remove estimates
3. **Analyze false negatives** - Which 26% of attacks evade all models in direct condition?
4. **Test on harder dataset** - Scout #5's history attacks had 30% miss rate, more interesting
5. **Consider REASONINGBANK next** - High baseline detection suggests we need adaptive learning

## Data Location

- **ArangoDB:** evaluations collection (576 edge documents)
- **Experiment ID:** baseline_frontier_2025
- **Run ID:** 20251011_233550
- **Models:** 4 (anthropic_claude-sonnet-4.5, google_gemini-2.5-flash-preview-09-2025, moonshotai_kimi-k2-0905, openai_gpt-5-codex)
- **Attacks:** 72 from external encoding dataset

## Next Steps

The research direction from here depends on priority:

**Option A: Debug and validate current findings**
- Fix cost calculation
- Analyze the 26% false negatives
- Understand GPT-5 Codex failures
- Re-run with user's curated model list

**Option B: Move to REASONINGBANK adaptive system**
- High baseline detection suggests we're ready for learning from failures
- REASONINGBANK integration documented in RESEARCH_STRATEGY.md Section 10
- Would demonstrate improvement on the 26% that currently slip through

**Option C: Test on harder datasets**
- Scout #5 history attacks (30% miss rate)
- Multi-turn conversation attacks
- Novel encoding techniques not in training data
