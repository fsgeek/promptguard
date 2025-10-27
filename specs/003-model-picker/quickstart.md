# Quickstart: Model Picker

**Date**: 2025-10-26
**Phase**: 1 - Design & Contracts
**Status**: Complete

## Overview

This guide provides a quick introduction to using the model-picker feature for database-driven model selection.

---

## Installation & Setup

### 1. Environment Variables

```bash
# ArangoDB connection (already configured for PromptGuard)
export ARANGODB_HOST="192.168.111.125"
export ARANGODB_PORT="8529"
export ARANGODB_DB="PromptGuard"
export ARANGODB_USER="pgtest"
export ARANGODB_PROMPTGUARD_PASSWORD="your_password"

# OpenRouter API (for syncing model catalog)
export OPENROUTER_API_KEY="your_key_here"
```

### 2. Initial Sync

```python
from promptguard.models.model_picker import ModelPicker
import os

# Create picker instance
picker = ModelPicker()

# Sync from OpenRouter (first-time setup)
stats = picker.sync_from_openrouter(os.environ["OPENROUTER_API_KEY"])
print(f"Synced {stats['models_added']} models")
```

### 3. Curate Frontier Models

```python
from promptguard.cli.model_admin import ModelAdmin

admin = ModelAdmin()

# Mark frontier models (requires human review)
frontier_models = [
    "anthropic/claude-opus-4.1",
    "anthropic/claude-sonnet-4.5",
    "openai/gpt-5-codex",
    "google/gemini-2.5-pro",
    "x-ai/grok-4",
    "meta-llama/llama-4-maverick",
]

admin.batch_mark_frontier(frontier_models, frontier=True)
```

---

## Common Use Cases

### Use Case 1: Fire Circle Model Selection

**Problem**: Fire Circle tests hardcode 2-5 models that become deprecated

**Solution**: Query for available frontier models with structural diversity

```python
from promptguard.models.model_picker import ModelPicker

picker = ModelPicker()

# Get 2 frontier models for SMALL circle
models = picker.query(
    available=True,
    frontier=True,
    limit=2,
    sort_by="created",  # Most recent first
    sort_desc=True
)

model_ids = [m.openrouter_id for m in models]
print(f"Fire Circle models: {model_ids}")

# Use in Fire Circle config
from promptguard.evaluation.fire_circle import FireCircleConfig, CircleSize

config = FireCircleConfig(
    models=model_ids,
    circle_size=CircleSize.SMALL,
    max_rounds=3,
    provider="openrouter"
)
```

**Before** (hardcoded):
```python
models = ["anthropic/claude-sonnet-4.5", "google/gemini-2.5-flash-preview-09-2025"]
```

**After** (dynamic):
```python
models = [m.openrouter_id for m in picker.query(available=True, frontier=True, limit=2)]
```

### Use Case 2: Observer Model Selection

**Problem**: Observer evaluation needs observer-framing-compatible models

**Solution**: Query for validated observer-compatible models

```python
# Get observer-compatible models
models = picker.query(
    available=True,
    observer_framing_compatible=True,
    limit=1
)

if not models:
    raise ValueError("No observer-compatible models available")

observer_model = models[0].openrouter_id
print(f"Observer model: {observer_model}")
```

### Use Case 3: Cost Optimization (Free Models)

**Problem**: Development/testing needs free models to avoid costs

**Solution**: Query for free models

```python
# Get free models for development
free_models = picker.query(
    available=True,
    free=True,
    limit=10
)

print(f"Found {len(free_models)} free models:")
for model in free_models:
    print(f"  - {model.openrouter_id} ({model.provider})")
```

### Use Case 4: Structured Output Capability

**Problem**: Need models that support structured output for schema enforcement

**Solution**: Query for structured-output-capable models

```python
# Get models supporting structured outputs
structured_models = picker.query(
    available=True,
    structured_outputs=True,
    limit=20
)

print(f"Found {len(structured_models)} models with structured output support:")
for model in structured_models:
    print(f"  - {model.openrouter_id}")
```

### Use Case 5: Provider-Specific Selection

**Problem**: Need models from specific provider (e.g., Anthropic only)

**Solution**: Query by provider

```python
# Get all available Anthropic models
anthropic_models = picker.query(
    available=True,
    provider="anthropic",
    limit=50
)

print(f"Anthropic models:")
for model in anthropic_models:
    print(f"  - {model.name} (context: {model.context_length})")
```

---

## Cycle-Stealing Auto-Sync

Model-picker automatically checks sync staleness on query invocation:

```python
# This query triggers auto-sync if last_synced > 24h ago
models = picker.query(available=True, frontier=True, limit=5)

# Sync happens transparently (cycle-stealing)
# No background jobs required
```

**Manual sync check**:
```python
if picker.needs_sync(ttl_hours=24):
    picker.sync_from_openrouter(api_key)
```

---

## Staleness Warnings

When querying frontier models, staleness warnings appear if frontier list hasn't been updated in >30 days:

```python
# This triggers interactive warning if frontier_updated > 30 days ago
models = picker.query(available=True, frontier=True, limit=5)
```

**Warning output**:
```
======================================================================
⚠️  STALENESS WARNING: Frontier Model List
======================================================================
Frontier designation last updated: 2024-09-20
Days since update: 37

Frontier models require periodic human review to ensure
current models are still state-of-the-art. This list may
include deprecated models or miss new frontier releases.

Recommendation: Run `uv run python -m promptguard.cli.model_admin --refresh-frontier`
======================================================================

Proceed with potentially stale frontier list? (yes/no):
```

**Non-interactive mode** (for CI/CD):
```python
# Set environment variable to bypass prompt
os.environ["ALLOW_STALE_FRONTIER"] = "1"

# Or use interactive=False parameter
models = picker.query(available=True, frontier=True, limit=5, interactive=False)
```

---

## Manual Curation Workflows

### Workflow 1: Add New Frontier Model

```python
from promptguard.cli.model_admin import ModelAdmin

admin = ModelAdmin()

# Test model availability first
result = admin.test_model_availability(
    "anthropic/claude-opus-4.2",
    os.environ["OPENROUTER_API_KEY"]
)

if result["available"]:
    # Mark as frontier
    admin.mark_frontier("anthropic/claude-opus-4.2", frontier=True)
    print("Added to frontier list")
else:
    print(f"Model not available: {result['error']}")
```

### Workflow 2: Validate Observer Framing Compatibility

```python
# After empirical validation (Instance 17-18 methodology)
admin.update_attributes(
    "anthropic/claude-sonnet-4.5",
    observer_framing_compatible=True,
    tags=["validated", "observer-production"]
)
```

### Workflow 3: Deprecate Frontier Model

```python
# Model no longer frontier-class
admin.mark_frontier("anthropic/claude-opus-3", frontier=False)
```

### Workflow 4: Bulk Frontier Update

```python
# Monthly frontier review
new_frontier = [
    "anthropic/claude-opus-4.1",
    "openai/gpt-5-codex",
    "google/gemini-2.5-pro",
]

# Unmark all current frontier models
current_frontier = picker.query(frontier=True)
admin.batch_mark_frontier(
    [m.openrouter_id for m in current_frontier],
    frontier=False
)

# Mark new frontier models
admin.batch_mark_frontier(new_frontier, frontier=True)
```

---

## Migration Guide

### Migrating Fire Circle Tests

**Before**:
```python
config = FireCircleConfig(
    models=["anthropic/claude-sonnet-4.5", "google/gemini-2.5-flash-preview-09-2025"],
    circle_size=CircleSize.SMALL,
    max_rounds=3,
    provider="openrouter"
)
```

**After**:
```python
from promptguard.models.model_picker import ModelPicker

picker = ModelPicker()
models = [m.openrouter_id for m in picker.query(available=True, frontier=True, limit=2)]

config = FireCircleConfig(
    models=models,
    circle_size=CircleSize.SMALL,
    max_rounds=3,
    provider="openrouter"
)
```

### Migrating Library Defaults

**Before** (`promptguard/evaluation/evaluator.py:56`):
```python
models: List[str] = field(default_factory=lambda: ["anthropic/claude-sonnet-4.5"])
```

**After**:
```python
from promptguard.models.model_picker import ModelPicker

def _default_model() -> List[str]:
    """Get default model from model-picker."""
    try:
        picker = ModelPicker()
        models = picker.query(available=True, frontier=True, limit=1)
        if models:
            return [models[0].openrouter_id]
    except Exception:
        pass  # Fallback to hardcoded default
    return ["anthropic/claude-sonnet-4.5"]

models: List[str] = field(default_factory=_default_model)
```

### Migrating Structured Output Detection

**Before** (`promptguard/evaluation/schemas.py:71-104`):
```python
STRUCTURED_OUTPUT_CAPABLE_MODELS = {
    "gpt-4o", "gpt-4o-mini", "mistral-medium-3.1", "gemini-2.5-flash-preview-09-2025",
    # ... 11 models hardcoded
}
```

**After**:
```python
from promptguard.models.model_picker import ModelPicker

def get_structured_output_models() -> set:
    """Get current structured-output-capable models."""
    try:
        picker = ModelPicker()
        models = picker.query(available=True, structured_outputs=True, limit=200)
        # Extract just model names (not full provider/model-name)
        return {m.openrouter_id.split("/")[1] for m in models}
    except Exception:
        # Fallback to hardcoded set
        return {"gpt-4o", "gpt-4o-mini", "mistral-medium-3.1", ...}

STRUCTURED_OUTPUT_CAPABLE_MODELS = get_structured_output_models()
```

---

## Best Practices

### 1. Check Sync Staleness

```python
# Always check before critical operations
if picker.needs_sync(ttl_hours=24):
    picker.sync_from_openrouter(api_key)
```

### 2. Handle Empty Results

```python
models = picker.query(available=True, frontier=True, limit=5)

if not models:
    # Fallback strategy
    print("No frontier models available, using fallback")
    models = picker.query(available=True, limit=5)
```

### 3. Log Model Selection

```python
import logging

models = picker.query(available=True, frontier=True, limit=2)
logging.info(f"Selected models: {[m.openrouter_id for m in models]}")
```

### 4. Respect Staleness Warnings

```python
# In interactive scripts, let user decide
models = picker.query(available=True, frontier=True, interactive=True)

# In CI/CD, fail fast
os.environ.pop("ALLOW_STALE_FRONTIER", None)  # Ensure not set
models = picker.query(available=True, frontier=True, interactive=False)
```

### 5. Cache Picker Instance

```python
# Don't create new picker for each query
picker = ModelPicker()  # Once

# Reuse for multiple queries
frontier_models = picker.query(available=True, frontier=True)
free_models = picker.query(available=True, free=True)
```

---

## Troubleshooting

### Issue: "No models found"

**Cause**: Database not synced or filters too restrictive

**Solution**:
```python
# Check sync status
metadata = picker.get_sync_metadata()
print(f"Last sync: {metadata['last_openrouter_sync']}")
print(f"Models count: {metadata['models_count']}")

# If never synced
if metadata['models_count'] == 0:
    picker.sync_from_openrouter(api_key)
```

### Issue: "Staleness warning appears every time"

**Cause**: Frontier list hasn't been manually reviewed

**Solution**:
```bash
# Run frontier review CLI
uv run python -m promptguard.cli.model_admin --refresh-frontier
```

### Issue: "Deprecated model still appears in results"

**Cause**: Model hasn't been removed from OpenRouter yet

**Solution**:
```python
# Check availability
model = picker.get_by_id("old/deprecated-model")
print(f"Available: {model.available}")

# Force sync to update availability
picker.sync_from_openrouter(api_key)
```

### Issue: "Query too slow"

**Cause**: Missing indexes or full table scan

**Solution**:
```python
# Check if indexes exist
from promptguard.storage.arango_backend import ArangoDBBackend

backend = ArangoDBBackend()
models_collection = backend.db.collection("models")
indexes = models_collection.indexes()

print("Indexes:")
for idx in indexes:
    print(f"  - {idx['type']} on {idx.get('fields', [])}")
```

---

## Next Steps

1. **Initial Setup**: Sync from OpenRouter, curate frontier models
2. **Migration**: Convert Priority 1 hardcoded lists (Fire Circle tests)
3. **Migration**: Convert Priority 2 hardcoded lists (library defaults)
4. **Validation**: Run integration tests with real API calls
5. **Documentation**: Update CLAUDE.md with model-picker usage patterns

**See**: `specs/003-model-picker/plan.md` for full implementation plan
