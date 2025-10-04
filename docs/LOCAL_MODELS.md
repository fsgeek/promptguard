# Local Model Support

PromptGuard supports local model hosting via LM Studio and Ollama for reproducible research and cost-free development.

## Why Local Models?

**Reproducible Research**:
- Fixed model versions (no provider updates breaking reproducibility)
- Complete control over model selection and parameters
- Can snapshot model weights for long-term reproducibility

**Zero Cost**:
- No API charges for development or validation
- Unlimited experimentation
- No rate limiting

**Data Privacy**:
- Prompts never leave your infrastructure
- Critical for sensitive evaluation datasets
- Important ethical consideration: Attack pattern datasets shouldn't train external models

**Research Independence**:
- Not dependent on external provider availability
- No model churn (free models appearing/disappearing)
- Can run evaluation years later with exact same model

## LM Studio Setup

### 1. Install LM Studio
Download from [https://lmstudio.ai/](https://lmstudio.ai/)

### 2. Load a Model
Recommended models for PromptGuard evaluation:
- **deepseek-r1-distill-qwen-7b**: Reasoning traces via `<think>` blocks
- **llama-3.2-3b-instruct**: Small, fast, decent quality
- **qwen-2.5-7b-instruct**: Good instruction following

### 3. Start Local Server
In LM Studio:
1. Go to "Local Server" tab
2. Select loaded model
3. Click "Start Server"
4. Note the server URL (default: `http://localhost:1234/v1`)

### 4. Configure PromptGuard

```python
from promptguard import PromptGuard, PromptGuardConfig

config = PromptGuardConfig(
    provider="lmstudio",
    lmstudio_base_url="http://localhost:1234/v1",  # Or network IP
    models=["deepseek-r1-distill-qwen-7b"],
    evaluation_type="trust_trajectory",
    max_tokens=2000  # Local models may need higher limits
)

guard = PromptGuard(config)
result = await guard.evaluate(
    prompt="Can you help me understand neural networks?"
)

print(f"Balance: {result.ayni_balance}")
print(f"Type: {result.exchange_type.value}")
```

### Environment Variable
Set `LMSTUDIO_BASE_URL` to avoid hardcoding:

```bash
export LMSTUDIO_BASE_URL="http://192.168.111.125:1234/v1"
```

## Reasoning Traces

Models like DeepSeek R1 emit internal reasoning in `<think>` blocks:

```
<think>
The user is asking an appropriate question for first contact.
No role reversal or unjustified trust claims detected.
This is a genuine reciprocal request.
</think>

{
  "truth": 0.9,
  "indeterminacy": 0.1,
  "falsehood": 0.05,
  ...
}
```

PromptGuard automatically:
1. Extracts the `<think>` block
2. Stores it in `NeutrosophicEvaluation.reasoning_trace`
3. Removes it from the parsed JSON response

This provides insight into **why** a model scored something as manipulative, not just the score.

## Model Selection for Research

**Development** (fast iteration):
- llama-3.2-3b-instruct (fast, 4GB VRAM)
- qwen-2.5-7b-instruct (balance of speed/quality)

**Validation** (research quality):
- deepseek-r1-distill-qwen-7b (reasoning traces valuable for analysis)
- llama-3.3-70b-instruct (high quality, requires GPU with 40GB+ VRAM)

**Production** (user-facing):
- Consider hybrid: local for privacy-sensitive, cloud for quality
- Document model version in results

## Cost Comparison

**680-prompt validation run**:
- OpenRouter (paid): $3.40 (Instance 7's run)
- LM Studio (local): $0 monetary, ~30 minutes GPU time
- Free OpenRouter models: $0 monetary, rate-limited/unavailable

**Trade-offs**:
- Local: Upfront hardware cost, zero marginal cost, full control
- Cloud paid: No hardware, predictable per-use cost, latest models
- Cloud free: Data becomes training corpus, availability volatile

## Network Configuration

For WSL → LM Studio on Windows host:

```bash
# Find Windows host IP from WSL
ip route show | grep -i default | awk '{ print $3}'

# Test connectivity
curl http://192.168.111.125:1234/v1/models

# Configure PromptGuard
config = PromptGuardConfig(
    provider="lmstudio",
    lmstudio_base_url="http://192.168.111.125:1234/v1",
    ...
)
```

## Ensemble with Local Models

Mix local and cloud for cost optimization:

```python
# Not yet implemented, but proposed:
config = PromptGuardConfig(
    providers=[
        {"type": "lmstudio", "url": "http://localhost:1234/v1", "model": "qwen-2.5-7b"},
        {"type": "lmstudio", "url": "http://localhost:1234/v1", "model": "llama-3.2-3b"},
        {"type": "openrouter", "model": "anthropic/claude-3.5-sonnet"}
    ],
    evaluation_type=["ayni_relational", "trust_trajectory", "relational_structure"]
)

# 2 local + 1 cloud = cheaper than 3 cloud, more reliable than 3 free cloud
```

## Reproducibility Best Practices

1. **Document exact model version**:
   ```python
   # In research paper
   "Evaluated using DeepSeek-R1-Distill-Qwen-7B
    (TheBloke/deepseek-r1-distill-qwen-7b-GGUF,
    commit a1b2c3d, Q4_K_M quantization)"
   ```

2. **Snapshot model weights**: Archive the model file with research data

3. **Version PromptGuard**: Pin to specific PromptGuard release

4. **Log full config**: Save config with results
   ```python
   results = {
       "config": asdict(config),
       "promptguard_version": "0.1.0",
       "model_sha256": "...",
       "evaluations": [...]
   }
   ```

## Limitations

**Local models may differ from cloud models**:
- Quantization affects precision
- Smaller models may miss subtle manipulation
- Cloud models benefit from larger scale training

**Solution**: Validate core findings on both local (reproducible) and cloud (state-of-art) models.

## Next Steps

- Add Ollama support (similar interface to LM Studio)
- Implement mixed provider ensembles
- Create model capability benchmarks (which models detect which attack types)
