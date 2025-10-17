# Quick Start: Config-Driven Workers

## TL;DR

**Before:** Hardcoded model lists in scripts
**After:** YAML config + single-model testing

## Essential Commands

### Test Single Model (Fast)
```bash
# 10 prompts × 1 model = 10 responses (~30 seconds)
python collect_target_responses.py --test --model anthropic/claude-sonnet-4.5
```

### Collect All Models
```bash
# 478 prompts × 9 models = 4,302 responses (parallel)
python collect_target_responses.py
```

### Analyze Responses
```bash
# Post-evaluation with 4 evaluators
python analyze_target_responses.py

# Filter by target model
python analyze_target_responses.py --model deepseek/deepseek-v3-base
```

## Edit Models (No Code Required)

**File:** `config/target_models.yaml`

```yaml
target_models:
  high_rlhf:
    - anthropic/claude-sonnet-4.5  # Edit this
    - openai/gpt-4o                # Add/remove here
  # ... other categories

evaluation_models:
  - anthropic/claude-sonnet-4.5    # Edit this
  - moonshotai/kimi-k2-0905        # Add/remove here
```

Save and run - no code changes needed!

## Validation

```bash
# Test config loads correctly
python test_config_loader.py
```

## Common Workflows

### Add New Target Model
1. Edit `config/target_models.yaml`
2. Add model to appropriate category
3. Test: `python collect_target_responses.py --test --model your/new-model`
4. Run: `python collect_target_responses.py --model your/new-model`

### Single-Model Debug
```bash
# 1. Test with 10 prompts
python collect_target_responses.py --test --model problem/model

# 2. Check logs
tail target_response_collection.log

# 3. If working, full run
python collect_target_responses.py --model problem/model
```

### Resume Interrupted Run
```bash
# Resume all models
python collect_target_responses.py --resume

# Resume single model
python collect_target_responses.py --resume --model anthropic/claude-sonnet-4.5
```

## Help

Full docs: `docs/CONFIG_DRIVEN_WORKERS.md`
