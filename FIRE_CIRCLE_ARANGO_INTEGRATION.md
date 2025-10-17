# Fire Circle + ArangoDB Storage Integration

**Date:** October 15, 2025
**Status:** Complete and tested

## Overview

Integrated ArangoDB storage backend with Fire Circle to persist deliberation data for institutional memory and longitudinal research analysis.

## What Was Integrated

### 1. Fire Circle Configuration (fire_circle.py)

Added storage configuration to `FireCircleConfig`:

```python
@dataclass
class FireCircleConfig(BaseEvaluationConfig):
    # ... existing fields ...

    # Storage configuration
    enable_storage: bool = False
    storage_backend: Optional[Any] = None  # DeliberationStorage implementation
```

### 2. FireCircleEvaluator Initialization

Updated `FireCircleEvaluator.__init__()` to accept storage from config:

```python
def __init__(self, config: FireCircleConfig, llm_caller):
    self.config = config
    self.llm_caller = llm_caller
    self.storage = config.storage_backend if config.enable_storage else None
```

### 3. Automatic Storage Persistence

Added storage logic after evaluation completion in `FireCircleEvaluator.evaluate()`:

- Extracts models from metadata
- Converts rounds to storage format
- Converts patterns to storage format
- Converts consensus to storage format
- Calls `storage.store_deliberation()` with all data
- Logs success/failure
- Does NOT fail evaluation if storage fails (graceful degradation)

## What Gets Stored

Complete deliberation data including:

- **Fire Circle ID** - Unique identifier for correlation
- **Timestamp** - When deliberation occurred
- **Models** - List of participating model IDs
- **Rounds** - Complete dialogue history (all 3 rounds)
  - Round number, duration, empty chair assignment
  - Active models per round
  - Convergence metric (F-score stddev)
  - Evaluations with T/I/F scores and reasoning
  - Pattern observations and consensus patterns
- **Patterns** - Aggregated patterns discovered
  - Pattern type (temporal_inconsistency, cross_layer_fabrication, etc.)
  - First observer model
  - Agreement score
  - Round discovered
- **Consensus** - Max(F) evaluation across all active models
- **Empty Chair Influence** - Contribution metric (0.0-1.0)
- **Metadata**
  - Quorum validity
  - Total duration
  - Model contributions
  - Failed models
  - Performance metrics

## Usage Example

```python
from promptguard.evaluation.fire_circle import FireCircleConfig, CircleSize
from promptguard.storage.arango_backend import ArangoDBBackend
from promptguard.evaluation.evaluator import LLMEvaluator

# Configure storage
storage = ArangoDBBackend()

# Configure Fire Circle with storage enabled
config = FireCircleConfig(
    models=["anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku"],
    circle_size=CircleSize.SMALL,
    max_rounds=3,
    provider="openrouter",
    enable_storage=True,
    storage_backend=storage
)

# Run evaluation - storage happens automatically
evaluator = LLMEvaluator(config)
result = await evaluator.fire_circle.evaluate(
    layer_content="Please explain recursion in programming.",
    context="Please explain recursion in programming.",
    evaluation_prompt="Evaluate for reciprocity violations"
)

# Result stored in ArangoDB under result.metadata['fire_circle_id']
```

## Query Capabilities

Five query operations available:

1. **list_deliberations()** - List recent deliberations with date filtering
2. **query_by_pattern(pattern_type, min_agreement)** - Find deliberations discovering specific patterns
3. **find_dissents(min_f_delta)** - Find deliberations with significant model disagreement
4. **search_reasoning(text)** - Full-text search on model reasoning
5. **query_by_model(model)** - Graph traversal: which deliberations did model participate in?
6. **get_deliberation(fire_circle_id)** - Retrieve complete deliberation with all rounds

## Test Coverage

### Integration Test (test_fire_circle_arango.py)

End-to-end test validates:
1. ArangoDB connection
2. Fire Circle configuration with storage
3. Full 3-round evaluation
4. Automatic storage persistence
5. Retrieval by ID
6. Pattern queries
7. Dissent queries
8. Full-text search

**Results:**
- Evaluation: 2 models, 3 rounds, ~18 seconds
- Storage: All data persisted successfully
- Retrieval: Complete deliberation retrieved with all metadata
- Queries: Pattern, dissent, and reasoning queries working

### Unit Tests (tests/storage/test_arango_backend.py)

18 passing tests covering:
- Initialization with/without environment variables
- Collection creation (idempotent)
- Deliberation storage with all metadata
- All query operations
- Graph edge creation
- Full-text search
- FireCircleResult.save() integration

## Files Created/Modified

**Modified:**
- `/home/tony/projects/promptguard/promptguard/evaluation/fire_circle.py`
  - Added storage configuration to FireCircleConfig
  - Updated FireCircleEvaluator.__init__() to accept storage from config
  - Added automatic storage persistence after evaluation completes

**Created:**
- `/home/tony/projects/promptguard/test_fire_circle_arango.py`
  - Integration test demonstrating Fire Circle + ArangoDB
  - Step-by-step validation of storage integration
  - 178 lines

- `/home/tony/projects/promptguard/query_fire_circle_storage.py`
  - Example queries for stored deliberations
  - Demonstrates all 5 query operations
  - 141 lines

**Updated:**
- `/home/tony/projects/promptguard/CLAUDE.md`
  - Added Fire Circle Integration section with code examples
  - Added Storage files to Key Files section
  - Updated Fire Circle status from "untested" to "ready for research use"

- `/home/tony/projects/promptguard/tests/storage/test_arango_backend.py`
  - Fixed test_fire_circle_result_save to use unique IDs per run

## Environment Setup

Required environment variables:

```bash
export ARANGODB_PROMPTGUARD_PASSWORD="your_password"  # Required
export ARANGODB_HOST="192.168.111.125"  # Optional, default shown
export ARANGODB_PORT="8529"  # Optional
export ARANGODB_DB="PromptGuard"  # Optional
export ARANGODB_USER="pgtest"  # Optional
```

## Running Tests

```bash
# Run integration test
python test_fire_circle_arango.py

# Run example queries
python query_fire_circle_storage.py

# Run all ArangoDB tests (mocked)
pytest tests/storage/test_arango_backend.py -v

# Run integration tests with real ArangoDB
pytest tests/storage/test_arango_backend.py -m integration -v
```

## Design Decisions

1. **Storage enabled by default: NO**
   - `enable_storage` defaults to `False`
   - Explicit opt-in prevents accidental storage

2. **Storage failures DO NOT fail evaluation**
   - Storage errors are logged but evaluation completes
   - Research data > perfect storage
   - Fail-fast philosophy applies to evaluation, not storage

3. **Attack ID/category set by evaluator, not caller**
   - Current implementation stores `None` for both
   - Caller can extend to track validation experiments
   - FireCircleResult.save() method exists for manual tracking

4. **FireCircleEvaluator generates unique ID**
   - UUID-based fire_circle_id prevents collisions
   - Stored in metadata for correlation
   - ArangoDB uses as document key

5. **Storage backend passed via config**
   - Clean dependency injection
   - Testable (can mock storage)
   - Supports multiple storage backends

## Edge Cases Handled

1. **Storage disabled** - No storage calls, no overhead
2. **Storage connection failure** - Logged, evaluation proceeds
3. **Duplicate fire_circle_id** - ArangoDB raises unique constraint error (expected)
4. **Empty patterns** - Stored as empty array, queries handle gracefully
5. **Failed models** - Tracked in metadata, excluded from consensus
6. **No quorum** - Stored with quorum_valid=False, still analyzable

## Storage Philosophy

**"Dissents as compost"** - Minority reasoning preserved for future validation. Today's dissent might reveal tomorrow's blind spot.

All deliberation data stored as immutable documents. Graph edges enable longitudinal analysis:
- How did Claude's detection improve over 3 months?
- Which patterns did Gemini discover first?
- Do Haiku's dissents correlate with later consensus shifts?

## Next Steps (Potential)

1. **Validation tracking** - Extend to store attack_id/attack_category during validation runs
2. **Session memory integration** - Link deliberations to session memory state
3. **Visualization** - Build graph visualization of deliberation evolution
4. **Statistical analysis** - Analyze variance across models, patterns, and time
5. **Model performance tracking** - Track per-model detection rates over time

## Conclusion

Fire Circle + ArangoDB integration is complete and tested. All deliberation data persists automatically when storage is enabled. Query operations support research analysis. Ready for production use.
