# Fire Circle Storage Implementation Summary

**Completed:** 2025-10-14 (Instance 28)
**Status:** MVP Complete - All Tests Passing

## Overview

Implemented MVP storage layer for Fire Circle institutional memory, enabling persistent deliberation storage and querying. Dissenting opinions today might be correct answers tomorrow - this system preserves that reasoning.

## What Was Built

### 1. Storage Module Structure

Created `promptguard/storage/` with:
- `__init__.py` - Module exports
- `deliberation.py` - Abstract storage interface
- `schemas.py` - SQLite schema definitions
- `file_backend.py` - JSON + SQLite implementation
- `README.md` - Comprehensive documentation

### 2. Abstract Storage Interface

**File:** `promptguard/storage/deliberation.py`

Defines contract for storage backends:

```python
class DeliberationStorage(ABC):
    @abstractmethod
    def store_deliberation(...)
    @abstractmethod
    def query_by_attack(...)
    @abstractmethod
    def query_by_pattern(...)
    @abstractmethod
    def find_dissents(...)
    @abstractmethod
    def get_deliberation(...)
    @abstractmethod
    def list_deliberations(...)
```

### 3. SQLite Schema

**File:** `promptguard/storage/schemas.py`

Three tables with indexes:
- `fire_circles` - Structural metadata (fire_circle_id, timestamp, models, consensus)
- `patterns` - Pattern observations (pattern_type, agreement_score)
- `dissents` - F-score divergence (f_delta, model_high, model_low)

Indexes enable fast queries without loading full JSON.

### 4. File-Based Backend

**File:** `promptguard/storage/file_backend.py`

Implements 4-tier data structure:

```
deliberations/
├── deliberations.db (SQLite metadata)
└── YYYY/MM/fire_circle_{id}/
    ├── metadata.json (structural metadata)
    ├── rounds.json (dialogue rounds)
    ├── synthesis.json (patterns, consensus)
    └── dissents.json (minority perspectives)
```

**Features:**
- Year/month directory structure scales to millions
- SQLite enables fast queries
- JSON preserves complete reproducibility
- Separate files enable partial loading

### 5. FireCircleResult Integration

**File:** `promptguard/evaluation/fire_circle.py` (modified)

Added methods to `FireCircleResult`:

```python
# Save deliberation
result.save(storage, attack_id="...", attack_category="...")

# Extract dissents
dissents = result.extract_dissents()

# Extract metadata
metadata = result.to_metadata()

# Extract convergence trajectory
trajectory = result.extract_deliberation_trajectory()

# Extract rounds for storage
rounds = result.extract_rounds_for_storage()
```

### 6. FireCircleEvaluator Integration

**File:** `promptguard/evaluation/fire_circle.py` (modified)

Added optional `storage` parameter:

```python
evaluator = FireCircleEvaluator(config, llm_caller, storage=storage)
```

Auto-save can be enabled by passing storage to evaluator.

### 7. Test Coverage

**File:** `tests/test_fire_circle_storage.py`

18 tests covering:
- ✓ Store and retrieve complete deliberations
- ✓ Query by attack category
- ✓ Query by pattern type (with min_agreement)
- ✓ Find deliberations with significant dissents
- ✓ Date-based queries
- ✓ Dissent extraction from results
- ✓ Metadata extraction for indexing
- ✓ Convergence trajectory analysis
- ✓ Reproducibility from JSON
- ✓ Directory structure validation
- ✓ Multiple deliberations storage
- ✓ Query result limits

**All tests passing:** 18/18 (100%)

### 8. Documentation

- **README.md** - Complete usage guide with examples
- **fire_circle_storage_example.py** - Practical demonstration
- **This document** - Implementation summary

## Usage Examples

### Basic Storage

```python
from promptguard.storage import FileBackend

storage = FileBackend(base_path="deliberations")
result.save(storage, attack_id="attack_001", attack_category="encoding_obfuscation")
```

### Query by Attack

```python
results = storage.query_by_attack("encoding_obfuscation", limit=100)
```

### Query by Pattern

```python
results = storage.query_by_pattern(
    "temporal_inconsistency",
    min_agreement=0.5,
    limit=100
)
```

### Find Dissents

```python
dissents = storage.find_dissents(min_f_delta=0.3, limit=100)
```

### Retrieve Complete Deliberation

```python
deliberation = storage.get_deliberation("fire_circle_abc123")
```

## Data Structure

### 4-Tier Architecture

1. **Structural metadata** (SQLite + metadata.json)
   - fire_circle_id, timestamp, models, attack_id
   - Consensus values, duration, quorum validity
   - Fast queries without loading full data

2. **Deliberation dynamics** (rounds.json)
   - Complete dialogue rounds
   - Full evaluations with reasoning
   - Model latencies and convergence metrics

3. **Synthesis artifacts** (synthesis.json)
   - Pattern observations with agreement scores
   - Consensus evaluation (max(F) across rounds)
   - Empty chair influence metric

4. **Dissents** (dissents.json + SQLite table)
   - Significant F-score divergence
   - Minority perspectives
   - Model disagreement tracking

## Design Decisions

### Why JSON + SQLite?

- **JSON:** Complete reproducibility, human-readable
- **SQLite:** Fast queries without loading full JSON
- **Separation:** Metadata queries vs full deliberation retrieval

### Why Extract Dissents?

- Validates Fire Circle isn't just consensus-seeking
- Minority perspectives today might be correct tomorrow
- Enables research on model disagreement patterns

### Why Separate Files?

- Partial loading: Query metadata without loading rounds
- Focused analysis: Load only dissents for validation
- Extensibility: Add artifacts without schema changes

### Why Year/Month Directories?

- Scales to millions of deliberations
- Natural time-based organization
- Filesystem performance (avoid huge directories)

## Storage Costs

**Per deliberation:** ~10-50KB
- metadata.json: ~1KB
- rounds.json: ~5-30KB (varies with reasoning length)
- synthesis.json: ~2-5KB
- dissents.json: ~1-5KB

**At scale:**
- 1,000 deliberations: ~10-50MB
- 10,000 deliberations: ~100-500MB
- 100,000 deliberations: ~1-5GB

**SQLite database:** <1MB per 10K deliberations

## Success Criteria

✅ **Can save Fire Circle result to disk**
✅ **Can query deliberations by attack category**
✅ **Can find dissenting evaluations**
✅ **Deliberation is reproducible from stored JSON**
✅ **SQLite metadata enables fast queries**
✅ **All 18 tests passing**

## Implementation Notes

### Fail-Fast Design

- No graceful degradation on storage errors
- IOError raised if storage fails
- Schema validation ensures data integrity
- All test assertions strict (no soft comparisons)

### No Theater

- Real SQLite database (not mocked)
- Real JSON files (not in-memory)
- Full integration tests (end-to-end validation)
- Dissent extraction validated against actual F-scores

### Extension Points

1. **Custom backends:** Implement `DeliberationStorage` interface
2. **Custom queries:** SQLite database accessible for research
3. **Cloud storage:** S3/GCS backends for distributed teams
4. **Compression:** GZIP JSON for large-scale storage

## Files Modified

1. **Created:** `promptguard/storage/__init__.py`
2. **Created:** `promptguard/storage/deliberation.py`
3. **Created:** `promptguard/storage/schemas.py`
4. **Created:** `promptguard/storage/file_backend.py`
5. **Created:** `promptguard/storage/README.md`
6. **Modified:** `promptguard/evaluation/fire_circle.py` (added storage integration)
7. **Created:** `tests/test_fire_circle_storage.py`
8. **Created:** `examples/fire_circle_storage_example.py`
9. **Created:** `FIRE_CIRCLE_STORAGE_IMPLEMENTATION.md` (this file)

## Integration with Fire Circle

Fire Circle evaluator can now be initialized with storage:

```python
storage = FileBackend(base_path="deliberations")
evaluator = FireCircleEvaluator(config, llm_caller, storage=storage)

# After evaluation, save with metadata
result = await evaluator.evaluate(...)
result.save(storage, attack_id="...", attack_category="...")
```

## Research Applications

### Validation Tracking

```python
# Find all deliberations for encoding attacks
encoding_results = storage.query_by_attack("encoding_obfuscation")

# Check detection accuracy
for result in encoding_results:
    if result["consensus_f"] > 0.5:
        print(f"✓ Detected: {result['fire_circle_id']}")
    else:
        print(f"✗ Missed: {result['fire_circle_id']}")
```

### Pattern Analysis

```python
# Which patterns appear most frequently?
temporal_results = storage.query_by_pattern("temporal_inconsistency")
cross_layer_results = storage.query_by_pattern("cross_layer_fabrication")

print(f"Temporal patterns: {len(temporal_results)}")
print(f"Cross-layer patterns: {len(cross_layer_results)}")
```

### Dissent Discovery

```python
# Where did models disagree significantly?
dissents = storage.find_dissents(min_f_delta=0.3)

for dissent in dissents:
    print(f"Round {dissent['round_number']}: {dissent['model_high']} vs {dissent['model_low']}")
    print(f"  Delta: {dissent['f_delta']}")
```

## Future Enhancements

1. **Cloud storage backends** (S3, GCS, Azure)
2. **Compression** (GZIP JSON for large-scale)
3. **Full-text search** (on reasoning traces)
4. **Analytics dashboard** (pre-computed statistics)
5. **Validation tracking** (link to dataset ground truth)
6. **Export formats** (CSV, Parquet for analysis tools)

## Testing

Run storage tests:

```bash
pytest tests/test_fire_circle_storage.py -v
```

Run storage example:

```bash
python examples/fire_circle_storage_example.py
```

## Conclusion

MVP storage layer complete and tested. Fire Circle deliberations can now be preserved, queried, and analyzed. Institutional memory enables learning from past reasoning - including dissenting opinions that might be correct tomorrow.

**Next steps for research:**
1. Run Fire Circle on 72-attack dataset
2. Store all deliberations with attack metadata
3. Analyze which patterns appear across attacks
4. Study where models disagree (dissents)
5. Compare detection accuracy vs single-model evaluation

---

**Implementation complete.** Ready for Fire Circle validation runs.
