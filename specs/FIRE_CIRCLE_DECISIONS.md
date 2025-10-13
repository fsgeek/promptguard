# Fire Circle Specification: Key Design Decisions

**Created:** 2025-10-12
**Specification:** fire_circle_specification.md

---

## Critical Decisions Made

### 1. Variable Circle Size Architecture
**Decision:** Single implementation supporting 2-10 models via configuration enum.

**Alternatives considered:**
- Separate implementations for small/medium/large circles
- Hard-coded circle sizes

**Rationale:** Configuration-based approach avoids code duplication, simplifies testing, maintains architectural consistency.

**Impact:** CircleSize enum defines valid ranges, config validation enforces constraints.

---

### 2. Round Count Scaling
**Decision:** Round count does NOT scale linearly with model count. Default 3 rounds for all circle sizes.

**Alternatives considered:**
- Linear scaling: 2 models = 2 rounds, 10 models = 10 rounds
- Fixed 2 rounds (rejected - insufficient for pattern emergence)

**Rationale:** Dialogue converges through pattern discussion regardless of participant count. Three rounds enable: (1) baseline assessment, (2) pattern discussion with ayni_relational, (3) consensus refinement. Diminishing returns after Round 3. Large circles MAY add Round 4 if convergence fails.

**Impact:** Cost scales with model count, not round depth. Keeps Fire Circle feasible for research. Round 1 baseline purity allows measuring dialogue value-add.

---

### 3. Empty Chair Rotation
**Decision:** Rotate empty chair role across rounds using `models[(round_number - 1) % len(models)]`.

**Alternatives considered:**
- Fixed empty chair model (first in list)
- Random selection
- No empty chair (performative concern)

**Rationale:** Rotation ensures multiple models contribute "future/absent" perspective, prevents single model dominating that role, structurally enforces empty chair integration.

**Impact:** Empty chair influence measured per-round, aggregated across dialogue. Threshold detection for performative empty chair (<0.05 mean influence).

---

### 4. Failure Handling Default
**Decision:** RESILIENT mode default, STRICT mode opt-in.

**Alternatives considered:**
- STRICT mode default (fail-fast principle)
- No failure handling (crash on error)

**Rationale:** Research use case tolerates partial results. Pattern discovery from 2 models still valuable. STRICT mode available for production testing where partial results unacceptable.

**Impact:** Minimum viable circle = 2 models. If failures degrade below this, Fire Circle aborts with partial results.

---

### 5. Consensus Algorithm
**Decision:** max(F) across ALL rounds for ALL active models (not just final round).

**Alternatives considered:**
- max(F) from final round only (original - flawed, loses signal to groupthink)
- Average F-scores
- Weighted by model confidence
- Euclidean consensus (existing PARALLEL mode method)

**Rationale:** Fire Circle is a detection system, not a democracy. Goal: capture highest vigilance reached by any model at any point in dialogue. If a model detects F=0.9 in Round 2 but groupthink lowers it to F=0.4 in Round 3, we preserve the Round 2 detection signal. Active models only - zombie models (failed mid-dialogue) don't vote.

**Impact:** Consensus captures peak detection sensitivity across entire dialogue. Dialogue surfaces truths rather than smoothing them over. Prevents groupthink from washing out valid detections.

---

### 6. Pattern Classification
**Decision:** Heuristic-based classification default, LLM classification opt-in.

**Alternatives considered:**
- LLM classification only (more accurate)
- Manual classification (human-in-loop)

**Rationale:** Cost control for research phase. Heuristic keyword matching sufficient for initial validation. Can upgrade to LLM if heuristics prove insufficient.

**Impact:** Pattern extraction cost = $0.00 (heuristic) vs ~$0.01 per pattern (LLM). Research budget optimized.

---

### 7. Caching Strategy
**Decision:** Caching DISABLED by default for Fire Circle dialogue.

**Alternatives considered:**
- Cache all rounds (cost savings)
- Cache Round 1 only (independent assessments)

**Rationale:** Fire Circle dialogue is unique per evaluation. Want fresh reasoning incorporating peer perspectives, not cached responses. Round 1 could be cached but consistency favors full fresh evaluation.

**Impact:** No cost savings from cache, but ensures dialogue authenticity. Research value prioritized over cost.

---

### 8. Pattern Threshold
**Decision:** 0.5 (50%) model agreement required for pattern extraction. Denominator = active model count, not starting count.

**Alternatives considered:**
- 0.66 (2/3 majority)
- 0.33 (1/3 minority perspective)
- Using starting model count (rejected - makes threshold impossible if models fail)

**Rationale:** Balance between pattern robustness (multiple models observe) and sensitivity (not requiring supermajority). For 3-model circle: ≥2 models must agree. CRITICAL: If 10 models start but 5 fail, denominator is 5 (active), not 10 (starting). Otherwise threshold becomes mathematically impossible.

**Impact:** Pattern library includes patterns with moderate-to-strong consensus among active participants, excludes idiosyncratic observations. Threshold remains achievable even with model failures.

---

### 9. Dialogue Prompt Structure
**Decision:** Explicit pattern type prompts (temporal, cross-layer, extraction masking, narrative plausibility).

**Alternatives considered:**
- Generic "look for patterns" prompt
- Blank slate (no guidance)

**Rationale:** Guided pattern recognition based on Scout #5 findings. Temporal verification and cross-layer coordination are known blind spots. Prompts direct attention to these gaps without prescribing findings.

**Impact:** Higher likelihood of discovering actionable patterns. Risk of confirmation bias, but acceptable for initial research phase.

---

### 10. Integration Strategy
**Decision:** Fire Circle as optional mode in PromptGuard.evaluate(), not separate API.

**Alternatives considered:**
- Separate fire_circle_evaluate() function
- New FireCircle class

**Rationale:** Consistency with existing EvaluationMode enum (SINGLE/PARALLEL/FIRE_CIRCLE). User experience: same API, different mode. Reduces cognitive overhead.

**Impact:** PromptGuard.evaluate() returns ReciprocityMetrics with optional patterns field when mode="fire_circle".

---

## Ambiguities Resolved

### Empty Chair Prompt Content
**Ambiguity:** Design mentions "speak for those not present" but doesn't specify exact prompt.

**Resolution:** Specified explicit prompt addition for empty chair models focusing on:
1. Future users who will interact with pattern
2. Communities affected by extraction success
3. System maintainers inheriting consequences

**Validation:** Empty chair influence measurement ensures prompt has structural effect.

---

### Pattern Format
**Ambiguity:** Design shows examples but not schema.

**Resolution:** Defined PatternObservation dataclass with:
- pattern_type: str (enum value)
- description: str
- model_agreement: float
- examples: List[str]
- observed_in_round: int
- models_observing: List[str]

**Implementation:** Structured for REASONINGBANK storage and future retrieval.

---

### Round Count for Large Circles
**Ambiguity:** Should 7-10 model circles automatically get more rounds?

**Resolution:** Default 3 rounds for all sizes. Optional 4th round if Round 3 shows divergence (stddev(F) > 0.3). Configurable via max_rounds parameter.

**Rationale:** Dialogue converges regardless of size. 4th round only if needed.

---

### Failure Recovery for Empty Chair
**Ambiguity:** What happens if empty chair model fails?

**Resolution:**
- STRICT mode: Abort (empty chair structural requirement)
- RESILIENT mode: Skip empty chair for that round, continue
- Log failure with round annotation

**Impact:** Empty chair treated as important but not critical in RESILIENT mode.

---

## Questions for Human Input

### 1. Pattern Classification Investment
**Question:** Should we use LLM-based classification from start, or validate heuristics first?

**Tradeoff:**
- Heuristics: Fast, free, may miss nuanced patterns
- LLM: Accurate, costly (~$0.01/pattern), requires additional API calls

**Recommendation:** Start with heuristics. Upgrade if validation shows misclassification rate >20%.

---

### 2. Round 4 Trigger
**Question:** Should LARGE circles (7-10 models) automatically get 4 rounds, or only if divergence detected?

**Tradeoff:**
- Automatic: Simpler logic, consistent experience, higher cost
- Conditional: Cost-efficient, but adds complexity

**Recommendation:** Conditional (stddev(F) > 0.3 after Round 3). Can revisit if research shows large circles consistently diverge.

---

### 3. Empty Chair Prompt Customization
**Question:** Use default prompt in spec, or require custom prompt path for research flexibility?

**Tradeoff:**
- Default: Consistent experiments, reproducible results
- Custom: Research flexibility, prompt engineering experimentation

**Recommendation:** Default prompt with optional override path. Enable experimentation without forcing it.

---

### 4. REASONINGBANK Schema
**Question:** What structure should pattern storage use for future retrieval and analysis?

**Current proposal:**
```
category="fire_circle_pattern"
subcategory=pattern_type
content={
    "description": str,
    "agreement": float,
    "attack_id": str,
    "examples": List[str],
    "models": List[str]
}
```

**Recommendation:** Validate with REASONINGBANK maintainer before implementation.

---

## Implementation Priority

### Phase 1: Core Dialogue (Must Have)
1. 3-round dialogue protocol
2. Empty chair rotation
3. Pattern extraction (heuristic)
4. RESILIENT failure handling
5. max(F) consensus

### Phase 2: Robustness (Should Have)
6. STRICT mode
7. Convergence detection (early stop)
8. Unparseable response recovery
9. Empty chair influence measurement

### Phase 3: Research Features (Nice to Have)
10. LLM-based pattern classification
11. Round 4 conditional logic
12. REASONINGBANK integration
13. Custom empty chair prompts

---

**Decision rationale documented. Ready for implementation review.**
