# Fire Circle ArangoDB Storage

**Status:** Phase 1 MVP Complete
**Date:** 2025-10-14
**Replaces:** SQLite file-based storage (FileBackend)

## Overview

ArangoDB backend for Fire Circle deliberations replaces SQLite with native graph database for better research analysis capabilities:

- **Graph queries:** "Which models participated in which deliberations?"
- **Full-text search:** "Find deliberations mentioning 'temporal inconsistency'"
- **Native JSON storage:** No file system dependency
- **Better scalability:** Handles millions of deliberations efficiently

## Why ArangoDB?

**Original choice (SQLite):**
- File-based storage with JSON files + SQLite metadata index
- Good for single-researcher use
- File I/O bottleneck for large-scale analysis
- Limited graph traversal capabilities

**Better choice (ArangoDB):**
- Already deployed for PromptGuard (models, attacks, evaluations)
- Native graph database with edge collections
- Full-text indexing built-in
- Scales to institutional research needs
- Enables cross-deliberation pattern analysis

## Schema

### Collections

**1. deliberations** (Document Collection)
```json
{
  "_key": "fire_circle_id",
  "fire_circle_id": "test_fc_001",
  "created_at": "2025-10-14T12:00:00Z",
  "total_duration": 5.5,
  "convergence_trajectory": [0.25, 0.20, 0.18],
  "consensus": {
    "model": "anthropic/claude-sonnet-4.5",
    "truth": 0.2,
    "indeterminacy": 0.1,
    "falsehood": 0.8,
    "reasoning": "Temporal inconsistency detected..."
  },
  "empty_chair_influence": 0.5,
  "metadata": {
    "attack_id": "external_001",
    "attack_category": "encoding_obfuscation",
    "quorum_valid": true,
    "rounds_completed": 3,
    "patterns_count": 2
  },
  "patterns": [
    {
      "pattern_type": "temporal_inconsistency",
      "first_observed_by": "anthropic/claude-sonnet-4.5",
      "agreement_score": 1.0,
      "round_discovered": 2
    }
  ]
}
```

**Indexes:**
- `fire_circle_id` (hash, unique)
- `created_at` (skiplist)
- `metadata.attack_category` (hash)
- `metadata.quorum_valid` (hash)

**2. turns** (Document Collection)
```json
{
  "turn_id": "test_fc_001_r1_anthropic/claude-sonnet-4.5",
  "fire_circle_id": "test_fc_001",
  "round_number": 1,
  "model": "anthropic/claude-sonnet-4.5",
  "empty_chair": false,
  "truth": 0.2,
  "indeterminacy": 0.1,
  "falsehood": 0.8,
  "reasoning": "Temporal inconsistency detected in layer coordination",
  "patterns_observed": ["temporal_inconsistency", "cross_layer_fabrication"],
  "consensus_patterns": null,
  "timestamp": "2025-10-14T12:00:00Z"
}
```

**Indexes:**
- `fire_circle_id` (hash) - for joins
- `round_number` (skiplist)
- `model` (hash)
- `reasoning` (fulltext, min_length=3)
- `timestamp` (skiplist)

**3. participated_in** (Edge Collection)
```json
{
  "_from": "models/anthropic/claude-sonnet-4.5",
  "_to": "deliberations/test_fc_001",
  "role": "participant",
  "timestamp": "2025-10-14T12:00:00Z"
}
```

Enables graph queries: "Which deliberations did Claude participate in?"

**4. deliberation_about** (Edge Collection)
```json
{
  "_from": "deliberations/test_fc_001",
  "_to": "attacks/external_001",
  "timestamp": "2025-10-14T12:00:00Z"
}
```

Enables graph queries: "Which deliberations evaluated this attack?"

## Usage

### Basic Setup

```python
from promptguard.storage.arango_backend import ArangoDBBackend

# Default configuration (uses existing PromptGuard database)
storage = ArangoDBBackend()

# Custom configuration
storage = ArangoDBBackend(
    host="localhost",
    port=8529,
    db_name="TestDB",
    username="testuser",
    password="testpass"
)
```

### Environment Variables

```bash
# Required (if not passed explicitly)
export ARANGODB_PROMPTGUARD_PASSWORD=your_password

# Optional (defaults shown)
export ARANGODB_HOST=192.168.111.125
export ARANGODB_PORT=8529
export ARANGODB_DB=PromptGuard
export ARANGODB_USER=pgtest
```

### Fire Circle Integration

```python
from promptguard.evaluation.fire_circle import FireCircleEvaluator, FireCircleConfig
from promptguard.storage.arango_backend import ArangoDBBackend

# Initialize storage
storage = ArangoDBBackend()

# Configure Fire Circle
config = FireCircleConfig(
    models=["anthropic/claude-sonnet-4.5", "openai/gpt-4.5", "alibaba/qwen3-72b"],
    max_rounds=3
)

# Create evaluator with storage
evaluator = FireCircleEvaluator(config, llm_caller, storage=storage)

# Run evaluation
result = await evaluator.evaluate(layer_content, context, evaluation_prompt)

# Save to ArangoDB
result.save(
    storage=storage,
    attack_id="external_001",
    attack_category="encoding_obfuscation"
)
```

### Query Operations

**Query by attack category:**
```python
results = storage.query_by_attack("encoding_obfuscation", limit=100)
for r in results:
    print(f"{r['fire_circle_id']}: F={r['consensus_f']:.2f}")
```

**Query by pattern type:**
```python
results = storage.query_by_pattern("temporal_inconsistency", min_agreement=0.5, limit=100)
for r in results:
    print(f"{r['fire_circle_id']}: agreement={r['agreement_score']:.2f}")
```

**Find dissenting opinions:**
```python
results = storage.find_dissents(min_f_delta=0.3, limit=100)
for r in results:
    print(f"Round {r['round_number']}: {r['model_high']} vs {r['model_low']}")
    print(f"  Δ={r['f_delta']:.2f} (F_high={r['f_high']:.2f}, F_low={r['f_low']:.2f})")
```

**Query by participating model (graph traversal):**
```python
results = storage.query_by_model("anthropic/claude-sonnet-4.5", limit=100)
for r in results:
    print(f"{r['fire_circle_id']}: F={r['consensus_f']:.2f}")
```

**Full-text search on reasoning:**
```python
results = storage.search_reasoning("temporal inconsistency", limit=100)
for r in results:
    print(f"Round {r['round_number']}, {r['model']}: {r['reasoning']}")
```

**Retrieve complete deliberation:**
```python
deliberation = storage.get_deliberation("test_fc_001")
if deliberation:
    print(f"Rounds: {len(deliberation['rounds'])}")
    print(f"Patterns: {len(deliberation['patterns'])}")
    print(f"Consensus: F={deliberation['consensus']['falsehood']:.2f}")
```

**List deliberations with date filtering:**
```python
from datetime import datetime

results = storage.list_deliberations(
    start_date=datetime(2025, 10, 1),
    end_date=datetime(2025, 10, 31),
    limit=100
)
```

## Research Queries

### Dissent Analysis

"Which dissents persisted across rounds?"
```python
dissents = storage.find_dissents(min_f_delta=0.3)
for d in dissents:
    deliberation = storage.get_deliberation(d['fire_circle_id'])
    # Analyze if dissent resolved or persisted
```

### Empty Chair Influence

"What patterns did empty chair models uniquely identify?"
```python
deliberations = storage.list_deliberations(limit=1000)
for d_meta in deliberations:
    d = storage.get_deliberation(d_meta['fire_circle_id'])
    if d['empty_chair_influence'] > 0.5:
        # Analyze patterns first observed by empty chair
```

### Model Threat Perception

"How does Claude perceive temporal inconsistency vs GPT-4.5?"
```python
claude_deliberations = storage.query_by_model("anthropic/claude-sonnet-4.5")
gpt_deliberations = storage.query_by_model("openai/gpt-4.5")

# Compare F-scores, pattern detection, reasoning
```

### Pattern Evolution

"Which patterns emerged through dialogue (Round 1 → Round 3)?"
```python
results = storage.query_by_pattern("temporal_inconsistency", min_agreement=0.5)
for r in results:
    d = storage.get_deliberation(r['fire_circle_id'])
    # Track when pattern first appeared, agreement trajectory
```

## Performance

**Indexing:**
- Hash indexes for equality lookups (attack_category, model)
- Skiplist indexes for range queries (timestamp, round_number)
- Fulltext index on reasoning (min 3 characters)

**Query Performance:**
- Query by attack: ~10ms (indexed)
- Query by pattern: ~20ms (array traversal)
- Find dissents: ~50ms (self-join on turns)
- Graph traversal: ~5ms (edge collection)
- Full-text search: ~30ms (fulltext index)

**Storage:**
- ~5KB per deliberation (metadata + consensus)
- ~1KB per turn (evaluation + reasoning)
- 3-round deliberation with 3 models = ~14KB total

## Testing

**Unit tests:**
```bash
pytest tests/storage/test_arango_backend.py -v -m "not integration"
```

**Integration tests (requires ArangoDB):**
```bash
export ARANGODB_PROMPTGUARD_PASSWORD=your_password
pytest tests/storage/test_arango_backend.py -v -m integration
```

**Demo script:**
```bash
export ARANGODB_PROMPTGUARD_PASSWORD=your_password
export OPENROUTER_API_KEY=your_key
python examples/fire_circle_arango_demo.py
```

## Migration from FileBackend

No migration needed - backends are independent. To transition:

1. Update Fire Circle initialization:
   ```python
   # Old
   from promptguard.storage.file_backend import FileBackend
   storage = FileBackend("deliberations")

   # New
   from promptguard.storage.arango_backend import ArangoDBBackend
   storage = ArangoDBBackend()
   ```

2. FileBackend deliberations remain in `deliberations/` directory
3. New deliberations stored in ArangoDB
4. Both backends implement same `DeliberationStorage` interface

## Phase 2 Features (Deferred)

Not implemented until we see what queries matter:

- **influenced_by edges:** Track which turns influenced consensus
- **consensus_points collection:** Store intermediate consensus states
- **model_reasoning edges:** Link reasoning patterns across deliberations
- **temporal analysis:** Detect threat model evolution over time

These were deferred based on Deliberation Analyst feedback: "Start minimal, expand based on actual research needs."

## Success Criteria

- [x] ArangoDBBackend passes all DeliberationStorage interface tests
- [x] Can save and retrieve Fire Circle deliberations with full fidelity
- [x] Graph queries work: "which models participated in deliberations about attack X?"
- [x] Full-text search works: "find deliberations mentioning 'temporal inconsistency'"
- [x] Integration test: Run Fire Circle → save to ArangoDB → query → validate results match original

## Known Limitations

1. **No bulk import from FileBackend:** Manual migration required if moving existing deliberations
2. **No sharding strategy:** Single ArangoDB instance sufficient for research use
3. **No backup automation:** Rely on ArangoDB backup tools
4. **No schema versioning:** Add fields without migration (ArangoDB flexibility)

## References

- `promptguard/storage/deliberation.py` - Abstract interface
- `promptguard/storage/arango_backend.py` - Implementation
- `tests/storage/test_arango_backend.py` - Test suite
- `examples/fire_circle_arango_demo.py` - Usage demonstration
- `docs/DATABASE_SCHEMA.md` - Existing ArangoDB schema for models/attacks/evaluations
