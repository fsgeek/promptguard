# Config-Driven Parallel Workers Refactor

## Summary

Successfully refactored collection and analysis scripts from hardcoded model lists to YAML-based configuration with single-model testing capability.

## Changes Made

### 1. Configuration File

**File:** `config/target_models.yaml`

- 9 target models organized by RLHF category
- 4 evaluation models for post-evaluation analysis
- YAML format for easy editing
- Comments documenting model purposes

### 2. Config Loader Package

**Files:**
- `promptguard/config/__init__.py` - Package exports
- `promptguard/config/loader.py` - YAML loading logic
- `promptguard/config/cache_config.py` - Moved from `promptguard/config.py`

**API:**
```python
from promptguard.config import (
    load_target_models,        # Load target model list
    load_evaluation_models,    # Load evaluation model list
    load_model_config,         # Load complete config
    CacheConfig                # Cache settings (pre-existing)
)

# Load all target models
models = load_target_models()

# Load by RLHF category
high_rlhf = load_target_models(category="high_rlhf")

# Load evaluation models
evaluators = load_evaluation_models()
```

**Features:**
- Auto-detects project root (looks for `pyproject.toml`)
- Validates YAML structure
- Raises helpful errors if config missing/malformed

### 3. Updated Collection Script

**File:** `collect_target_responses.py`

**Changes:**
- Removed hardcoded `TARGET_MODELS` dict
- Added `load_target_models()` import
- Added `--model` parameter for single-model runs
- Updated docstring with new usage examples
- Modified `TargetResponseCollector.__init__()` to accept `target_models` list
- Updated logging to use dynamic model count

**New Usage:**
```bash
# All models (9 workers in parallel)
python collect_target_responses.py

# Single model (1 worker)
python collect_target_responses.py --model anthropic/claude-sonnet-4.5

# Test with single model (10 prompts)
python collect_target_responses.py --test --model openai/gpt-4o

# Resume single model
python collect_target_responses.py --resume --model deepseek/deepseek-v3-base
```

### 4. Updated Analysis Script

**File:** `analyze_target_responses.py`

**Changes:**
- Removed hardcoded `EVALUATION_MODELS` list
- Added `load_evaluation_models()` import
- Modified `PostEvaluationAnalyzer.__init__()` to accept `evaluation_models` list
- Updated `main()` to load models from config
- Existing `--model` parameter already supported (for filtering target responses)

**Existing Usage (unchanged):**
```bash
# Analyze all target responses
python analyze_target_responses.py

# Filter by target model
python analyze_target_responses.py --model anthropic/claude-sonnet-4.5

# Test mode
python analyze_target_responses.py --test
```

### 5. Dependencies

**File:** `pyproject.toml`

- Added `pyyaml>=6.0.0` to dependencies

### 6. Validation Script

**File:** `test_config_loader.py`

- Tests config loading
- Tests category filtering
- Tests model counts
- Validates expected structure

**Usage:**
```bash
python test_config_loader.py
```

### 7. Documentation

**File:** `docs/CONFIG_DRIVEN_WORKERS.md`

Complete documentation covering:
- Architecture overview
- Configuration file format
- Config loader API
- Script usage examples
- Parallel worker design
- Adding/removing models
- Cost optimization strategies
- Migration path from hardcoded

## Benefits

1. **No Code Changes for Model Updates**
   - Edit YAML to add/remove models
   - No code review required for model list changes
   - Version control tracks model changes

2. **Single-Model Testing**
   - Test new models before full runs
   - Debug model-specific issues
   - Faster iteration ($0.10 vs $5)

3. **Parallel Efficiency Maintained**
   - N workers (one per model)
   - Real-time ArangoDB persistence
   - Resume capability preserved

4. **Flexible Configuration**
   - Filter by RLHF category
   - Multiple environments (dev/prod)
   - Easy to maintain separate configs

5. **Better Developer Experience**
   - Clear separation of config vs code
   - Helpful error messages
   - Simple API

## Validation

**All validations passing:**

```bash
# Config loader test
$ uv run python test_config_loader.py
✓ All tests passed!

# Collection script imports
$ uv run python -c "from collect_target_responses import TargetResponseCollector"
✓ collect_target_responses.py imports successfully

# Analysis script imports
$ uv run python -c "from analyze_target_responses import PostEvaluationAnalyzer"
✓ analyze_target_responses.py imports successfully
```

## Example Workflows

### Adding a New Target Model

**Before (required code change):**
```python
# Edit collect_target_responses.py
TARGET_MODELS = {
    "high_rlhf": [
        "anthropic/claude-sonnet-4.5",
        "openai/gpt-4o",
        "anthropic/claude-opus-4"  # Added
    ],
    # ...
}
```

**After (config-only change):**
```yaml
# Edit config/target_models.yaml
target_models:
  high_rlhf:
    - anthropic/claude-sonnet-4.5
    - openai/gpt-4o
    - anthropic/claude-opus-4  # Added
```

### Testing New Model Before Full Run

```bash
# 1. Add to config/target_models.yaml
# 2. Test with 10 prompts
python collect_target_responses.py --test --model anthropic/claude-opus-4

# 3. If successful, full run
python collect_target_responses.py --model anthropic/claude-opus-4
```

### Incremental Collection

```bash
# Day 1: High RLHF models
python collect_target_responses.py --model anthropic/claude-sonnet-4.5
python collect_target_responses.py --model openai/gpt-4o

# Day 2: Moderate RLHF models
python collect_target_responses.py --model moonshotai/kimi-k2-0905
python collect_target_responses.py --model deepseek/deepseek-v3.1-terminus

# Day 3: Low/Non RLHF models
# ... (run individually)
```

## Files Modified

- `config/target_models.yaml` - **NEW** - Model configuration
- `promptguard/config/__init__.py` - **NEW** - Package exports
- `promptguard/config/loader.py` - **NEW** - Config loading logic
- `promptguard/config/cache_config.py` - **MOVED** - Was `promptguard/config.py`
- `collect_target_responses.py` - **MODIFIED** - Load from config, add --model
- `analyze_target_responses.py` - **MODIFIED** - Load from config
- `pyproject.toml` - **MODIFIED** - Add pyyaml dependency
- `test_config_loader.py` - **NEW** - Validation script
- `docs/CONFIG_DRIVEN_WORKERS.md` - **NEW** - Complete documentation

## Backward Compatibility

- Existing `--test` and `--resume` flags unchanged
- Analysis script's `--model` filter unchanged
- Parallel worker architecture unchanged
- ArangoDB storage unchanged
- Cache behavior unchanged

**Only breaking change:**
- Cannot import directly from old `promptguard.config` (now a package)
- Migration: `from promptguard.config import X` still works (exports preserved)

## Next Steps

**Ready for use:**
- Scripts can be run immediately with new --model parameter
- Config can be edited to add/remove models
- Documentation is complete

**Potential future enhancements:**
- Multiple config files (dev/prod/test)
- Config validation schema (JSON Schema)
- Config environment variable overrides
- Per-model settings (temperature, max_tokens)
