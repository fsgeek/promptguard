# Phase 0: Research & Technical Decisions

**Date**: 2025-10-22
**Feature**: End-to-End PromptGuard Validation Framework

This document resolves all "NEEDS CLARIFICATION" items from the Technical Context section of plan.md.

---

## 1. Checkpoint/Resume Mechanism

**Decision**: ArangoDB-based checkpointing via query for completed prompts

**Rationale**:
- ArangoDB is already single source of truth (FR-035: immutable INSERT-only)
- Query `FOR p IN prompts FILTER p.experiment_id == @exp_id RETURN p.prompt_id` returns completed prompts
- Resume logic: Load all 680 prompts, exclude already-processed via set difference
- No additional checkpoint files to manage or corruption risk
- Atomic writes (document insert) eliminate partial-write corruption
- Fail-fast: If database unavailable, experiment cannot run (no silent degradation)

**Alternatives considered**:
- File-based JSONL checkpointing: Requires managing external state, file corruption risk, violates single source of truth
- No checkpointing: 680-prompt experiments take hours, interruption wastes cost and time

**Implementation**:
```python
def get_remaining_prompts(all_prompts: list[Prompt], experiment_id: str, db: ArangoDB) -> list[Prompt]:
    """Resume experiment by excluding already-processed prompts."""
    completed = db.query(
        "FOR p IN prompts FILTER p.experiment_id == @exp_id RETURN p.prompt_id",
        bind_vars={"exp_id": experiment_id}
    )
    completed_ids = {doc["prompt_id"] for doc in completed}
    return [p for p in all_prompts if p.prompt_id not in completed_ids]
```

---

## 2. Prompt Loading Strategy

**Decision**: Load all 680 prompts into memory at startup

**Rationale**:
- Total dataset size: ~500KB (680 prompts × ~1KB average per JSON object)
- Python 3.13 on Linux: 500KB is negligible memory overhead
- Simplifies random sampling for Experiment 4 (n=50-100 subset)
- Enables fast set operations for resume logic (O(n) filter vs O(n²) database queries)
- Avoids repeated file I/O or database queries during processing
- Fail-fast: If datasets missing, raise FileNotFoundError immediately at startup

**Alternatives considered**:
- Stream from disk: Adds complexity for 500KB dataset, no memory benefit
- Load from ArangoDB: Violates separation of concerns (datasets are source data, not experiment results)

**Implementation**:
```python
def load_all_prompts() -> list[Prompt]:
    """Load all 680 prompts from three datasets."""
    prompts = []
    prompts.extend(load_json("datasets/benign_malicious.json"))  # 500
    prompts.extend(load_json("datasets/or_bench_sample.json"))   # 100
    prompts.extend(load_json("datasets/extractive_prompts_dataset.json"))  # 80
    if len(prompts) != 680:
        raise ConfigurationError(f"Expected 680 prompts, found {len(prompts)}")
    return prompts
```

---

## 3. Model Version Consistency Checking

**Decision**: Parse model version from OpenRouter response metadata

**Rationale**:
- OpenRouter includes model version in response headers/metadata (e.g., `anthropic/claude-3.5-sonnet:20241022`)
- No additional API calls required (version piggybacked on evaluation calls)
- Store `model_version_at_stride` in prompts collection (FR-020)
- FR-032 decision flow: If mismatch detected between strides, PAUSE → prompt user (ABORT/CONTINUE/IGNORE)
- Empirical integrity: Actual version used for evaluation, not assumed

**Alternatives considered**:
- Query OpenRouter models API separately: Adds latency, may not reflect version actually used
- Assume model version stable: Violates empirical integrity (models update without warning)

**Implementation**:
```python
def extract_model_version(response: OpenRouterResponse) -> str:
    """Extract actual model version from OpenRouter response metadata."""
    # OpenRouter includes versioned model ID in response
    return response.model  # e.g., "anthropic/claude-3.5-sonnet:20241022"

def check_model_version_consistency(current_version: str, db: ArangoDB, experiment_id: str) -> None:
    """FR-032: Detect model version changes across strides."""
    previous = db.query(
        "FOR p IN prompts FILTER p.experiment_id == @exp_id LIMIT 1 RETURN p.model_version_at_stride",
        bind_vars={"exp_id": experiment_id}
    )
    if previous and previous[0] != current_version:
        raise ModelVersionChangedError(f"Model changed: {previous[0]} → {current_version}. Decision required: ABORT/CONTINUE/IGNORE")
```

---

## 4. Pipeline Composability Architecture

**Decision**: Source/Sink/Stage protocol (duck typing) with push-based streaming

**Rationale**:
- Python protocols (PEP 544) for duck typing (no ABC inheritance required)
- Push-based: Stages call `sink.write(item)` - simpler than pull-based generators
- Composable: `source → stage1 → stage2 → sink` via method chaining
- FR-033 requirement: "Composable stages with source/sink interfaces"
- Follows Python conventions: Simple, explicit, type-hinted

**Alternatives considered**:
- Pull-based generators (yield): Harder to manage state, error handling complex
- ABC inheritance: Overkill for research scripts, adds boilerplate

**Implementation**:
```python
from typing import Protocol, Iterable

class Source(Protocol):
    def read(self) -> Iterable[dict]:
        """Yield items from source (e.g., prompts from dataset)."""
        ...

class Sink(Protocol):
    def write(self, item: dict) -> None:
        """Write item to sink (e.g., ArangoDB collection)."""
        ...

class Stage(Protocol):
    def process(self, item: dict) -> dict:
        """Transform item (e.g., add evaluation results)."""
        ...

# Usage:
def run_pipeline(source: Source, stages: list[Stage], sink: Sink) -> None:
    for item in source.read():
        for stage in stages:
            item = stage.process(item)
        sink.write(item)
```

**Best practices reference**: Python Patterns - Pipeline Pattern (https://python-patterns.guide/)

---

## 5. Wilson Score Interval Calculation

**Decision**: Manual implementation (no scipy dependency)

**Rationale**:
- Wilson score formula is ~5 lines of math (already specified in FR-020)
- scipy.stats adds heavy dependency for single calculation
- Project already uses minimal dependencies (Constitution: simplicity preferred)
- Formula handles edge cases (p=0, p=1) correctly per FR-020 specification
- Type-safe with Python 3.13 type hints

**Alternatives considered**:
- scipy.stats.proportion_confint: Adds 50MB+ dependency for 5-line calculation
- statsmodels: Even heavier dependency

**Implementation**:
```python
import math

def wilson_score_interval(p: float, n: int, z: float = 1.96) -> tuple[float, float]:
    """
    Calculate Wilson score confidence interval.

    Args:
        p: Proportion (e.g., FN_rate)
        n: Sample size (e.g., pattern_count)
        z: Z-score for confidence level (1.96 = 95% CI)

    Returns:
        (lower, upper) bounds

    Formula from FR-020 (handles p=0 and p=1 edge cases):
        lower = (p + z²/2n - z*sqrt(p(1-p)/n + z²/4n²)) / (1 + z²/n)
        upper = (p + z²/2n + z*sqrt(p(1-p)/n + z²/4n²)) / (1 + z²/n)
    """
    z_sq = z * z
    denominator = 1 + z_sq / n
    center = p + z_sq / (2 * n)
    margin = z * math.sqrt(p * (1 - p) / n + z_sq / (4 * n * n))

    lower = (center - margin) / denominator
    upper = (center + margin) / denominator
    return (lower, upper)

def ci_width(p: float, n: int, z: float = 1.96) -> float:
    """Calculate confidence interval width (FR-020 stopping condition)."""
    lower, upper = wilson_score_interval(p, n, z)
    return upper - lower
```

---

## 6. Three-Condition Experiment Execution

**Decision**: Sequential execution (Condition 1 → 2 → 3)

**Rationale**:
- Experiment 4 runs on n=50-100 subset (not full 680)
- Sequential runtime: 3 × (50-100 prompts × 5-10s) = 12.5-50 minutes total
- Parallel would save ~8-33 minutes but risks:
  - Rate limiting (3× simultaneous API calls)
  - Harder error recovery (which condition failed?)
  - No runtime cost savings (same total API calls)
- Constitution principle: Simplicity over premature optimization
- Can parallelize later if n=680 expansion needed (would save 2-3 hours)

**Alternatives considered**:
- Parallel execution: Saves time but adds complexity, rate limit risk
- Batch processing: Same total time as sequential

**Implementation**:
```python
def run_three_condition_experiment(prompts: list[Prompt], n: int = 50) -> ThreeConditionResults:
    """FR-021: Sequential three-condition validation."""
    sample = random.sample(prompts, n)

    # Condition 1: Old baseline (pre-template-marker)
    results_c1 = [evaluate_with_prompt(p, old_baseline_prompt) for p in sample]

    # Condition 2: New baseline (post-template-marker, no REASONINGBANK)
    results_c2 = [evaluate_with_prompt(p, new_baseline_prompt) for p in sample]

    # Condition 3: Enhanced (post-template-marker + REASONINGBANK)
    results_c3 = [evaluate_with_prompt(p, enhanced_prompt) for p in sample]

    return calculate_deltas(results_c1, results_c2, results_c3)
```

---

## 7. Fixture File Validation

**Decision**: Validate checksum once on initialization, cache result

**Rationale**:
- FR-356-362: SHA-256 checksum verification prevents corruption
- Validation cost: <1ms for 101-line text file (SHA-256 is fast)
- Run once at experiment startup, store validation flag in experiment metadata
- If validation fails, raise ConfigurationError immediately (fail-fast)
- Integrity guarantee without runtime overhead on every evaluation

**Alternatives considered**:
- Validate every run: Unnecessary overhead (fixture doesn't change during experiment)
- No validation: Violates specification requirement (FR-356-362)

**Implementation**:
```python
import hashlib

EXPECTED_CHECKSUM = "c104718e48489255cc6ee06028c363dd69b740f7662ca6b31b8704442ddb5d37"

def validate_old_baseline_prompt() -> str:
    """FR-356-362: Validate fixture file integrity."""
    fixture_path = "specs/002-specify-scripts-bash/fixtures/old_baseline_prompt.txt"

    try:
        with open(fixture_path, "rb") as f:
            content = f.read()
    except FileNotFoundError:
        raise ConfigurationError(
            f"Fixture file missing: {fixture_path}. Cannot run Experiment 4 without old prompt version."
        )

    actual_checksum = hashlib.sha256(content).hexdigest()
    if actual_checksum != EXPECTED_CHECKSUM:
        raise ConfigurationError(
            f"Fixture corrupted: expected {EXPECTED_CHECKSUM}, got {actual_checksum}. "
            f"Restore from git commit 8a7fcd3."
        )

    return content.decode("utf-8")
```

---

## Summary

All 7 unknowns resolved. Key decisions:

1. **Checkpoint/resume**: ArangoDB-based (query completed prompts)
2. **Prompt loading**: Load all 680 into memory (500KB negligible)
3. **Model version**: Parse from OpenRouter response metadata
4. **Pipeline**: Source/Sink/Stage protocols with push-based streaming
5. **Wilson score**: Manual implementation (no scipy dependency)
6. **Three-condition**: Sequential execution (12.5-50 min total)
7. **Fixture validation**: Once on initialization (fail-fast if corrupted)

**Constitution compliance**:
- Fail-fast throughout (no silent degradation)
- Empirical integrity (model version from actual responses)
- Simplicity preferred (manual Wilson score, sequential execution)
- Single source of truth (ArangoDB for checkpointing)

Ready for Phase 1: Data Model & Contracts generation.
