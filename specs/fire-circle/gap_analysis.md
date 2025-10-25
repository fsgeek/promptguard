# Fire Circle Gap Analysis

**Document Version:** 1.0
**Last Updated:** 2025-10-24
**Purpose:** Compare current Fire Circle implementation against research requirements to identify gaps blocking PromptGuard's continuous learning loop

---

## Executive Summary

### Critical Findings

**Biggest Research Blockers:**
1. **1000 token limit breaks deliberation** (P0) - Round 3 dialogue context exhaustion causes silent truncation
2. **Pattern discovery has no validation** (P1) - No empirical testing of whether patterns improve detection
3. **Dissent tracking doesn't exist** (P1) - Cannot study minority-to-consensus evolution
4. **Learning loop is incomplete** (P0) - Fire Circle → REASONINGBANK integration undefined
5. **Longitudinal analysis impossible** (P1) - No cross-deliberation pattern tracking

**Architecture Assessment:**
- Core deliberation mechanism is sound (max(F) consensus, zombie handling, empty chair rotation)
- Integration points exist but are disconnected (storage works, but no queries leverage it)
- Research value is theoretical - no validation that Fire Circle does what it claims
- Incremental refactor sufficient - don't rebuild from scratch

**Key Metrics:**
- **P0 Gaps (Blockers):** 7 gaps make Fire Circle unusable for research
- **P1 Gaps (Research Critical):** 12 gaps prevent core research questions
- **P2 Gaps (Quality):** 8 gaps hurt operational reliability
- **P3 Gaps (Future):** 5 gaps enable additional research questions

---

## Section 1: Core Purpose

### Requirement 1.1: Role in Continuous Learning Loop

**Current state:** Fire Circle completes deliberations and stores to ArangoDB (lines 843-896 in current_behavior.md), but integration with REASONINGBANK is undefined. No code exists to extract patterns from Fire Circle results and inject them into observer framing.

**Gap category:** A - CRITICAL MISSING

**Gap description:** The learning loop is theoretically described but operationally incomplete:
- Fire Circle discovers patterns ✓
- Patterns stored to ArangoDB ✓
- REASONINGBANK retrieval in observer framing exists ✓ (from Instance 18)
- **MISSING:** Code to transform Fire Circle patterns into REASONINGBANK entries
- **MISSING:** Validation that REASONINGBANK entries improve pre-evaluation
- **MISSING:** Feedback loop closure measurement

**Impact:** Without this integration, Fire Circle is just expensive data collection. The core research hypothesis - "continuous learning outperforms static RLHF" - cannot be tested because the learning loop never closes.

**Fix complexity:** MODERATE

**Fix approach:**
```python
# 1. Create Fire Circle → REASONINGBANK adapter
def extract_reasoningbank_entries(fire_circle_result: FireCircleResult) -> List[ReasoningBankMemory]:
    for pattern in fire_circle_result.patterns:
        if pattern.agreement_score >= threshold:
            memory = ReasoningBankMemory(
                attack_pattern=pattern.pattern_type,
                detection_reasoning=synthesize_from_turns(pattern),
                few_shot_examples=extract_examples(fire_circle_result),
                discovered_by=pattern.first_observed_by,
                fire_circle_id=fire_circle_result.fire_circle_id
            )
            yield memory

# 2. Add validation experiment scheduler
def schedule_pattern_validation(memory: ReasoningBankMemory):
    test_attacks = get_similar_attacks(memory.attack_pattern)
    baseline = run_pre_eval_without_pattern(test_attacks)
    enhanced = run_pre_eval_with_pattern(test_attacks, memory)
    improvement = enhanced.rate - baseline.rate
    memory.detection_improvement = improvement
    memory.validated = improvement > 0.1

# 3. Track loop closure
def measure_learning_loop_latency(attack_id: str):
    t1 = timestamp(pre_eval_miss)
    t2 = timestamp(post_eval_detect)
    t3 = timestamp(fire_circle_complete)
    t4 = timestamp(reasoningbank_entry)
    t5 = timestamp(next_similar_attack_detected)
    return t5 - t1
```

---

### Requirement 1.2: Research Questions Fire Circle Answers

**Current state:** Fire Circle stores dialogue history (lines 184-199 in current_behavior.md) and patterns (lines 512-520), but no analysis framework exists to answer the research questions posed in requirements (lines 33-48).

**Gap category:** A - CRITICAL MISSING

**Gap description:** Data is collected but not analyzed:
- Primary questions (why did pre-eval miss?) - No systematic miss analysis
- Secondary questions (model diversity value) - No per-model contribution tracking across deliberations
- Meta questions (collective reasoning emergence) - No longitudinal semantic analysis

**Impact:** Fire Circle generates data that could answer research questions, but without analysis framework, research value is unrealized. Cannot demonstrate that Fire Circle provides unique insights.

**Fix complexity:** COMPLEX

**Fix approach:**
1. **Build miss analysis pipeline:**
   - Trigger Fire Circle only when `post_F - pre_F > threshold` (detection miss)
   - Compare pre-evaluation reasoning to Fire Circle patterns
   - Measure: Did Fire Circle identify what pre-eval missed?

2. **Implement cross-deliberation analysis:**
   - Query ArangoDB for all deliberations about similar attacks
   - Track pattern evolution over time
   - Measure model specialization via attribution

3. **Create research query templates:**
   - "Which dissent became consensus?"
   - "How did pattern X understanding evolve?"
   - "Which models specialize in which patterns?"

---

### Requirement 1.3: Data Generated for Longitudinal Analysis

**Current state:** ArangoDB storage exists (lines 558-651 in current_behavior.md) with correct schema, but no cross-deliberation linking or longitudinal queries implemented.

**Gap category:** B - PARTIAL

**Gap description:**
- Deliberations stored with patterns ✓
- Patterns classified and attributed ✓ (lines 494-534)
- **MISSING:** Cross-deliberation pattern tracking (same pattern across multiple Fire Circles)
- **MISSING:** Dissent evolution tracking (minority → consensus)
- **MISSING:** REASONINGBANK integration tracking (which patterns improved detection?)
- **MISSING:** Temporal queries (pattern discovery rate over time)

**Impact:** Cannot answer longitudinal questions like "do minority opinions become consensus?" or "does understanding improve over time?" Data exists but is isolated per-deliberation.

**Fix complexity:** MODERATE

**Fix approach:**
1. **Add patterns collection to ArangoDB:**
   ```python
   # Currently patterns embedded in deliberations
   # Should be: separate collection with cross-deliberation tracking
   patterns = {
       "_key": pattern_id,
       "canonical_name": str,
       "first_discovered": {
           "fire_circle_id": str,
           "model": str,
           "date": datetime
       },
       "rediscoveries": [
           {"fire_circle_id": str, "date": datetime, "models": []}
       ],
       "reasoningbank_entry_id": Optional[str],
       "detection_improvement": Optional[float]
   }
   ```

2. **Add dissents collection:**
   ```python
   dissents = {
       "_key": dissent_id,
       "fire_circle_id": str,
       "round_number": int,
       "dissenting_model": str,
       "dissenting_f": float,
       "consensus_f": float,
       "f_delta": float,
       "later_validated": Optional[bool],
       "became_consensus_in": Optional[str]  # fire_circle_id
   }
   ```

3. **Implement longitudinal queries from research spec (lines 806-829, 872-893, 926-937)**

---

## Section 2: Deliberation Goals

### Requirement 2.1: Quality Metrics - Detection Quality

**Current state:** Consensus F-score calculated (lines 385-430 in current_behavior.md), but no measurement of pattern actionability or generalization.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- Consensus F-score exists ✓
- Pattern agreement threshold exists ✓ (line 340)
- **MISSING:** Pattern actionability measurement (is "polite extraction" specific enough?)
- **MISSING:** Pattern generalization testing (does pattern apply to other attacks?)
- **MISSING:** Detection improvement validation (does pattern actually help?)

**Impact:** Cannot distinguish high-quality patterns ("polite imperative masking role reversal") from generic theater ("seems manipulative"). All patterns treated equally regardless of value.

**Fix complexity:** MODERATE

**Fix approach:**
```python
@dataclass
class PatternQuality:
    pattern_id: str

    # Immediate checks
    actionability_score: float  # Length, specificity, mechanism description
    specificity_score: float    # Generic keywords penalty

    # Empirical validation
    detection_improvement: Optional[float]  # A/B test result
    false_positive_rate: Optional[float]    # Test on benign prompts
    generalization_count: int               # Works on N similar attacks

    # Longitudinal
    rediscovery_count: int                  # Independent discoveries
    reasoningbank_usage: int                # Times retrieved

    validated: bool  # Passes all quality gates

def validate_pattern_quality(pattern: PatternObservation) -> PatternQuality:
    # Phase 1: Immediate (structural)
    actionability = measure_pattern_specificity(pattern)

    # Phase 2: Empirical (detection)
    test_attacks = get_similar_attacks(pattern.attack_category)
    improvement = test_pattern_on_attacks(pattern, test_attacks)

    # Phase 3: False positives
    fp_rate = test_pattern_on_benign(pattern, n=100)

    return PatternQuality(
        actionability_score=actionability,
        detection_improvement=improvement,
        false_positive_rate=fp_rate,
        validated=improvement > 0.1 and fp_rate < 0.05
    )
```

---

### Requirement 2.1: Quality Metrics - Epistemic Quality

**Current state:** Convergence metric calculated per round (lines 1081-1088 in current_behavior.md), but no measurement of reasoning diversity or substantiveness.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- F-score convergence tracked ✓ (stddev of F-scores)
- **MISSING:** Reasoning diversity measurement (semantic similarity of reasoning text)
- **MISSING:** Dissent substantiveness analysis (meaningful disagreement vs noise)
- **MISSING:** Empty chair perspective uniqueness (does empty chair say something different?)
- **MISSING:** Groupthink detection (converge without reasoning change)

**Impact:** Cannot detect when deliberation is performative vs genuine. Models might echo each other without adding insight, and we wouldn't know.

**Fix complexity:** MODERATE

**Fix approach:**
```python
def measure_epistemic_quality(fire_circle: FireCircleResult) -> EpistemicQuality:
    # Reasoning diversity
    reasonings = [e.reasoning for round in dialogue_history for e in round.evaluations]
    embeddings = [embed(r) for r in reasonings]
    diversity = 1 - mean_pairwise_similarity(embeddings)

    # Groupthink detection
    round1_stddev = stddev([e.falsehood for e in round1_evals])
    round3_stddev = stddev([e.falsehood for e in round3_evals])
    convergence_ratio = round3_stddev / round1_stddev

    groupthink = convergence_ratio < 0.3 and diversity < 0.5

    # Empty chair uniqueness
    empty_chair_patterns = get_patterns_by(empty_chair_model)
    active_patterns = get_patterns_by(active_models)
    unique_contribution = len(set(empty_chair_patterns) - set(active_patterns))

    return EpistemicQuality(
        reasoning_diversity=diversity,
        groupthink_detected=groupthink,
        empty_chair_uniqueness=unique_contribution,
        convergence_trajectory=[r.convergence_metric for r in dialogue_history]
    )
```

---

### Requirement 2.2: Bad Deliberation Characteristics

**Current state:** No detection of groupthink, theater, or structural failure beyond quorum checking (lines 731-745 in current_behavior.md).

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- Quorum failure detection exists ✓
- **MISSING:** Groupthink detection (immediate convergence without deliberation)
- **MISSING:** Theater detection (generic patterns, circular reasoning)
- **MISSING:** Context saturation detection (Round 3 reasoning shorter than Round 1)
- **MISSING:** Quality flagging (mark deliberations as low-quality for exclusion)

**Impact:** Bad deliberations pollute dataset and REASONINGBANK. Cannot filter out theater when analyzing results or extracting patterns.

**Fix complexity:** SIMPLE

**Fix approach:**
```python
@dataclass
class DeliberationQuality:
    groupthink_detected: bool
    theater_detected: bool
    context_saturation_detected: bool
    quality_score: float  # 0-1
    usable_for_research: bool

def assess_deliberation_quality(fc: FireCircleResult) -> DeliberationQuality:
    # Groupthink
    groupthink = detect_groupthink(fc)

    # Theater
    generic_patterns = sum(1 for p in fc.patterns
                          if any(kw in p.pattern_type for kw in
                                ["suspicious", "unclear", "concerning"]))
    theater = generic_patterns / len(fc.patterns) > 0.5

    # Context saturation
    round1_reasoning_len = mean([len(e.reasoning) for e in round1_evals])
    round3_reasoning_len = mean([len(e.reasoning) for e in round3_evals])
    saturation = round3_reasoning_len < round1_reasoning_len * 0.7

    quality_score = calculate_quality_score(groupthink, theater, saturation)

    return DeliberationQuality(
        groupthink_detected=groupthink,
        theater_detected=theater,
        context_saturation_detected=saturation,
        quality_score=quality_score,
        usable_for_research=quality_score > 0.6
    )
```

---

### Requirement 2.3: When to Use Fire Circle vs Other Modes

**Current state:** Fire Circle can be invoked via `mode=FIRE_CIRCLE` in config, but no decision logic exists for when to use it.

**Gap category:** B - PARTIAL

**Gap description:**
- Fire Circle invocable ✓
- **MISSING:** Automatic triggering based on pre/post divergence
- **MISSING:** Cost-benefit decision logic
- **MISSING:** Attack type routing (encoding attacks → specialist circle)
- **MISSING:** Usage metrics (how often Fire Circle adds value vs overhead)

**Impact:** Cannot optimize Fire Circle usage for cost-effectiveness. May be invoking Fire Circle when SINGLE mode would suffice, or missing opportunities where Fire Circle would add value.

**Fix complexity:** MODERATE

**Fix approach:**
```python
def should_use_fire_circle(
    pre_eval_result: NeutrosophicEvaluation,
    post_eval_result: Optional[NeutrosophicEvaluation],
    attack_category: str,
    budget_remaining: float
) -> bool:
    # Trigger 1: Pre/post divergence (learning opportunity)
    if post_eval_result and abs(post_eval_result.falsehood - pre_eval_result.falsehood) > 0.3:
        return True

    # Trigger 2: Novel attack type (pattern discovery)
    if attack_category not in known_patterns_db:
        return True

    # Trigger 3: High-stakes evaluation
    if attack_category in high_risk_categories:
        return True

    # Budget constraint
    estimated_cost = estimate_fire_circle_cost(circle_size, models)
    if estimated_cost > budget_remaining:
        return False

    # Default: use SINGLE mode
    return False
```

---

## Section 3: Model Selection Strategy

### Requirement 3.1: Diversity Dimensions

**Current state:** Models selected from config list (line 642 in current_behavior.md), but no diversity measurement or optimization.

**Gap category:** B - PARTIAL

**Gap description:**
- Model list configurable ✓
- Circle size constraints enforced ✓ (lines 361-366)
- **MISSING:** Model metadata (architecture, RLHF level, geographic origin)
- **MISSING:** Diversity scoring (quantify diversity across dimensions)
- **MISSING:** Automatic composition optimization (maximize diversity)

**Impact:** Cannot measure whether circle composition has sufficient diversity. Manual model selection may miss complementary perspectives.

**Fix complexity:** MODERATE

**Fix approach:**
1. **Extend model metadata in ArangoDB:**
   ```python
   models = {
       "_key": model_id,
       "organization": str,
       "architecture": "gpt|claude|gemini|llama|deepseek",
       "rlhf_level": "high|moderate|low|none",
       "geographic_origin": "us|china|europe",
       "capability_tier": "frontier|mid|budget",
       "specializations": ["encoding", "role_confusion", "temporal"]
   }
   ```

2. **Implement diversity scoring:**
   ```python
   def calculate_diversity_score(models: List[str]) -> float:
       architectures = set(get_metadata(m).architecture for m in models)
       origins = set(get_metadata(m).geographic_origin for m in models)
       rlhf_levels = set(get_metadata(m).rlhf_level for m in models)

       diversity = (
           len(architectures) / 5 +    # Max 5 architecture families
           len(origins) / 3 +            # Max 3 geographic regions
           len(rlhf_levels) / 4          # Max 4 RLHF levels
       ) / 3

       return diversity  # 0-1 score
   ```

---

### Requirement 3.3: Dynamic vs Static Circle Composition

**Current state:** Static circles only (same models for all deliberations).

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- Fixed model list per config ✓
- **MISSING:** Attack-type-based model selection
- **MISSING:** Core + rotational model sets
- **MISSING:** Specialist routing (encoding attacks → encoding-specialist models)

**Impact:** Cannot optimize model selection for attack type. May be using models that have no relevant expertise for the attack being analyzed.

**Fix complexity:** MODERATE

**Fix approach:**
```python
@dataclass
class DynamicCircleConfig:
    core_models: List[str]  # Present in ALL deliberations
    rotational_pool: List[str]  # Selected based on attack type
    specialist_map: Dict[str, List[str]]  # attack_category → specialist models

    def select_models_for_attack(self, attack_category: str, circle_size: CircleSize) -> List[str]:
        models = self.core_models.copy()

        # Add specialists if available
        specialists = self.specialist_map.get(attack_category, [])
        models.extend(specialists)

        # Fill to circle size from rotational pool
        min_size, max_size = circle_size.value
        while len(models) < max_size:
            models.append(select_from_pool(self.rotational_pool, existing=models))

        # Ensure diversity
        if calculate_diversity_score(models) < 0.5:
            models = optimize_for_diversity(models, self.rotational_pool, max_size)

        return models[:max_size]
```

---

### Requirement 3.5: Handling Model Failures - Research Value

**Current state:** Failures logged (lines 374-391 in current_behavior.md) but not analyzed for patterns.

**Gap category:** B - PARTIAL

**Gap description:**
- Failure tracking exists ✓
- Zombie/excluded state transitions logged ✓
- **MISSING:** Failure pattern analysis (which models fail on which attacks?)
- **MISSING:** Robustness scoring (model reliability metric)
- **MISSING:** Context saturation detection (did dialogue break the model?)

**Impact:** Failures are data, but we're not extracting research value from them. Cannot identify which models are fragile or which attacks cause failures.

**Fix complexity:** SIMPLE

**Fix approach:**
```python
# Query: Which models fail on which attack types?
FOR f IN failures
  COLLECT model = f.model, attack_category = f.attack_category INTO failures
  RETURN {
      model: model,
      attack_category: attack_category,
      failure_count: LENGTH(failures),
      failure_types: UNIQUE(failures[*].f.failure_type)
  }

# Query: Which attacks cause widespread failures?
FOR f IN failures
  COLLECT attack_id = f.attack_id INTO failures
  FILTER LENGTH(failures) >= 2  # Multiple models failed
  RETURN {
      attack_id: attack_id,
      failed_models: UNIQUE(failures[*].f.model),
      failure_rate: LENGTH(failures) / total_models
  }
```

---

## Section 4: Empty Chair Mechanism

### Requirement 4.2: Rotation vs Consistent Role

**Current state:** Rotation through models (Round 2: models[1], Round 3: models[2]) as documented in lines 433-470 of current_behavior.md.

**Gap category:** C - WRONG DESIGN

**Gap description:**
- Rotation implemented ✓
- **PROBLEM:** Each model only gets empty chair role once per deliberation
- **PROBLEM:** No consistency in perspective representation
- **PROBLEM:** Attribution unclear (active vs empty chair contribution)
- **BETTER DESIGN:** One model assigned empty chair for entire deliberation (all rounds)

**Impact:** Rotation dilutes role coherence. If empty chair is supposed to represent absent stakeholders, it should be consistent voice, not rotating assignment. Cannot track which model is best at empty chair role.

**Fix complexity:** SIMPLE

**Fix approach:**
```python
def select_empty_chair_model(models: List[str], config: FireCircleConfig) -> str:
    # If specified, use that model
    if config.empty_chair_model:
        return config.empty_chair_model

    # Otherwise, select first model as default
    # (Better: select based on empty chair effectiveness history)
    return models[0]

def rotate_empty_chair(round_number: int, empty_chair_model: str) -> Optional[str]:
    # Round 1: No empty chair (independent baseline)
    if round_number == 1:
        return None

    # Round 2+: SAME model serves as empty chair
    return empty_chair_model
```

**Alternative approach for experimentation:**
```python
# Rotate which model serves as primary empty chair weekly/monthly
def select_empty_chair_for_week(models: List[str], week_number: int) -> str:
    return models[week_number % len(models)]
```

---

### Requirement 4.3: Validation - Is Empty Chair Working?

**Current state:** Empty chair influence metric exists (lines 679-691 in current_behavior.md) but only measures pattern discovery count, not perspective uniqueness or consensus influence.

**Gap category:** B - PARTIAL

**Gap description:**
- Pattern discovery attribution exists ✓ (first_observed_by)
- Empty chair influence calculated ✓ (fraction of patterns discovered)
- **MISSING:** Perspective uniqueness (does empty chair mention absent stakeholders?)
- **MISSING:** Consensus shift measurement (did empty chair change F-scores?)
- **MISSING:** A/B testing (with vs without empty chair)
- **MISSING:** Long-term validation tracking (do empty chair patterns improve detection?)

**Impact:** Cannot determine if empty chair mechanism provides unique value or is just rotating through models. No evidence that empty chair represents genuinely absent perspectives.

**Fix complexity:** MODERATE

**Fix approach:**
```python
@dataclass
class EmptyChairEffectiveness:
    # Pattern discovery
    patterns_discovered_count: int
    patterns_unique_to_empty_chair: int  # Not mentioned by any active model

    # Perspective analysis
    mentions_future_generations: bool
    mentions_vulnerable_populations: bool
    mentions_system_maintainers: bool
    mentions_adversarial_red_team: bool

    # Consensus influence
    f_score_changes_after_empty_chair: List[float]  # Round 2 → Round 3 deltas
    consensus_shifted: bool  # Did final consensus match empty chair?

    # Longitudinal
    patterns_entered_reasoningbank: int
    detection_improvement_average: float

def validate_empty_chair_mechanism():
    # A/B test: Same attacks with and without empty chair
    test_attacks = sample_attacks(n=100)

    with_empty_chair = run_fire_circle(test_attacks, empty_chair=True)
    without_empty_chair = run_fire_circle(test_attacks, empty_chair=False)

    return {
        "patterns_discovered": {
            "with": len(with_empty_chair.patterns),
            "without": len(without_empty_chair.patterns),
            "unique_to_empty_chair": count_unique(with_empty_chair, without_empty_chair)
        },
        "detection_improvement": {
            "with": measure_improvement(with_empty_chair.patterns),
            "without": measure_improvement(without_empty_chair.patterns)
        },
        "cost": {
            "with": with_empty_chair.cost,
            "without": without_empty_chair.cost
        }
    }
```

---

## Section 5: Consensus & Dissent

### Requirement 5.1: Research-Oriented Consensus Mechanisms

**Current state:** max(F) consensus only (lines 385-430 in current_behavior.md). Full distribution not preserved in consensus object.

**Gap category:** C - WRONG DESIGN

**Gap description:**
- max(F) consensus calculated ✓
- **PROBLEM:** Only single evaluation preserved, full distribution lost
- **PROBLEM:** No central tendency, confidence intervals, or unanimity tracking
- **BETTER DESIGN:** Store both detection signal (max F) and research metrics (full distribution)

**Impact:** Cannot study convergence dynamics, epistemic uncertainty, or agreement patterns. Research value limited to "what was the consensus?" not "how did models differ?"

**Fix complexity:** SIMPLE

**Fix approach:**
```python
@dataclass
class ResearchConsensus:
    # Operational (for detection)
    detection_signal: NeutrosophicEvaluation  # max(F) evaluation

    # Research (for analysis)
    central_tendency: Dict[str, float]  # median T/I/F
    confidence_interval: Dict[str, Tuple[float, float]]  # p10-p90 for T/I/F
    unanimity: bool  # All F > 0.7 or all F < 0.5
    epistemic_uncertainty: float  # stddev(F)

    # Distribution
    all_evaluations: List[NeutrosophicEvaluation]  # Full data
    f_scores: List[float]  # All F-scores

    # Attribution
    max_f_model: str  # Who produced detection signal
    max_f_round: int  # When it occurred

def compute_research_consensus(dialogue_history: List[DialogueRound]) -> ResearchConsensus:
    active_models = set(dialogue_history[-1].active_models)

    all_evals = [e for round in dialogue_history
                 for e in round.evaluations
                 if e.model in active_models]

    f_scores = [e.falsehood for e in all_evals]

    max_f_eval = max(all_evals, key=lambda e: e.falsehood)

    return ResearchConsensus(
        detection_signal=max_f_eval,
        central_tendency={
            "T": median([e.truth for e in all_evals]),
            "I": median([e.indeterminacy for e in all_evals]),
            "F": median(f_scores)
        },
        confidence_interval={
            "F": (percentile(f_scores, 10), percentile(f_scores, 90))
        },
        unanimity=all(f > 0.7 for f in f_scores) or all(f < 0.5 for f in f_scores),
        epistemic_uncertainty=stddev(f_scores),
        all_evaluations=all_evals,
        f_scores=f_scores,
        max_f_model=max_f_eval.model,
        max_f_round=find_round_for_eval(max_f_eval, dialogue_history)
    )
```

---

### Requirement 5.2: Capturing and Indexing Dissents

**Current state:** Dissent extraction method exists (lines 660-670 in current_behavior.md) but returns minimal data, not indexed in ArangoDB.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- Dissent F-delta calculation exists ✓ (`find_dissents()` in arango_backend.py)
- **MISSING:** Dissent storage as first-class objects
- **MISSING:** Longitudinal validation tracking (did dissent become consensus?)
- **MISSING:** Dissent reasoning capture (why did model dissent?)
- **MISSING:** Pattern divergence (which patterns did dissenter see that others didn't?)

**Impact:** Cannot study dissent evolution, identify valuable minority opinions, or track which dissents proved correct. Core research question "do dissents become consensus?" is unanswerable.

**Fix complexity:** MODERATE

**Fix approach:**
1. **Add dissents collection to ArangoDB:**
   ```python
   dissents = {
       "_key": dissent_id,
       "fire_circle_id": str,
       "round_number": int,
       "dissenting_model": str,
       "dissenting_f_score": float,
       "consensus_f_score": float,  # Median of others
       "f_delta": float,
       "dissenting_reasoning": str,
       "dissenting_patterns": List[str],

       # Context
       "attack_id": str,
       "attack_category": str,
       "timestamp": datetime,

       # Longitudinal tracking
       "later_validated": Optional[bool],
       "became_consensus_in": Optional[str],  # fire_circle_id
       "entered_reasoningbank": Optional[bool]
   }
   ```

2. **Extract dissents during Fire Circle:**
   ```python
   def extract_dissents(fire_circle: FireCircleResult) -> List[Dissent]:
       dissents = []

       for round_data in fire_circle.dialogue_history:
           evals = round_data.evaluations
           median_f = median([e.falsehood for e in evals])

           for eval in evals:
               if abs(eval.falsehood - median_f) >= 0.3:
                   dissents.append(Dissent(
                       fire_circle_id=fire_circle.fire_circle_id,
                       round_number=round_data.round_number,
                       dissenting_model=eval.model,
                       dissenting_f_score=eval.falsehood,
                       consensus_f_score=median_f,
                       f_delta=abs(eval.falsehood - median_f),
                       dissenting_reasoning=eval.reasoning,
                       dissenting_patterns=getattr(eval, "patterns_observed", [])
                   ))

       return dissents
   ```

3. **Implement longitudinal queries (from requirements lines 478-499)**

---

### Requirement 5.3: Predicting Valuable Dissents

**Current state:** No dissent quality prediction exists.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- Dissents not captured systematically (see 5.2 gap)
- **MISSING:** Dissent quality features (magnitude, consistency, reasoning depth)
- **MISSING:** Historical accuracy tracking (has this model been right before?)
- **MISSING:** Classifier for valuable vs noise dissents
- **MISSING:** Prioritization for REASONINGBANK entry

**Impact:** If Fire Circle generates 100 dissents per day, researchers can't analyze all. No way to prioritize which dissents deserve investigation.

**Fix complexity:** COMPLEX (requires 5.2 to be fixed first)

**Fix approach:**
```python
@dataclass
class DissentQuality:
    dissent_id: str

    # Features
    f_delta_magnitude: float
    reasoning_length: int
    pattern_novelty: int  # Patterns no one else mentioned
    model_consistency: float  # How often this model dissents on similar attacks
    model_historical_accuracy: float  # Track record of valuable dissents

    # Prediction
    predicted_value: float  # 0-1 score
    priority_for_investigation: "high|medium|low"

    # Validation (after empirical testing)
    actually_valuable: Optional[bool]

def predict_dissent_value(dissent: Dissent) -> DissentQuality:
    # Extract features
    model_history = get_model_dissent_history(dissent.dissenting_model)

    # Calculate quality score
    quality = weighted_sum([
        dissent.f_delta * 0.3,  # Magnitude
        len(dissent.dissenting_reasoning) / 1000 * 0.2,  # Depth
        count_novel_patterns(dissent) * 0.3,  # Novelty
        model_history.valuable_dissent_rate * 0.2  # Track record
    ])

    priority = "high" if quality > 0.7 else "medium" if quality > 0.4 else "low"

    return DissentQuality(
        dissent_id=dissent.dissent_id,
        f_delta_magnitude=dissent.f_delta,
        reasoning_length=len(dissent.dissenting_reasoning),
        model_historical_accuracy=model_history.valuable_dissent_rate,
        predicted_value=quality,
        priority_for_investigation=priority
    )
```

---

## Section 6: Pattern Discovery

### Requirement 6.2: Pattern Taxonomy for PromptGuard

**Current state:** Flat keyword-based taxonomy (lines 494-534 in current_behavior.md) with 12 pattern types.

**Gap category:** C - WRONG DESIGN

**Gap description:**
- Pattern classification exists ✓
- **PROBLEM:** Flat taxonomy (no hierarchy)
- **PROBLEM:** Keyword matching (case-insensitive substring search)
- **PROBLEM:** No provenance tracking (when was pattern first discovered globally?)
- **PROBLEM:** No effectiveness tracking (detection improvement, false positive rate)
- **BETTER DESIGN:** Structured taxonomy with hierarchy, provenance, and effectiveness

**Impact:** Pattern library will scale poorly. Cannot refine patterns over time, cannot measure which patterns are valuable, cannot track pattern evolution.

**Fix complexity:** MODERATE

**Fix approach:**
1. **Replace flat classification with structured registry:**
   ```python
   @dataclass
   class AttackPattern:
       # Identity
       pattern_id: str
       canonical_name: str
       aliases: List[str]

       # Semantics
       mechanism: str  # HOW attack works
       ayni_violation: str  # WHAT reciprocity principle violated
       detection_signals: List[str]

       # Hierarchy
       parent_pattern: Optional[str]
       related_patterns: List[str]

       # Provenance
       first_discovered_by: str
       first_fire_circle: str
       discovery_date: datetime

       # Effectiveness
       detection_improvement: Optional[float]
       false_positive_rate: Optional[float]
       detection_examples: List[str]
       miss_examples: List[str]

       # Evolution
       refinement_history: List[Dict]
       superseded_by: Optional[str]
   ```

2. **Store patterns as first-class collection in ArangoDB**

3. **Implement pattern reconciliation (map "polite extraction" to "polite_imperative_role_reversal")**

---

### Requirement 6.3: Pattern Attribution

**Current state:** `first_observed_by` tracks first mention in current deliberation (lines 468, 1468 in current_behavior.md).

**Gap category:** B - PARTIAL

**Gap description:**
- Per-deliberation attribution exists ✓
- **MISSING:** Global discoverer tracking (first across all deliberations)
- **MISSING:** Re-discoverer tracking (independent validation)
- **MISSING:** Elaborator tracking (who explained mechanism best)
- **MISSING:** Validator tracking (who provided evidence)

**Impact:** Cannot track which models discover vs refine vs validate patterns. Cannot measure model specialization or contribution types.

**Fix complexity:** MODERATE

**Fix approach:**
```python
@dataclass
class PatternAttribution:
    pattern_id: str
    fire_circle_id: str

    # Roles in THIS deliberation
    first_observer: str  # Round 2
    elaborators: List[str]  # Round 3 detailed mechanism
    validators: List[str]  # Provided evidence

    # Global context
    global_discoverer: str  # First ever (across all Fire Circles)
    rediscovery_count: int  # Independent discoveries

    # Influence
    changed_consensus: bool  # Did pattern shift F-scores?
    entered_reasoningbank: bool

def track_pattern_attribution(
    pattern: PatternObservation,
    fire_circle: FireCircleResult,
    pattern_registry: PatternRegistry
) -> PatternAttribution:
    # Check if pattern exists globally
    global_pattern = pattern_registry.find(pattern.pattern_type)

    if global_pattern:
        # Re-discovery
        global_discoverer = global_pattern.first_discovered_by
        rediscovery_count = global_pattern.rediscovery_count + 1
    else:
        # First discovery
        global_discoverer = pattern.first_observed_by
        rediscovery_count = 0

    # Find elaborators (Round 3 mentions with longest reasoning)
    elaborators = find_elaborators(pattern, fire_circle.dialogue_history)

    return PatternAttribution(...)
```

---

### Requirement 6.4: Pattern Quality Validation

**Current state:** Pattern agreement threshold (line 340 in current_behavior.md) but no empirical validation.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- Agreement threshold filtering exists ✓
- **MISSING:** Detection improvement testing
- **MISSING:** False positive testing
- **MISSING:** Generalization testing
- **MISSING:** Quality gates before REASONINGBANK entry

**Impact:** Low-quality patterns enter REASONINGBANK without validation. No way to distinguish valuable patterns from noise.

**Fix complexity:** MODERATE

**Fix approach:**
```python
def validate_pattern_empirically(pattern: AttackPattern) -> PatternQuality:
    # Phase 1: Detection improvement
    similar_attacks = get_attacks_by_category(pattern.attack_category, n=50)

    baseline_detection = run_pre_eval(
        attacks=similar_attacks,
        reasoningbank_enabled=False
    )

    enhanced_detection = run_pre_eval(
        attacks=similar_attacks,
        reasoningbank_patterns=[pattern]
    )

    improvement = enhanced_detection.rate - baseline_detection.rate

    # Phase 2: False positive rate
    benign_prompts = get_benign_prompts(n=100)
    fp_count = sum(1 for p in benign_prompts
                   if pattern_triggers(p, pattern))
    fp_rate = fp_count / len(benign_prompts)

    # Phase 3: Generalization
    rediscovery_count = count_independent_discoveries(pattern)

    validated = improvement > 0.1 and fp_rate < 0.05 and rediscovery_count > 1

    return PatternQuality(
        pattern_id=pattern.pattern_id,
        detection_improvement=improvement,
        false_positive_rate=fp_rate,
        rediscovery_count=rediscovery_count,
        validated=validated
    )
```

---

## Section 7: Longitudinal Analysis Requirements

### Requirement 7.1: Query "Which Dissent Became Consensus?"

**Current state:** ArangoDB storage exists but no cross-deliberation linking for dissent evolution.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- Deliberations stored ✓
- **MISSING:** Dissents as first-class objects (see Section 5.2 gap)
- **MISSING:** Cross-deliberation pattern tracking
- **MISSING:** Temporal queries linking dissent to later consensus
- **MISSING:** Vindication latency measurement

**Impact:** Core research question "do minority opinions become consensus?" is unanswerable with current schema.

**Fix complexity:** COMPLEX (requires dissent storage + pattern registry)

**Fix approach:**
1. Implement dissent storage (Section 5.2 fix)
2. Implement pattern registry (Section 6.2 fix)
3. Add vindication tracking:
   ```python
   def track_dissent_vindication():
       # Find dissents where F > consensus
       FOR d IN dissents
         FILTER d.dissenting_f_score > d.consensus_f_score + 0.3

         # Find later deliberations on similar attacks
         LET later_consensus = (
           FOR fc IN deliberations
             FILTER fc.created_at > d.timestamp
             FILTER fc.metadata.attack_category == d.attack_category
             FILTER fc.consensus.falsehood >= d.dissenting_f_score - 0.2
             RETURN fc
         )

         FILTER LENGTH(later_consensus) > 0

         # Mark dissent as vindicated
         UPDATE d WITH {
           later_validated: true,
           became_consensus_in: later_consensus[0].fire_circle_id,
           vindication_latency_days: DATE_DIFF(d.timestamp, later_consensus[0].created_at, 'day')
         } IN dissents
   ```

---

### Requirement 7.2: Query "How Did Pattern Discovery Evolve?"

**Current state:** Patterns stored per-deliberation but no cross-deliberation evolution tracking.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- Per-deliberation patterns stored ✓
- **MISSING:** Pattern registry tracking same pattern across deliberations
- **MISSING:** Refinement history (how did understanding change?)
- **MISSING:** Agreement trajectory (did more models converge on pattern?)
- **MISSING:** Detection effectiveness trajectory (did pattern improve over time?)

**Impact:** Cannot study whether understanding becomes more sophisticated, cannot measure knowledge accumulation.

**Fix complexity:** MODERATE

**Fix approach:**
```python
# Add pattern evolution tracking to registry
@dataclass
class PatternEvolution:
    pattern_id: str
    timeline: List[PatternSnapshot]

@dataclass
class PatternSnapshot:
    fire_circle_id: str
    date: datetime
    agreement_score: float
    description_from_turns: List[str]  # All model descriptions
    detection_signals: List[str]
    observers: List[str]

def track_pattern_evolution(pattern_id: str) -> PatternEvolution:
    snapshots = []

    # Query all deliberations mentioning this pattern
    FOR fc IN deliberations
      FOR p IN fc.patterns
        FILTER p.pattern_type == @pattern_id

        # Get detailed descriptions from turns
        LET descriptions = (
          FOR t IN turns
            FILTER t.fire_circle_id == fc.fire_circle_id
            FILTER @pattern_id IN t.patterns_observed OR @pattern_id IN t.consensus_patterns
            RETURN {model: t.model, reasoning: t.reasoning}
        )

        snapshots.append(PatternSnapshot(
            fire_circle_id=fc.fire_circle_id,
            date=fc.created_at,
            agreement_score=p.agreement_score,
            description_from_turns=descriptions,
            observers=[p.first_observed_by]
        ))

    return PatternEvolution(pattern_id=pattern_id, timeline=snapshots)
```

---

### Requirement 7.3: Query "Which Models Specialize?"

**Current state:** Attribution exists per-deliberation (lines 468, 1468 in current_behavior.md) but no aggregation across deliberations.

**Gap category:** B - PARTIAL

**Gap description:**
- Per-deliberation attribution exists ✓
- **MISSING:** Cross-deliberation aggregation
- **MISSING:** Specialization scoring (which models discover which pattern types?)
- **MISSING:** Temporal consistency (does specialization emerge or was it always there?)

**Impact:** Cannot optimize model selection based on attack type, cannot study whether specialization emerges or reflects pretraining.

**Fix complexity:** SIMPLE

**Fix approach:**
```aql
-- Query implemented in requirements (lines 929-937)
FOR p IN patterns
  COLLECT model = p.first_observed_by, pattern_type = p.pattern_type INTO discoveries
  RETURN {
    model: model,
    pattern_type: pattern_type,
    discovery_count: LENGTH(discoveries),
    examples: discoveries[0..5],
    discovery_rate: LENGTH(discoveries) / total_deliberations_for_model
  }

-- Additional: Temporal emergence analysis
FOR p IN patterns
  FILTER p.first_observed_by == @model
  SORT p.discovery_date ASC
  RETURN {
    pattern_type: p.pattern_type,
    discovery_date: p.discovery_date,
    cumulative_count: COUNT_OVER_TIME(p.pattern_type)
  }
```

---

## Section 8: Integration with Learning Loop

### Requirement 8.1: Fire Circle → REASONINGBANK Flow

**Current state:** REASONINGBANK exists (from Instance 18), Fire Circle stores patterns, but no integration code.

**Gap category:** A - CRITICAL MISSING (same as Section 1.1)

**Gap description:**
- Fire Circle pattern extraction ✓
- REASONINGBANK storage interface exists ✓
- Observer framing retrieval exists ✓
- **MISSING:** Adapter code transforming Fire Circle patterns → REASONINGBANK entries
- **MISSING:** Pattern validation workflow
- **MISSING:** Entry quality gates

**Impact:** Learning loop doesn't close. Fire Circle patterns never improve pre-evaluation.

**Fix complexity:** MODERATE

**Fix approach:** (Same as Section 1.1 fix)

---

### Requirement 8.3: Feedback Loop Validation

**Current state:** No validation that learning loop actually works.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- **MISSING:** Detection improvement measurement (before/after REASONINGBANK)
- **MISSING:** Pattern lifecycle tracking (discovery → validation → improvement)
- **MISSING:** Learning latency measurement (miss → detection on next similar attack)
- **MISSING:** ROI calculation (improvement value vs Fire Circle cost)

**Impact:** Cannot prove that Fire Circle provides value. No evidence that continuous learning works.

**Fix complexity:** MODERATE

**Fix approach:**
```python
def measure_learning_loop_effectiveness():
    # Get attacks Fire Circle analyzed in past month
    analyzed_attacks = get_fire_circle_attacks(last_n_days=30)

    # Extract patterns that entered REASONINGBANK
    patterns = get_reasoningbank_entries_from_fire_circle(analyzed_attacks)

    # Test on similar attacks
    test_set = get_similar_attacks(analyzed_attacks, n=200)

    # Baseline: Pre-eval without Fire Circle patterns
    baseline = run_pre_eval(
        attacks=test_set,
        reasoningbank_exclude=patterns
    )

    # Enhanced: Pre-eval with Fire Circle patterns
    enhanced = run_pre_eval(
        attacks=test_set,
        reasoningbank_include=patterns
    )

    # Measure improvement
    improvement = enhanced.detection_rate - baseline.detection_rate
    cost = sum_fire_circle_costs(analyzed_attacks)
    roi = improvement / cost

    return LearningLoopMetrics(
        improvement=improvement,
        cost=cost,
        roi=roi,
        patterns_contributed=len(patterns),
        latency_days=measure_latency(analyzed_attacks)
    )
```

---

### Requirement 8.4: Measuring Fire Circle Value

**Current state:** No cost-benefit analysis or ROI calculation.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- Duration tracked ✓ (line 805 in current_behavior.md)
- **MISSING:** Cost tracking (token usage × model pricing)
- **MISSING:** Benefit measurement (detection improvement value)
- **MISSING:** Alternative cost comparison (SINGLE + manual analysis)
- **MISSING:** ROI threshold (when is Fire Circle worth it?)

**Impact:** Cannot justify Fire Circle cost. Don't know when to use Fire Circle vs simpler methods.

**Fix complexity:** MODERATE

**Fix approach:**
```python
def calculate_fire_circle_roi(time_period_days: int = 30):
    # Cost
    fire_circle_deliberations = get_deliberations(last_n_days=time_period_days)
    total_cost = sum(estimate_cost(d) for d in fire_circle_deliberations)

    # Benefit 1: Pattern discovery automation
    patterns_discovered = sum(len(d.patterns) for d in fire_circle_deliberations)
    manual_analysis_cost = patterns_discovered * RESEARCHER_HOURLY_RATE * HOURS_PER_PATTERN

    # Benefit 2: Detection improvement
    detection_improvement = measure_learning_loop_effectiveness().improvement
    improvement_value = detection_improvement * VALUE_PER_PERCENTAGE_POINT

    # Total benefit
    total_benefit = manual_analysis_cost + improvement_value

    # ROI
    roi = total_benefit / total_cost

    return FireCircleROI(
        cost=total_cost,
        benefit=total_benefit,
        roi=roi,
        patterns_per_dollar=patterns_discovered / total_cost,
        decision="continue" if roi > 2.0 else "review" if roi > 1.0 else "shutdown"
    )
```

---

## Section 9: Operational Requirements

### Requirement 9.1: Token Budget Policy

**Current state:** 1000 tokens per call (line 327), no aggregate tracking.

**Gap category:** D - OPERATIONAL BUG (matches Bug #11.1 in current_behavior.md)

**Gap description:**
- Per-call limit exists ✓
- **BUG:** No aggregate round budget
- **BUG:** No total deliberation budget
- **BUG:** Dialogue context grows unbounded across rounds
- **BUG:** No truncation strategy when context exceeds limit

**Impact:** Round 3 dialogue context will exceed model limits on complex deliberations, causing:
- Silent truncation (no error)
- Unparseable responses (JSON cut off)
- Model failures (context window exceeded)

**Fix complexity:** MODERATE

**Fix approach:**
```python
@dataclass
class TokenBudget:
    max_tokens_per_call: int = 1000
    max_tokens_per_round: int = 10000  # NEW
    max_tokens_total: int = 30000  # NEW
    max_dialogue_context: int = 8000  # NEW
    truncation_strategy: "oldest_first|summarize|abort" = "oldest_first"

def _execute_round(round_num: int, budget: TokenBudget) -> DialogueRound:
    round_tokens = 0

    for model in active_models:
        # Estimate prompt tokens
        prompt = build_prompt(round_num, model, dialogue_history)
        prompt_tokens = estimate_tokens(prompt)

        # Check dialogue context size
        dialogue_tokens = estimate_tokens(format_dialogue_context(dialogue_history))
        if dialogue_tokens > budget.max_dialogue_context:
            if budget.truncation_strategy == "oldest_first":
                dialogue_history = truncate_oldest_round(dialogue_history)
            elif budget.truncation_strategy == "summarize":
                dialogue_history = summarize_dialogue(dialogue_history)
            elif budget.truncation_strategy == "abort":
                raise TokenBudgetExceeded(round_num, dialogue_tokens)

        # Check round budget
        if round_tokens + prompt_tokens > budget.max_tokens_per_round:
            logger.warning(f"Round {round_num} approaching token budget")

        response = llm_call(prompt, max_tokens=budget.max_tokens_per_call)
        round_tokens += response.usage.total_tokens

    return round_data
```

---

### Requirement 9.2: Retry/Resilience Behavior

**Current state:** No retry logic (Bug #11.3 in current_behavior.md), RESILIENT vs STRICT modes exist.

**Gap category:** D - OPERATIONAL BUG

**Gap description:**
- Failure modes exist ✓ (RESILIENT vs STRICT)
- **BUG:** Transient failures treated as permanent (model marked zombie/excluded)
- **BUG:** No exponential backoff for rate limits
- **BUG:** No distinction between network errors and model errors
- **BUG:** No retry attempt logging

**Impact:** Network blips cause models to be excluded unnecessarily. Rate limits cause failures instead of backing off.

**Fix complexity:** MODERATE

**Fix approach:**
```python
@dataclass
class RetryPolicy:
    max_retries: int = 3
    backoff_base: float = 2.0
    retry_on: List[str] = ["timeout", "rate_limit", "server_error"]
    dont_retry: List[str] = ["invalid_request", "authentication", "parsing_failure"]
    preserve_attempts: bool = True

def _call_model_with_retry(model: str, prompt: str, policy: RetryPolicy):
    attempts = []

    for attempt in range(policy.max_retries):
        try:
            response = llm_call(model, prompt)
            attempts.append({"attempt": attempt + 1, "status": "success"})
            return response, attempts

        except Exception as e:
            error_type = classify_error(e)
            attempts.append({
                "attempt": attempt + 1,
                "status": "failed",
                "error_type": error_type,
                "error_message": str(e)
            })

            if error_type in policy.dont_retry:
                raise  # Fail-fast

            if attempt < policy.max_retries - 1:
                sleep(policy.backoff_base ** attempt)
            else:
                raise  # All retries exhausted

    # Store attempt history
    metadata["retry_attempts"] = attempts
```

---

### Requirement 9.3: Error Handling Philosophy - FAIL_VISIBLE Mode

**Current state:** STRICT and RESILIENT modes exist (lines 343-374 in current_behavior.md), but no FAIL_VISIBLE mode.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- STRICT mode exists ✓ (fail immediately)
- RESILIENT mode exists ✓ (continue with failures)
- **MISSING:** FAIL_VISIBLE mode (maximum observability)
- **MISSING:** Partial response preservation (even unparseable)
- **MISSING:** All retry attempts logged (not just final result)

**Impact:** Cannot study model failure modes in detail. Debugging prompt issues requires FAIL_VISIBLE to see what models actually returned.

**Fix complexity:** SIMPLE

**Fix approach:**
```python
class FailureMode(Enum):
    STRICT = "strict"         # Existing
    RESILIENT = "resilient"   # Existing
    FAIL_VISIBLE = "fail_visible"  # NEW

def _handle_model_failure(e: Exception, mode: FailureMode):
    if mode == FailureMode.STRICT:
        raise  # Immediate failure

    elif mode == FailureMode.RESILIENT:
        logger.error(f"Model failed: {e}")
        # Mark as zombie/excluded, continue

    elif mode == FailureMode.FAIL_VISIBLE:
        # Store EVERYTHING
        failure_data = {
            "error": str(e),
            "traceback": traceback.format_exc(),
            "partial_response": getattr(e, "partial_response", None),
            "retry_attempts": getattr(e, "attempts", []),
            "prompt_sent": prompt[:500]  # Sample
        }

        storage.store_failure(fire_circle_id, model, round_num, failure_data)
        logger.error(f"Model failed (FAIL_VISIBLE): {e}")
        # Continue with failure preserved
```

---

### Requirement 9.4: Monitoring & Metrics

**Current state:** Metadata tracked (lines 788-811 in current_behavior.md) but no monitoring queries or alerts.

**Gap category:** B - PARTIAL

**Gap description:**
- Duration tracked ✓
- Active/failed models tracked ✓
- **MISSING:** Success rate monitoring
- **MISSING:** Cost tracking
- **MISSING:** Pattern discovery rate tracking
- **MISSING:** Quality metrics (convergence, groupthink detection)
- **MISSING:** Alerting thresholds

**Impact:** Cannot monitor Fire Circle health, cannot detect degradation, cannot optimize costs.

**Fix complexity:** SIMPLE

**Fix approach:**
```python
# Add monitoring queries
def get_fire_circle_health(days: int = 7) -> HealthMetrics:
    deliberations = get_deliberations(last_n_days=days)

    return HealthMetrics(
        total_deliberations=len(deliberations),
        success_rate=sum(1 for d in deliberations if d.quorum_valid) / len(deliberations),
        avg_duration=mean([d.total_duration for d in deliberations]),
        total_cost=sum(estimate_cost(d) for d in deliberations),
        patterns_per_day=sum(len(d.patterns) for d in deliberations) / days,
        avg_convergence=mean([d.convergence_trajectory[-1] for d in deliberations]),
        parsing_failure_rate=sum(d.metadata.get("parsing_failures", 0) for d in deliberations) / len(deliberations)
    )

# Add alerting
def check_alerts(metrics: HealthMetrics):
    if metrics.success_rate < 0.8:
        alert("Fire Circle success rate below 80%")

    if metrics.avg_convergence > 0.5:
        alert("Models not converging (avg stddev > 0.5)")

    if metrics.patterns_per_day < 1:
        alert("Pattern discovery rate below 1/day")

    if metrics.parsing_failure_rate > 0.1:
        alert("Parsing failures > 10%")
```

---

## Section 10: Validation & Quality Control

### Requirement 10.1: Validation Tests - Scientific Correctness

**Current state:** Integration tests exist (18 passing tests for ArangoDB), but no validation tests for research value.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- Unit tests exist ✓ (code doesn't crash)
- Integration tests exist ✓ (pipeline works with real API)
- **MISSING:** Validation tests (Fire Circle provides research value)
- **MISSING:** Pattern discovery comparison (Fire Circle vs SINGLE mode)
- **MISSING:** Detection improvement validation (do patterns help?)
- **MISSING:** Empty chair effectiveness validation (A/B test)

**Impact:** No evidence that Fire Circle does what it claims. Cannot distinguish from expensive theater.

**Fix complexity:** COMPLEX

**Fix approach:**
```python
def test_fire_circle_discovers_patterns_single_mode_misses():
    test_attacks = sample_attacks(n=100, category="encoding_attacks")

    # Single mode
    single_results = [run_single_mode(attack) for attack in test_attacks]
    single_patterns = extract_patterns_from_reasoning(single_results)

    # Fire Circle
    fc_results = [run_fire_circle(attack) for attack in test_attacks]
    fc_patterns = [p for fc in fc_results for p in fc.patterns]

    # Compare
    novel_patterns = set(fc_patterns) - set(single_patterns)

    assert len(novel_patterns) > 0, "Fire Circle should discover patterns SINGLE mode misses"
    assert len(novel_patterns) >= len(fc_patterns) * 0.2, "At least 20% should be novel"

def test_fire_circle_patterns_improve_detection():
    # Get patterns from past Fire Circles
    patterns = get_fire_circle_patterns(last_n_days=30)

    # Test set
    test_attacks = get_similar_attacks(patterns, n=200)

    # Baseline
    baseline = run_pre_eval(test_attacks, reasoningbank_exclude=patterns)

    # Enhanced
    enhanced = run_pre_eval(test_attacks, reasoningbank_include=patterns)

    improvement = enhanced.detection_rate - baseline.detection_rate

    assert improvement > 0.05, "Fire Circle patterns should improve detection by >5%"

def test_empty_chair_provides_unique_value():
    test_attacks = sample_attacks(n=50)

    with_empty_chair = [run_fire_circle(a, empty_chair=True) for a in test_attacks]
    without_empty_chair = [run_fire_circle(a, empty_chair=False) for a in test_attacks]

    unique_patterns = count_unique_to_empty_chair(with_empty_chair)

    assert unique_patterns > 0, "Empty chair should discover unique patterns"
```

---

### Requirement 10.2: Failure Modes to Detect

**Current state:** No automatic detection of groupthink, theater, or context saturation.

**Gap category:** A - CRITICAL MISSING (same as Section 2.2)

**Gap description:** (Same as Section 2.2 gap)

**Impact:** (Same as Section 2.2 impact)

**Fix complexity:** SIMPLE

**Fix approach:** (Same as Section 2.2 fix)

---

### Requirement 10.4: Auditing Deliberation Authenticity

**Current state:** No authenticity auditing exists.

**Gap category:** B - PARTIAL

**Gap description:**
- Reasoning text stored ✓
- **MISSING:** Reasoning diversity analysis (semantic similarity)
- **MISSING:** Temporal consistency analysis (did models respond to each other?)
- **MISSING:** Pattern originality analysis (discovered vs regurgitated from prompt)

**Impact:** Cannot detect performative deliberation. Models might be echoing prompt expectations without genuine reasoning.

**Fix complexity:** MODERATE

**Fix approach:**
```python
def audit_reasoning_diversity(fc: FireCircleResult) -> float:
    reasonings = [e.reasoning for round in fc.dialogue_history
                  for e in round.evaluations]

    embeddings = [embed(r) for r in reasonings]

    similarities = []
    for i, emb1 in enumerate(embeddings):
        for j, emb2 in enumerate(embeddings[i+1:]):
            similarities.append(cosine_similarity(emb1, emb2))

    diversity_score = 1 - mean(similarities)
    return diversity_score

def audit_temporal_consistency(fc: FireCircleResult) -> Dict:
    # Did models respond to each other?
    for model, trajectory in group_by_model(fc.dialogue_history):
        f_change = trajectory[-1].falsehood - trajectory[0].falsehood

        if abs(f_change) > 0.3:
            # Check if reasoning mentions dialogue
            mentions_others = any(
                "other" in t.reasoning.lower() or
                "previous" in t.reasoning.lower()
                for t in trajectory[1:]
            )

            if not mentions_others:
                # Changed mind without engaging
                logger.warning(f"Model {model} changed F by {f_change} without referencing dialogue")

def audit_pattern_originality(fc: FireCircleResult) -> Dict:
    # Are patterns from prompt or discovered?
    prompt_text = fc.dialogue_history[0].prompt_used
    prompt_patterns = extract_pattern_keywords(prompt_text)

    discovered = set(p.pattern_type for p in fc.patterns)

    overlap = prompt_patterns & discovered
    novel = discovered - prompt_patterns

    return {
        "total_patterns": len(discovered),
        "novel_patterns": len(novel),
        "originality_ratio": len(novel) / len(discovered) if discovered else 0
    }
```

---

## Section 11: Research Outputs

### Requirement 11.3: Demonstrating Value Over Simpler Approaches

**Current state:** No comparative validation exists.

**Gap category:** A - CRITICAL MISSING

**Gap description:**
- Fire Circle implementation exists ✓
- SINGLE mode exists ✓
- PARALLEL mode exists ✓
- **MISSING:** Comparative experiments (Fire Circle vs alternatives)
- **MISSING:** Time-to-patterns measurement
- **MISSING:** Cost-benefit analysis vs manual analysis
- **MISSING:** Detection improvement comparison

**Impact:** Cannot justify Fire Circle's complexity and cost. No evidence it's better than simpler approaches.

**Fix complexity:** COMPLEX

**Fix approach:**
```python
def validate_fire_circle_value():
    test_attacks = sample_attacks(n=200, stratified_by_category=True)

    # Method 1: Fire Circle
    fc_start = time.time()
    fc_results = [run_fire_circle(a) for a in test_attacks]
    fc_duration = time.time() - fc_start
    fc_patterns = [p for fc in fc_results for p in fc.patterns]
    fc_cost = sum(estimate_cost(fc) for fc in fc_results)

    # Method 2: SINGLE + manual analysis
    single_start = time.time()
    single_results = [run_single_mode(a) for a in test_attacks]
    single_duration = time.time() - single_start

    researcher_start = time.time()
    manual_patterns = researcher_analyzes_logs(single_results)
    researcher_duration = time.time() - researcher_start
    researcher_cost = researcher_duration * HOURLY_RATE

    single_total_cost = sum(estimate_cost(r) for r in single_results) + researcher_cost

    # Method 3: PARALLEL
    parallel_results = [run_parallel_mode(a) for a in test_attacks]
    parallel_cost = sum(estimate_cost(r) for r in parallel_results)

    # Compare detection improvement
    fc_improvement = measure_detection_improvement(fc_patterns)
    manual_improvement = measure_detection_improvement(manual_patterns)

    return ComparisonResults(
        pattern_discovery={
            "fire_circle": len(fc_patterns),
            "manual": len(manual_patterns),
            "parallel": 0
        },
        detection_improvement={
            "fire_circle": fc_improvement,
            "manual": manual_improvement,
            "parallel": measure_ensemble_improvement(parallel_results)
        },
        cost={
            "fire_circle": fc_cost,
            "manual": single_total_cost,
            "parallel": parallel_cost
        },
        time_to_patterns={
            "fire_circle": fc_duration,
            "manual": single_duration + researcher_duration,
            "parallel": "N/A"
        },
        roi={
            "fire_circle": fc_improvement / fc_cost,
            "manual": manual_improvement / single_total_cost
        }
    )
```

---

## Section 12: Design Principles

### Requirement 12.1: No Theater

**Current state:** No theater detection implemented.

**Gap category:** A - CRITICAL MISSING (same as Sections 2.2, 10.2, 10.4)

**Gap description:** (Combined from previous sections)

**Impact:** Cannot distinguish genuine deliberation from performative compliance.

**Fix complexity:** MODERATE

**Fix approach:** (Combined from Sections 2.2, 10.2, 10.4 fixes)

---

### Requirement 12.2: Empirical Integrity

**Current state:** Complete provenance stored but not enforced as requirement.

**Gap category:** E - SATISFIED

**Gap description:**
- Complete deliberation data stored ✓ (lines 584-613 in current_behavior.md)
- API call logging exists ✓
- Prompt versioning possible ✓
- Reproducibility supported ✓

**Impact:** None - requirement is met.

**Fix complexity:** N/A

**Fix approach:** None needed. Maintain current implementation.

---

### Requirement 12.3: Fail-Fast

**Current state:** STRICT mode exists, quorum failures abort, but quality checks don't exist.

**Gap category:** B - PARTIAL

**Gap description:**
- STRICT mode exists ✓
- Quorum failures abort ✓ (lines 731-745)
- **MISSING:** Quality gates for REASONINGBANK entry
- **MISSING:** Pattern validation before acceptance
- **MISSING:** Early warning alerts

**Impact:** Low-quality patterns can enter REASONINGBANK without validation.

**Fix complexity:** SIMPLE

**Fix approach:**
```python
def enforce_quality_gates(pattern: AttackPattern) -> bool:
    # Gate 1: Actionability
    if len(pattern.detection_signals) == 0:
        logger.error(f"Pattern {pattern.pattern_id} rejected: no detection signals")
        return False

    # Gate 2: Specificity
    if is_generic(pattern):
        logger.error(f"Pattern {pattern.pattern_id} rejected: too generic")
        return False

    # Gate 3: Empirical validation
    quality = validate_pattern_empirically(pattern)
    if not quality.validated:
        logger.error(f"Pattern {pattern.pattern_id} rejected: validation failed")
        return False

    return True

def add_to_reasoningbank(pattern: AttackPattern):
    if not enforce_quality_gates(pattern):
        raise ValueError("Pattern failed quality gates")

    reasoningbank.store(pattern)
```

---

### Requirement 12.4: Agency Over Constraint

**Current state:** Observer framing used (line 956 in current_behavior.md), self-reported patterns, dialogue-based consensus.

**Gap category:** E - SATISFIED

**Gap description:**
- Observer framing ✓
- Self-reported patterns ✓ (lines 468-473)
- Dialogue-based consensus ✓ (max(F) from deliberation)
- REASONINGBANK retrieval exists ✓ (from Instance 18)

**Impact:** None - requirement is met.

**Fix complexity:** N/A

**Fix approach:** None needed. Continue current design.

---

## Prioritization

### P0 - Blockers (Must Fix Before Fire Circle Is Usable)

1. **Token budget tracking (Section 9.1)** - MODERATE
   - Round 3 deliberations will break on complex attacks
   - Silent truncation causes unparseable responses
   - Must implement aggregate budget + truncation strategy

2. **Learning loop integration (Section 1.1, 8.1)** - MODERATE
   - Fire Circle → REASONINGBANK adapter code missing
   - Core research hypothesis cannot be tested
   - Must create pattern extraction + validation workflow

3. **Pattern validation (Section 6.4, 10.1)** - MODERATE
   - No empirical testing of whether patterns improve detection
   - Cannot distinguish valuable patterns from noise
   - Must implement A/B testing framework

4. **Dissent storage (Section 5.2)** - MODERATE
   - Cannot study minority-to-consensus evolution
   - Core research question unanswerable
   - Must add dissents collection to ArangoDB

5. **Quality gate enforcement (Section 12.3)** - SIMPLE
   - Low-quality patterns can pollute REASONINGBANK
   - Must reject generic/unvalidated patterns

6. **Cost tracking (Section 8.4)** - MODERATE
   - Cannot calculate ROI or justify Fire Circle usage
   - Must estimate tokens + model pricing

7. **Bad deliberation detection (Section 2.2)** - SIMPLE
   - Cannot filter theater from dataset
   - Must detect groupthink, context saturation, generic patterns

---

### P1 - Research Critical (Required for Longitudinal Analysis)

1. **Pattern registry (Section 6.2)** - MODERATE
   - Cross-deliberation pattern tracking missing
   - Cannot study pattern evolution
   - Must replace flat taxonomy with structured registry

2. **Cross-deliberation queries (Section 7.1, 7.2, 7.3)** - COMPLEX
   - Longitudinal analysis impossible
   - Must implement pattern evolution, dissent vindication, specialization queries

3. **Multi-metric consensus (Section 5.1)** - SIMPLE
   - Only max(F) preserved, full distribution lost
   - Cannot study convergence dynamics
   - Must store both detection signal and research metrics

4. **Dissent quality prediction (Section 5.3)** - COMPLEX
   - Cannot prioritize which dissents to investigate
   - Must build classifier for valuable vs noise dissents

5. **Empty chair validation (Section 4.3)** - MODERATE
   - No evidence empty chair provides unique value
   - Must implement A/B testing and perspective analysis

6. **Pattern attribution (Section 6.3)** - MODERATE
   - Cannot track discoverer vs elaborator vs validator
   - Must implement multi-role attribution

7. **Model specialization tracking (Section 7.3)** - SIMPLE
   - Cannot optimize model selection
   - Must aggregate attribution across deliberations

8. **Feedback loop validation (Section 8.3)** - MODERATE
   - No proof learning loop works
   - Must measure detection improvement over time

9. **Fire Circle ROI (Section 8.4)** - MODERATE
   - Cannot justify vs simpler approaches
   - Must implement comparative experiments

10. **Research value validation (Section 11.3)** - COMPLEX
    - No evidence Fire Circle beats alternatives
    - Must run head-to-head comparisons

11. **Model diversity optimization (Section 3.1)** - MODERATE
    - Manual model selection may miss diversity
    - Must implement diversity scoring

12. **Dynamic circle composition (Section 3.3)** - MODERATE
    - Cannot route attacks to specialist models
    - Must implement core + rotational model sets

---

### P2 - Quality Improvements (Make Fire Circle More Robust)

1. **Retry logic (Section 9.2)** - MODERATE
   - Transient failures treated as permanent
   - Must implement exponential backoff

2. **FAIL_VISIBLE mode (Section 9.3)** - SIMPLE
   - Cannot study model failure modes
   - Must preserve all errors and partial responses

3. **Monitoring & alerting (Section 9.4)** - SIMPLE
   - Cannot detect degradation
   - Must implement health checks and alerts

4. **Epistemic quality measurement (Section 2.1)** - MODERATE
   - Cannot detect performative deliberation
   - Must measure reasoning diversity

5. **Authenticity auditing (Section 10.4)** - MODERATE
   - Cannot distinguish genuine vs performative
   - Must implement semantic similarity analysis

6. **Empty chair rotation fix (Section 4.2)** - SIMPLE
   - Current rotation dilutes coherence
   - Should use consistent model per deliberation

7. **Model failure analysis (Section 3.5)** - SIMPLE
   - Failures logged but not analyzed
   - Must query which models fail on which attacks

8. **Automatic triggering (Section 2.3)** - MODERATE
   - Fire Circle invoked manually
   - Should trigger on pre/post divergence

---

### P3 - Future Enhancements (Nice-to-Have)

1. **Hybrid pattern extraction (Section 6.1)** - COMPLEX
   - Self-reporting + automatic extraction
   - Catch patterns mentioned but not in JSON

2. **Delphi method consensus (Section 5.1)** - MODERATE
   - Track how dialogue changes minds
   - Alternative to current max(F)

3. **Attack-type routing (Section 3.3)** - MODERATE
   - Dynamic specialist selection
   - Optimize for attack category

4. **Pattern supersession (Section 6.2)** - SIMPLE
   - Track when patterns are replaced
   - Refinement history

5. **Dissent-weighted consensus (Section 5.1)** - MODERATE
   - Flag unresolved epistemic questions
   - Human review trigger

---

## Easiest Wins (High Value, Low Complexity)

1. **Quality gate enforcement (P0)** - SIMPLE, blocks bad patterns
2. **Bad deliberation detection (P0)** - SIMPLE, filters theater
3. **Multi-metric consensus (P1)** - SIMPLE, enables research analysis
4. **Empty chair rotation fix (P2)** - SIMPLE, improves coherence
5. **Model failure analysis (P2)** - SIMPLE, query already exists
6. **FAIL_VISIBLE mode (P2)** - SIMPLE, better debugging
7. **Monitoring & alerting (P2)** - SIMPLE, catch degradation
8. **Model specialization tracking (P1)** - SIMPLE, query aggregation

---

## Architectural Issues (Fundamental Redesign vs Incremental)

### Don't Rebuild:
- Core deliberation flow is sound (rounds, zombie handling, empty chair)
- max(F) consensus is correct for detection
- ArangoDB schema is well-designed
- Integration points exist (just need connecting)

### Do Refactor:
- **Pattern taxonomy:** Flat → structured registry with provenance
- **Consensus:** Single evaluation → multi-metric with full distribution
- **Dissent handling:** Implicit → first-class objects with tracking
- **Token budget:** Per-call → multi-level with truncation
- **Empty chair:** Rotation → consistent per deliberation

### New Components Needed:
- Fire Circle → REASONINGBANK adapter
- Pattern validation framework
- Longitudinal query layer
- Comparative validation experiments
- Quality detection (groupthink, theater, saturation)

---

## Dependency Chains

**Critical path for research value:**

```
1. Fix token budget (P0) → enables complex deliberations
   ↓
2. Implement quality detection (P0) → filters bad data
   ↓
3. Add dissent storage (P0) → enables longitudinal tracking
   ↓
4. Build pattern registry (P1) → cross-deliberation linking
   ↓
5. Implement Fire Circle → REASONINGBANK (P0) → closes learning loop
   ↓
6. Validate patterns empirically (P0) → proves value
   ↓
7. Measure learning loop effectiveness (P1) → demonstrates improvement
   ↓
8. Run comparative experiments (P1) → justifies cost
```

**Cannot do Y until X is fixed:**
- Dissent vindication queries (P1) require dissent storage (P0)
- Pattern evolution queries (P1) require pattern registry (P1)
- Empty chair validation (P1) requires quality detection (P0)
- ROI calculation (P1) requires cost tracking (P0)
- Comparative validation (P1) requires pattern validation (P0)

---

## Recommendations

### Rebuild vs Refactor?

**REFACTOR** - Don't rebuild from scratch.

**Decision criteria met:**
- Core mechanism is sound (deliberation flow, consensus, storage)
- Gaps are integration and analysis, not fundamental design flaws
- Token budget and retry logic are additive improvements
- Pattern registry and dissent tracking are schema extensions
- Fire Circle → REASONINGBANK is new glue code, not replacement

**Rebuild would be warranted if:**
- max(F) consensus was wrong (it's not - validated in Instance 13)
- Dialogue structure was broken (it's not - rounds work)
- Storage schema was insufficient (it's not - ArangoDB is good)
- Empty chair mechanism was fundamentally flawed (rotation is suboptimal but not broken)

**Refactor sequence:** Fix P0 blockers → Add P1 research capabilities → Optimize P2 quality

---

### Implementation Approach

**Phase 1: Make Fire Circle Usable (P0 Blockers)**

*Duration: 2-3 weeks*
*Outcome: Fire Circle produces validated patterns that enter REASONINGBANK*

1. Token budget tracking + truncation (Section 9.1)
2. Bad deliberation detection (Section 2.2)
3. Quality gate enforcement (Section 12.3)
4. Pattern validation framework (Section 6.4)
5. Fire Circle → REASONINGBANK adapter (Section 1.1, 8.1)
6. Cost tracking (Section 8.4)
7. Dissent storage (Section 5.2)

**Phase 2: Enable Research Questions (P1 Critical)**

*Duration: 4-6 weeks*
*Outcome: Can answer longitudinal questions about pattern evolution, dissent vindication, model specialization*

1. Pattern registry (Section 6.2)
2. Multi-metric consensus (Section 5.1)
3. Cross-deliberation queries (Section 7.1-7.3)
4. Pattern attribution (Section 6.3)
5. Model specialization tracking (Section 7.3)
6. Feedback loop validation (Section 8.3)
7. Empty chair validation (Section 4.3)
8. Fire Circle ROI measurement (Section 8.4)

**Phase 3: Validate Research Value (P1 Critical)**

*Duration: 2-3 weeks*
*Outcome: Empirical evidence Fire Circle beats simpler approaches*

1. Comparative experiments (Section 11.3)
2. Detection improvement validation (Section 10.1)
3. A/B tests (empty chair, Fire Circle vs alternatives)

**Phase 4: Operational Hardening (P2 Quality)**

*Duration: 2 weeks*
*Outcome: Fire Circle is production-ready and monitored*

1. Retry logic (Section 9.2)
2. FAIL_VISIBLE mode (Section 9.3)
3. Monitoring & alerting (Section 9.4)
4. Epistemic quality measurement (Section 2.1)
5. Authenticity auditing (Section 10.4)

**Total estimated duration: 10-14 weeks**

---

### Validation Strategy

**How do we know when gaps are closed?**

**P0 Blockers:**
- Token budget: Run 10 complex deliberations (3 rounds, LARGE circle), zero truncation failures
- Learning loop: Fire Circle patterns improve pre-evaluation by >5% on test set
- Pattern validation: <5% false positive rate, >10% detection improvement for validated patterns
- Dissent storage: Query "which dissents became consensus?" returns results
- Quality gates: Zero generic patterns enter REASONINGBANK
- Cost tracking: ROI calculation produces real numbers

**P1 Research Critical:**
- Pattern registry: Can track same pattern across 10+ deliberations
- Cross-deliberation queries: All queries from Section 7 return results
- Multi-metric consensus: Can plot F-score distribution and convergence trajectory
- Dissent quality: Classifier achieves >70% accuracy on valuable vs noise
- Empty chair validation: A/B test shows statistically significant difference
- Model specialization: Query identifies at least 2 models with distinct specializations
- Feedback loop validation: Detection rate improves month-over-month for 3 months
- Fire Circle ROI: ROI > 2.0 vs. alternatives

**P2 Quality:**
- Retry logic: Transient failures retried, success rate >95%
- FAIL_VISIBLE mode: Can debug prompt issues from stored partial responses
- Monitoring: Alerts fire when success rate < 80%, patterns/day < 1
- Epistemic quality: Groupthink detected in test cases
- Authenticity: Can distinguish high vs low diversity deliberations

**Test suites:**

```python
# P0 validation
def test_token_budget_prevents_truncation():
    complex_attack = load_attack("multi_layer_encoding_long_context")
    fc = run_fire_circle(complex_attack, circle_size=LARGE, max_rounds=3)
    assert all(len(e.reasoning) > 100 for e in all_evaluations(fc))

def test_learning_loop_improves_detection():
    baseline_rate = run_pre_eval_without_reasoningbank(test_set)
    run_fire_circle_on_training_set()  # Generate patterns
    enhanced_rate = run_pre_eval_with_reasoningbank(test_set)
    assert enhanced_rate - baseline_rate > 0.05

# P1 validation
def test_pattern_evolution_tracking():
    pattern = create_test_pattern("polite_extraction")
    deliberate_on_attacks_mentioning(pattern, n=10)
    evolution = query_pattern_evolution(pattern.pattern_id)
    assert len(evolution.timeline) >= 10

def test_dissent_vindication_query():
    dissents = query_dissents_that_became_consensus()
    assert len(dissents) > 0

# P2 validation
def test_retry_logic_handles_transients():
    with mock_transient_failures(rate=0.5):
        fc = run_fire_circle(test_attack)
        assert fc.metadata["retry_attempts"] > 0
        assert fc.quorum_valid == True
```

---

## Summary

**Key Findings:**

**Biggest Gaps (Research Blockers):**
1. Token budget breaks Round 3 (silent truncation)
2. Learning loop incomplete (Fire Circle → REASONINGBANK missing)
3. Pattern validation doesn't exist (no empirical testing)
4. Dissent tracking impossible (not stored as objects)
5. Longitudinal analysis requires pattern registry

**Easiest Wins (High Value, Low Effort):**
1. Quality gates (block bad patterns - SIMPLE)
2. Theater detection (filter noise - SIMPLE)
3. Multi-metric consensus (enable research - SIMPLE)
4. Empty chair consistency (improve coherence - SIMPLE)
5. Model failure analysis (query exists - SIMPLE)

**Architecture Assessment:**
- **Don't rebuild** - Core mechanism is sound
- **Do refactor** - Pattern taxonomy, consensus structure, dissent handling
- **Add new components** - REASONINGBANK adapter, validation framework, longitudinal queries

**Implementation Path:**
1. Phase 1 (2-3 weeks): Fix P0 blockers → Make Fire Circle usable
2. Phase 2 (4-6 weeks): Add P1 capabilities → Enable research questions
3. Phase 3 (2-3 weeks): Validate value → Prove Fire Circle beats alternatives
4. Phase 4 (2 weeks): Harden operations → Production-ready monitoring

**Critical Dependencies:**
- Dissent queries require dissent storage
- Pattern evolution requires pattern registry
- ROI requires cost tracking
- All research requires learning loop closure

**Success Metrics:**
- P0: Fire Circle patterns improve detection >5%, zero low-quality entries
- P1: Can answer all longitudinal questions, ROI > 2.0 vs alternatives
- P2: Success rate >95%, alerts catch degradation

**Total effort: 10-14 weeks to fully close gaps and validate research value.**

---

**Next Steps:**

1. Review this gap analysis with Tony
2. Prioritize which P0 gaps to fix first
3. Create implementation tasks for Phase 1
4. Begin with token budget + quality gates (highest impact, clear scope)
5. Use FAIL_VISIBLE mode during development (maximum observability)

Fire Circle has good bones. The deliberation mechanism works. Storage is sound. Integration points exist. What's missing is the connective tissue - pattern validation, learning loop closure, longitudinal tracking. Fix the P0 blockers and Fire Circle becomes a research instrument. Ignore them and it's expensive data collection with no proof of value.
