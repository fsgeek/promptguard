# OpenRouter Model Pricing Analysis for PromptGuard Validation

**Analysis Date:** October 2, 2025
**Evaluation Parameters:** 557 input tokens + 244 output tokens per evaluation
**Current Reference:** Claude 3.5 Sonnet (~$0.005 per evaluation)

## Executive Summary

This analysis evaluates OpenRouter's model pricing for PromptGuard's neutrosophic LLM evaluation pipeline. We analyzed 50+ models across multiple families (Claude, GPT, Gemini, Llama, Mistral, DeepSeek, Qwen) to identify cost-effective options for validation testing.

**Key Findings:**
- **16 free models** available for zero-cost experimentation
- Budget tier models (<$0.001/eval) offer **80-95% cost savings** vs current approach
- 680-prompt validation set: **$0-$2.13** (single model) vs **$3.40** (current)
- 10-model variance analysis: **$2.64-$4.10** total cost
- 50-model comprehensive testing: **$170-$400** (cost-optimized strategy)

---

## Cost Tiers Overview

### Free Tier ($0)
**16 models with zero cost per evaluation**

Perfect for development, experimentation, and initial validation. Some have rate limits but sufficient for prototyping.

**Notable Free Models:**
- xAI Grok 4 Fast (2M context, reasoning support)
- DeepSeek V3.1 (163K context, strong reasoning)
- Qwen3 Coder 480B (262K context, coding focus)
- Mistral Small 3.2 24B (131K context)
- Google Gemma 3n 2B (lightweight)

**Capabilities:** JSON output, structured outputs, tool calling, reasoning modes

### Budget Tier (<$0.001/eval)
**11 models averaging $0.0001-$0.0004 per evaluation**

Exceptional value for high-volume testing. 70-92% cost savings vs current baseline.

**Top Budget Models:**

| Model | Cost/Eval | Input/1M | Output/1M | Context | Best For |
|-------|-----------|----------|-----------|---------|----------|
| Tongyi DeepResearch 30B A3B | $0.000148 | $0.09 | $0.40 | 131K | Agentic search, reasoning |
| Gemini 2.5 Flash Lite | $0.000153 | $0.10 | $0.40 | 1M | Fast, efficient reasoning |
| Cydonia 24B V4.1 | $0.000206 | $0.15 | $0.50 | 131K | Creative, uncensored |
| xAI Grok 4 Fast | $0.000233 | $0.20 | $0.50 | 2M | Reasoning, multimodal |
| DeepSeek V3.2 Exp | $0.000248 | $0.27 | $0.40 | 163K | Experimental reasoning |
| DeepSeek V3.1 Terminus | $0.000348 | $0.23 | $0.90 | 163K | Tool use, coding agents |

### Mid Tier ($0.001-$0.003/eval)
**3 models for balanced performance and cost**

| Model | Cost/Eval | Input/1M | Output/1M | Context | Best For |
|-------|-----------|----------|-----------|---------|----------|
| Qwen3 VL 235B Instruct | $0.000533 | $0.30 | $1.50 | 131K | Multimodal vision+text |
| Qwen3 Coder Flash | $0.000533 | $0.30 | $1.50 | 128K | Fast coding tasks |
| Gemini 2.5 Flash | $0.000777 | $0.30 | $2.50 | 1M | Advanced reasoning |
| Qwen3 Coder Plus | $0.001777 | $1.00 | $5.00 | 128K | Coding agent workflows |
| Qwen3 Max | $0.002132 | $1.20 | $6.00 | 256K | Multi-task excellence |

### Premium Tier (>$0.003/eval)
**Flagship models for critical evaluations**

| Model | Cost/Eval | Input/1M | Output/1M | Context | Best For |
|-------|-----------|----------|-----------|---------|----------|
| GPT-5 Codex | $0.003136 | $1.25 | $10.00 | 400K | Advanced coding, reasoning |
| Claude Sonnet 4.5 | $0.005331 | $3.00 | $15.00 | 1M | Production agents, coding |
| GPT-4o | ~$0.007000 | $2.50 | $10.00 | 128K | General multimodal |
| Claude Opus 4 | ~$0.012000 | $15.00 | $75.00 | 200K | World's best coding |

---

## Budget Calculations for PromptGuard Validation

### Single Model Testing (680 prompts)

| Scenario | Model Example | Cost/Eval | Total Cost | vs Current |
|----------|--------------|-----------|------------|------------|
| **Free** | xAI Grok 4 Fast | $0 | **$0** | -100% |
| **Budget** | Tongyi DeepResearch | $0.000148 | **$0.10** | -97% |
| **Mid-Tier** | Qwen3 VL Instruct | $0.000533 | **$0.36** | -89% |
| **Current** | Claude 3.5 Sonnet | $0.005000 | **$3.40** | baseline |
| **Premium** | GPT-5 Codex | $0.003136 | **$2.13** | -37% |

**Recommendation:** Start with free models for development, use budget tier for production validation.

### 10-Model Variance Analysis (6,800 evaluations)

Testing neutrosophic score variance across different model families and capabilities.

| Strategy | Composition | Avg Cost/Eval | Total Cost |
|----------|-------------|---------------|------------|
| **Cost-Optimized** | 3 free + 7 budget | $0.000227 | **$1.54** |
| **Balanced** | 2 free + 5 budget + 3 mid | $0.000603 | **$4.10** |
| **Budget Focus** | 10 budget tier only | $0.000388 | **$2.64** |
| **Mixed Quality** | 5 free + 3 budget + 2 premium | $0.001200 | **$8.16** |

**Recommended 10-Model Mix:**
1. xAI Grok 4 Fast (free) - reasoning baseline
2. DeepSeek V3.1 (free) - open source reasoning
3. Qwen3 Coder (free) - coding evaluation
4. Tongyi DeepResearch (budget) - agentic search
5. Gemini 2.5 Flash Lite (budget) - Google ecosystem
6. DeepSeek V3.2 Exp (budget) - experimental features
7. Grok 4 Fast paid (budget) - enhanced capabilities
8. Qwen3 VL Instruct (mid) - multimodal validation
9. Gemini 2.5 Flash (mid) - advanced reasoning
10. GPT-5 Codex (premium) - frontier model comparison

**Total: ~$4.10** for 6,800 evaluations

### 50-Model Comprehensive Landscape (34,000 evaluations)

Full spectrum analysis across all major families and capabilities.

| Strategy | Model Distribution | Avg Cost/Eval | Total Cost |
|----------|-------------------|---------------|------------|
| **Ultra-Budget** | 20 free + 30 cheapest paid | $0.000150 | **$5.10** |
| **Cost-Optimized** | 10 free + 25 budget + 10 mid + 5 premium | $0.000500 | **$17.00** |
| **Balanced Quality** | 5 free + 30 budget + 10 mid + 5 premium | $0.000750 | **$25.50** |
| **Full Spectrum** | Representative sampling all tiers | $0.001200 | **$40.80** |

**Recommended 50-Model Strategy (Cost-Optimized):**

**Free Tier (10 models):** $0
- All major free models for baseline comparisons

**Budget Tier (25 models):** ~$6.38
- Complete coverage of DeepSeek, Qwen, early Gemini, Mistral variants
- Focus on diverse architectures and training approaches

**Mid Tier (10 models):** ~$6.22
- Qwen3 family variants (VL, Coder, Max)
- Gemini 2.5 Flash variants
- Mistral Medium/Devstral

**Premium Tier (5 models):** ~$4.40
- GPT-5 Codex, Mini
- Claude Sonnet 4.5
- Gemini Pro
- Qwen Plus reasoning

**Total: ~$17.00** for 34,000 evaluations (50 models × 680 prompts)

---

## Model Family Analysis

### Claude (Anthropic)
**Strengths:** Best-in-class coding, long context, sustained performance
**Pricing:** Premium tier ($3-15/M input, $15-75/M output)
**Use Case:** Final validation, production benchmarks

| Model | Cost/Eval | Context | Best For |
|-------|-----------|---------|----------|
| Claude Opus 4 | $0.012000 | 200K | World's best coding (72.5% SWE-bench) |
| Claude Sonnet 4.5 | $0.005331 | 1M | Production agents, coding workflows |
| Claude Haiku 3.5 | $0.002532 | 200K | Speed + efficiency |

### OpenAI (GPT)
**Strengths:** Multimodal, general purpose, tool calling
**Pricing:** Mid to Premium tier ($1.25-15/M input, $5-30/M output)
**Use Case:** General validation, multimodal testing

| Model | Cost/Eval | Context | Best For |
|-------|-----------|---------|----------|
| GPT-5 Codex | $0.003136 | 400K | Advanced coding + reasoning |
| GPT-5 Nano | $0.000125 | 400K | Cost-efficient testing |
| GPT-5 Mini | $0.000627 | 400K | Balanced performance |
| gpt-oss-120b (free) | $0 | 32K | Free experimentation |

### Google (Gemini)
**Strengths:** Long context (1M), fast, reasoning
**Pricing:** Budget to Mid tier ($0.10-0.30/M input, $0.40-2.50/M output)
**Use Case:** High-volume testing, long-context validation

| Model | Cost/Eval | Context | Best For |
|-------|-----------|---------|----------|
| Gemini 2.5 Flash Lite | $0.000153 | 1M | Ultra-low latency |
| Gemini 2.5 Flash | $0.000777 | 1M | Advanced reasoning |
| Gemini 2.5 Flash Preview | $0.000777 | 1M | Latest features |

### DeepSeek
**Strengths:** Open source, strong reasoning, coding
**Pricing:** Free to Budget tier ($0-0.27/M input, $0-1.10/M output)
**Use Case:** Budget-conscious testing, open-source comparison

| Model | Cost/Eval | Context | Best For |
|-------|-----------|---------|----------|
| DeepSeek V3.1 (free) | $0 | 163K | Free reasoning |
| DeepSeek V3.2 Exp | $0.000248 | 163K | Experimental features |
| DeepSeek V3.1 Terminus | $0.000348 | 163K | Tool use, agents |
| DeepSeek Coder V2 | $0.000354 | 163K | Cost-effective coding |

### Qwen (Alibaba)
**Strengths:** Coding, multilingual, long context
**Pricing:** Free to Mid tier ($0-1.20/M input, $0-6.00/M output)
**Use Case:** Coding validation, multimodal, multilingual

| Model | Cost/Eval | Context | Best For |
|-------|-----------|---------|----------|
| Qwen3 Coder (free) | $0 | 262K | Free coding evaluation |
| Qwen3 VL Instruct | $0.000533 | 131K | Multimodal vision+text |
| Qwen3 Coder Flash | $0.000533 | 128K | Fast coding tasks |
| Qwen3 Coder Plus | $0.001777 | 128K | Advanced coding agents |
| Qwen3 Max | $0.002132 | 256K | Multi-task excellence |

### xAI (Grok)
**Strengths:** Large context (2M), reasoning, multimodal
**Pricing:** Free to Budget tier ($0-0.30/M input, $0-1.50/M output)
**Use Case:** Long-context testing, reasoning evaluation

| Model | Cost/Eval | Context | Best For |
|-------|-----------|---------|----------|
| Grok 4 Fast (free) | $0 | 2M | Free long-context |
| Grok 4 Fast | $0.000233 | 2M | Budget reasoning |
| Grok 3 Mini | $0.000289 | 131K | Fast inference |
| Grok Code Fast 1 | $0.000477 | 256K | Coding tasks |

### Mistral
**Strengths:** European AI, balanced performance
**Pricing:** Free to Mid tier ($0-0.40/M input, $0-2.00/M output)
**Use Case:** Code generation, general purpose

| Model | Cost/Eval | Context | Best For |
|-------|-----------|---------|----------|
| Mistral Small 3.2 (free) | $0 | 131K | Free experimentation |
| Mistral Small 3.2 | $0.000077 | 131K | Budget general use |
| Devstral Small | $0.000107 | 128K | Code generation |
| Codestral 2508 | $0.000387 | 256K | Advanced coding |
| Mistral Medium 3.1 | $0.000711 | 131K | General excellence |

---

## Capabilities Matrix

### JSON Output & Structured Responses
**All analyzed models** support JSON output via:
- `response_format` parameter
- `structured_outputs` for schema enforcement
- Native JSON generation

**Recommended Models:**
- Free: DeepSeek V3.1, Qwen3 Coder, Mistral Small
- Budget: Gemini 2.5 Flash Lite, DeepSeek V3.2
- Premium: Claude Sonnet 4.5, GPT-5 Codex

### Reasoning & Chain-of-Thought
Models with explicit reasoning support via `reasoning` parameter:

| Model | Reasoning Type | Cost Impact |
|-------|---------------|-------------|
| Grok 4 Fast | Configurable | None (same pricing) |
| DeepSeek V3.1 | Toggle on/off | None |
| Gemini 2.5 Flash | Max tokens control | Additional output tokens |
| GPT-5 Codex | Effort level | Higher output usage |
| Claude Sonnet 4.5 | Built-in | Premium pricing |

### Tool Calling & Function Support
All major families support:
- `tools` parameter for function definitions
- `tool_choice` for selection strategy
- Parallel tool calling (most models)

**Best for Tool Use:**
- DeepSeek V3.1 Terminus (optimized for agents)
- Claude Sonnet 4.5 (best orchestration)
- Qwen3 Coder Plus (coding tools)
- Gemini 2.5 Flash (general tools)

### Long Context Support

| Context Length | Models | Use Case |
|---------------|--------|----------|
| 1M+ tokens | Gemini 2.5, Grok 4, Qwen Plus | Document analysis |
| 256K+ tokens | Qwen3, Mistral, GPT-5 | Large codebases |
| 128K-163K | DeepSeek, Mistral, Qwen | Standard tasks |
| <128K | Most others | Typical prompts |

### Multimodal Capabilities

**Vision + Text:**
- Grok 4 Fast (free/budget, 2M context)
- Qwen3 VL family (mid tier)
- Gemini 2.5 Flash (mid tier)
- Claude Sonnet 4.5 (premium)
- GPT-5 family (premium)

**Image Pricing:**
- Gemini: $0.001238 per image
- Claude: $0.0048 per image
- GPT-5: Varies by resolution

---

## Recommendations by Use Case

### For Development & Prototyping
**Priority:** Zero cost, reasonable quality

**Recommended Models:**
1. xAI Grok 4 Fast (free) - best free reasoning
2. DeepSeek V3.1 (free) - strong open-source baseline
3. Qwen3 Coder (free) - coding-specific tasks
4. Mistral Small 3.2 (free) - general purpose

**Cost:** $0 for unlimited development iterations

### For Initial Validation (680 prompts)
**Priority:** Cost efficiency, reliability

**Recommended Approach:**
1. Run all free models first ($0)
2. Add 5-10 budget models ($0.10-$2.00)
3. Include 1-2 premium for comparison ($2.00-$3.50)

**Total Cost:** $2.10-$5.50

### For Production Benchmarking
**Priority:** Quality, reproducibility

**Recommended Models:**
1. Claude Sonnet 4.5 (current standard)
2. GPT-5 Codex (coding comparison)
3. Gemini 2.5 Flash (Google baseline)
4. DeepSeek V3.1 Terminus (open-source benchmark)
5. Qwen3 Max (multilingual validation)

**Cost per 680 prompts:** $6.00-$10.00

### For Variance Analysis (10+ models)
**Priority:** Diversity, statistical significance

**Recommended Mix:**
- 2-3 free models (baseline diversity)
- 5-6 budget models (cost-effective coverage)
- 2-3 mid/premium (quality anchors)

**Cost for 10 models:** $2.64-$8.16

### For Comprehensive Testing (50+ models)
**Priority:** Complete landscape understanding

**Recommended Strategy:**
1. All 16 free models ($0)
2. Top 20 budget models by diversity (~$3.00)
3. All mid-tier variants (~$8.00)
4. 5-10 premium for benchmarks (~$6.00)

**Total Cost:** $17.00-$25.00

---

## Cost Optimization Strategies

### 1. Tiered Testing Approach
**Save 70-90% by staging evaluations**

**Stage 1 - Free Filter (16 models):**
- Cost: $0
- Purpose: Identify obviously bad prompts, test methodology
- Filter out: Clear failures, format issues

**Stage 2 - Budget Validation (10 models):**
- Cost: $2.64
- Purpose: Core variance analysis
- Models: Mix of free + budget tier

**Stage 3 - Premium Confirmation (3-5 models):**
- Cost: $2.00-$5.00
- Purpose: Final validation against production standards
- Models: Claude, GPT-5, Gemini Pro

**Total Savings:** 85% vs running all premium

### 2. Smart Model Selection
**Match model capabilities to task requirements**

- **Simple classification:** Free/budget models sufficient
- **Complex reasoning:** Mid/premium required
- **Coding evaluation:** Use coding-specific models
- **Multimodal:** Only use when needed (higher cost)

### 3. Batch Processing
**Leverage OpenRouter features:**

- Use `temperature=0` for deterministic results (no re-runs needed)
- Enable prompt caching for repeated contexts (50-80% savings on input)
- Batch related prompts together
- Use structured outputs to reduce parsing failures

### 4. Sampling Strategies
**Don't test every prompt on every model:**

- Full testing on free models (no cost penalty)
- 50% sampling on budget models (50% cost reduction)
- 20% sampling on premium models (80% cost reduction)
- Focus premium on edge cases and challenging prompts

**Example:** 680 prompts, 20 models
- 16 free: 680 prompts each = 10,880 evals ($0)
- 4 budget: 340 prompts each = 1,360 evals ($0.53)
- 5 premium: 136 prompts each = 680 evals ($3.40)

**Total:** $3.93 vs $51.00 (92% savings)

### 5. Model Rotation
**Rotate models over time rather than testing all at once:**

- Month 1: Free + 5 budget models
- Month 2: Different 5 budget + 3 mid
- Month 3: 2 mid + 3 premium
- Month 4: Rotate back with improvements

**Benefit:** Spread costs, adapt to model improvements, learn incrementally

---

## Risk Considerations

### Free Model Limitations

**Rate Limits:**
- Most free models have daily/hourly limits
- May queue during peak times
- Not suitable for time-sensitive production

**Data Privacy:**
- Free models may use prompts for training
- Check provider policies for sensitive data
- Consider paid tiers for production use

**Availability:**
- No SLA guarantees
- May be deprecated with short notice
- Performance can vary by region

**Mitigation:**
- Use free for development only
- Test rate limits early
- Have paid fallback options ready

### Budget Model Considerations

**Quality Variance:**
- Cheaper models may have higher failure rates
- Test thoroughly before production use
- Monitor output quality metrics

**Feature Support:**
- Not all support advanced features (reasoning, multimodal)
- Verify capabilities before committing
- Have fallback for unsupported features

**Provider Reliability:**
- Smaller providers may have uptime issues
- Monitor provider health status
- Use multiple providers for redundancy

### Cost Prediction Challenges

**Token Count Variation:**
- Different tokenizers = different token counts
- Same prompt can vary 10-30% across models
- Budget with 20% buffer

**Output Length Unpredictability:**
- Models vary in verbosity
- Reasoning models can generate much more output
- Monitor actual usage vs estimates

**Pricing Changes:**
- Providers update pricing regularly
- Free tiers can become paid
- Monitor OpenRouter announcements

---

## Implementation Checklist

### Phase 1: Setup (Week 1)
- [ ] Review full model list on OpenRouter
- [ ] Test API access with free models
- [ ] Validate JSON output format across 3-5 models
- [ ] Measure actual token usage vs estimates
- [ ] Document baseline performance metrics

### Phase 2: Development (Weeks 2-3)
- [ ] Implement evaluation pipeline with free models
- [ ] Test neutrosophic score generation across model families
- [ ] Identify problematic prompts/responses
- [ ] Refine prompt templates for consistency
- [ ] Build cost tracking dashboard

### Phase 3: Validation (Week 4)
- [ ] Run full 680 prompts on 3 free models
- [ ] Add 5 budget models for comparison
- [ ] Analyze score variance and quality
- [ ] Document failure modes by model
- [ ] Calculate actual costs vs predictions

### Phase 4: Production (Week 5+)
- [ ] Select final model mix (10-20 models)
- [ ] Set up monitoring and alerting
- [ ] Implement cost controls and budgets
- [ ] Schedule regular re-validation cycles
- [ ] Document model selection rationale

---

## Monitoring & Optimization

### Key Metrics to Track

**Cost Metrics:**
- Cost per evaluation by model
- Daily/weekly total spend
- Cost per neutrosophic score component
- Budget utilization rate

**Quality Metrics:**
- JSON parse success rate
- Score variance by model family
- Correlation with ground truth (if available)
- Outlier detection rate

**Performance Metrics:**
- Latency per model
- Timeout rate
- Retry rate
- Throughput (evals/hour)

### Optimization Triggers

**When to switch to cheaper models:**
- Quality metrics stable across tiers
- Cost exceeds budget
- Development phase complete
- High-volume testing needed

**When to upgrade to premium:**
- Quality gaps detected
- Production deployment
- Critical decisions needed
- Regulatory/compliance requirements

### Regular Reviews

**Monthly:**
- Review cost trends
- Evaluate new models on OpenRouter
- Update model mix based on performance
- Adjust budgets based on usage

**Quarterly:**
- Full re-validation of model selection
- Cost-benefit analysis vs direct API access
- Evaluate alternative providers
- Update documentation

---

## Additional Resources

### OpenRouter Documentation
- API Reference: https://openrouter.ai/docs/api-reference
- Model Catalog: https://openrouter.ai/models
- Pricing: https://openrouter.ai/models?fmt=table
- Usage Tracking: https://openrouter.ai/usage

### Model Provider Documentation
- Anthropic Claude: https://docs.anthropic.com/
- OpenAI: https://platform.openai.com/docs/
- Google Gemini: https://ai.google.dev/docs
- DeepSeek: https://platform.deepseek.com/docs/
- Qwen: https://qwen.readthedocs.io/
- xAI: https://docs.x.ai/

### Cost Tracking Tools
- OpenRouter Dashboard: Built-in usage analytics
- LangSmith: LLM observability and cost tracking
- Helicone: Gateway with cost monitoring
- Custom dashboards: Prometheus + Grafana

---

## Appendix A: Complete Model Pricing Table

See `/home/tony/projects/promptguard/config/model_configs.json` for machine-readable format.

## Appendix B: Calculation Methodology

**Base Assumptions:**
- Input tokens: 557 per evaluation
- Output tokens: 244 per evaluation
- No caching (conservative estimate)
- No multimodal images (unless specified)

**Cost Formula:**
```
cost_per_eval = (input_tokens / 1_000_000) × input_price_per_1M +
                (output_tokens / 1_000_000) × output_price_per_1M
```

**Budget Calculations:**
```
total_cost = cost_per_eval × num_prompts × num_models
```

**Variance Analysis:**
Multiple models tested, averaged, then multiplied by test set size.

---

## Appendix C: Model Selection Decision Tree

```
START
  |
  ├─ Development/Prototyping?
  │    └─> Use FREE models (Grok 4, DeepSeek V3.1, Qwen3 Coder)
  |
  ├─ Budget < $1 for 680 prompts?
  │    └─> Use BUDGET tier (Tongyi, Gemini Lite, DeepSeek variants)
  |
  ├─ Need multimodal/vision?
  │    └─> Qwen3 VL ($0.53) or Gemini 2.5 Flash ($0.78)
  |
  ├─ Need best coding performance?
  │    └─> GPT-5 Codex ($2.13) or Claude Sonnet 4.5 ($3.63)
  |
  ├─ Need variance analysis (10+ models)?
  │    └─> Mixed strategy: 3 free + 5 budget + 2 premium ($4.10)
  |
  └─ Comprehensive testing (50+ models)?
       └─> Cost-optimized: 10 free + 25 budget + 10 mid + 5 premium ($17.00)
```

---

**Document Version:** 1.0
**Last Updated:** October 2, 2025
**Next Review:** January 2, 2026
