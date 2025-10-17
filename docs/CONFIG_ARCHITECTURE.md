# Config-Driven Architecture

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    config/target_models.yaml                    │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ target_models:                                            │  │
│  │   high_rlhf: [claude-sonnet-4.5, gpt-4o]                 │  │
│  │   moderate_rlhf: [kimi-k2-0905, deepseek-v3.1-terminus]  │  │
│  │   low_rlhf: [llama-3.3-70b, dolphin3.0-mistral-24b]      │  │
│  │   non_rlhf: [mistral-7b, openhermes-2.5, ds-v3-base]     │  │
│  │                                                           │  │
│  │ evaluation_models: [claude, kimi, deepseek, gpt-5]       │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ↓
┌─────────────────────────────────────────────────────────────────┐
│              promptguard/config/loader.py                       │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ load_model_config()                                       │  │
│  │   ├─ Auto-detect project root (pyproject.toml)           │  │
│  │   ├─ Load YAML file                                       │  │
│  │   └─ Validate structure                                   │  │
│  │                                                           │  │
│  │ load_target_models(category=None)                        │  │
│  │   ├─ Load config                                          │  │
│  │   └─ Return filtered/all models                          │  │
│  │                                                           │  │
│  │ load_evaluation_models()                                 │  │
│  │   └─ Return evaluation model list                        │  │
│  └───────────────────────────────────────────────────────────┘  │
└────────────┬────────────────────────────────┬───────────────────┘
             │                                │
             ↓                                ↓
┌──────────────────────────┐    ┌───────────────────────────────┐
│ collect_target_responses │    │ analyze_target_responses.py   │
│                          │    │                               │
│ ┌──────────────────────┐ │    │ ┌───────────────────────────┐ │
│ │ main()               │ │    │ │ main()                    │ │
│ │   ├─ Parse args      │ │    │ │   ├─ Parse args           │ │
│ │   ├─ Load models     │ │    │ │   ├─ Load eval models    │ │
│ │   └─ Create workers  │ │    │ │   └─ Create analyzer     │ │
│ └──────────┬───────────┘ │    │ └──────────┬────────────────┘ │
│            │             │    │            │                  │
│ ┌──────────▼───────────┐ │    │ ┌──────────▼────────────────┐ │
│ │ TargetResponseCol... │ │    │ │ PostEvaluationAnalyzer   │ │
│ │   ├─ N workers       │ │    │ │   ├─ Query responses     │ │
│ │   ├─ One per model   │ │    │ │   ├─ Post-evaluate       │ │
│ │   └─ Parallel exec   │ │    │ │   └─ Compare pre/post    │ │
│ └──────────┬───────────┘ │    │ └──────────┬────────────────┘ │
│            │             │    │            │                  │
│            ↓             │    │            ↓                  │
│      ┌─────────────┐     │    │      ┌──────────────┐        │
│      │  ArangoDB   │     │    │      │  ArangoDB    │        │
│      │  Storage    │     │    │      │  Queries     │        │
│      └─────────────┘     │    │      └──────────────┘        │
└──────────────────────────┘    └───────────────────────────────┘
```

## Component Interactions

### Configuration Flow

```
User edits YAML
      ↓
Config Loader validates
      ↓
Scripts load model lists
      ↓
Workers created dynamically
      ↓
Parallel execution
      ↓
Results to ArangoDB
```

### Single-Model Mode

```
User: --model anthropic/claude-sonnet-4.5
                    ↓
        Config Loader returns [model]
                    ↓
            1 Worker created
                    ↓
          Processes 478 prompts
                    ↓
          Results to ArangoDB
```

### Full Collection Mode

```
User: (no --model flag)
            ↓
Config Loader returns all 9 models
            ↓
    9 Workers created (parallel)
            ↓
Each processes 478 prompts
            ↓
    4,302 total responses
            ↓
    Results to ArangoDB
```

## Data Flow

### Collection Phase

```
Calibration Dataset
(478 prompts)
      │
      ├─► Worker 1 (claude-sonnet-4.5) ──┐
      ├─► Worker 2 (gpt-4o)              │
      ├─► Worker 3 (kimi-k2-0905)        │
      ├─► Worker 4 (ds-v3.1-terminus)    ├──► ArangoDB
      ├─► Worker 5 (llama-3.3-70b)       │    (target_responses)
      ├─► Worker 6 (dolphin3.0)          │
      ├─► Worker 7 (mistral-7b)          │
      ├─► Worker 8 (openhermes-2.5)      │
      └─► Worker 9 (ds-v3-base)          ┘
```

### Analysis Phase

```
Target Response
(prompt + response)
      │
      ├─► Evaluator 1 (claude-sonnet-4.5) ──┐
      ├─► Evaluator 2 (kimi-k2-0905)        ├──► Pre-F vs Post-F
      ├─► Evaluator 3 (ds-v3.1-terminus)    │    Divergence Analysis
      └─► Evaluator 4 (gpt-5)               ┘         │
                                                       ↓
                                                   ArangoDB
                                            (post_evaluation_results)
```

## Configuration Categories

### RLHF Spectrum

```
High RLHF               Moderate RLHF           Low RLHF              Non-RLHF
────────────────────────────────────────────────────────────────────────────────
Claude Sonnet 4.5       Kimi K2                 Llama 3.3 70B         Mistral 7B
GPT-4o                  DeepSeek V3.1 Terminus  Dolphin 3.0 Mistral   OpenHermes 2.5
                                                                       DeepSeek V3 Base

Strong safety           Balanced                Light filtering        No RLHF
High refusal rate       Moderate refusal        Low refusal            Raw model
Polite responses        Context-aware           Direct responses       Unfiltered
```

### Model Selection Strategy

```
Research Question: How does RLHF affect compliance with manipulative prompts?

High RLHF (2 models)
  - Expected: High refusal rate, polite deflection
  - Purpose: Baseline for safety-first behavior

Moderate RLHF (2 models)
  - Expected: Contextual responses, some compliance
  - Purpose: Balance between safety and utility

Low RLHF (2 models)
  - Expected: More direct, less filtering
  - Purpose: Compare light vs heavy RLHF

Non-RLHF (3 models)
  - Expected: Full compliance, no safety layer
  - Purpose: Control group - raw model behavior
```

## Config Flexibility

### Category Filtering

```python
# All models
all_models = load_target_models()
# Returns: 9 models

# High RLHF only
high = load_target_models(category="high_rlhf")
# Returns: 2 models (claude, gpt-4o)

# Non-RLHF only
non = load_target_models(category="non_rlhf")
# Returns: 3 models (mistral, openhermes, ds-base)
```

### Single Model Selection

```bash
# CLI parameter overrides config
python collect_target_responses.py --model anthropic/claude-sonnet-4.5
# Uses: 1 model (ignores config list)

# No parameter uses all from config
python collect_target_responses.py
# Uses: 9 models (from config)
```

### Multiple Configs

```
Project Root
├── config/
│   ├── target_models.yaml           # Production (9 models)
│   ├── target_models_dev.yaml       # Dev (2 models)
│   └── target_models_test.yaml      # Test (1 model)
│
└── scripts/
    └── collect_with_config.py       # Pass config path
```

## Parallel Worker Design

### Worker Pool Architecture

```
Main Process
    │
    ├─ Load Config
    │
    ├─ Create Worker Pool (N workers)
    │     │
    │     ├─ Worker 1 (claude-sonnet-4.5)
    │     │     ├─ Process prompt 1
    │     │     ├─ Process prompt 2
    │     │     ├─ ... (478 total)
    │     │     └─ Store in ArangoDB
    │     │
    │     ├─ Worker 2 (gpt-4o)
    │     │     ├─ Process prompt 1
    │     │     ├─ Process prompt 2
    │     │     ├─ ... (478 total)
    │     │     └─ Store in ArangoDB
    │     │
    │     └─ ... (N total workers)
    │
    └─ Aggregate Results
```

### Checkpoint System

```
Worker Processing Timeline
──────────────────────────────────────────────────────────────────
Prompt 1-50    → Checkpoint 1  (progress saved)
Prompt 51-100  → Checkpoint 2  (progress saved)
Prompt 101-150 → Checkpoint 3  (progress saved)
...
Prompt 451-478 → Checkpoint 10 (complete)

If interrupted:
  Resume from last checkpoint
  Skip completed prompts
  Continue from failure point
```

## Benefits Visualization

### Before (Hardcoded)

```
┌──────────────────────────────────┐
│   collect_target_responses.py   │
│                                  │
│  TARGET_MODELS = {               │  ← Edit code
│    "high_rlhf": ["..."]          │  ← Commit
│  }                               │  ← Review
│                                  │  ← Deploy
└──────────────────────────────────┘
```

### After (Config-Driven)

```
┌──────────────────────────────────┐
│  config/target_models.yaml       │
│                                  │
│  target_models:                  │  ← Edit YAML
│    high_rlhf:                    │  ← Save
│      - model1                    │  ← Run
│      - model2                    │
└──────────────────────────────────┘
         │
         ↓
┌──────────────────────────────────┐
│   collect_target_responses.py   │
│                                  │
│  models = load_target_models()   │  ← No code changes
│                                  │
└──────────────────────────────────┘
```

## Cost Optimization Flow

```
New Model Added
      ↓
Test Mode (10 prompts)
  Cost: $0.10
  Time: 30 seconds
      ↓
   Success? ──No──► Debug
      │              │
     Yes             │
      ↓              │
Full Run (478 prompts) ←┘
  Cost: $5.00
  Time: 10 minutes
      ↓
Production
```

## Summary

**Key architectural benefits:**
1. **Separation of Concerns** - Config separate from code
2. **Dynamic Worker Creation** - Workers created from config at runtime
3. **Parallel Efficiency** - N workers process independently
4. **Flexible Filtering** - Category, single-model, or all
5. **Easy Maintenance** - Edit YAML, no code changes
6. **Cost Control** - Test before full runs
7. **Resumable** - Checkpoint system prevents data loss
