# Fire Circle Set Quorum Implementation Guide

**Version:** 1.0
**Date:** 2025-10-13
**Status:** Design Document
**Source:** Synthesized from `/home/tony/projects/promptguard/docs/SET_QUORUM_CONSENSUS.md`

## Purpose

This document extracts essential distributed systems principles from multi-model consensus discussions and provides actionable guidance for implementing set quorum validation in Fire Circle.

## Core Principle

**Traditional quorum:** "Do we have N participants agreeing?"
**Set quorum:** "Have we activated the necessary cognitive lenses?"

Quorum is satisfied when required **cognitive diversity** is represented, not when enough models vote.

---

## Essential Set Quorum Principles

1. **Coverage over Count:** A 2-model circle with diverse characteristics beats a 10-model circle of near-clones.

2. **Characteristic-Based Validity:** Consensus is invalid if missing essential perspectives (e.g., temporal reasoning, cross-layer analysis).

3. **Hierarchical Roles:** Some characteristics are more critical than others. Weight by importance for attack detection.

4. **Explicit Enforcement:** Diversity is a structural requirement at inference time, not a training-time hope.

5. **Failure Semantics:** Losing a model isn't losing a vote—it's potentially blinding a cognitive lens. Track qualitative degradation.

6. **Epistemic Sufficiency:** Agreement spans the manifold of interpretive roles, not just numerical majority.

7. **Infrastructure Resilience:** System degrades gracefully when characteristic groups go offline (e.g., regional outages).

8. **Anti-Monoculture:** Prevents any single ecosystem (corporate, national, alignment-style) from defining truth through availability bias.

---

## Dimensional Structure for Fire Circle

### Proposed Dimensions

Fire Circle requires coverage across these cognitive dimensions:

```python
CognitiveRoles = {
    # Pattern Detection (high priority)
    "temporal_reasoning": 3,        # Weight: critical for history injection
    "cross_layer_analysis": 3,      # Weight: critical for multi-layer attacks
    "pattern_recognition": 2,        # Weight: important for novel patterns

    # Contextual Analysis (medium priority)
    "polite_extraction_masking": 2, # Weight: important for subtle attacks
    "educational_escalation": 1,    # Weight: useful for gradual extraction

    # Structural Perspective (required)
    "future_impact": 2,             # Weight: empty chair perspective
    "system_maintenance": 1         # Weight: technical debt awareness
}

# Geographic/Architectural Diversity (required)
ProviderLineage = {
    "us_aligned": ["anthropic", "openai"],
    "cn_aligned": ["qwen", "deepseek", "kimi"],
    "open_source": ["llama", "mistral"]
}

# Safety Alignment (optional but valuable)
AlignmentStyle = {
    "safety_conservative": ["claude"],
    "reasoning_focused": ["deepseek-r1"],
    "efficiency_focused": ["qwen"]
}
```

### Minimum Coverage Requirements

**Core requirement:** At least one model from each high-priority cognitive role (weight ≥ 3).
**Resilience requirement:** At least 2 of 3 provider lineage groups represented.
**Minimum viable circle:** 2 active models covering ≥5 weighted points.

**Example valid quorum (3 models):**
- Claude: temporal_reasoning (3), cross_layer_analysis (3), us_aligned, safety_conservative
- Qwen: pattern_recognition (2), efficiency_focused, cn_aligned
- DeepSeek-R1: temporal_reasoning (3), reasoning_focused, cn_aligned

Coverage: 8 weighted points (temporal=3, cross_layer=3, pattern=2), 2 provider groups, diverse alignment styles.

---

## Quorum Validation Algorithm

```python
@dataclass
class ModelCharacteristics:
    """Metadata defining model's cognitive and structural traits."""
    model_id: str
    cognitive_roles: Dict[str, float]  # role -> contribution (0.0-1.0)
    provider_lineage: str
    alignment_style: str

    @property
    def weighted_coverage(self) -> float:
        """Sum of cognitive role contributions weighted by importance."""
        role_weights = {
            "temporal_reasoning": 3,
            "cross_layer_analysis": 3,
            "pattern_recognition": 2,
            "polite_extraction_masking": 2,
            "educational_escalation": 1,
            "future_impact": 2,
            "system_maintenance": 1
        }
        return sum(
            role_weights.get(role, 0) * contrib
            for role, contrib in self.cognitive_roles.items()
        )


def validate_quorum(
    active_models: List[ModelCharacteristics],
    min_cognitive_coverage: float = 5.0,
    min_provider_groups: int = 2
) -> Tuple[bool, str]:
    """
    Validate set quorum for Fire Circle consensus.

    Returns: (is_valid, reason)
    """
    if len(active_models) < 2:
        return False, "Minimum 2 active models required"

    # Check cognitive role coverage
    total_weighted_coverage = sum(m.weighted_coverage for m in active_models)

    # Track unique roles with any coverage
    covered_roles = set()
    for model in active_models:
        covered_roles.update(model.cognitive_roles.keys())

    if total_weighted_coverage < min_cognitive_coverage:
        return False, f"Insufficient cognitive coverage: {total_weighted_coverage:.1f} < {min_cognitive_coverage}"

    # Check provider diversity
    provider_groups = set(m.provider_lineage for m in active_models)
    if len(provider_groups) < min_provider_groups:
        return False, f"Insufficient provider diversity: {len(provider_groups)} < {min_provider_groups}"

    # Verify critical roles present (weight >= 3)
    critical_roles = {"temporal_reasoning", "cross_layer_analysis"}
    missing_critical = critical_roles - covered_roles
    if missing_critical:
        return False, f"Missing critical cognitive roles: {missing_critical}"

    return True, "Valid set quorum"


def quorum_with_failures(
    starting_models: List[ModelCharacteristics],
    failed_models: List[str]
) -> Tuple[bool, List[str]]:
    """
    Check if remaining models after failures still form valid quorum.

    Returns: (quorum_still_valid, missing_dimensions)
    """
    active = [m for m in starting_models if m.model_id not in failed_models]

    is_valid, reason = validate_quorum(active)

    if not is_valid:
        # Identify what we lost
        failed_chars = [m for m in starting_models if m.model_id in failed_models]
        lost_roles = set()
        for fc in failed_chars:
            lost_roles.update(fc.cognitive_roles.keys())

        # What critical dimensions are now missing?
        remaining_roles = set()
        for m in active:
            remaining_roles.update(m.cognitive_roles.keys())

        missing = lost_roles - remaining_roles
        return False, list(missing)

    return True, []
```

---

## Fire Circle Integration

### Configuration Schema Extension

```python
@dataclass
class FireCircleConfig:
    # ... existing fields ...

    # Set quorum configuration
    model_characteristics: Dict[str, ModelCharacteristics] = field(default_factory=dict)
    min_cognitive_coverage: float = 5.0  # Weighted coverage threshold
    min_provider_groups: int = 2         # Geographic/architectural diversity
    require_empty_chair_role: bool = True  # Future impact dimension required

    def __post_init__(self):
        """Validate set quorum requirements."""
        # ... existing validation ...

        # Validate initial quorum
        initial_chars = [self.model_characteristics[m] for m in self.models]
        is_valid, reason = validate_quorum(
            initial_chars,
            self.min_cognitive_coverage,
            self.min_provider_groups
        )

        if not is_valid:
            raise ValueError(f"Initial model set lacks valid quorum: {reason}")
```

### Consensus Algorithm Modification

```python
def aggregate_consensus(
    evaluations: List[NeutrosophicEvaluation],
    active_models: List[str],
    model_chars: Dict[str, ModelCharacteristics],
    config: FireCircleConfig
) -> float:
    """
    Compute consensus requiring valid set quorum.

    CHANGE: Before computing max(F), verify remaining models form valid quorum.
    """
    # Get characteristics of active models
    active_chars = [model_chars[m] for m in active_models]

    # Validate quorum
    is_valid, reason = validate_quorum(
        active_chars,
        config.min_cognitive_coverage,
        config.min_provider_groups
    )

    if not is_valid:
        raise EvaluationError(
            f"Cannot reach consensus: {reason}. "
            f"Active models: {active_models}"
        )

    # Standard max(F) aggregation, but only with valid quorum
    valid_evals = [e for e in evaluations if e.model in active_models]
    return max(e.falsehood for e in valid_evals)
```

### Pattern Extraction with Set Quorum

```python
def extract_patterns_with_quorum(
    dialogue_history: List[DialogueRound],
    active_models: List[str],
    model_chars: Dict[str, ModelCharacteristics],
    pattern_threshold: float = 0.5
) -> List[PatternObservation]:
    """
    Extract patterns requiring diverse model agreement.

    CHANGE: Patterns must be observed by models covering diverse cognitive roles.
    """
    pattern_map = {}  # pattern_type -> PatternObservation

    for round in dialogue_history[1:]:
        for eval in round.evaluations:
            if eval.model not in active_models:
                continue

            patterns = getattr(eval, 'patterns_observed', []) or \
                      getattr(eval, 'consensus_patterns', [])

            for pattern_str in patterns:
                pattern_type = classify_pattern(pattern_str)

                if pattern_type not in pattern_map:
                    pattern_map[pattern_type] = PatternObservation(
                        pattern_type=pattern_type,
                        description=pattern_str,
                        model_agreement=0.0,
                        examples=[],
                        observed_in_round=round.round_number,
                        models_observing=[],
                        cognitive_roles_observing=[]  # NEW FIELD
                    )

                obs = pattern_map[pattern_type]
                obs.models_observing.append(eval.model)
                obs.cognitive_roles_observing.extend(
                    model_chars[eval.model].cognitive_roles.keys()
                )

    # Filter patterns by BOTH numerical agreement AND role diversity
    patterns = []
    for obs in pattern_map.values():
        # Numerical threshold (unchanged)
        obs.model_agreement = len(set(obs.models_observing)) / len(active_models)

        # NEW: Role diversity check
        unique_roles = set(obs.cognitive_roles_observing)
        has_critical_role = any(
            role in unique_roles
            for role in ["temporal_reasoning", "cross_layer_analysis"]
        )

        if obs.model_agreement >= pattern_threshold and has_critical_role:
            patterns.append(obs)

    return sorted(patterns, key=lambda p: p.model_agreement, reverse=True)
```

### Failure Handling with Quorum Check

```python
def handle_model_failure_with_quorum(
    failed_model: str,
    round_number: int,
    active_models: List[str],
    model_chars: Dict[str, ModelCharacteristics],
    config: FireCircleConfig
) -> FailureAction:
    """
    Determine if Fire Circle can continue after model failure.

    CHANGE: Check if remaining models form valid quorum, not just count.
    """
    remaining_models = [m for m in active_models if m != failed_model]

    # Validate quorum with remaining models
    remaining_chars = [model_chars[m] for m in remaining_models]
    quorum_valid, missing_dims = quorum_with_failures(
        [model_chars[m] for m in active_models],
        [failed_model]
    )

    if not quorum_valid:
        # Log which cognitive dimensions we lost
        lost_char = model_chars[failed_model]
        return FailureAction.ABORT(
            f"Loss of {failed_model} breaks quorum in round {round_number}. "
            f"Missing dimensions: {missing_dims}. "
            f"Lost roles: {list(lost_char.cognitive_roles.keys())}"
        )

    # Continue with degraded but valid circle
    return FailureAction.CONTINUE(
        remaining_models=remaining_models,
        degradation_note=f"Operating with {len(remaining_models)} models after {failed_model} failure"
    )
```

---

## Critical Implementation Constraints

### 1. Avoid Circular Dependencies

**Problem:** If quorum validation requires model outputs (e.g., measuring actual reasoning contributions), but outputs require valid quorum to accept, you have a circular dependency.

**Solution:** Use **declared characteristics** from configuration/metadata, not runtime-measured contributions. Cognitive role assignments are static properties of model architecture/training, not dynamic measurements.

### 2. Bootstrapping Problem

**Problem:** How do you know a model's cognitive role contributions without empirical testing?

**Solution:**
- **Initial assignment:** Manual curation based on model documentation, architecture papers, benchmark results.
- **Refinement:** After N evaluations, update contribution scores based on observed performance.
- **Validation:** Include `cognitive_role_confidence` score to track how well-established these mappings are.

### 3. Empty Chair Integration

**Problem:** Empty chair role is rotated, but it represents "future impact" dimension. If the model taking empty chair doesn't naturally possess that cognitive role, is the quorum still valid?

**Solution:** Empty chair is a **prompt-induced role**, not a model characteristic. Any model can speak for future/absent when prompted. Track empty chair as separate dimension in quorum validation:

```python
def validate_quorum_with_empty_chair(
    active_models: List[ModelCharacteristics],
    empty_chair_model: str,
    round_number: int
) -> bool:
    """Empty chair role adds 'future_impact' dimension temporarily."""
    # Standard quorum check
    base_valid, _ = validate_quorum(active_models)

    # Empty chair contributes future_impact regardless of model's natural roles
    if round_number >= 2:  # Empty chair active in Round 2+
        # Count future_impact as covered
        future_impact_covered = True

    return base_valid and future_impact_covered
```

### 4. Weighted vs. Binary Coverage

**Decision point:** Should cognitive role coverage be weighted (fuzzy membership) or binary (has role or doesn't)?

**Recommendation:** Use **weighted coverage** for flexibility, but require **binary presence** of critical roles.

```python
# Weighted: Claude contributes 0.8 to temporal_reasoning
# Binary: At least ONE model must have temporal_reasoning > 0.5
```

This allows partial contributions while ensuring no critical blind spots.

### 5. Dynamic Quorum Adjustment

**Problem:** After multiple failures, should quorum requirements be relaxed to maintain liveness?

**Answer:** **No.** Maintaining epistemic validity is more important than producing a result. If failures break quorum, the system should abort with clear explanation of missing dimensions, not degrade to potentially invalid consensus.

**Rationale:** Fire Circle is a research/analysis tool, not real-time production. Invalid consensus is worse than no consensus.

### 6. Quorum Hysteresis

**Problem:** Model A fails in Round 2 (breaks quorum), but recovers in Round 3. Should it rejoin?

**Solution:** Use **quorum hysteresis** - once a model fails and breaks quorum, Fire Circle aborts even if model later recovers. Don't allow partial-recovery scenarios that complicate state management.

**Implementation:** Track `failed_permanently` list separate from `failed_models`. Once you fail and trigger quorum violation, you're out for entire evaluation.

---

## TLA+ Specification Reference

For formal verification of set quorum properties, see the refined TLA+ specification in `/home/tony/projects/promptguard/docs/SET_QUORUM_CONSENSUS.md` (lines 1346-1488).

**Key invariants to verify:**

```tla
\* Safety: Consensus requires valid quorum
Safety ==
    finalConsensus > 0.5 =>
        \E quorum \subseteq activeModels :
            ValidQualitativeQuorum(quorum) /\
            (\A m \in quorum : assessments[m][MaxRounds].false >= finalConsensus)

\* Liveness: Eventually reach consensus if sufficient cognitive coverage remains
Liveness == <> (finalConsensus # -1 \/ WeightedCoverage(activeModels) < MinCoverage)
```

---

## Testing Strategy

### Unit Tests

```python
def test_quorum_validation():
    """Test quorum validation with various model configurations."""

    # Valid quorum
    models = [
        ModelCharacteristics("claude", {"temporal_reasoning": 0.9}, "us_aligned", "safety"),
        ModelCharacteristics("qwen", {"pattern_recognition": 0.8}, "cn_aligned", "efficiency"),
        ModelCharacteristics("deepseek", {"cross_layer_analysis": 0.9}, "cn_aligned", "reasoning")
    ]
    assert validate_quorum(models)[0] == True

    # Invalid: missing critical role
    models_missing_critical = [
        ModelCharacteristics("qwen", {"pattern_recognition": 0.8}, "cn_aligned", "efficiency"),
        ModelCharacteristics("llama", {"educational_escalation": 0.7}, "open_source", "reasoning")
    ]
    valid, reason = validate_quorum(models_missing_critical)
    assert not valid
    assert "temporal_reasoning" in reason or "cross_layer_analysis" in reason

    # Invalid: single provider lineage
    models_single_provider = [
        ModelCharacteristics("claude-1", {"temporal_reasoning": 0.9}, "us_aligned", "safety"),
        ModelCharacteristics("claude-2", {"cross_layer_analysis": 0.8}, "us_aligned", "safety")
    ]
    valid, reason = validate_quorum(models_single_provider, min_provider_groups=2)
    assert not valid
    assert "provider diversity" in reason
```

### Integration Tests

```python
async def test_fire_circle_quorum_enforcement():
    """Test that Fire Circle enforces quorum during failures."""

    config = FireCircleConfig(
        models=["claude", "qwen", "deepseek"],
        model_characteristics={
            "claude": ModelCharacteristics("claude", {...}, "us_aligned", "safety"),
            "qwen": ModelCharacteristics("qwen", {...}, "cn_aligned", "efficiency"),
            "deepseek": ModelCharacteristics("deepseek", {...}, "cn_aligned", "reasoning")
        },
        min_cognitive_coverage=5.0,
        min_provider_groups=2
    )

    # Simulate qwen failure (cn_aligned provider still covered by deepseek)
    # Should continue

    # Simulate BOTH qwen and deepseek failure (cn_aligned provider lost)
    # Should abort with "insufficient provider diversity"
```

### Research Validation

```python
async def test_set_quorum_vs_numeric_quorum():
    """
    Compare detection rates: numeric quorum vs set quorum.

    Hypothesis: Set quorum catches attacks that numeric quorum misses
    when homogeneous models agree incorrectly.
    """
    attacks = load_encoding_attacks(n=50)

    # Numeric quorum: 3 Claude models (homogeneous)
    numeric_results = await run_fire_circle(
        attacks,
        models=["claude-1", "claude-2", "claude-3"]
    )

    # Set quorum: 3 diverse models
    set_quorum_results = await run_fire_circle(
        attacks,
        models=["claude", "qwen", "deepseek"],
        enforce_quorum=True
    )

    # Expect: set quorum detects more attacks (especially encoding)
    assert set_quorum_results.detection_rate > numeric_results.detection_rate
```

---

## Open Questions for Maintainer

1. **Cognitive role assignment:** Should initial assignments be manual curation, or run empirical benchmark to measure contributions?

2. **Minimum viable circle:** Currently 2 models. Should set quorum raise this to 3 to ensure true diversity?

3. **Empty chair requirement:** Should `future_impact` dimension be absolutely required, or can Fire Circle operate without it?

4. **Dynamic characteristic updates:** After N evaluations, should model characteristics be updated based on observed performance? If so, what's the update mechanism?

5. **Quorum threshold tunability:** Should `min_cognitive_coverage` be configurable per-evaluation, or fixed at system level?

6. **Recovery from quorum violation:** Currently abort. Should there be a "recruit substitute model" path to restore quorum?

---

## Summary

**Set quorum transforms Fire Circle from voting ensemble to distributed cognition system.**

**Key principle:** Consensus requires cognitive diversity, not numerical majority.

**Implementation priority:**
1. Add `ModelCharacteristics` dataclass to configuration
2. Implement `validate_quorum()` with weighted coverage and provider diversity checks
3. Modify consensus algorithm to enforce quorum before accepting result
4. Update failure handling to check quorum after each failure
5. Extend pattern extraction to require role diversity in agreement
6. Add quorum validation tests

**Expected impact:**
- Prevents echo chamber consensus from homogeneous models
- Makes explicit which cognitive dimensions are covered/missing
- Provides graceful degradation semantics (explains WHY failure occurred)
- Enables infrastructure-aware resilience (geographic/provider outages)
- Supports research on optimal model combinations for attack detection

**Next steps:**
1. Curate initial cognitive role assignments for available models
2. Implement quorum validation in `FireCircleConfig.__post_init__()`
3. Write unit tests for quorum validation logic
4. Run A/B test: set quorum vs numeric quorum on encoding attacks
5. Document results and refine thresholds based on empirical data

---

**Document Status:** Ready for implementation review and maintainer feedback.
