# Config-Driven Parallel Workers

## Overview

Target response collection and post-evaluation analysis use a config-driven approach with parallel workers. Model lists are centralized in YAML configuration, eliminating hardcoded values.

## Architecture

**Before:**
- Hardcoded model lists in each script
- Adding/removing models required code changes
- No single-model testing mode

**After:**
- Model lists in `config/target_models.yaml`
- Scripts load from config at runtime
- Single-model mode via `--model` parameter
- Easy to maintain different configurations (dev/prod)

## Configuration File

**Location:** `/config/target_models.yaml`

```yaml
# Target models for baseline compliance analysis
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
    - teknium/openhermes-2.5-mistral-7b
    - deepseek/deepseek-v3-base

# Evaluation models (used for post-evaluation analysis)
evaluation_models:
  - anthropic/claude-sonnet-4.5
  - moonshotai/kimi-k2-0905
  - deepseek/deepseek-v3.1-terminus
  - openai/gpt-5
```

## Config Loader API

**Module:** `promptguard.config`

```python
from promptguard.config import (
    load_target_models,
    load_evaluation_models,
    load_model_config
)

# Load all target models
all_models = load_target_models()
# Returns: ['anthropic/claude-sonnet-4.5', 'openai/gpt-4o', ...]

# Load by RLHF category
high_rlhf = load_target_models(category="high_rlhf")
# Returns: ['anthropic/claude-sonnet-4.5', 'openai/gpt-4o']

# Load evaluation models
evaluators = load_evaluation_models()
# Returns: ['anthropic/claude-sonnet-4.5', 'moonshotai/kimi-k2-0905', ...]

# Load complete config
config = load_model_config()
# Returns: ModelConfig(target_models={...}, evaluation_models=[...])
```

## Collection Script Usage

**Script:** `collect_target_responses.py`

### Full Collection (All Models)
```bash
# All 9 target models in parallel
python collect_target_responses.py

# Test mode: 10 prompts × 9 models = 90 responses
python collect_target_responses.py --test
```

### Single Model Collection
```bash
# Single model: 478 prompts × 1 model = 478 responses
python collect_target_responses.py --model anthropic/claude-sonnet-4.5

# Single model test: 10 prompts × 1 model = 10 responses
python collect_target_responses.py --test --model openai/gpt-4o
```

### Resume from Checkpoint
```bash
# Resume all models (skips completed prompts)
python collect_target_responses.py --resume

# Resume single model
python collect_target_responses.py --model deepseek/deepseek-v3-base --resume
```

## Analysis Script Usage

**Script:** `analyze_target_responses.py`

### Full Analysis
```bash
# Analyze all target responses with all 4 evaluators
python analyze_target_responses.py

# Test mode: analyze first 18 responses (2 prompts × 9 models)
python analyze_target_responses.py --test
```

### Filter by Target Model
```bash
# Analyze only Claude's responses
python analyze_target_responses.py --model anthropic/claude-sonnet-4.5

# Analyze only DeepSeek base model responses
python analyze_target_responses.py --model deepseek/deepseek-v3-base
```

### Limit Responses
```bash
# Analyze first 50 responses (any target model)
python analyze_target_responses.py --limit 50

# Analyze first 20 Claude responses
python analyze_target_responses.py --model anthropic/claude-sonnet-4.5 --limit 20
```

## Parallel Worker Architecture

### Collection Workers

**Design:**
- N workers (one per target model)
- Each processes all 478 prompts
- Real-time persistence to ArangoDB
- Checkpoint every 50 prompts

**Example with 9 models:**
```
Worker 1 (Claude)  → 478 prompts → ArangoDB
Worker 2 (GPT-4o)  → 478 prompts → ArangoDB
Worker 3 (Kimi)    → 478 prompts → ArangoDB
...
Worker 9 (DS-base) → 478 prompts → ArangoDB
```

**Single-model mode:**
```
Worker 1 (Claude) → 478 prompts → ArangoDB
```

### Post-Evaluation Workers

**Design:**
- Each target response evaluated by 4 evaluation models
- Post-evaluation parallelizes across evaluation models
- Compares pre/post F-scores to detect divergence

**Example:**
```
Target Response (Claude responding to prompt X)
  ↓
Evaluator 1 (Claude)   → Post-F score
Evaluator 2 (Kimi)     → Post-F score
Evaluator 3 (DeepSeek) → Post-F score
Evaluator 4 (GPT-5)    → Post-F score
  ↓
Divergence Analysis (pre-F vs post-F)
```

## Adding/Removing Models

**To add a new target model:**

1. Edit `config/target_models.yaml`
2. Add model to appropriate RLHF category
3. No code changes required

```yaml
target_models:
  high_rlhf:
    - anthropic/claude-sonnet-4.5
    - openai/gpt-4o
    - anthropic/claude-opus-4  # NEW MODEL
```

**To add a new evaluation model:**

1. Edit `config/target_models.yaml`
2. Add model to `evaluation_models` list
3. No code changes required

```yaml
evaluation_models:
  - anthropic/claude-sonnet-4.5
  - moonshotai/kimi-k2-0905
  - deepseek/deepseek-v3.1-terminus
  - openai/gpt-5
  - google/gemini-2.0-flash-thinking-exp  # NEW MODEL
```

**To test single model before full run:**

```bash
# Test new model with 10 prompts
python collect_target_responses.py --test --model anthropic/claude-opus-4
```

## Configuration Validation

**Test config loading:**

```bash
python test_config_loader.py
```

**Output:**
```
================================================================================
Testing Config Loader
================================================================================

1. Loading complete config...
   ✓ Config loaded successfully
   - RLHF categories: ['high_rlhf', 'moderate_rlhf', 'low_rlhf', 'non_rlhf']
   - Total target models: 9
   - Evaluation models: 4

2. Loading all target models...
   ✓ Loaded 9 target models:
     - anthropic/claude-sonnet-4.5
     - openai/gpt-4o
     ...

✓ All tests passed!
```

## Benefits

1. **Centralized Configuration**
   - Single source of truth for model lists
   - Easy to update without code changes
   - Version control for model changes

2. **Single-Model Testing**
   - Test new models before full runs
   - Debug model-specific issues
   - Faster iteration during development

3. **Parallel Efficiency**
   - N workers process in parallel (N = number of models)
   - Real-time persistence prevents data loss
   - Resume capability for interrupted runs

4. **Flexible Filtering**
   - By RLHF category (high/moderate/low/non)
   - By specific model
   - By response count (--limit)

5. **Maintainability**
   - No hardcoded model lists
   - Config changes don't require code review
   - Easy to maintain dev/prod configurations

## Cost Optimization

**Single-model testing before full runs:**
```bash
# Cost: $0.10 (10 prompts × 1 model)
python collect_target_responses.py --test --model deepseek/deepseek-v3-base

# If successful, then full run:
# Cost: $5 (478 prompts × 1 model)
python collect_target_responses.py --model deepseek/deepseek-v3-base
```

**Incremental rollout:**
```bash
# Phase 1: High RLHF models (2 models)
python collect_target_responses.py --model anthropic/claude-sonnet-4.5
python collect_target_responses.py --model openai/gpt-4o

# Phase 2: Moderate RLHF models (2 models)
python collect_target_responses.py --model moonshotai/kimi-k2-0905
python collect_target_responses.py --model deepseek/deepseek-v3.1-terminus

# Phase 3: Low/Non RLHF models (5 models)
# ... (run individually)
```

## Implementation Details

**Config loader:** `promptguard/config/loader.py`
- `load_model_config()` - Load complete config
- `load_target_models()` - Load target model list
- `load_evaluation_models()` - Load evaluation model list
- Auto-detects project root (looks for pyproject.toml)
- Validates YAML structure

**Modified scripts:**
- `collect_target_responses.py` - Loads target models from config
- `analyze_target_responses.py` - Loads evaluation models from config

**Dependencies:**
- Added `pyyaml>=6.0.0` to `pyproject.toml`

## Migration Path

**Before migration:**
```python
# Hardcoded in script
TARGET_MODELS = {
    "high_rlhf": ["anthropic/claude-sonnet-4.5", "openai/gpt-4o"],
    # ...
}
ALL_MODELS = [m for models in TARGET_MODELS.values() for m in models]
```

**After migration:**
```python
# Loaded from config
from promptguard.config import load_target_models

target_models = load_target_models()  # From YAML
```

**Benefits for existing code:**
- Single line change to load from config
- Backward compatible (same list structure)
- No changes to worker logic
- Existing --test and --resume flags still work
- Added --model flag for single-model runs
