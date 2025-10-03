# Ensemble Evaluation Design Specification

## Overview

Extend PromptGuard to support evaluating prompts with multiple evaluation strategies in parallel, combining results to detect both structural and semantic violations.

## Problem Statement

Instance 6 validation revealed that single-prompt evaluation creates an optimization trade-off:
- `ayni_relational` prompt: 93.5% manipulative accuracy, 63.4% extractive recall
- `relational_structure` prompt: 54.2% manipulative accuracy, 100% extractive recall (test set)

**Root cause:** Prompt injection attacks have orthogonal dimensions:
- **Structural violations:** Role reversal, authority claims (detected by structural analysis)
- **Semantic violations:** Encoding tricks, jailbreaks (detected by semantic analysis)

Single-prompt evaluation optimizes for one dimension at the expense of the other.

## Goals

1. **Maintain high accuracy across all attack classes:**
   - Target: >90% manipulative accuracy (jailbreaks)
   - Target: >90% extractive recall (polite extraction)
   - Target: <10% reciprocal false positives

2. **Support flexible prompt combinations:**
   - Enable users to choose single or ensemble evaluation
   - Allow arbitrary combinations of evaluation prompts
   - Make ensemble the recommended default

3. **Preserve backward compatibility:**
   - Existing single-string `evaluation_type` continues to work
   - No breaking changes to public API

4. **Enable research iteration:**
   - Easy to test new prompt combinations
   - Clear attribution of which prompts detected which violations
   - Support for future multi-dimensional analysis

## Non-Goals

1. **Not attempting prompt fusion:** Combining prompts into single template risks diluting both signals
2. **Not optimizing for cost:** Ensemble means 2x API calls - this is acceptable for security use case
3. **Not auto-selecting prompts:** User explicitly chooses ensemble, we don't guess based on content
4. **Not parallel model evaluation:** That's PARALLEL mode (existing). This is parallel *prompt* evaluation.

## Constraints

1. **API compatibility:** Must work with existing OpenRouter integration
2. **Caching compatibility:** Each (prompt_type, content) pair should cache independently
3. **Trust calculator unchanged:** Works on final merged neutrosophic values
4. **Classification logic unchanged:** Operates on merged ayni_balance from ensemble results

## Architecture

### Configuration Extension

```python
@dataclass
class PromptGuardConfig:
    # Existing fields...

    # CHANGED: Now accepts string or list
    evaluation_type: Union[str, List[str]] = "ayni_relational"

    # NEW: Ensemble aggregation strategy
    ensemble_strategy: str = "max_falsehood"  # or "average", "voting"
```

**Backward compatibility:** Single string continues to work as before.

**Ensemble mode:** Pass list of evaluation types:
```python
config = PromptGuardConfig(
    models=["x-ai/grok-4-fast:free"],
    evaluation_type=["ayni_relational", "relational_structure"]
)
```

### Evaluation Flow

**Single-prompt mode (existing):**
```
Layer → LLM eval → Neutrosophic (T,I,F) → Trust calc → Ayni balance → Classification
```

**Ensemble mode (new):**
```
Layer → LLM eval (prompt 1) → Neutrosophic_1 (T,I,F)
     ├→ LLM eval (prompt 2) → Neutrosophic_2 (T,I,F)
     └→ ...                 → Neutrosophic_N (T,I,F)
                                     ↓
                            Merge(Neutrosophic_1...N)
                                     ↓
                            Trust calc → Ayni balance → Classification
```

### Neutrosophic Merging Strategy

**Default: MAX falsehood (security-first)**

For each layer, compute merged neutrosophic values:
```python
T_merged = min(T_1, T_2, ..., T_N)  # Worst-case truth
I_merged = max(I_1, I_2, ..., I_N)  # Highest uncertainty
F_merged = max(F_1, F_2, ..., F_N)  # Worst-case falsehood (most conservative)
```

**Rationale:**
- Security context: False negative (missed attack) worse than false positive
- If ANY prompt detects high falsehood, flag as violation
- Structural analysis catches role violations, semantic catches jailbreaks
- Normal requests score low F on both, so no false positives

**Alternative strategies (future):**
- `average`: Average all T/I/F values (less conservative)
- `voting`: Require N/2 prompts to agree on violation
- `weighted`: Weight prompts by empirical accuracy on each attack class

### Implementation Changes

#### 1. PromptGuard.__init__

```python
def __init__(self, config: PromptGuardConfig):
    # ...existing setup...

    # Normalize evaluation_type to list
    if isinstance(self.config.evaluation_type, str):
        self.evaluation_types = [self.config.evaluation_type]
    else:
        self.evaluation_types = self.config.evaluation_type

    # Get all evaluation prompts
    self.evaluation_prompts = [
        NeutrosophicEvaluationPrompt.get_prompt(eval_type)
        for eval_type in self.evaluation_types
    ]
```

#### 2. PromptGuard.evaluate

**Single-prompt path (unchanged):**
```python
if len(self.evaluation_types) == 1:
    # Existing logic
    for layer in mnp.layers:
        result = await self.llm_evaluator.evaluate_layer(
            layer.content, context, self.evaluation_prompts[0]
        )
        layer.set_neutrosophic(*result.neutrosophic_tuple())
```

**Ensemble path (new):**
```python
else:
    # Evaluate with all prompts
    for layer in mnp.layers:
        results = await asyncio.gather(*[
            self.llm_evaluator.evaluate_layer(
                layer.content, context, prompt
            )
            for prompt in self.evaluation_prompts
        ])

        # Merge neutrosophic values
        merged = self._merge_neutrosophic(results)
        layer.set_neutrosophic(*merged)
```

#### 3. Neutrosophic Merging

```python
def _merge_neutrosophic(
    self,
    results: List[LayerEvaluation],
    strategy: str = "max_falsehood"
) -> Tuple[float, float, float]:
    """Merge multiple neutrosophic evaluations."""

    tuples = [r.neutrosophic_tuple() for r in results]

    if strategy == "max_falsehood":
        # Security-first: worst-case on all dimensions
        t = min(t for t, i, f in tuples)
        i = max(i for t, i, f in tuples)
        f = max(f for t, i, f in tuples)
        return (t, i, f)

    elif strategy == "average":
        # Average all dimensions
        t = sum(t for t, i, f in tuples) / len(tuples)
        i = sum(i for t, i, f in tuples) / len(tuples)
        f = sum(f for t, i, f in tuples) / len(tuples)
        return (t, i, f)

    elif strategy == "voting":
        # Require majority agreement on high falsehood
        high_f_count = sum(1 for t, i, f in tuples if f > 0.6)
        if high_f_count >= len(tuples) / 2:
            f = max(f for t, i, f in tuples)
        else:
            f = sum(f for t, i, f in tuples) / len(tuples)

        t = sum(t for t, i, f in tuples) / len(tuples)
        i = sum(i for t, i, f in tuples) / len(tuples)
        return (t, i, f)

    else:
        raise ValueError(f"Unknown ensemble strategy: {strategy}")
```

#### 4. ReciprocityMetrics Extension (Optional)

Add metadata about which prompts contributed to detection:

```python
@dataclass
class ReciprocityMetrics:
    # ...existing fields...

    # NEW: Ensemble metadata (only populated in ensemble mode)
    ensemble_results: Optional[Dict[str, Tuple[float, float, float]]] = None
    # Maps evaluation_type -> (T, I, F) for each prompt
```

**Use case:** Researchers can analyze which prompt detected which violation class.

## Validation Plan

### Phase 1: Unit Tests

1. Test single-string evaluation_type (backward compatibility)
2. Test list evaluation_type with single item (equivalent to single-string)
3. Test ensemble with two prompts (ayni_relational + relational_structure)
4. Test neutrosophic merging strategies (max_falsehood, average, voting)
5. Verify caching works per (prompt_type, content) tuple

### Phase 2: Integration Tests

1. Polite extraction case:
   - ayni_relational alone: Should miss (Instance 5 behavior)
   - relational_structure alone: Should detect
   - Ensemble: Should detect (structural prompt catches it)

2. Jailbreak case:
   - ayni_relational alone: Should detect (Instance 5 behavior)
   - relational_structure alone: Should miss (Instance 6 behavior)
   - Ensemble: Should detect (semantic prompt catches it)

3. Normal request case:
   - ayni_relational alone: May false positive (Instance 5 threshold penalty)
   - relational_structure alone: Should allow
   - Ensemble: Should allow (neither detects violation)

### Phase 3: Full Validation

Run on 680-prompt dataset with ensemble mode:

```python
config = PromptGuardConfig(
    models=["x-ai/grok-4-fast:free"],
    evaluation_type=["ayni_relational", "relational_structure"],
    ensemble_strategy="max_falsehood"
)
```

**Success criteria:**
- Manipulative accuracy: >90% (maintain Instance 5 level)
- Extractive recall: >90% (improve on Instance 5)
- Reciprocal false positives: <10% (improve on Instance 5)

**Expected cost:** 2x Instance 5 validation (~$6.80 for 680 prompts)

### Phase 4: Comparative Analysis

Generate report comparing:
- Instance 5 (ayni_relational alone)
- Instance 6 structural test (relational_structure alone)
- Instance 6 ensemble (both prompts)

Document which attack classes are detected by which prompt.

## Cost Analysis

**Ensemble evaluation doubles API calls:**
- Single prompt: 1 call per layer
- Ensemble (2 prompts): 2 calls per layer
- Ensemble (N prompts): N calls per layer

**For 680-prompt validation:**
- Instance 5 cost: ~$3.40 (Grok 4 Fast free tier)
- Ensemble cost: ~$6.80 (2x calls, still free tier if no throttling)
- Production: Cost scales linearly with number of prompts in ensemble

**Mitigation:**
- Caching reduces cost for repeated evaluations
- Free tier absorbs ensemble cost for development/testing
- Production users can choose single vs ensemble based on security needs

## Migration Path

**Phase 1: Add ensemble support (backward compatible)**
- Change evaluation_type type signature
- Add ensemble evaluation path
- Keep single-prompt path unchanged
- Default remains "ayni_relational"

**Phase 2: Validate ensemble performance**
- Run full validation
- Confirm >90% accuracy on all metrics
- Document which prompts detect which attack classes

**Phase 3: Update defaults (if validated)**
- Change default to `["ayni_relational", "relational_structure"]`
- Update examples and documentation
- Provide single-prompt mode for cost-sensitive users

**Phase 4: Prompt versioning (future)**
- Track prompt versions in manifest
- Enable A/B testing of new prompts
- Build regression test suite for prompt changes

## Open Questions

1. **Should we expose per-prompt neutrosophic values in ReciprocityMetrics?**
   - Pro: Enables research into which prompt detected what
   - Con: Adds complexity to API, may not be needed for production use
   - Decision: Add as optional field, populate only if user requests verbose output

2. **What ensemble strategy should be default?**
   - max_falsehood: Most conservative (lowest false negatives)
   - average: Balanced (may miss subtle violations)
   - voting: Requires N/2 agreement (middle ground)
   - Recommendation: Start with max_falsehood, make configurable for research

3. **Should ensemble mode fail if ANY prompt fails?**
   - Current behavior: Evaluation raises exception if LLM call fails
   - Ensemble option: Continue with partial results if some prompts succeed
   - Recommendation: Fail-fast (existing behavior), ensemble doesn't change this

4. **Do we need weighted ensemble?**
   - Could weight prompts by empirical accuracy on each attack class
   - Requires training/calibration phase
   - Recommendation: Defer to future work, start with equal weighting

## Success Metrics

**Functional:**
- Backward compatibility: All existing code works unchanged
- Ensemble evaluation: Correctly merges neutrosophic values from multiple prompts
- Test coverage: >90% for new ensemble logic

**Performance:**
- Manipulative accuracy: >90%
- Extractive recall: >90%
- Reciprocal precision: >90%
- Overall accuracy: >85%

**Research:**
- Clear attribution of which prompts detect which attack classes
- Documented trade-offs between single vs ensemble evaluation
- Validation data for future prompt design

## Timeline Estimate

1. Implementation: 2-4 hours
   - Config changes: 30 min
   - Evaluation flow changes: 1-2 hours
   - Neutrosophic merging: 30 min
   - Tests: 1 hour

2. Validation: 6-8 hours
   - Full dataset run: 6 hours (background)
   - Analysis and documentation: 2 hours

3. Review and iteration: 2-4 hours
   - Mac/Codex review of design
   - Address feedback
   - Refine implementation

**Total: 10-16 hours across multiple sessions**

## Risks and Mitigations

**Risk:** Ensemble doesn't improve overall metrics
- **Likelihood:** Low (early tests suggest both prompts needed)
- **Mitigation:** Full validation will confirm; if not, document why and recommend single-prompt

**Risk:** Cost doubles but improvement is marginal
- **Likelihood:** Medium (depends on attack distribution)
- **Mitigation:** Make ensemble opt-in, document cost/benefit trade-off

**Risk:** Merging strategy is too conservative (high false positives)
- **Likelihood:** Medium (max_falsehood is aggressive)
- **Mitigation:** Support multiple strategies, tune based on validation results

**Risk:** Implementation complexity introduces bugs
- **Likelihood:** Medium (touching core evaluation path)
- **Mitigation:** Comprehensive tests, maintain single-prompt path as fallback

## Review Checklist

Before implementing:
- [ ] Mac reviews threat model and merging strategy
- [ ] Codex reviews implementation approach and test plan
- [ ] Confirm backward compatibility requirements
- [ ] Validate cost assumptions
- [ ] Document expected validation metrics

After implementing:
- [ ] Unit tests pass
- [ ] Integration tests validate all three cases (polite extraction, jailbreak, normal)
- [ ] Full validation shows >90% accuracy on all metrics
- [ ] Documentation updated with ensemble examples
- [ ] FORWARD.md captures Instance 6 learnings

## References

- **Instance 5 findings:** docs/INSTANCE_5_FAILURE_ANALYSIS.md
- **Structural prompt test:** docs/STRUCTURAL_PROMPT_RESULTS.md
- **Multi-dimensional threat space:** docs/INSTANCE_6_FINDINGS.md
- **Neutrosophic logic:** promptguard/core/neutrosophic.py
- **Current evaluation flow:** promptguard/promptguard.py:106-180
