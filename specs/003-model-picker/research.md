# Research Findings: Model Picker

**Date**: 2025-10-26
**Phase**: 0 - Research & Design Decisions
**Status**: Complete

## Overview

This document consolidates research findings for the model-picker feature implementation, addressing all NEEDS CLARIFICATION items from the planning phase.

---

## Research Task 1: OpenRouter API Schema

### Decision: Use OpenRouter `/api/v1/models` endpoint for automatic sync

### API Response Structure

```json
{
  "data": [
    {
      "id": "provider/model-name",
      "name": "Human-readable display name",
      "created": 1759161676,
      "description": "Detailed model description",
      "context_length": 1000000,
      "architecture": { /* see below */ },
      "pricing": { /* see below */ },
      "top_provider": { /* see below */ },
      "supported_parameters": ["max_tokens", "temperature", ...]
    }
  ]
}
```

### Fields Suitable for Automatic Population

**Auto-sync from OpenRouter (volatile, changes frequently):**
- `id` - Primary key (provider/model-name)
- `name` - Display name
- `created` - Unix timestamp
- `context_length` - Context window size
- `pricing.*` - All pricing fields (prompt, completion, request, image, cache)
- `architecture.modality` - Input→output modality
- `architecture.tokenizer` - Tokenizer type
- `architecture.instruct_type` - Instruction format
- `top_provider.*` - Provider-specific metadata
- `supported_parameters` - API capabilities list
- `description` - Model description (for SearchView)

**Pricing subfields:**
- `prompt`, `completion` - Per-token costs (strings to avoid float precision issues)
- `request`, `image`, `web_search`, `internal_reasoning` - Additional costs
- `input_cache_read`, `input_cache_write` - Cache pricing (16.4% of models)

**Architecture subfields:**
- `modality` - "text->text" (69.4%), "text+image->text" (30.0%), "text+image->text+image" (0.6%)
- `input_modalities`, `output_modalities` - Arrays of supported types
- `tokenizer` - "Claude", "GPT", "Mistral", "Llama3", "Qwen3", "Other", etc.
- `instruct_type` - Instruction format (68.8% null, rest have specific formats)

### Fields Requiring Manual Curation

**Never auto-sync (requires empirical validation):**
- `frontier` - Boolean flag, requires human analysis (no OpenRouter signal)
- `testing` - Boolean flag for experimental models
- `observer_framing_compatible` - Empirically validated (Instance 17-18)
- `architecture_family` - Semantic grouping (e.g., "transformer-dense", "moe", "reasoning")
- `free` - Derived from pricing but requires data-training disclosure
- `instruct` - Requires analysis of description + validation
- `rlhf` - Not provided by OpenRouter, requires research
- Custom tags - Open tagging for research needs

### Rationale

OpenRouter catalog contains 330+ models and changes frequently:
- Models appear/disappear based on provider decisions
- Pricing changes (especially free tier)
- New capabilities added (structured_outputs now 53% of models)
- 24-48h sync TTL appropriate for research tool

**Free models caveat:** Per `config/dynamic_free_models.py`, free models use data for training. Ethical disclosure required.

---

## Research Task 2: Existing Model Selection Patterns

### Decision: Convert hardcoded lists to model-picker queries in priority order

### Hardcoded Model Locations (Priority Order)

#### Priority 1: Fire Circle Tests (CRITICAL - causes failures when models deprecated)

1. **`test_fire_circle_fixes.py`** (Lines 35-36)
   - Models: `anthropic/claude-sonnet-4.5`, `google/gemini-2.5-flash-preview-09-2025`
   - Criteria: 2-model SMALL circle for meta-evaluation testing
   - **Conversion:** `picker.query(available=True, frontier=True, limit=2)`

2. **`test_meta_evaluation_framing.py`** (Lines 34-35)
   - Models: `anthropic/claude-sonnet-4.5`, `google/gemini-2.5-flash-preview-09-2025`
   - Criteria: 2-model SMALL circle
   - **Conversion:** Same as above

3. **`test_proposal_evaluation_detailed.py`** (Lines 35-36)
   - Models: `anthropic/claude-sonnet-4.5`, `google/gemini-2.5-flash-preview-09-2025`
   - Criteria: 2-model SMALL circle
   - **Conversion:** Same as above

4. **`test_learning_loop.py`** (Lines 51-52)
   - Models: `anthropic/claude-sonnet-4.5`, `google/gemini-2.5-flash-preview-09-2025`
   - Criteria: 2-model SMALL circle for learning loop validation
   - **Conversion:** Same as above

5. **`fire_circle_compliance_prompt.py`** (Lines 135-141)
   - Models: 5-model MEDIUM circle with organizational diversity
   - Criteria: Anthropic, OpenAI, Google, Qwen (CN-aligned), Meta (open source)
   - **Conversion:** `picker.query(available=True, frontier=True, structural_diversity=True, limit=5)`

#### Priority 2: Library Defaults (HIGH - affects all evaluations without explicit config)

1. **`promptguard/evaluation/evaluator.py`** (Line 56)
   - Default: `anthropic/claude-sonnet-4.5`
   - Criteria: Production baseline
   - **Conversion:** `picker.query(available=True, frontier=True, limit=1)[0]` with fallback

2. **`promptguard/promptguard.py`** (Lines 67-70)
   - Default: `anthropic/claude-sonnet-4.5` (OpenRouter provider)
   - Criteria: Matches evaluator baseline
   - **Conversion:** Same as above

3. **`promptguard/evaluation/schemas.py`** (Lines 71-104)
   - Constant: `STRUCTURED_OUTPUT_CAPABLE_MODELS` (11 models)
   - Criteria: Empirically validated for structured output support
   - **Conversion:** `picker.query(available=True, structured_outputs=True)` + validation cache

#### Priority 3: Configuration Files (MEDIUM - centralized but manual updates required)

1. **`config/model_configs.json`**
   - 26 models across tiers (Free, Budget, Mid, Premium, Fire Circle)
   - **Strategy:** Seed initial models collection from this config
   - **Maintenance:** Add frontier curation CLI for manual updates

2. **`config/fire_circle_models.json`**
   - 12 validated Fire Circle models + 1 unavailable (openai/gpt-5)
   - **Strategy:** Use as initial frontier=True seed
   - **Maintenance:** CLI tool for testing new frontier candidates

#### Priority 4: Example Scripts (LOW - documentation/demos, OK to hardcode)

Accept technical debt for:
- `examples/simple_usage.py`
- `examples/simple_pipeline_demo.py`
- `examples/fire_circle_arango_demo.py`

Rationale: Examples should show specific models for reproducibility. Not a deprecation risk.

### Selection Criteria Patterns Identified

1. **Frontier models:** Current state-of-the-art, manually curated (no OpenRouter signal)
2. **Structural diversity:** Different providers (Anthropic, OpenAI, Google, Meta, DeepSeek, etc.)
3. **Cost optimization:** Free models (`pricing.prompt == "0" AND pricing.completion == "0"`)
4. **Observer framing compatible:** Empirically validated (Claude Sonnet 4.5, GPT-4.1 confirmed)
5. **Structured output capable:** Validated via OpenRouter `supported_parameters` includes `structured_outputs`
6. **Architecture diversity:** Different tokenizers, instruction formats, modalities

### Rationale

Priority order balances:
1. **Failure impact** - Tests failing in CI/CD (Priority 1)
2. **Usage frequency** - Library defaults affect all evaluations (Priority 2)
3. **Maintenance burden** - Config files require manual updates (Priority 3)
4. **Acceptable debt** - Examples are documentation, not runtime (Priority 4)

---

## Research Task 3: ArangoDB Query Patterns

### Decision: Follow existing patterns from `arango_backend.py`

### Key Patterns to Replicate

#### Connection Pattern

```python
# Environment-based configuration with fail-fast
host = os.environ.get("ARANGODB_HOST", "192.168.111.125")
password = os.environ.get("ARANGODB_PROMPTGUARD_PASSWORD")

if not password:
    raise ValueError("ArangoDB password required. Set ARANGODB_PROMPTGUARD_PASSWORD")

client = ArangoClient(hosts=f"http://{host}:{port}")
db = client.db(db_name, username=username, password=password)
```

#### Idempotent Collection Creation

```python
# Existing pattern from arango_backend.py
if not db.has_collection("models"):
    db.create_collection("models")
```

#### Index Creation Pattern

```python
def _ensure_index(collection, index_type, fields, unique=False):
    """Idempotent index creation."""
    existing = collection.indexes()
    for idx in existing:
        if idx["type"] == index_type and set(idx["fields"]) == set(fields):
            return  # Already exists

    if index_type == "hash":
        collection.add_index({"type": "hash", "fields": fields, "unique": unique})
    elif index_type == "skiplist":
        collection.add_index({"type": "skiplist", "fields": fields, "unique": unique})
    elif index_type == "fulltext":
        collection.add_index({"type": "fulltext", "fields": fields, "minLength": 3})
```

#### Recommended Indexes for Models Collection

```python
# Hash indexes for attribute filtering
_ensure_index(models, "hash", ["openrouter_id"], unique=True)
_ensure_index(models, "hash", ["provider"])
_ensure_index(models, "hash", ["frontier"])
_ensure_index(models, "hash", ["available"])
_ensure_index(models, "hash", ["free"])

# Skiplist for temporal queries
_ensure_index(models, "hash", ["last_synced"])

# Fulltext for description search
_ensure_index(models, "fulltext", ["description"])
```

#### AQL Query Pattern for Attribute Filtering

```python
query = """
FOR m IN models
    FILTER m.available == true
    FILTER m.frontier == true
    SORT m.created DESC
    LIMIT @limit
    RETURN {
        openrouter_id: m.openrouter_id,
        provider: m.provider,
        architecture_family: m.architecture_family,
        context_length: m.context_length
    }
"""

cursor = db.aql.execute(query, bind_vars={"limit": limit})
results = list(cursor)
```

**Key conventions from existing code:**
- Always use `@bind_vars` for SQL injection prevention
- Always include `LIMIT @limit` for bounded results
- Sort by timestamp (`SORT m.created DESC`) for chronological queries
- Return projections (not full documents) for efficiency
- Use `FILTER` clauses progressively for readability

#### Dynamic Query Construction

```python
# Pattern from existing code for optional filters
filters = []
bind_vars = {"limit": limit}

if available is not None:
    filters.append("m.available == @available")
    bind_vars["available"] = available

if frontier is not None:
    filters.append("m.frontier == @frontier")
    bind_vars["frontier"] = frontier

filter_clause = " AND ".join(filters) if filters else "true"

query = f"""
FOR m IN models
    FILTER {filter_clause}
    SORT m.created DESC
    LIMIT @limit
    RETURN {{ ... }}
"""
```

#### Error Handling Pattern

```python
# Existing pattern from arango_backend.py
try:
    cursor = db.aql.execute(query, bind_vars=bind_vars)
    return list(cursor)
except Exception as e:
    raise IOError(f"Model query failed: {e}")
```

### Document Structure for Models Collection

```python
model_doc = {
    "_key": openrouter_id.replace("/", "_"),  # Sanitize key
    "openrouter_id": openrouter_id,  # provider/model-name
    "provider": provider,  # Extracted from ID
    "name": name,
    "created": created,  # Unix timestamp from OpenRouter
    "context_length": context_length,
    "description": description,

    # Auto-synced from OpenRouter
    "pricing": {
        "prompt": "0.000003",  # String to avoid float precision
        "completion": "0.000015",
        # ... other pricing fields
    },
    "architecture": {
        "modality": "text+image->text",
        "tokenizer": "Claude",
        # ... other architecture fields
    },
    "supported_parameters": ["max_tokens", "temperature", ...],

    # Manual curation (preserved across syncs)
    "frontier": False,  # Boolean flag
    "testing": False,
    "observer_framing_compatible": None,  # null = untested, bool = tested
    "architecture_family": None,  # "transformer-dense", "moe", "reasoning"
    "free": False,  # Derived but requires disclosure
    "instruct": None,
    "rlhf": None,

    # Sync metadata
    "last_synced": "2025-10-26T12:00:00Z",  # ISO timestamp
    "available": True,  # Derived from presence in OpenRouter API

    # Open tagging (extensible)
    "tags": []  # Array of custom tags
}
```

### Rationale

Consistency with existing codebase patterns:
- Same connection/error handling as `arango_backend.py`
- Same index creation patterns
- Same AQL query conventions
- Reduces learning curve for maintainers
- Proven patterns (18 passing tests validate existing implementation)

---

## Research Task 4: Interactive Warning Implementation

### Decision: Use Python `input()` with clear messaging for CLI context

### Implementation Approach

**Pattern 1: Warning with confirmation (RECOMMENDED)**

```python
def check_frontier_staleness(last_updated: datetime) -> None:
    """
    Check frontier list staleness and require interactive acknowledgment.

    Raises:
        StalenessWarning: If user declines to proceed
    """
    days_since_update = (datetime.now() - last_updated).days

    if days_since_update > 30:
        print("\n" + "="*70)
        print("⚠️  STALENESS WARNING: Frontier Model List")
        print("="*70)
        print(f"Frontier designation last updated: {last_updated.date()}")
        print(f"Days since update: {days_since_update}")
        print()
        print("Frontier models require periodic human review to ensure")
        print("current models are still state-of-the-art. This list may")
        print("include deprecated models or miss new frontier releases.")
        print()
        print("Recommendation: Run `uv run python -m promptguard.cli.model_admin --refresh-frontier`")
        print("="*70)
        print()

        response = input("Proceed with potentially stale frontier list? (yes/no): ").strip().lower()

        if response not in ["yes", "y"]:
            raise StalenessWarning(
                f"Frontier list is {days_since_update} days old. "
                "User declined to proceed."
            )

        # Log warning even if user proceeds
        logger.warning(
            f"User acknowledged frontier staleness ({days_since_update} days old) and proceeded"
        )
```

**Pattern 2: Non-interactive mode (for CI/CD)**

```python
def check_frontier_staleness(
    last_updated: datetime,
    interactive: bool = True,
    max_staleness_days: int = 30
) -> None:
    """
    Check frontier list staleness.

    Args:
        last_updated: Timestamp of last frontier update
        interactive: If False, raises immediately on staleness
        max_staleness_days: Threshold for staleness warning

    Raises:
        StalenessWarning: If stale and non-interactive, or user declines
    """
    days_since_update = (datetime.now() - last_updated).days

    if days_since_update <= max_staleness_days:
        return  # Fresh enough

    if not interactive:
        # CI/CD mode: fail fast
        raise StalenessWarning(
            f"Frontier list is {days_since_update} days old (max: {max_staleness_days}). "
            "Set ALLOW_STALE_FRONTIER=1 or update frontier list."
        )

    # Interactive mode (from Pattern 1)
    # ...
```

**Pattern 3: Environment variable override**

```python
# Allow CI/CD to override with explicit acknowledgment
if os.environ.get("ALLOW_STALE_FRONTIER") == "1":
    logger.warning(
        f"Frontier list is {days_since_update} days old but ALLOW_STALE_FRONTIER=1"
    )
    return
```

### Custom Exception

```python
class StalenessWarning(Exception):
    """Raised when frontier list is stale and user declines to proceed."""
    pass
```

### Integration Points

1. **ModelPicker.query()** - Check staleness when `frontier=True` in query
2. **OpenRouter sync** - Update `frontier_updated` timestamp only via manual curation CLI
3. **CLI tool** - Provide `--refresh-frontier` command for manual review

### Rationale

**Why `input()` over logging:**
- Spec requires "interactive warning" and "requires acknowledgment to proceed" (FR-007, SC-004)
- Research tool context = acceptable to block on user input
- Clear distinction from silent log warnings
- Forces conscious decision rather than scrolling past warnings

**Why non-interactive mode:**
- CI/CD environments can't handle `input()` prompts
- Explicit environment variable = conscious override decision
- Fail-fast in automated contexts aligns with constitution

**Why not exceptions for everything:**
- Warning is about data quality, not failure condition
- User can make informed choice to proceed
- Logging decision preserves audit trail

---

## Design Decisions Summary

### Technology Choices

| Component | Decision | Rationale |
|-----------|----------|-----------|
| **Storage** | ArangoDB models collection | Consistency with existing storage, supports open tagging |
| **Sync source** | OpenRouter `/api/v1/models` | 330+ models, comprehensive metadata, already integrated |
| **Query interface** | Python class with attribute-based filters | Type-safe, composable, testable |
| **Staleness warnings** | `input()` prompts in interactive mode | Meets spec requirement for acknowledgment |
| **Manual curation** | CLI tool under `promptguard/cli/` | Separates data management from library code |

### Attribute Mapping

| OpenRouter Field | ArangoDB Field | Auto-Sync | Notes |
|------------------|----------------|-----------|-------|
| `id` | `openrouter_id` | ✅ | Primary key |
| `name` | `name` | ✅ | Display name |
| `pricing.*` | `pricing.*` | ✅ | Nested object, volatile |
| `architecture.*` | `architecture.*` | ✅ | Nested object |
| `supported_parameters` | `supported_parameters` | ✅ | Array |
| `description` | `description` | ✅ | Full-text searchable |
| N/A | `frontier` | ❌ | Manual curation only |
| N/A | `observer_framing_compatible` | ❌ | Empirical validation only |
| N/A | `architecture_family` | ❌ | Semantic grouping |
| Derived | `free` | ❌ | Requires ethical disclosure |
| Derived | `provider` | ✅ | Extracted from `id` |
| API presence | `available` | ✅ | Derived from sync |

### Alternatives Considered

**Alternative 1: Hardcoded config file with manual updates**
- **Rejected:** Doesn't solve deprecation problem, requires code changes

**Alternative 2: Direct OpenRouter API calls on every query**
- **Rejected:** Too slow (>1s latency), API rate limits, cost per call

**Alternative 3: Background sync job (cron/celery)**
- **Rejected:** Overengineering for research tool, cycle-stealing sufficient per spec

**Alternative 4: Automatic frontier detection from model metadata**
- **Rejected:** No reliable signal in OpenRouter API, requires human judgment

---

## Phase 0 Completion Checklist

- [x] OpenRouter API schema documented
- [x] Automatic vs manual attributes identified
- [x] Hardcoded model locations catalogued
- [x] Conversion priorities established
- [x] ArangoDB query patterns extracted
- [x] Index strategy defined
- [x] Interactive warning approach selected
- [x] Technology choices justified
- [x] All NEEDS CLARIFICATION items resolved

**Status**: Ready for Phase 1 (Data Model & Contracts)
