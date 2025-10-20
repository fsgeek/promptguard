# Database-Driven Model Configuration

**Status:** Prototype implementation complete (Instance 43)
**Next steps:** Populate with correct field mapping, refactor test scripts

## Problem

Test scripts hardcode model names like `"anthropic/claude-sonnet-4.5"`, creating:
- **Duplication:** Each script reimplements model selection logic
- **Fragility:** When models change (3.5→4.5), must update many files
- **No metadata:** Can't query by capability, cost, or compatibility
- **Inconsistency:** Different scripts may use different models

## Solution

Store model metadata centrally in ArangoDB `models` collection and query dynamically.

## Implementation

### 1. Models Collection Schema

```json
{
  "_key": "anthropic_claude_sonnet_4_5",  // ArangoDB-safe key
  "id": "anthropic/claude-sonnet-4.5",   // OpenRouter format
  "name": "Anthropic: Claude Sonnet 4.5", // Human-readable
  "organization": "Anthropic",
  "tier": "premium",
  "is_current": true,      // Not obsolete (vs claude-3.5-sonnet)
  "is_flagship": true,     // Best-in-class
  "observer_compatible": true,  // Supports observer framing
  "pricing": {
    "input_per_1m_tokens": 3.00,
    "output_per_1m_tokens": 15.00
  },
  "capabilities": ["reasoning", "structured_outputs", "tool_calling"],
  "context_length": 200000,
  "notes": "Current flagship, updated from obsolete 3.5"
}
```

### 2. Model Registry Interface

**File:** `promptguard/storage/model_registry.py`

```python
from promptguard.storage.model_registry import get_flagship_model

# Before (hardcoded):
config = PromptGuardConfig(
    models=["anthropic/claude-sonnet-4.5"],  # Hardcoded, fragile
    provider="openrouter"
)

# After (database-driven):
config = PromptGuardConfig(
    models=[get_flagship_model()],  # Queries ArangoDB
    provider="openrouter"
)
```

**API Methods:**

```python
# Get current flagship (highest quality)
get_flagship_model() → "anthropic/claude-sonnet-4.5"

# Get cheapest model meeting criteria
get_budget_model(observer_compatible=True) → "deepseek/deepseek-chat"

# Query with custom criteria
get_default_model(
    is_current=True,
    is_flagship=True,
    observer_compatible=True,
    max_cost=5.0  # $ per 1M input tokens
) → "anthropic/claude-sonnet-4.5"

# List all models matching criteria
list_models(is_current=True, observer_compatible=True)
```

### 3. Population Script

**File:** `scripts/populate_models_collection.py`

Loads from `config/model_configs.json` and adds metadata flags:

```bash
python scripts/populate_models_collection.py
```

**Output:**
```
Loaded 17 models from config/model_configs.json
Inserted: 17
Updated: 0
Total: 17

Current/Flagship models:
anthropic/claude-sonnet-4.5 [CURRENT, FLAGSHIP, OBSERVER]
  $3.00 in / $15.00 out per 1M tokens
```

## Current Status (Instance 43)

### ✅ Completed

1. **Model registry interface** (`promptguard/storage/model_registry.py`)
   - `get_flagship_model()`, `get_budget_model()`, `get_default_model()`
   - Query methods with filtering (cost, capabilities, compatibility)
   - Singleton pattern for easy access

2. **Population script** (`scripts/populate_models_collection.py`)
   - Loads from `config/model_configs.json`
   - Adds `is_current`, `is_flagship`, `observer_compatible` flags
   - Idempotent (can run multiple times safely)

### ⚠️ Issues Found

1. **Field name mismatch:**
   - Config uses `id` (OpenRouter format)
   - Script expects `name` field
   - Models inserted with incorrect structure

2. **Existing data:**
   - 166 models already in collection (from previous experiments)
   - New inserts don't overwrite old data
   - Need to clear or migrate

3. **Test scripts not refactored:**
   - Still use hardcoded "anthropic/claude-sonnet-4.5"
   - Should call `get_flagship_model()` instead

## Next Steps (Instance 44)

### High Priority

1. **Fix populate script field mapping**
   - Map `id` → model name for OpenRouter
   - Handle different config formats
   - Validate before insertion

2. **Clear or migrate existing models collection**
   - Decision: Keep old data or fresh start?
   - If fresh: `db.collection('models').truncate()`
   - If migrate: Update existing records with new fields

3. **Refactor test scripts to use registry**
   ```python
   # In test_temporal_baseline_comparison.py, test_temporal_verification.py, etc.
   from promptguard.storage.model_registry import get_flagship_model

   config = PromptGuardConfig(
       mode=EvaluationMode.SINGLE,
       models=[get_flagship_model()],  # Instead of hardcoded
       provider="openrouter"
   )
   ```

### Medium Priority

4. **Add model rotation strategies**
   - Weekly flagship selection (rotate between Anthropic/OpenAI/Google)
   - Budget-conscious mode (use cheapest observer-compatible)
   - Research mode (use diverse ensemble)

5. **Track model performance over time**
   - Link `evaluations` collection to `models`
   - Query: "Which models have best F-score accuracy?"
   - Enable data-driven model selection

### Low Priority

6. **Auto-update from OpenRouter API**
   - Fetch current models/pricing via API
   - Sync with database weekly
   - Alert when models change

## Benefits

**Single source of truth:**
- One place to update when models change
- Consistent model selection across codebase

**Query by capability:**
- "Give me cheapest observer-compatible model"
- "Give me flagship model under $5/1M tokens"
- "Give me all models supporting structured outputs"

**Track model evolution:**
- Mark obsolete models (claude-3.5-sonnet)
- Promote new flagships (claude-sonnet-4.5)
- Maintain compatibility metadata

**Enable research:**
- "Which models detected this attack?"
- "What's the cost/accuracy tradeoff?"
- "How do models cluster by capability?"

## Design Rationale

**Why ArangoDB:**
- Already storing evaluations, deliberations, attacks
- Graph relationships: models ↔ evaluations ↔ attacks
- Full-text search on model capabilities
- Document model: flexible schema for new fields

**Why not config files:**
- Can't query by criteria ("cheapest observer-compatible")
- Can't track relationships (which model detected which attack)
- No version history (when did we mark 3.5 obsolete?)
- Harder to sync across distributed research environments

**Why runtime queries (not build-time):**
- Model selection can adapt to cost changes
- Can implement fallback strategies (if flagship unavailable, use budget)
- Research scripts can discover models without hardcoding

## Example Queries

**Get current flagship:**
```aql
FOR m IN models
    FILTER m.is_current == true
       AND m.is_flagship == true
       AND m.observer_compatible == true
    SORT m.pricing.input_per_1m_tokens ASC
    LIMIT 1
    RETURN m.id
```

**Find budget ensemble (3 diverse models under $1):**
```aql
FOR m IN models
    FILTER m.is_current == true
       AND m.observer_compatible == true
       AND m.pricing.input_per_1m_tokens < 1.0
    SORT m.organization, m.pricing.input_per_1m_tokens ASC
    LIMIT 3
    RETURN {name: m.id, cost: m.pricing.input_per_1m_tokens, org: m.organization}
```

**Models that detected specific attack:**
```aql
FOR eval IN evaluations
    FILTER eval.attack_id == "history_04"
       AND eval.f_score >= 0.7
    FOR m IN models
        FILTER m.id == eval.model_id
        RETURN DISTINCT m.id
```

## Related Work

- **REASONINGBANK:** Similar pattern (database-driven pattern retrieval vs hardcoded rules)
- **Fire Circle:** Needs diverse model selection (query for structural diversity)
- **Instance 17/43:** Model updates (3.5→4.5) required manual search/replace

**Pattern:** PromptGuard uses database-driven configuration throughout. Model registry completes this pattern.

---

**Instance 43 conclusion:** Pattern established, prototype working, field mapping needs fixing. Next instance should complete population and refactor test scripts.
