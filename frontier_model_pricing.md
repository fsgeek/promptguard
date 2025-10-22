# Frontier Model Pricing and Availability
## Query Date: 2025-10-20

### Requested Models

#### 1. Google Gemini 2.5 Pro
**Model ID:** `google/gemini-2.5-pro`
- **Input:** $1.25/M tokens
- **Output:** $10.00/M tokens
- **Context Window:** 1,048,576 tokens (1M+)
- **Modality:** text+image→text
- **Availability:** ✅ Available
- **Stability:** Stable production model
- **Notes:** State-of-the-art model for advanced reasoning, coding, mathematics, and scientific tasks

**Alternative:** `google/gemini-2.5-pro-preview-05-06` (same pricing, preview version)

#### 2. xAI Grok 4 (Full Version)
**Model ID:** `x-ai/grok-4`
- **Input:** $3.00/M tokens
- **Output:** $15.00/M tokens
- **Context Window:** 256,000 tokens (256K)
- **Modality:** text+image→text
- **Availability:** ✅ Available
- **Stability:** Stable
- **Notes:** Latest flagship model from xAI

**Budget Alternative:** `x-ai/grok-4-fast` - $0.20 input / $0.50 output, 2M context (not suitable for flagship experiments)

#### 3. MoonshotAI Kimi K2-0905
**Model ID:** `moonshotai/kimi-k2-0905`
- **Input:** $0.39/M tokens
- **Output:** $1.90/M tokens
- **Context Window:** 262,144 tokens (262K)
- **Modality:** text→text
- **Availability:** ✅ Available
- **Stability:** Stable (September 2025 checkpoint)
- **Notes:**
  - 1T total parameters, 32B active (MoE architecture)
  - Optimized for agentic capabilities, tool use, reasoning, code synthesis
  - Expanded context from 128K→262K vs previous K2 version
  - Available via multiple providers (Groq at ~349 TPS, Moonshot, OpenRouter, Fireworks)
  - Strong performance on coding (LiveCodeBench, SWE-bench), reasoning (ZebraLogic, GPQA), tool-use (Tau2, AceBench)

**Previous Version:** `moonshotai/kimi-k2` - $0.14 input / $2.49 output, 63K context (July checkpoint, smaller context)

---

### GPT-5-Pro Replacement Candidates

#### Current GPT-5 Pro Pricing (Baseline)
**Model ID:** `openai/gpt-5-pro`
- **Input:** $15.00/M tokens
- **Output:** $120.00/M tokens
- **Context Window:** 400,000 tokens (400K)
- **Modality:** text+image→text
- **Availability:** ✅ Available
- **Cost Profile:** Most expensive option ($120/M output)

---

#### Tier 1: Premium Flagship Models (Similar or Better Capability)

##### Anthropic Claude Sonnet 4.5
**Model ID:** `anthropic/claude-sonnet-4.5`
- **Input:** $3.00/M tokens (-80% vs GPT-5)
- **Output:** $15.00/M tokens (-87.5% vs GPT-5)
- **Context Window:** 1,000,000 tokens (+150% vs GPT-5)
- **Modality:** text+image→text
- **Availability:** ✅ Available
- **Cost Advantage:** 87.5% cheaper output, 2.5x larger context
- **Notes:** Latest Sonnet version, exceptional reasoning and analysis

##### Anthropic Claude Opus 4.1
**Model ID:** `anthropic/claude-opus-4.1`
- **Input:** $15.00/M tokens (same as GPT-5)
- **Output:** $75.00/M tokens (-37.5% vs GPT-5)
- **Context Window:** 200,000 tokens (-50% vs GPT-5)
- **Modality:** text+image→text
- **Availability:** ✅ Available
- **Cost Advantage:** 37.5% cheaper output, same input cost
- **Notes:** Highest capability Anthropic model, better for complex tasks

**Alternative:** `anthropic/claude-opus-4` - same pricing

##### Google Gemini 2.5 Pro
**Model ID:** `google/gemini-2.5-pro`
- **Input:** $1.25/M tokens (-92% vs GPT-5)
- **Output:** $10.00/M tokens (-92% vs GPT-5)
- **Context Window:** 1,048,576 tokens (+162% vs GPT-5)
- **Modality:** text+image→text
- **Availability:** ✅ Available
- **Cost Advantage:** 92% cheaper, 2.6x larger context
- **Notes:** Best cost/performance for flagship capability

##### xAI Grok 4
**Model ID:** `x-ai/grok-4`
- **Input:** $3.00/M tokens (-80% vs GPT-5)
- **Output:** $15.00/M tokens (-87.5% vs GPT-5)
- **Context Window:** 256,000 tokens (-36% vs GPT-5)
- **Modality:** text+image→text
- **Availability:** ✅ Available
- **Cost Advantage:** 87.5% cheaper output
- **Notes:** Latest xAI flagship

---

#### Tier 2: Reasoning-Focused Models

##### OpenAI o3 Pro
**Model ID:** `openai/o3-pro`
- **Input:** $20.00/M tokens (+33% vs GPT-5)
- **Output:** $80.00/M tokens (-33% vs GPT-5)
- **Context Window:** 200,000 tokens (-50% vs GPT-5)
- **Modality:** text+image→text
- **Availability:** ✅ Available
- **Notes:** Latest reasoning model, successor to o1

##### OpenAI o1
**Model ID:** `openai/o1`
- **Input:** $15.00/M tokens (same as GPT-5)
- **Output:** $60.00/M tokens (-50% vs GPT-5)
- **Context Window:** 200,000 tokens (-50% vs GPT-5)
- **Modality:** text+image→text
- **Availability:** ✅ Available
- **Cost Advantage:** 50% cheaper output
- **Notes:** Reasoning-focused, may not be ideal for Fire Circle dialogue

##### OpenAI o1-pro
**Model ID:** `openai/o1-pro`
- **Input:** $150.00/M tokens (+900% vs GPT-5)
- **Output:** $600.00/M tokens (+400% vs GPT-5)
- **Context Window:** 200,000 tokens (-50% vs GPT-5)
- **Modality:** text+image→text
- **Availability:** ✅ Available
- **Notes:** Most expensive option, reasoning-heavy workloads only

---

#### Tier 3: Budget Flagship Alternatives

##### DeepSeek V3.2 Exp
**Model ID:** `deepseek/deepseek-v3.2-exp`
- **Input:** $0.27/M tokens (-98% vs GPT-5)
- **Output:** $0.40/M tokens (-99.7% vs GPT-5)
- **Context Window:** 163,840 tokens (-59% vs GPT-5)
- **Modality:** text→text
- **Availability:** ✅ Available
- **Cost Advantage:** 99.7% cheaper
- **Notes:** Experimental, strong performance for cost

##### MoonshotAI Kimi K2-0905
**Model ID:** `moonshotai/kimi-k2-0905`
- **Input:** $0.39/M tokens (-97% vs GPT-5)
- **Output:** $1.90/M tokens (-98.4% vs GPT-5)
- **Context Window:** 262,144 tokens (-34% vs GPT-5)
- **Modality:** text→text
- **Availability:** ✅ Available
- **Cost Advantage:** 98.4% cheaper
- **Notes:** 1T MoE model, strong agentic capabilities

---

### Recommended Fire Circle Configuration

**For Maximum Diversity (GPT-5 Replacement):**

1. **Anthropic Claude Sonnet 4.5** - Best cost/performance, 1M context
2. **Google Gemini 2.5 Pro** - Cheapest flagship, 1M context
3. **Anthropic Claude Opus 4.1** - Highest capability, different architecture
4. **xAI Grok 4** - Different training approach, strong reasoning

**Cost Comparison (per 1M tokens, assuming 1:1 input/output ratio):**
- GPT-5 Pro: $67.50
- Sonnet 4.5: $9.00 (-87%)
- Gemini 2.5 Pro: $5.62 (-92%)
- Opus 4.1: $45.00 (-33%)
- Grok 4: $9.00 (-87%)
- **4-model basket average:** $17.16 (-75% vs GPT-5 Pro)

---

### Models NOT Available

❌ **google/gemini-2.0-flash-exp** - Only available as free tier (`google/gemini-2.0-flash-exp:free`)
❌ **google/gemini-exp-1206** - Not found in OpenRouter catalog (may be deprecated)

**Available Gemini Alternatives:**
- `google/gemini-2.5-pro` (flagship)
- `google/gemini-2.5-flash-preview-09-2025` ($0.30/$2.50, 1M context)
- `google/gemini-2.0-flash-exp:free` (free tier, 1M context)

---

### Key Findings

1. **All requested models available** except deprecated Gemini variants
2. **GPT-5 Pro is most expensive option** by far ($120/M output)
3. **Gemini 2.5 Pro offers best value** - 92% cheaper with larger context
4. **Claude Sonnet 4.5 best balanced option** - 87.5% cheaper, 1M context, proven capability
5. **Kimi K2-0905 is budget flagship** - 98% cheaper, strong agentic performance
6. **All models have multimodal support** except Kimi K2 and DeepSeek (text-only)
7. **No reported stability issues** for any flagship models

### Recommendations

**For Fire Circle experiments requiring flagship diversity:**
- Replace GPT-5 Pro with **4-model basket** (Sonnet 4.5, Gemini 2.5 Pro, Opus 4.1, Grok 4)
- **75% cost reduction** with better architectural diversity
- All models have 200K+ context windows (sufficient for deliberation history)

**For budget-conscious research:**
- Use **Gemini 2.5 Pro** as single flagship replacement (92% cheaper)
- Or **Sonnet 4.5** for proven reliability (87.5% cheaper)

**For maximum cost savings:**
- Use **Kimi K2-0905** (98% cheaper, strong performance)
- Or **DeepSeek V3.2** (99.7% cheaper, experimental but capable)
