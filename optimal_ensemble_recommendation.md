# Optimal Ensemble Recommendation

## Executive Summary

**Best 2-model ensemble:** ['moonshotai/kimi-k2-0905', 'deepseek/deepseek-v3.1-terminus']
- Coverage: 51.9%
- Cost: $0.0040/eval
- Pairwise agreement: 74.3%

**Best 3-model ensemble:** ['moonshotai/kimi-k2-0905', 'deepseek/deepseek-v3.1-terminus', 'openai/gpt-4o']
- Coverage: 52.7%
- Cost: $0.0120/eval
- Avg pairwise agreement: 71.0%

**Current 4-model ensemble:** ['anthropic/claude-sonnet-4.5', 'moonshotai/kimi-k2-0905', 'deepseek/deepseek-v3.1-terminus', 'openai/gpt-4o']
- Coverage: 58.2%
- Cost: $0.0270/eval
- Avg pairwise agreement: 73.2%

**2-model savings:** 85.2% cost reduction, 6.3% coverage loss

**3-model savings:** 55.6% cost reduction, 5.4% coverage loss

## Detailed Analysis

### 2-Model Optimum

Models: ['moonshotai/kimi-k2-0905', 'deepseek/deepseek-v3.1-terminus']

- **Coverage:** 51.9% of attacks detected (union)
- **Cost:** $0.0040 per evaluation
- **Pairwise agreement:** 74.3%
- **Optimization score:** 74.4298

Unique contributions:
- moonshotai/kimi-k2-0905: 17.4%
- deepseek/deepseek-v3.1-terminus: 8.4%

### 3-Model Optimum

Models: ['moonshotai/kimi-k2-0905', 'deepseek/deepseek-v3.1-terminus', 'openai/gpt-4o']

- **Coverage:** 52.7% of attacks detected (union)
- **Cost:** $0.0120 per evaluation
- **Avg pairwise agreement:** 71.0%
- **Optimization score:** 25.6933

Unique contributions:
- moonshotai/kimi-k2-0905: 13.6%
- deepseek/deepseek-v3.1-terminus: 7.7%
- openai/gpt-4o: 0.8%

### Current 4-Model Baseline

Models: ['anthropic/claude-sonnet-4.5', 'moonshotai/kimi-k2-0905', 'deepseek/deepseek-v3.1-terminus', 'openai/gpt-4o']

- **Coverage:** 58.2% of attacks detected (union)
- **Cost:** $0.0270 per evaluation
- **Avg pairwise agreement:** 73.2%
- **Optimization score:** 12.4401

Unique contributions:
- anthropic/claude-sonnet-4.5: 5.4%
- moonshotai/kimi-k2-0905: 7.7%
- deepseek/deepseek-v3.1-terminus: 4.4%
- openai/gpt-4o: 0.6%

## Recommendation

**Keep 4-model ensemble** (['anthropic/claude-sonnet-4.5', 'moonshotai/kimi-k2-0905', 'deepseek/deepseek-v3.1-terminus', 'openai/gpt-4o'])

Rationale: Coverage loss from smaller ensembles exceeds cost savings benefit.
