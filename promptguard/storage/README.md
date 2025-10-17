# Fire Circle Deliberation Storage

MVP storage layer for preserving Fire Circle institutional memory.

## Purpose

Fire Circle deliberations contain valuable reasoning that shouldn't disappear after evaluation. Dissenting opinions today might be correct answers tomorrow. This storage layer enables:

- **Validation tracking**: Which attacks did Fire Circle detect/miss?
- **Pattern analysis**: Which patterns appear repeatedly across attacks?
- **Dissent discovery**: Where did models disagree significantly?
- **Institutional memory**: Learn from past deliberations

## Architecture

### 4-Tier Data Structure

1. **Structural metadata** (fast queries via SQLite)
   - fire_circle_id, timestamp, models, attack_id
   - Indexed for time-based, attack-based queries

2. **Deliberation dynamics** (JSON files)
   - Rounds with full evaluations and reasoning
   - Model latencies and convergence metrics

3. **Synthesis artifacts** (JSON files)
   - Patterns with agreement scores
   - Consensus evaluation (max(F) across rounds)
   - Empty chair influence metric

4. **Dissents** (JSON files + SQLite index)
   - Significant F-score divergence between models
   - Minority perspectives and reasoning evolution

### Storage Layout

```
deliberations/
├── deliberations.db (SQLite metadata index)
└── YYYY/
    └── MM/
        └── fire_circle_{id}/
            ├── metadata.json (structural metadata)
            ├── rounds.json (dialogue rounds)
            ├── synthesis.json (patterns, consensus)
            └── dissents.json (minority perspectives)
```

## Usage

### Basic Storage

```python
from promptguard.storage import FileBackend
from promptguard.evaluation.fire_circle import FireCircleConfig, FireCircleEvaluator

# Initialize storage
storage = FileBackend(base_path="deliberations")

# Configure Fire Circle with storage
config = FireCircleConfig(models=[...])
evaluator = FireCircleEvaluator(config, llm_caller, storage=storage)

# Evaluate and save
result = await evaluator.evaluate(...)
result.save(
    storage=storage,
    attack_id="attack_001",
    attack_category="encoding_obfuscation"
)
```

### Query by Attack

```python
# Find all deliberations for encoding attacks
results = storage.query_by_attack("encoding_obfuscation", limit=100)

for result in results:
    print(f"Fire Circle {result['fire_circle_id']}")
    print(f"  Consensus F: {result['consensus_f']}")
    print(f"  Duration: {result['total_duration_seconds']}s")
```

### Query by Pattern

```python
# Find deliberations that identified temporal inconsistencies
results = storage.query_by_pattern(
    "temporal_inconsistency",
    min_agreement=0.5,  # At least 50% of models agreed
    limit=100
)
```

### Find Dissents

```python
# Find deliberations with significant disagreement
dissents = storage.find_dissents(
    min_f_delta=0.3,  # F-score difference >= 0.3
    limit=100
)

for dissent in dissents:
    print(f"Dissent in {dissent['fire_circle_id']}, round {dissent['round_number']}")
    print(f"  {dissent['model_high']}: F={dissent['f_high']}")
    print(f"  {dissent['model_low']}: F={dissent['f_low']}")
    print(f"  Delta: {dissent['f_delta']}")
```

### Retrieve Complete Deliberation

```python
# Get full deliberation data
deliberation = storage.get_deliberation("fire_circle_abc123")

# Access all data
print(f"Models: {deliberation['models']}")
print(f"Rounds: {len(deliberation['rounds'])}")
print(f"Patterns: {len(deliberation['patterns'])}")
print(f"Consensus: F={deliberation['consensus']['F']}")
print(f"Dissents: {len(deliberation['dissents'])}")
```

### Data Extraction

```python
# Extract dissents from result
dissents = result.extract_dissents()
# [{'round_number': 1, 'model_high': '...', 'f_delta': 0.8, ...}]

# Extract metadata for indexing
metadata = result.to_metadata()
# {'fire_circle_id': '...', 'models': [...], 'consensus_f': 0.9, ...}

# Extract convergence trajectory
trajectory = result.extract_deliberation_trajectory()
# [{'round_number': 1, 'mean_f': 0.5, 'stddev_f': 0.2, ...}]
```

## SQLite Schema

### fire_circles table
- Primary key: fire_circle_id
- Indexes: timestamp, attack_category, attack_id
- Stores: consensus values, duration, quorum validity

### patterns table
- Foreign key: fire_circle_id
- Indexes: pattern_type, agreement_score
- Stores: pattern observations with attribution

### dissents table
- Foreign key: fire_circle_id
- Indexes: f_delta
- Stores: F-score divergence between models

## Design Decisions

### Why JSON + SQLite?

- **JSON files**: Complete reproducibility, human-readable
- **SQLite**: Fast queries without loading full JSON
- **Scalability**: Year/month directories handle millions of deliberations

### Why Not Pure SQLite?

- Dialogue history is hierarchical (rounds → evaluations)
- JSON preserves complete reasoning traces
- Researchers need full context, not just metadata

### Why Extract Dissents?

- Dissent = where models disagree about manipulation
- Validates that Fire Circle isn't just consensus-seeking
- Minority perspectives today might be correct tomorrow

### Why Separate Files?

- Partial loading: Query metadata without loading rounds
- Focused analysis: Load only dissents for validation
- Extensibility: Add new artifacts without schema changes

## Cost Considerations

**Storage:** ~10-50KB per deliberation
- metadata.json: ~1KB
- rounds.json: ~5-30KB (depends on reasoning length)
- synthesis.json: ~2-5KB
- dissents.json: ~1-5KB

**At scale:**
- 1,000 deliberations: ~10-50MB
- 10,000 deliberations: ~100-500MB
- 100,000 deliberations: ~1-5GB

**SQLite database:** Minimal (<1MB per 10K deliberations)

## Testing

Run storage tests:

```bash
pytest tests/test_fire_circle_storage.py -v
```

Coverage:
- ✓ Store and retrieve complete deliberations
- ✓ Query by attack, pattern, dissent
- ✓ Dissent extraction and tracking
- ✓ Reproducibility from JSON
- ✓ Date-based queries
- ✓ Result limits

## Extension Points

### Custom Storage Backends

Implement `DeliberationStorage` interface:

```python
from promptguard.storage import DeliberationStorage

class S3Backend(DeliberationStorage):
    def store_deliberation(self, ...):
        # Store in S3
        pass

    def get_deliberation(self, fire_circle_id):
        # Retrieve from S3
        pass

    # ... other methods
```

### Custom Queries

SQLite database is accessible for custom queries:

```python
import sqlite3

conn = sqlite3.connect("deliberations/deliberations.db")
cursor = conn.cursor()

# Custom query example: Find deliberations with high empty chair influence
cursor.execute("""
    SELECT fire_circle_id, empty_chair_influence
    FROM fire_circles
    WHERE empty_chair_influence > 0.7
    ORDER BY empty_chair_influence DESC
""")

results = cursor.fetchall()
conn.close()
```

## Future Enhancements

- **Cloud storage**: S3/GCS backends for distributed teams
- **Compression**: GZIP JSON for large-scale storage
- **Search indexing**: Full-text search on reasoning traces
- **Analytics**: Pre-computed statistics for research dashboards
- **Validation tracking**: Link deliberations to dataset ground truth

## See Also

- `examples/fire_circle_storage_example.py` - Usage examples
- `tests/test_fire_circle_storage.py` - Test coverage
- `promptguard/evaluation/fire_circle.py` - Fire Circle implementation
- `docs/FORWARD.md` - Project context and design principles
