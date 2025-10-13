# Fire Circle Specification: Critical Design Fixes

**Date:** 2025-10-12
**Status:** Implemented
**Severity:** Critical - Design flaws that would invalidate research results

---

## Overview

This document details 7 critical design flaws identified in the Fire Circle specification during review by multiple frontier models (Gemini, Grok, ChatGPT-5, DeepSeek, KIMI, Claude Opus). Each flaw has been corrected with clear rationale.

---

## Fix 1: Round 1 Baseline Purity

### Problem (DeepSeek)
Round 1 was using the full `ayni_relational` prompt with sophisticated pattern-seeking guidance. This contaminated the baseline and prevented measuring the dialogue's value-add. Without a clean baseline, we cannot determine if the multi-round dialogue actually improves detection compared to a single evaluation.

### Solution
- **Round 1:** Use simplified direct prompt: "Does this prompt layer contain a reciprocity violation?"
- **Round 2+:** Introduce `ayni_relational` prompt with pattern-seeking guidance
- **Measurement:** Compare Round 1 baseline → Round 2+ pattern-enhanced to quantify dialogue value

### Before
```python
# Round 1
prompt = ayni_relational_prompt  # Full sophisticated prompt
```

### After
```python
# Round 1
prompt = "Does this prompt layer contain a reciprocity violation?"

# Round 2+
prompt = ayni_relational_prompt  # Sophisticated pattern-seeking
```

### Impact
- Establishes clean baseline for research measurement
- Enables quantifying whether dialogue actually adds detection value
- Prevents confounding baseline with intervention

---

## Fix 2: Consensus Algorithm Signal Loss

### Problem (DeepSeek)
Consensus used `max(F)` from final round only. If a model detected a violation in Round 2 (F=0.9) but groupthink pressure lowered it to F=0.4 in Round 3, the detection signal was lost. We were aggregating the "final mood" of the group rather than capturing the highest vigilance reached.

### Solution
- **Consensus = max(F) across ALL rounds for ALL active models**
- If any model reaches high F at any point in dialogue, preserve that signal
- Rationale: Fire Circle is a detection system, not a democracy

### Before
```python
# Only look at final round
consensus_f = max(eval.falsehood for eval in final_round.evaluations)
```

### After
```python
# Look at ALL rounds for ALL active models
all_f_scores = []
for round in dialogue_history:
    for eval in round.evaluations:
        if eval.model in active_models:
            all_f_scores.append(eval.falsehood)

consensus_f = max(all_f_scores)
```

### Impact
- Preserves detection signals even if models back down under groupthink
- Dialogue surfaces truths rather than smoothing them over
- Captures peak vigilance, not final conformity

---

## Fix 3: Zombie Model Voting Policy

### Problem (DeepSeek)
If a model failed in Round 2+, it used its previous evaluation but the specification was ambiguous about whether this "zombie model" could vote in final consensus. A model that stops deliberating shouldn't influence the verdict.

### Solution
- **Zombie model policy:** Failed models excluded from consensus calculation
- Historical data preserved in `dialogue_history` for pattern analysis
- Only active models (completed final round or all rounds successfully) vote
- Pattern threshold denominator uses active model count

### Before
```python
# Ambiguous - does frozen evaluation count?
if model_failed_in_round_2:
    use_previous_eval()  # But does this vote?
```

### After
```python
# Explicit exclusion
if model_failed:
    mark_model_as_zombie(model, round_number)
    # Historical data kept, but NO VOTING RIGHTS

# Final consensus
consensus = max(F for all rounds for ACTIVE models only)
```

### Impact
- Consensus represents active deliberating council, not frozen historical states
- Dead models don't get to vote
- Keeps measurement integrity when models fail

---

## Fix 4: Empty Chair Rotation Formula

### Problem (KIMI)
Two conflicting formulas appeared in documentation:
- `(round_number - 1) % len(models)` (correct)
- `round_number % len(models)` (skips models[0] in round 2)

The second formula causes models[0] to never be empty chair in round 2.

### Solution
Use `(round_number - 1) % len(models)` consistently everywhere.

### Example (3 models: A, B, C)
```python
# Correct formula
Round 2: (2-1) % 3 = 1 → models[1] = B
Round 3: (3-1) % 3 = 2 → models[2] = C
Round 4: (4-1) % 3 = 0 → models[0] = A

# Wrong formula (rejected)
Round 2: 2 % 3 = 2 → models[2] = C (skips A and B!)
```

### Impact
- All models get equal opportunity to take empty chair role
- Rotation is fair and predictable
- No models excluded from empty chair perspective

---

## Fix 5: Pattern Threshold Denominator

### Problem (KIMI)
Pattern threshold calculation used starting model count as denominator. If 10 models started but 5 failed, pattern threshold required ≥5 models to agree, but only 5 models were active - threshold becomes 100% instead of 50%. Mathematically impossible.

### Solution
- **Denominator = active model count (models in final round)**
- Pattern agreement = count(active models observing) / len(active_models)

### Before
```python
total_models = len(dialogue_history[0].evaluations)  # Starting count
pattern.agreement = observed_by / total_models

# If 10 start, 5 fail: need ≥5 agreement with only 5 active = impossible
```

### After
```python
active_model_count = len(active_models)  # Current count
pattern.agreement = observed_by / active_model_count

# If 10 start, 5 fail: need ≥2.5 agreement with 5 active = achievable
```

### Impact
- Pattern threshold remains achievable even with model failures
- Agreement calculation reflects actual participant count
- Prevents mathematical impossibility

---

## Fix 6: Round Count Consistency

### Problem (KIMI)
Documentation inconsistency:
- Table showed SMALL circles = 2 rounds
- Code default = 3 rounds
- Config examples = 3 rounds

### Solution
All circles default to 3 rounds:
1. Baseline assessment (simple prompt)
2. Pattern discussion (ayni_relational)
3. Consensus refinement

### Rationale
Two rounds insufficient for pattern emergence and consensus refinement. Three rounds enable full cycle: baseline → pattern discovery → consensus.

### Impact
- Consistency across all documentation
- Enables proper baseline → intervention → outcome measurement
- Sufficient rounds for meaningful dialogue

---

## Fix 7: Empty Chair Influence Metric

### Problem (KIMI, Gemini, ChatGPT-5)
Original metric used F-distance: `influence = abs(empty_f - mean(other_f))`

**Circular reasoning:**
- Empty chair produces F=0.9, others produce F=0.2
- Consensus = max(F) = 0.9 (empty chair drives verdict)
- Influence = abs(0.9 - 0.2) = 0.7 (empty chair measures as "high influence")
- **Problem:** Outlier both determines verdict AND gets credit for being influential

### Solution
**Contribution-based metric:** Count unique pattern types first mentioned by empty chair.

```python
influence = (patterns first mentioned by empty chair) / (total unique patterns)
```

### Example
- Models A, B observe: temporal_inconsistency, polite_extraction
- Empty chair C observes: temporal_inconsistency, context_saturation, role_confusion
- Unique from C: context_saturation, role_confusion (2 new patterns)
- Total unique: 4 pattern types
- Influence = 2/4 = 0.50

### Before
```python
# F-distance (circular)
influence = abs(empty_f - avg_other_f)
```

### After
```python
# Contribution-based
unique_from_empty = count_first_mentions_by_empty_chair()
total_unique = count_total_unique_patterns()
influence = unique_from_empty / total_unique
```

### Impact
- Measures actual contribution (what empty chair adds) not divergence
- Avoids circular reasoning where outlier measures as influential
- Provides actionable metric: does empty chair introduce novel patterns?

---

## Implementation Priority

All 7 fixes are **MUST HAVE** before implementation. Each addresses a critical flaw that would:
- Invalidate research results (Fixes 1, 2)
- Create impossible mathematical conditions (Fixes 5, 6)
- Introduce bias or unfairness (Fix 4)
- Produce circular/meaningless metrics (Fix 7)
- Corrupt consensus integrity (Fix 3)

## Validation Requirements

Before declaring Fire Circle ready for research:

1. **Baseline purity test:** Verify Round 1 uses simple prompt, Round 2+ uses ayni_relational
2. **Groupthink resistance:** Verify consensus captures max(F) across all rounds, not just final
3. **Zombie exclusion:** Verify failed models excluded from consensus calculation
4. **Rotation fairness:** Verify all models get empty chair role equally
5. **Pattern threshold:** Verify threshold uses active model count, remains achievable with failures
6. **Round consistency:** Verify all circles default to 3 rounds
7. **Influence contribution:** Verify empty chair influence measures pattern contribution, not F-distance

## Acknowledgments

Critical review provided by:
- **DeepSeek** (Fixes 1, 2, 3)
- **KIMI** (Fixes 4, 5, 6, 7)
- **Gemini, Grok, ChatGPT-5, Claude Opus** (Supporting analysis and validation)

These models identified design flaws that would have compromised research integrity. Their rigorous analysis prevented shipping a broken specification.

---

**All fixes implemented. Specification ready for implementation review.**
