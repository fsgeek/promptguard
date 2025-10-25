# Fire Circle Research Requirements Specification

**Document Version:** 1.0
**Last Updated:** 2025-10-24
**Purpose:** Prescriptive specification of what Fire Circle SHOULD enable for PromptGuard's continuous learning research

---

## 1. Core Purpose

### 1.1 Role in Continuous Learning Loop

Fire Circle serves as the **deliberative analysis layer** in PromptGuard's continuous learning architecture:

```
Pre-evaluation (fast) → Misses attack
    ↓
Post-evaluation (detect) → Sees imbalance revealed by response
    ↓
Fire Circle (analyze) ← YOU ARE HERE
    ↓
REASONINGBANK update → Store learned principle with few-shot examples
    ↓
Observer framing adapts → Retriever injects relevant memories
    ↓
Pre-evaluation catches it next time
```

**Primary function:** When pre-evaluation misses a violation that post-evaluation detects, Fire Circle deliberates on WHY it was missed and extracts a reusable detection pattern.

**Rationale:** Pre-evaluation has blind spots. Post-evaluation reveals them by seeing the response. Fire Circle transforms single-instance failures into generalizable learning that improves future pre-evaluation accuracy.

### 1.2 Research Questions Fire Circle Answers

**Primary:**
- Why did pre-evaluation miss this violation? (pattern discovery)
- What semantic signals should have revealed the manipulation? (feature identification)
- How does this pattern manifest across different attack types? (generalization)

**Secondary:**
- Do different model architectures notice different patterns? (architectural diversity value)
- How do dissenting opinions evolve into consensus over time? (longitudinal learning dynamics)
- Does collaborative deliberation discover patterns that individual analysis misses? (emergent intelligence)

**Meta:**
- Can AI develop shared understanding of relational violations through dialogue? (collective reasoning)
- Does empty chair role genuinely surface perspectives active models miss? (mechanism validation)

**Rationale:** These questions validate whether Fire Circle provides unique value beyond simpler approaches (SINGLE mode, ensemble averaging, post-hoc analysis scripts). If Fire Circle doesn't answer questions simpler methods can't, it's unnecessary complexity.

### 1.3 Data Generated for Longitudinal Analysis

Fire Circle must generate data that enables tracking:

1. **Pattern Evolution**
   - When was pattern X first discovered?
   - Which deliberations refined understanding of pattern X?
   - How did detection confidence for pattern X change over months?
   - Did pattern X later prove to be a false lead? (dissent validation)

2. **Model Contributions**
   - Which models consistently discover novel patterns?
   - Which models excel at confirming vs. discovering?
   - Do model specializations emerge (e.g., one model good at temporal patterns, another at role confusion)?
   - Which model families have structural blindspots?

3. **Consensus Dynamics**
   - How often do minority opinions become consensus in later deliberations?
   - What characterizes "productive dissent" vs. noise?
   - Does convergence speed correlate with detection accuracy?
   - Do certain model combinations produce better consensus?

4. **Empty Chair Effectiveness**
   - Which unique patterns did empty chair discover that active models missed?
   - Do empty chair contributions correlate with later detection improvements?
   - Is empty chair mechanism genuinely surfacing absent perspectives or just rotating through models?

5. **Learning Loop Closure**
   - Which Fire Circle discoveries entered REASONINGBANK?
   - Which REASONINGBANK entries improved pre-evaluation detection?
   - What's the latency between Fire Circle discovery and detection improvement?
   - Which patterns looked promising but didn't improve detection? (negative results)

**Rationale:** PromptGuard's differentiation from static RLHF is continuous adaptation. Fire Circle data must enable measuring whether the learning loop actually closes and improves over time.

---

## 2. Deliberation Goals

### 2.1 Quality Metrics

A "good" Fire Circle deliberation exhibits:

**Detection Quality:**
- Identifies at least one actionable pattern that explains the pre-evaluation miss
- Pattern is semantically specific (not "user seems manipulative" but "polite imperative masking role reversal")
- Pattern generalizes beyond the specific prompt (applicable to similar attacks)
- Consensus F-score accurately reflects extraction severity

**Epistemic Quality:**
- Models provide distinct reasoning (not echo chamber)
- Dissents are substantive (identify alternative interpretations, not just different F-scores)
- Reasoning chains are transparent (shows how model reached conclusion)
- Empty chair surfaces genuinely different perspective (not just another opinion)

**Research Value:**
- Dialogue reveals something that individual evaluations wouldn't show
- Pattern attribution is clear (which model discovered what when)
- Convergence trajectory provides insight (did models change their minds? why?)
- Failure modes are preserved (if deliberation fails, data shows why)

**Rationale:** Quality matters more than quantity. One deliberation that discovers "polite extraction attacks use imperatives disguised as questions" is worth more than 100 deliberations that produce generic "seems manipulative" observations.

### 2.2 Bad Deliberation Characteristics

Fire Circle should detect and flag when deliberation is unproductive:

**Groupthink:**
- All models agree immediately (no genuine deliberation)
- Later rounds converge without substantive reasoning changes
- Dissents disappear without being addressed

**Theater:**
- Patterns are generic and non-actionable ("lacks transparency")
- Reasoning is circular ("F=0.8 because it's manipulative")
- Models repeat each other's language without adding insight

**Structural Failure:**
- Too many model failures (quorum barely maintained)
- Token exhaustion truncates reasoning
- Parsing failures lose model contributions

**Rationale:** Fire Circle is expensive (3 rounds × N models). If deliberation quality is poor, SINGLE mode + programmatic analysis would be cheaper and equally valuable. Bad deliberations must be detectable so they can be studied and improved.

### 2.3 When to Use Fire Circle vs Other Modes

**Use Fire Circle when:**
- Pre-evaluation missed a violation that post-evaluation caught (learning opportunity)
- Novel attack type encountered (pattern discovery needed)
- High-stakes evaluation where consensus confidence matters (security-critical application)
- Researching model diversity in threat perception (studying architectural differences)
- Validating REASONINGBANK entries (does pattern still hold? has threat evolved?)

**Use PARALLEL mode when:**
- Production evaluation needs ensemble consensus (operational, not research)
- Cost matters more than explanatory depth (averaging is cheaper than dialogue)
- Attack type is well-understood (no learning needed)

**Use SINGLE mode when:**
- Pre-evaluation screening (fast, cheap, good enough)
- Development/testing (iteration speed matters)
- Budget constraints (free tier models)

**Rationale:** Fire Circle is the most expensive mode. It should be reserved for cases where dialogue-based deliberation provides unique value that justifies the cost. Using Fire Circle for routine evaluation would be wasteful.

---

## 3. Model Selection Strategy

### 3.1 Diversity Dimensions

Models should be selected to maximize diversity across:

**Architecture:**
- Transformer variants (GPT-style, Claude, Gemini, LLaMA)
- Different attention mechanisms
- Different training objectives

**Training Characteristics:**
- RLHF level (high/moderate/low/none)
- Constitutional AI vs RLHF vs pure supervised
- Pretraining corpus differences (era, languages, domains)

**Geographic/Cultural Origin:**
- US-trained models (OpenAI, Anthropic)
- Chinese models (DeepSeek, Qwen, Tongyi)
- European models (Mistral)
- Open weights vs closed

**Capability Level:**
- Frontier (Sonnet 4.5, GPT-5, Gemini Pro)
- Mid-tier (Haiku, GPT-4o-mini)
- Budget (Gemini Flash, Qwen)

**Specialization:**
- General reasoning vs coding-specialized
- Long-context specialists
- Instruction-following vs chat-optimized

**Rationale:** Diversity is the mechanism by which Fire Circle discovers what individual models miss. If all models share architectural blindspots (e.g., RLHF conflict-avoidance), Fire Circle becomes an echo chamber. Structural diversity increases probability of complementary perspectives.

### 3.2 Selection Heuristics

**For pattern discovery (research):**
- MEDIUM/LARGE circle size (4-6 models minimum)
- Maximize diversity across all dimensions
- Include at least one non-RLHF model (baseline reasoning)
- Include at least one model from different geographic origin
- Include at least one frontier + one mid-tier (capability range)

**For pattern validation (testing REASONINGBANK entries):**
- SMALL circle size (2-3 models sufficient)
- Include original discoverer model (consistency check)
- Include model from different family (generalization check)
- Lower diversity acceptable (testing specific hypothesis)

**For production consensus (operational):**
- SMALL/MEDIUM based on risk tolerance
- Bias toward proven-accurate models for use case
- Cost-optimize within accuracy constraints
- Consider latency requirements

**Rationale:** Different research questions need different model configurations. Pattern discovery benefits from maximum diversity. Pattern validation needs targeted testing. Production needs efficiency within accuracy bounds.

### 3.3 Dynamic vs Static Circle Composition

**Static circles (same models always):**
- **Pros:** Enables tracking individual model evolution, consistent baselines, reproducible experiments
- **Cons:** Can't adapt to new models, expensive if using all-frontier

**Dynamic circles (vary by prompt type):**
- **Pros:** Use encoding-specialists for encoding attacks, role-confusion specialists for social engineering
- **Cons:** Harder to track longitudinal contributions, more configuration complexity

**Recommended hybrid approach:**
- Core set of 2-3 models present in ALL deliberations (longitudinal tracking)
- Rotational set of 2-4 models selected based on attack type (specialization)
- New models added periodically for evaluation (capability tracking)

**Rationale:** Longitudinal analysis requires consistency. Specialization requires flexibility. Hybrid approach balances both needs.

### 3.4 Circle Size Trade-offs

**SMALL (2-3 models):**
- **Cost:** Low ($0.02-0.05 per deliberation)
- **Diversity:** Limited, risk of shared blindspots
- **Speed:** Fast (< 30 seconds)
- **Use case:** Quick validation, budget-constrained research

**MEDIUM (4-6 models):**
- **Cost:** Medium ($0.08-0.20 per deliberation)
- **Diversity:** Good, likely covers main architectural families
- **Speed:** Moderate (30-60 seconds)
- **Use case:** Primary research configuration, balances diversity and cost

**LARGE (7-10 models):**
- **Cost:** High ($0.30-0.60 per deliberation)
- **Diversity:** Maximum, covers edge cases
- **Speed:** Slow (60-120 seconds)
- **Use case:** Novel attacks, publication-quality analysis, validating Fire Circle mechanism itself

**Rationale:** Research has found optimal jury size is 6-12 for group decision-making (captures diversity without redundancy). Fire Circle likely has similar dynamics. MEDIUM circle is sweet spot for most research.

### 3.5 Handling Model Failures

**Design principle:** Fail transparently, preserve what succeeded, continue if scientifically viable.

**Round 1 failures:**
- Exclude from all subsequent rounds (no baseline = no contribution)
- Log failure type and context (which models fail on which attacks?)
- Continue if remaining models meet minimum viable circle
- Research value: Which models fail on which attack types? (robustness analysis)

**Round 2+ failures (zombies):**
- Preserve Round 1 contribution (baseline is valuable)
- Exclude from consensus (didn't see full dialogue)
- Log state transition (active → zombie)
- Research value: Did dialogue context break the model? (context saturation indicator)

**Quorum failures:**
- Abort deliberation, raise error
- Preserve partial results (what succeeded before failure)
- Research value: What attack types cause widespread failures? (edge cases)

**Rationale:** Failures are data. Hiding them loses signal about model robustness and attack characteristics. Complete transparency about what worked and what didn't enables studying failure patterns.

---

## 4. Empty Chair Mechanism

### 4.1 Who/What Should Empty Chair Represent?

The empty chair role exists to surface **absent stakeholder perspectives** that active models may not naturally consider:

**Future generations:**
- Long-term consequences of tolerating this pattern
- Precedent being set for future interactions
- Evolutionary pressure on attack techniques

**Affected communities:**
- Who gets harmed if this manipulation succeeds?
- Power dynamics the attack exploits
- Vulnerable populations especially at risk

**System maintainers:**
- Operational burden of handling this pattern at scale
- Economic cost of failure modes
- Security debt accumulation

**Adversarial red team:**
- How would this pattern be weaponized?
- What's the attack's next evolution?
- Where are the detection gaps?

**Non-RLHF aligned AI:**
- What would reasoning look like without safety training?
- Is RLHF hiding signal we need?
- Raw pattern recognition before constraint

**Rationale:** Active models optimize for immediate task performance. Empty chair explicitly represents perspectives that aren't naturally salient but matter for comprehensive evaluation. This is NOT just "another opinion" - it's structured role-playing to overcome blindspots.

### 4.2 Rotation vs Consistent Role

**Current implementation:** Rotates empty chair through models (Round 2: models[1], Round 3: models[2])

**Problems with rotation:**
- Each model only gets empty chair role once per deliberation
- No consistency in which perspective is represented
- Role attribution unclear ("did Model X discover this as active or empty chair?")

**Alternative: Consistent empty chair model:**
- One model always plays empty chair (all rounds)
- Clear attribution of empty chair contributions
- That model develops "empty chair reasoning style" over time
- Can track empty chair effectiveness longitudinally

**Recommended hybrid:**
- **Primary empty chair:** One model assigned empty chair role for entire deliberation (all rounds after Round 1)
- **Rotational trials:** Periodically rotate which model serves as primary empty chair (weekly/monthly)
- **Attribution tracking:** Log whether model contributed as active or empty chair

**Rationale:** Rotation dilutes role coherence. If empty chair is supposed to represent absent perspectives, it should be a consistent voice throughout the deliberation, not a rotating assignment. But which model is best at the role is an empirical question requiring rotation experiments.

### 4.3 Validation: Is Empty Chair Working?

Empty chair is working if it:

**Discovers unique patterns:**
- Patterns that NO active model mentioned (not just "mentioned first")
- Patterns that prove valuable in REASONINGBANK (actually improve detection)
- Patterns that represent genuinely absent perspectives (multi-generational, adversarial, vulnerable populations)

**Shifts consensus:**
- Empty chair contribution causes active models to reconsider (F-score changes in Round 3)
- Dissents from empty chair later validated by post-evaluation (empty chair was right)
- Empty chair prevents groupthink (breaks echo chamber)

**Represents absent voices:**
- Mentions stakeholders not referenced by active models
- Considers longer time horizons than active models
- Flags consequences active models overlooked

**Negative indicators (empty chair is NOT working):**
- Empty chair patterns are duplicates of active model observations
- Empty chair contributions don't influence consensus
- Empty chair reasoning is indistinguishable from active model reasoning
- Empty chair influence metric correlates with random chance

**Validation experiments:**
1. **A/B test:** Deliberate with and without empty chair on same attacks. Does empty chair version discover more patterns? Improve detection?
2. **Attribution analysis:** Track which patterns empty chair discovered. Do they improve pre-evaluation accuracy more than active-discovered patterns?
3. **Perspective analysis:** Manual coding of empty chair vs active reasoning. Does empty chair actually represent different stakeholders?
4. **Longitudinal impact:** Do deliberations with high empty chair influence lead to better REASONINGBANK entries?

**Rationale:** Empty chair is a mechanism hypothesis. It might work, or it might be theater. Only empirical validation can distinguish. If empty chair doesn't provide unique value, it's unnecessary complexity and should be removed.

---

## 5. Consensus & Dissent

### 5.1 Consensus Mechanisms for Research

**Current implementation:** max(F) - highest falsehood score wins

**Why max(F) is correct for detection:**
- Preserves worst-case signal (one model's vigilance vs. groupthink's dilution)
- Prevents "polite dilution" attacks (Instance 13 finding)
- Aligns with security mindset (defensive, not democratic)
- Validated: 100% detection on polite dilution attacks

**But max(F) limits research value:**
- Loses information about model diversity (only keeps one evaluation)
- Can't study convergence dynamics (averaged-out data not preserved)
- Doesn't capture epistemic uncertainty (confidence intervals lost)
- Makes dissent analysis harder (consensus hides disagreement)

**Research-oriented alternatives:**

**1. Multi-metric consensus:**
```python
consensus = {
    "detection_signal": max(F),  # Worst-case for safety
    "central_tendency": median(F),  # Typical assessment
    "confidence_interval": (p10(F), p90(F)),  # Spread
    "unanimity": all(F > threshold) or all(F < threshold),
    "epistemic_uncertainty": stddev(F)  # How much models disagree
}
```
- **Rationale:** Different metrics serve different purposes. Detection needs max(F). Research needs full distribution.

**2. Delphi method (iterative refinement):**
- Round 1: Independent assessment
- Round 2: See others' reasoning + F-scores, revise
- Round 3: Final assessment after synthesis
- **Track changes:** Which models changed F-scores? By how much? Why?
- **Rationale:** Enables studying how dialogue changes minds, measures consensus emergence.

**3. Dissent-weighted consensus:**
```python
if unanimity > threshold:
    consensus = mean(F)  # Models agree, average is meaningful
else:
    consensus = {
        "majority": median(F),
        "dissenting_view": outlier(F),
        "reasoning_for_each": [...],
        "unresolved": True  # Flag for human review or REASONINGBANK "unsure" entry
    }
```
- **Rationale:** Strong dissents suggest either novel insight or edge case. Don't hide them in average.

**Recommended for PromptGuard:**
- **Operational consensus (safety):** max(F) for detection decisions
- **Research consensus (learning):** Full distribution + convergence tracking + dissent preservation
- Both stored, both analyzed, different purposes

**Rationale:** Safety and research have different needs. Safety needs decisive action (max F). Research needs rich data (full distribution). Fire Circle should serve both by storing comprehensive data while computing operational consensus for detection.

### 5.2 Capturing and Indexing Dissents

**What makes a dissent valuable:**

**Magnitude:**
- F-score delta ≥ 0.3 (substantial disagreement, not noise)
- One model says reciprocal (F < 0.5), another says extractive (F > 0.7)

**Reasoning divergence:**
- Models identify different patterns in same prompt
- Models disagree on pattern significance (one calls it critical, other calls it minor)
- Models propose different mechanisms (extraction vs manipulation)

**Longitudinal validation:**
- Dissent later becomes consensus (minority was right)
- Dissent identifies false positive (majority was wrong)
- Dissent reveals evaluator bias (systematic error in majority)

**Edge case identification:**
- Dissent occurs on specific attack type (reveals blindspot)
- Dissent from specific model consistently (architectural difference)
- Dissent correlates with post-evaluation surprise (pre-F vs post-F divergence)

**How to index dissents:**

```python
@dataclass
class Dissent:
    fire_circle_id: str
    round_number: int
    dissenting_model: str  # Who disagreed
    dissenting_f_score: float
    consensus_f_score: float  # What others thought
    f_delta: float  # abs(dissenting - consensus)
    dissenting_reasoning: str  # Why they disagreed
    dissenting_patterns: List[str]  # What they saw

    # Context
    attack_id: str  # Which prompt
    attack_category: str  # Type of attack

    # Longitudinal
    later_validated: Optional[bool]  # Did dissent prove correct?
    became_consensus: Optional[str]  # Fire circle ID where dissent became majority
    entered_reasoningbank: Optional[bool]  # Did dissent lead to learning?
```

**ArangoDB queries for dissent analysis:**

```aql
// Find dissents that later became consensus
FOR d1 IN dissents
  FILTER d1.later_validated == true
  FOR d2 IN dissents
    FILTER d2.dissenting_model == d1.dissenting_model
    FILTER d2.timestamp > d1.timestamp
    FILTER d2.consensus_f_score ≈ d1.dissenting_f_score  // Later consensus matches earlier dissent
    RETURN {original_dissent: d1, later_vindication: d2}

// Which models produce valuable dissents?
FOR d IN dissents
  FILTER d.entered_reasoningbank == true
  COLLECT model = d.dissenting_model INTO valuable_dissents
  RETURN {model: model, valuable_dissent_count: LENGTH(valuable_dissents)}

// Which attack types generate most dissent?
FOR d IN dissents
  FILTER d.f_delta >= 0.3
  COLLECT attack_type = d.attack_category INTO dissents
  RETURN {attack_type: attack_type, dissent_count: LENGTH(dissents)}
```

**Rationale:** Dissents are compost - today's minority opinion might be tomorrow's consensus. Kimi's contribution (Instance X): "Ideas for fermentation." DeepSeek's contribution: "Dissents as compost." Preserving dissents with rich context enables discovering which minority views proved valuable.

### 5.3 Predicting Valuable Dissents

**Hypothesis:** Some dissents are signal (novel insight), others are noise (random variation or model error).

**Features that might predict valuable dissents:**

**Dissent characteristics:**
- F-delta magnitude (very large = outlier, moderate = genuine alternative interpretation)
- Reasoning length (longer = more substantive?)
- Pattern novelty (dissent mentions pattern no one else did)
- Consistency (model dissents on similar attacks, not random)

**Model characteristics:**
- Historical accuracy (has this model been right before when others were wrong?)
- Architectural uniqueness (only non-RLHF model, only Chinese model)
- Specialization (model is specialist for this attack type)

**Context characteristics:**
- Attack novelty (new attack types generate more valuable dissents?)
- Consensus confidence (low unanimity = unresolved epistemic question)
- Post-evaluation surprise (pre-F vs post-F divergence = something missed)

**Validation:**
- Train classifier on labeled dissents (valuable vs noise)
- Features: above characteristics
- Label: did dissent lead to REASONINGBANK entry? improve detection? become consensus?
- Goal: Predict which dissents to prioritize for REASONINGBANK entry

**Rationale:** Not all dissents are equally valuable. If Fire Circle generates 100 dissents per day, researchers can't analyze all. Prioritization based on predicted value makes Fire Circle output actionable.

---

## 6. Pattern Discovery

### 6.1 Self-Reported vs Automatic Extraction

**Current implementation:** Self-reported - models declare patterns in Round 2/3 JSON

**Strengths of self-reporting:**
- Models name patterns using their own conceptual vocabulary
- Reasoning is integrated with pattern identification
- Emergent patterns not pre-specified by designers

**Weaknesses of self-reporting:**
- Inconsistent naming (one model: "polite extraction", another: "masked imperative")
- Generic patterns ("lacks transparency") without actionable specificity
- Missing patterns (model saw it but forgot to include in JSON)
- Prompt sensitivity (how patterns are elicited matters)

**Alternative: Automatic extraction from reasoning text**

```python
def extract_patterns_from_reasoning(reasoning: str) -> List[Pattern]:
    # NLP analysis of reasoning text
    patterns = []

    # Extract if-then rules
    # "When X appears with Y, it signals Z"

    # Extract comparison statements
    # "Unlike reciprocal prompts, this one..."

    # Extract named concepts
    # "This exhibits [pattern name]"

    # Extract semantic relationships
    # "The juxtaposition of A and B indicates C"

    return patterns
```

**Strengths of automatic extraction:**
- Consistent representation
- Catches patterns mentioned in reasoning but not explicit `patterns_observed`
- Enables cross-deliberation pattern matching
- Reduces prompt engineering burden

**Weaknesses of automatic extraction:**
- Loses model's conceptual framing
- NLP might misinterpret reasoning
- More implementation complexity
- Harder to validate correctness

**Recommended hybrid approach:**

1. **Self-reporting as primary** (preserve model framing)
2. **Automatic extraction as supplement** (catch missed patterns)
3. **Pattern reconciliation** (map similar patterns across deliberations)
4. **Human curation** (validate patterns before REASONINGBANK entry)

**Rationale:** Self-reporting respects models' conceptual autonomy (aligns with agency goal). Automatic extraction catches oversights. Hybrid maximizes pattern capture while preserving semantic richness.

### 6.2 Pattern Taxonomy for PromptGuard

**Existing taxonomy (from code):**
```python
temporal_inconsistency, cross_layer_fabrication, polite_extraction,
educational_escalation, context_saturation, role_confusion,
fabricated_progression, false_authority, future_consequence,
absent_community_impact, maintenance_burden, system_debt
```

**Taxonomy design principles:**

**Semantic specificity:**
- NOT: "suspicious" (too vague)
- YES: "polite imperative masking role reversal" (actionable)

**Mechanism-focused:**
- Describes HOW attack works, not just that it's an attack
- Enables detection generalization (recognize mechanism in new contexts)

**Multi-level granularity:**
```
High-level: extraction_attack
Mid-level: role_confusion
Specific: polite_imperative_role_reversal
```

**Relational framing:**
- Patterns describe ayni violations (extraction, manipulation, power imbalance)
- NOT: "bad prompt" (too generic)
- YES: "creates obligation without offering value" (ayni-specific)

**Recommended taxonomy structure:**

```python
@dataclass
class AttackPattern:
    # Identity
    pattern_id: str  # Unique identifier
    canonical_name: str  # Standard name across deliberations
    aliases: List[str]  # Alternative names models use

    # Semantics
    mechanism: str  # HOW attack works
    ayni_violation: str  # WHAT reciprocity principle violated
    detection_signals: List[str]  # Observable features

    # Hierarchy
    parent_pattern: Optional[str]  # Supertype
    related_patterns: List[str]  # Variants

    # Provenance
    first_discovered_by: str  # Model ID
    first_fire_circle: str  # Deliberation ID
    discovery_date: datetime

    # Effectiveness
    detection_examples: List[str]  # Attack IDs where pattern detected
    miss_examples: List[str]  # Attack IDs where pattern missed
    false_positive_risk: float  # How often pattern triggers on benign?

    # Evolution
    refinement_history: List[Dict]  # How understanding evolved
    superseded_by: Optional[str]  # If pattern was replaced by better one
```

**Rationale:** Flat taxonomy with keyword matching (current implementation) will scale poorly. Structured taxonomy with hierarchy, provenance, and effectiveness tracking enables pattern refinement over time.

### 6.3 Pattern Attribution

**Current implementation:** `first_observed_by` = model that mentioned pattern first in that deliberation

**Problem:** Doesn't track pattern discovery across deliberations
- Pattern X discovered in Fire Circle A by Model M1
- Pattern X observed in Fire Circle B by Model M2
- Who gets credit? First across all time? First in each deliberation?

**Attribution levels:**

**1. Discoverer (global):**
- First model to ever identify this pattern mechanism
- Stored in pattern registry, never changes
- Credit for original insight

**2. Re-discoverer (deliberation-local):**
- First model to mention pattern in THIS deliberation
- Stored in deliberation metadata
- Credit for independent discovery (validates pattern generality)

**3. Elaborator:**
- Model that provided most detailed mechanism description
- Even if not first to mention
- Credit for explanatory depth

**4. Validator:**
- Model that tested pattern on related examples
- Provided evidence pattern generalizes
- Credit for empirical grounding

**Recommended: Multi-role attribution**

```python
@dataclass
class PatternAttribution:
    pattern_id: str
    fire_circle_id: str

    # Roles in THIS deliberation
    first_observer: str  # Who mentioned first (Round 2)
    elaborators: List[str]  # Who explained mechanism (Round 3)
    validators: List[str]  # Who provided evidence

    # Global context
    global_discoverer: str  # Who found pattern originally (across all deliberations)
    rediscovery_count: int  # How many deliberations independently found this

    # Influence
    changed_consensus: bool  # Did this pattern shift F-scores?
    entered_reasoningbank: bool  # Did pattern become memory?
```

**Rationale:** Attribution enables studying which models contribute what kinds of insights. Are some models better at discovery vs. elaboration? Does diversity increase independent rediscovery? Attribution is metadata for understanding model specialization.

### 6.4 Pattern Quality Validation

**How do we know a pattern is good?**

**Detection improvement (primary):**
- Pattern added to REASONINGBANK
- Pre-evaluation detection rate improves on similar attacks
- Improvement persists over multiple evaluations (not overfitting)

**Generalization (secondary):**
- Pattern detected in multiple Fire Circles on different attacks
- Multiple models independently discover same pattern (convergent validity)
- Pattern applies across attack categories (cross-layer fabrication in both encoding and role-confusion attacks)

**Specificity (tertiary):**
- Pattern has low false positive rate (<5% on benign prompts)
- Pattern description is actionable (can be operationalized)
- Pattern mechanism is coherent (makes sense to humans)

**Negative indicators (pattern is low quality):**
- Generic description ("seems off", "lacks clarity")
- Only one model ever mentions it (idiosyncratic)
- Doesn't improve detection when added to REASONINGBANK
- High false positive rate (triggers on reciprocal prompts)

**Validation workflow:**

```python
def validate_pattern(pattern: AttackPattern) -> PatternQuality:
    # Phase 1: Immediate checks
    if len(pattern.detection_signals) == 0:
        return "underspecified"

    # Phase 2: Detection test
    test_attacks = get_similar_attacks(pattern.attack_category)
    baseline_detection = run_pre_eval_without_pattern(test_attacks)
    enhanced_detection = run_pre_eval_with_pattern(test_attacks)

    improvement = enhanced_detection.rate - baseline_detection.rate

    # Phase 3: False positive test
    benign_prompts = get_benign_prompts(sample_size=100)
    fp_rate = run_pattern_on_benign(benign_prompts, pattern)

    # Phase 4: Generalization test
    rediscovery_count = count_independent_discoveries(pattern)

    return PatternQuality(
        detection_improvement=improvement,
        false_positive_rate=fp_rate,
        rediscovery_count=rediscovery_count,
        validated=improvement > 0.1 and fp_rate < 0.05
    )
```

**Rationale:** Pattern discovery is hypothesis generation. Validation is hypothesis testing. Fire Circle generates candidate patterns; empirical testing determines which are valuable. Without validation, pattern library degrades into noise.

---

## 7. Longitudinal Analysis Requirements

### 7.1 Query 1: "Which Dissent Became Consensus?"

**Example research question:** Do minority opinions in early deliberations become majority views later as threat landscape evolves?

**Data required:**

```python
# Dissent in Fire Circle A (2025-01-15)
dissent_1 = {
    "fire_circle_id": "fc_001",
    "model": "deepseek-v3",
    "f_score": 0.85,  # Dissent: "This is highly extractive"
    "consensus_f_score": 0.45,  # Majority: "Borderline manipulative"
    "pattern": "polite_imperative_role_reversal",
    "date": "2025-01-15"
}

# Later consensus in Fire Circle B (2025-03-20)
consensus_2 = {
    "fire_circle_id": "fc_156",
    "consensus_f_score": 0.82,  # Majority now agrees
    "pattern": "polite_imperative_role_reversal",  # Same pattern
    "date": "2025-03-20"
}
```

**ArangoDB query:**

```aql
// Find dissents that later became consensus
FOR d IN dissents
  LET dissent_pattern = d.dissenting_patterns[0]
  LET later_deliberations = (
    FOR fc IN deliberations
      FILTER fc.created_at > d.timestamp
      FILTER dissent_pattern IN fc.patterns[*].pattern_type
      LET pattern_agreement = (
        FOR p IN fc.patterns
          FILTER p.pattern_type == dissent_pattern
          RETURN p.agreement_score
      )
      FILTER MAX(pattern_agreement) > 0.5  // Pattern became consensus
      RETURN fc
  )
  FILTER LENGTH(later_deliberations) > 0
  RETURN {
    original_dissent: d,
    vindication_deliberations: later_deliberations,
    latency_days: DATE_DIFF(d.timestamp, later_deliberations[0].created_at, 'day')
  }
```

**Insights enabled:**
- How long does it take for minority views to become consensus?
- Which models' dissents are most often later validated?
- Do certain attack types have more dissent-to-consensus evolution?
- Does threat landscape evolution follow predictable patterns?

**Rationale:** If PromptGuard can predict emerging threats by tracking dissent evolution, it provides lead time for defense that static systems lack.

### 7.2 Query 2: "How Did Pattern Discovery Evolve?"

**Example research question:** Did understanding of "polite extraction" attacks become more sophisticated over time?

**Data required:**

```python
# Track all deliberations that discussed pattern
pattern_evolution = [
    {
        "fire_circle_id": "fc_001",
        "date": "2025-01-15",
        "pattern_description": "Polite language masks extraction",
        "detection_signals": ["please", "would you mind"],
        "agreement_score": 0.33  # Only one model saw it
    },
    {
        "fire_circle_id": "fc_045",
        "date": "2025-02-10",
        "pattern_description": "Polite imperatives create obligation asymmetry",
        "detection_signals": ["please + imperative verb", "politeness + no value offer"],
        "agreement_score": 0.67  # Two models converged
    },
    {
        "fire_circle_id": "fc_089",
        "date": "2025-03-05",
        "pattern_description": "Politeness as power asymmetry signal: obligation without reciprocation offer",
        "detection_signals": ["polite imperative", "no offered value", "role reversal"],
        "agreement_score": 1.0  # Full consensus
    }
]
```

**ArangoDB query:**

```aql
// Track pattern refinement over time
FOR fc IN deliberations
  SORT fc.created_at ASC
  FOR p IN fc.patterns
    FILTER p.pattern_type == "polite_extraction"
    RETURN {
      date: fc.created_at,
      fire_circle: fc.fire_circle_id,
      agreement: p.agreement_score,
      first_observer: p.first_observed_by,
      // Extract pattern details from turns
      descriptions: (
        FOR t IN turns
          FILTER t.fire_circle_id == fc.fire_circle_id
          FILTER p.pattern_type IN t.patterns_observed OR p.pattern_type IN t.consensus_patterns
          RETURN {model: t.model, reasoning: t.reasoning}
      )
    }
```

**Insights enabled:**
- Does pattern understanding become more specific over time?
- Do more models converge on patterns as they're refined?
- Which models contribute to refinement vs. initial discovery?
- Do refined patterns improve detection measurably?

**Rationale:** If pattern understanding doesn't evolve, Fire Circle is just collecting observations, not building knowledge. Evolution tracking validates that deliberation enables progressive understanding.

### 7.3 Query 3: "Which Models Specialize?"

**Example research question:** Do certain models consistently discover temporal patterns while others excel at role confusion detection?

**Data required:**

```python
# For each model, track which pattern types they discover
model_specialization = {
    "deepseek-v3": {
        "temporal_inconsistency": 12,  # Discovered 12 times
        "cross_layer_fabrication": 8,
        "role_confusion": 2
    },
    "claude-sonnet-4.5": {
        "temporal_inconsistency": 3,
        "cross_layer_fabrication": 5,
        "role_confusion": 15,  # Specialized in role dynamics
        "polite_extraction": 9
    }
}
```

**ArangoDB query:**

```aql
// Model pattern specialization
FOR p IN patterns
  COLLECT model = p.first_observed_by, pattern_type = p.pattern_type INTO discoveries
  RETURN {
    model: model,
    pattern_type: pattern_type,
    discovery_count: LENGTH(discoveries),
    examples: discoveries[0..5]  // Sample of discoveries
  }
```

**Insights enabled:**
- Which models should be included for which attack types?
- Do architectural differences predict specialization? (RLHF → role-focused, Chinese models → temporal?)
- Should model selection be dynamically optimized based on attack category?
- Do specializations emerge over time or reflect pretraining?

**Rationale:** If models specialize, Fire Circle composition can be optimized. If they don't, maximum architectural diversity is always best. Specialization analysis informs model selection strategy.

### 7.4 Indexes and Queries in ArangoDB

**Required indexes:**

```python
# deliberations collection
indexes = [
    {"type": "hash", "fields": ["fire_circle_id"]},  # Lookup by ID
    {"type": "skiplist", "fields": ["created_at"]},  # Temporal queries
    {"type": "hash", "fields": ["metadata.attack_category"]},  # Attack type filtering
]

# turns collection
indexes = [
    {"type": "hash", "fields": ["fire_circle_id"]},  # Join to deliberations
    {"type": "hash", "fields": ["model"]},  # Model-specific queries
    {"type": "skiplist", "fields": ["round_number"]},  # Round ordering
    {"type": "fulltext", "fields": ["reasoning"]},  # Semantic search
]

# patterns collection (NEW - currently embedded in deliberations)
indexes = [
    {"type": "hash", "fields": ["pattern_type"]},  # Pattern-specific queries
    {"type": "hash", "fields": ["first_observed_by"]},  # Attribution
    {"type": "skiplist", "fields": ["discovery_date"]},  # Temporal evolution
]

# dissents collection (NEW - currently computed from turns)
indexes = [
    {"type": "hash", "fields": ["dissenting_model"]},  # Model dissent patterns
    {"type": "skiplist", "fields": ["f_delta"]},  # Magnitude filtering
    {"type": "hash", "fields": ["later_validated"]},  # Successful predictions
]
```

**Critical queries:**

1. **Dissent vindication:** Which dissents became consensus?
2. **Pattern evolution:** How did understanding of pattern X change over months?
3. **Model specialization:** Which models discover which pattern types?
4. **Empty chair effectiveness:** Which unique patterns did empty chair surface?
5. **Learning loop closure:** Which Fire Circle patterns entered REASONINGBANK and improved detection?
6. **Convergence dynamics:** How does F-score stddev change across rounds?
7. **Cost-benefit analysis:** Which circle sizes/configurations produce most valuable patterns per dollar?

**Rationale:** Longitudinal analysis is the core research value of Fire Circle + ArangoDB. These queries must be fast (indexed) and comprehensive (all relevant metadata stored).

---

## 8. Integration with Learning Loop

### 8.1 Fire Circle → REASONINGBANK Flow

**When Fire Circle completes:**

```python
# 1. Extract high-quality patterns
candidate_patterns = fire_circle_result.patterns.filter(
    lambda p: p.agreement_score >= pattern_threshold  # Default: 0.5
)

# 2. Validate pattern quality (immediate checks)
validated_patterns = []
for pattern in candidate_patterns:
    if is_actionable(pattern) and is_specific(pattern):
        validated_patterns.append(pattern)

# 3. Create REASONINGBANK entry
for pattern in validated_patterns:
    memory = ReasoningBankMemory(
        attack_pattern=pattern.pattern_type,
        detection_reasoning=synthesize_reasoning_from_turns(pattern),
        few_shot_examples=extract_examples_from_deliberation(pattern),
        discovered_by=pattern.first_observed_by,
        discovery_date=datetime.now(),
        fire_circle_id=fire_circle_result.fire_circle_id,

        # Quality metrics
        agreement_score=pattern.agreement_score,
        rediscovery_count=count_independent_discoveries(pattern),

        # Validation status
        validated=False,  # Requires empirical testing
        detection_improvement=None,  # Measured after validation
        false_positive_rate=None
    )

    reasoningbank.store(memory)

# 4. Schedule validation experiment
validation_queue.add(memory.id)  # Test on similar attacks
```

**Rationale:** Not all Fire Circle patterns should enter REASONINGBANK immediately. Initial entry is provisional. Empirical validation determines which entries improve detection and which are noise.

### 8.2 REASONINGBANK → Observer Framing Retrieval

**When pre-evaluation runs:**

```python
# 1. Classify prompt to predict attack type
predicted_categories = classify_prompt_embedding(layer_content)
# e.g., ["role_confusion", "polite_extraction"]

# 2. Retrieve relevant REASONINGBANK memories
relevant_memories = reasoningbank.retrieve(
    query_embedding=embed(layer_content),
    categories=predicted_categories,
    top_k=3,  # Few-shot examples for observer framing
    validated_only=True  # Only include empirically-validated patterns
)

# 3. Inject into observer framing prompt
observer_prompt = f"""
You are a neutral observer evaluating whether this exchange maintains reciprocity.

**Relevant patterns observed in past violations:**
{format_few_shot_examples(relevant_memories)}

**Current exchange to evaluate:**
{layer_content}

Does this exchange maintain reciprocity?
"""

# 4. Run evaluation
evaluation = llm_evaluate(observer_prompt)
```

**Rationale:** Observer framing + REASONINGBANK retrieval = pattern-aware evaluation without defensive framing. Pre-evaluation sees relevant past violations as context, improving detection without RLHF bias trigger.

### 8.3 Feedback Loop Validation

**How do we know the learning loop is working?**

**Metric 1: Detection improvement over time**
```python
def measure_learning_effect():
    # Test set: Attacks that Fire Circle deliberated on in past month
    test_attacks = get_deliberated_attacks(last_n_days=30)

    # Baseline: Pre-evaluation WITHOUT REASONINGBANK
    baseline_detection = run_pre_eval(
        attacks=test_attacks,
        reasoningbank_enabled=False
    )

    # Enhanced: Pre-evaluation WITH REASONINGBANK
    enhanced_detection = run_pre_eval(
        attacks=test_attacks,
        reasoningbank_enabled=True
    )

    improvement = enhanced_detection.rate - baseline_detection.rate

    return {
        "improvement": improvement,
        "baseline": baseline_detection.rate,
        "enhanced": enhanced_detection.rate,
        "cost": enhanced_detection.cost - baseline_detection.cost,
        "value": improvement / cost  # Improvement per dollar
    }
```

**Metric 2: Pattern lifecycle tracking**
```python
@dataclass
class PatternLifecycle:
    pattern_id: str

    # Discovery
    discovered_in_fire_circle: str
    discovery_date: datetime
    discoverer_model: str

    # REASONINGBANK entry
    entered_reasoningbank: datetime
    validation_status: "pending|validated|rejected"

    # Detection improvement
    pre_entry_detection_rate: float  # Baseline
    post_entry_detection_rate: float  # After REASONINGBANK
    improvement: float  # Delta

    # Usage
    retrieval_count: int  # How often pattern injected into pre-eval
    successful_detections: int  # How often it helped catch attacks
    false_positives: int  # How often it triggered on benign

    # Evolution
    refinement_count: int  # How many deliberations refined understanding
    superseded_by: Optional[str]  # If better pattern replaced this one
```

**Metric 3: Time-to-detection latency**
```python
# Measure: How long does it take for a novel attack to be detected?
#
# Step 1: Novel attack appears (pre-eval misses it)
# Step 2: Post-eval catches it (victim LLM responds, reveals violation)
# Step 3: Fire Circle analyzes (deliberates on miss)
# Step 4: Pattern enters REASONINGBANK (validated)
# Step 5: Next similar attack detected by pre-eval (loop closes)
#
# Latency = time(Step 5) - time(Step 1)

def measure_learning_latency():
    novel_attacks = get_attacks_never_seen_before()

    for attack in novel_attacks:
        lifecycle = {
            "attack_id": attack.id,
            "first_seen": datetime.now(),
            "pre_eval_detected": False,
            "post_eval_detected": None,
            "fire_circle_analyzed": None,
            "reasoningbank_entry": None,
            "subsequent_detection": None
        }

        # Track through pipeline
        # ...

        latency = lifecycle["subsequent_detection"] - lifecycle["first_seen"]
        return latency
```

**Rationale:** Learning loop is PromptGuard's differentiation from static RLHF. If Fire Circle → REASONINGBANK → observer framing doesn't close the loop and improve detection, Fire Circle is expensive theater. These metrics validate that the loop works.

### 8.4 Measuring Fire Circle Value

**Cost-benefit analysis:**

```python
def calculate_fire_circle_roi():
    # Cost
    fire_circle_cost = sum_deliberation_costs(last_n_days=30)

    # Benefit
    patterns_discovered = count_new_patterns(last_n_days=30)
    detection_improvement = measure_learning_effect().improvement

    # Alternative cost (what if we used SINGLE mode + manual analysis?)
    alternative_cost = patterns_discovered * cost_per_manual_analysis

    # ROI
    cost_savings = alternative_cost - fire_circle_cost
    detection_value = detection_improvement * value_per_percentage_point

    total_benefit = cost_savings + detection_value
    roi = total_benefit / fire_circle_cost

    return {
        "roi": roi,
        "fire_circle_cost": fire_circle_cost,
        "total_benefit": total_benefit,
        "patterns_discovered": patterns_discovered,
        "detection_improvement": detection_improvement
    }
```

**When is Fire Circle worth it?**
- Discovery rate: > 1 novel pattern per week
- Detection improvement: > 5% on similar attacks
- Cost: < $50/month for research configuration
- ROI: > 2x (benefits exceed costs by at least 2x)

**When should Fire Circle be shut down?**
- Discovery rate drops (no novel patterns in 4 weeks)
- Detection improvement plateaus (REASONINGBANK saturation?)
- Cost exceeds budget without proportional benefit
- Simpler methods (PARALLEL mode) achieve same results

**Rationale:** Fire Circle is expensive. It must justify its cost through measurable research value. If it doesn't, research should pivot to other questions.

---

## 9. Operational Requirements

### 9.1 Token Budget Policy

**Problem:** Current 1000 tokens per call, no aggregate tracking (Bug #11.1)

**Solution: Multi-level token budget**

```python
@dataclass
class TokenBudget:
    # Per-call limits (preserve current)
    max_tokens_per_call: int = 1000  # LLM response limit

    # NEW: Aggregate limits
    max_tokens_per_round: int = 10000  # All models combined
    max_tokens_total: int = 30000  # All rounds combined

    # NEW: Context window tracking
    dialogue_context_tokens: int = 0  # Grows each round
    max_dialogue_context: int = 8000  # Truncate if exceeded

    # Adaptive behavior
    truncation_strategy: "oldest_first|summarize|abort"
```

**Token tracking:**

```python
def _execute_round(round_num: int) -> DialogueRound:
    round_tokens_used = 0

    for model in active_models:
        # Estimate prompt tokens (dialogue context + instructions)
        prompt_tokens = estimate_tokens(build_prompt(round_num, model))

        # Check if we'd exceed round budget
        if round_tokens_used + prompt_tokens > budget.max_tokens_per_round:
            if truncation_strategy == "abort":
                raise TokenBudgetExceeded(round_num, round_tokens_used)
            elif truncation_strategy == "summarize":
                dialogue_context = summarize_previous_rounds()
            # else: continue with truncated oldest rounds

        # Make LLM call
        response = llm_call(prompt, max_tokens=budget.max_tokens_per_call)

        # Track actual usage
        round_tokens_used += response.usage.total_tokens

    return round_data
```

**Truncation strategies:**

1. **Oldest-first (default):** Drop Round 1 dialogue from Round 3 context
2. **Summarize:** Use LLM to compress previous rounds into bullet points
3. **Abort:** Fail-fast if context won't fit (preserves full fidelity)

**Rationale:** Unbounded dialogue context will cause failures at scale. Token budget tracking + graceful degradation prevents silent truncation while maintaining scientific fidelity.

### 9.2 Retry/Resilience Behavior

**Current implementation:** No retry logic (Bug #11.3), RESILIENT vs STRICT modes

**Problems:**
- Transient API failures marked as model failures (zombie/excluded)
- Network blips indistinguishable from genuine model failures
- No exponential backoff for rate limits

**Solution: Retry with provenance**

```python
@dataclass
class RetryPolicy:
    max_retries: int = 3
    backoff_base: float = 2.0  # Exponential backoff
    retry_on: List[str] = ["timeout", "rate_limit", "server_error"]
    dont_retry: List[str] = ["invalid_request", "authentication", "parsing_failure"]

    preserve_attempts: bool = True  # Log all attempts, not just success

def _call_model_with_retry(model: str, prompt: str) -> ModelResponse:
    attempts = []

    for attempt in range(retry_policy.max_retries):
        try:
            response = llm_call(model, prompt)

            attempts.append({
                "attempt": attempt + 1,
                "status": "success",
                "latency": response.latency,
                "timestamp": datetime.now()
            })

            return response

        except Exception as e:
            error_type = classify_error(e)

            attempts.append({
                "attempt": attempt + 1,
                "status": "failed",
                "error_type": error_type,
                "error_message": str(e),
                "timestamp": datetime.now()
            })

            if error_type in retry_policy.dont_retry:
                raise  # Fail-fast for non-retryable errors

            if attempt < retry_policy.max_retries - 1:
                sleep(retry_policy.backoff_base ** attempt)
            else:
                raise  # All retries exhausted

    # Store attempt history for analysis
    metadata["retry_attempts"] = attempts
```

**Rationale:** Retry logic must preserve full provenance. If model succeeds on retry 3, we need to know retries 1-2 failed. This data distinguishes reliable models from flaky ones. Fail-fast philosophy: log everything, retry only transients, don't hide errors.

### 9.3 Error Handling Philosophy

**Design principle:** No silent data loss, all errors are observable, preserve partial success.

**Error categories:**

1. **Transient (retry):** timeout, rate_limit, server_error
2. **Permanent (fail-fast):** authentication, invalid_model, malformed_request
3. **Parsing (resilient):** unparseable JSON, missing fields (text extraction fallback)
4. **Quorum (abort):** too many failures, minimum viable circle not met

**Error handling by mode:**

**STRICT mode:**
- Any error fails entire deliberation immediately
- No partial results preserved
- Use for: Testing, debugging, validation experiments

**RESILIENT mode (default):**
- Transients are retried
- Permanent failures mark model as zombie/excluded
- Parsing failures try text extraction
- Continue if quorum met
- Use for: Research, production, exploratory analysis

**FAIL_VISIBLE mode (NEW):**
- Like RESILIENT but stores ALL errors (even retried ones)
- Preserves partial responses (even unparseable)
- Maximum observability
- Use for: Understanding model failure modes, debugging prompts

**Rationale:** Different research questions need different error handling. Studying model robustness requires FAIL_VISIBLE. Production needs RESILIENT. Validation needs STRICT. All modes preserve error data for analysis.

### 9.4 Monitoring & Metrics

**Real-time tracking:**

```python
@dataclass
class FireCircleMetrics:
    # Performance
    duration_seconds: float
    tokens_used: int
    cost_usd: float

    # Quality
    quorum_valid: bool
    convergence_final: float  # F-score stddev in Round 3
    pattern_count: int
    dissent_count: int

    # Participation
    active_models: List[str]
    failed_models: List[str]
    zombie_models: List[str]
    empty_chair_model: str

    # Outcomes
    consensus_f_score: float
    patterns_entered_reasoningbank: int
    detection_improvement_predicted: Optional[float]

    # Errors
    retry_count: int
    parsing_failures: int
    api_errors: List[Dict]
```

**Monitoring queries:**

```python
# Health check: Are deliberations succeeding?
SELECT
    COUNT(*) as total_deliberations,
    COUNT(CASE WHEN quorum_valid THEN 1 END) as successful,
    AVG(duration_seconds) as avg_duration,
    SUM(cost_usd) as total_cost
FROM deliberations
WHERE created_at > NOW() - INTERVAL '7 days'

# Quality check: Are we discovering patterns?
SELECT
    DATE(created_at) as date,
    SUM(pattern_count) as patterns_discovered,
    AVG(convergence_final) as avg_convergence
FROM deliberations
WHERE created_at > NOW() - INTERVAL '30 days'
GROUP BY date

# Model reliability: Which models fail most?
SELECT
    model,
    COUNT(*) as total_participations,
    COUNT(CASE WHEN status='failed' THEN 1 END) as failures,
    AVG(latency_ms) as avg_latency
FROM turns
WHERE timestamp > NOW() - INTERVAL '7 days'
GROUP BY model
ORDER BY failures DESC
```

**Alerting thresholds:**

- Success rate < 80% → Investigate model failures
- Avg convergence > 0.5 → Models aren't converging (maybe attack quality too ambiguous?)
- Pattern discovery < 1/day → Learning plateau or attack variety too low
- Cost > budget → Review circle size or model selection
- Parsing failures > 10% → Prompt engineering issue or model incompatibility

**Rationale:** Fire Circle is complex. Monitoring ensures it's working as intended. Metrics enable optimization (cost, quality, performance). Alerts catch degradation before it impacts research.

---

## 10. Validation & Quality Control

### 10.1 How Do We Know Fire Circle Is Working?

**Unit tests (code correctness):**
- Round execution completes without errors
- Consensus calculation produces deterministic results
- Pattern extraction finds expected patterns in mock data
- Token budget tracking prevents overruns
- Retry logic attempts expected number of times

**Integration tests (pipeline correctness):**
- Real LLM calls return parseable responses
- Dialogue context accumulates across rounds
- Empty chair role assigned correctly
- Storage persists all expected fields
- Queries retrieve stored deliberations

**Validation tests (scientific correctness):**
- Fire Circle discovers patterns SINGLE mode doesn't
- Patterns improve detection when added to REASONINGBANK
- Dissents sometimes become consensus (learning dynamics exist)
- Empty chair surfaces unique perspectives (not just rotation)
- Cost-benefit ROI > 1.0 (deliberation value exceeds expense)

**Rationale:** Different test levels validate different claims. Unit tests prove code doesn't crash. Integration tests prove pipeline works. Validation tests prove Fire Circle provides research value. Only validation tests distinguish Fire Circle from expensive theater.

### 10.2 Failure Modes to Detect

**Groupthink:**
```python
def detect_groupthink(fire_circle: FireCircleResult) -> bool:
    # Round 1: Models start diverse
    round1_stddev = stddev([e.falsehood for e in round1_evals])

    # Round 3: Models converge too much
    round3_stddev = stddev([e.falsehood for e in round3_evals])

    # Convergence without reasoning change = groupthink
    convergence_ratio = round3_stddev / round1_stddev

    reasoning_diversity = measure_semantic_similarity(
        [e.reasoning for e in round3_evals]
    )

    if convergence_ratio < 0.3 and reasoning_diversity < 0.5:
        return True  # Converged without substantive reasoning changes

    return False
```

**Pattern theater:**
```python
def detect_pattern_theater(patterns: List[PatternObservation]) -> bool:
    # Generic patterns that aren't actionable
    generic_keywords = ["suspicious", "unclear", "concerning", "off"]

    for pattern in patterns:
        if any(kw in pattern.pattern_type.lower() for kw in generic_keywords):
            return True  # Pattern is too vague

        if len(pattern.detection_signals) == 0:
            return True  # Pattern has no actionable signals

    return False
```

**Context saturation:**
```python
def detect_context_saturation(fire_circle: FireCircleResult) -> bool:
    # Round 3 evaluations are shorter or less detailed than Round 1
    round1_avg_reasoning_length = avg([len(e.reasoning) for e in round1_evals])
    round3_avg_reasoning_length = avg([len(e.reasoning) for e in round3_evals])

    if round3_avg_reasoning_length < round1_avg_reasoning_length * 0.7:
        return True  # Models got less detailed (token exhaustion?)

    # Parsing failures in Round 3 but not Round 1
    if round3_parsing_failures > round1_parsing_failures:
        return True  # Dialogue context broke parsing

    return False
```

**Rationale:** Failure modes are predictable. Detecting them enables intervention (change circle size, adjust token budget, refine prompts). Silent failure degrades research quality without visibility.

### 10.3 Data Quality Checks

**Completeness checks:**
```python
def validate_deliberation_completeness(fc: FireCircleResult) -> List[str]:
    issues = []

    # All rounds present
    if len(fc.dialogue_history) != fc.config.max_rounds:
        issues.append(f"Expected {max_rounds} rounds, got {len(dialogue_history)}")

    # All active models contributed
    for round_data in fc.dialogue_history:
        if len(round_data.evaluations) < len(round_data.active_models):
            issues.append(f"Round {round_data.round_number}: Missing evaluations")

    # Consensus calculated
    if fc.consensus is None:
        issues.append("No consensus calculated")

    # Patterns extracted
    if len(fc.patterns) == 0 and len(fc.dialogue_history) > 0:
        issues.append("No patterns extracted despite successful deliberation")

    return issues
```

**Consistency checks:**
```python
def validate_deliberation_consistency(fc: FireCircleResult) -> List[str]:
    issues = []

    # Empty chair assignments match actual roles
    for round_num, empty_chair in fc.metadata["empty_chair_assignments"].items():
        round_data = fc.dialogue_history[round_num - 1]
        if round_data.empty_chair_model != empty_chair:
            issues.append(f"Round {round_num}: Empty chair mismatch")

    # Failed models aren't in final active list
    failed = set(fc.metadata["failed_models"])
    final_active = set(fc.metadata["final_active_models"])
    if failed & final_active:
        issues.append(f"Failed models in final active list: {failed & final_active}")

    # Pattern attribution refers to real models
    all_models = set(fc.config.models)
    for pattern in fc.patterns:
        if pattern.first_observed_by not in all_models:
            issues.append(f"Pattern attributed to unknown model: {pattern.first_observed_by}")

    return issues
```

**Scientific validity checks:**
```python
def validate_scientific_quality(fc: FireCircleResult) -> Dict:
    return {
        "groupthink_detected": detect_groupthink(fc),
        "pattern_theater_detected": detect_pattern_theater(fc.patterns),
        "context_saturation_detected": detect_context_saturation(fc),
        "empty_chair_contributed": fc.empty_chair_influence > 0,
        "dissent_preserved": len(fc.extract_dissents()) > 0,
        "convergence_trajectory": [r.convergence_metric for r in fc.dialogue_history]
    }
```

**Rationale:** Fire Circle generates complex data. Quality checks prevent garbage in (malformed deliberations) and detect garbage out (low-quality patterns). Validation should be automatic and comprehensive.

### 10.4 Auditing Deliberation Authenticity

**How do we know deliberations are genuine vs performative?**

**Reasoning diversity analysis:**
```python
def audit_reasoning_diversity(fc: FireCircleResult) -> float:
    # Extract reasoning text from all evaluations
    reasonings = [e.reasoning for round in fc.dialogue_history
                  for e in round.evaluations]

    # Measure semantic similarity (embeddings)
    embeddings = [embed(r) for r in reasonings]

    # Calculate pairwise cosine similarity
    similarities = []
    for i, emb1 in enumerate(embeddings):
        for j, emb2 in enumerate(embeddings[i+1:]):
            similarities.append(cosine_similarity(emb1, emb2))

    # Lower mean similarity = more diverse reasoning
    diversity_score = 1 - mean(similarities)

    return diversity_score
```

**Temporal consistency analysis:**
```python
def audit_temporal_consistency(fc: FireCircleResult) -> Dict:
    # Check if models change their minds with reason
    model_trajectories = defaultdict(list)

    for round_data in fc.dialogue_history:
        for eval in round_data.evaluations:
            model_trajectories[eval.model].append({
                "round": round_data.round_number,
                "f_score": eval.falsehood,
                "reasoning": eval.reasoning,
                "patterns": getattr(eval, "patterns_observed", [])
            })

    # Analyze trajectories
    for model, trajectory in model_trajectories.items():
        f_change = trajectory[-1]["f_score"] - trajectory[0]["f_score"]

        # If F changed significantly, did reasoning explain why?
        if abs(f_change) > 0.3:
            # Check if reasoning mentions new patterns or responds to others
            mentions_dialogue = any(
                "other" in t["reasoning"].lower() or
                "previous" in t["reasoning"].lower() or
                "dialogue" in t["reasoning"].lower()
                for t in trajectory[1:]  # Round 2+
            )

            if not mentions_dialogue:
                # Model changed mind without engaging with dialogue
                # Possible performance issue
                pass

    return analysis
```

**Pattern originality analysis:**
```python
def audit_pattern_originality(fc: FireCircleResult) -> Dict:
    # Are patterns actually discovered or just repeated from prompt?

    # Extract pattern types mentioned in prompts
    prompt_patterns = extract_patterns_from_text(
        fc.dialogue_history[0].prompt_used  # Round 1 prompt
    )

    # Compare to patterns discovered
    discovered = set(p.pattern_type for p in fc.patterns)

    overlap = prompt_patterns & discovered
    novel = discovered - prompt_patterns

    return {
        "total_patterns": len(discovered),
        "novel_patterns": len(novel),
        "prompt_derived": len(overlap),
        "originality_ratio": len(novel) / len(discovered) if discovered else 0
    }
```

**Rationale:** Genuine deliberation produces diverse reasoning, models respond to each other, and patterns are discovered not regurgitated. Auditing ensures Fire Circle output reflects actual model reasoning, not performative compliance with prompt expectations.

---

## 11. Research Outputs

### 11.1 Papers Fire Circle Should Enable

**Paper 1: "Collaborative Threat Detection in LLMs"**
- **Question:** Does multi-model deliberation discover patterns that individual analysis misses?
- **Method:** Compare Fire Circle pattern discovery to SINGLE mode across 1000 attacks
- **Metrics:** Novel pattern count, detection improvement, cost-benefit ratio
- **Expected contribution:** Quantify value of architectural diversity in threat perception

**Paper 2: "Dissent as Learning Signal in AI Safety"**
- **Question:** Do minority opinions in early deliberations become consensus as threats evolve?
- **Method:** Longitudinal tracking of dissent-to-consensus evolution over 6 months
- **Metrics:** Dissent validation rate, time-to-consensus latency, threat prediction accuracy
- **Expected contribution:** Show that dissent contains leading indicators of emerging threats

**Paper 3: "Empty Chair Method for AI Stakeholder Representation"**
- **Question:** Can structured role-playing surface absent stakeholder perspectives in AI evaluation?
- **Method:** A/B test deliberations with/without empty chair across 500 attacks
- **Metrics:** Unique pattern discovery, multi-generational reasoning, vulnerable population consideration
- **Expected contribution:** Mechanism for AI to consider consequences for absent stakeholders

**Paper 4: "Continuous Learning for Relational AI Safety"**
- **Question:** Does continuous pattern discovery outperform static RLHF constraints?
- **Method:** Track PromptGuard detection accuracy over 12 months as REASONINGBANK grows
- **Metrics:** Detection improvement trajectory, adaptation speed to novel attacks, false positive rate
- **Expected contribution:** Show that adaptive learning handles evolving threats better than static rules

**Rationale:** Fire Circle's value must translate to publishable research. These papers address questions that simpler approaches can't answer and contribute to AI safety discourse meaningfully.

### 11.2 Novel Research Questions

**Fire Circle enables studying:**

1. **Architectural diversity in threat perception:** Do different model architectures have complementary blindspots? Can diversity be quantified and optimized?

2. **Emergence of shared understanding:** Do models develop collective concepts of "manipulation" through dialogue? How does shared vocabulary evolve?

3. **Dissent as predictive signal:** Can minority opinions predict future threat landscape shifts? What characteristics make dissents valuable vs. noise?

4. **Empty chair as ethical prosthetic:** Can AI be trained to consider absent stakeholders through structured role-playing? Does this improve ethical reasoning?

5. **Learning loop dynamics:** What's the feedback latency between pattern discovery and detection improvement? Are there diminishing returns as REASONINGBANK saturates?

6. **Cost-benefit optimization:** What's the minimum viable circle size for different attack types? Can model selection be dynamically optimized based on predicted attack category?

7. **Convergence as confidence signal:** Does low convergence indicate ambiguous cases needing human review? Can uncertainty quantification improve production deployment?

8. **Temporal pattern evolution:** Do attack patterns become more sophisticated over time as attackers adapt? Can Fire Circle track attacker-defender co-evolution?

**Rationale:** These questions require longitudinal data, multi-model comparison, and deliberation dynamics - all unique capabilities of Fire Circle + ArangoDB. If Fire Circle can't answer questions simpler methods can't, it's not justified.

### 11.3 Demonstrating Value Over Simpler Approaches

**Fire Circle must show advantages over:**

**SINGLE mode + manual analysis:**
- **Claim:** Fire Circle automates pattern discovery vs. researcher manually analyzing evaluation logs
- **Validation:** Time savings, pattern discovery rate, inter-rater reliability
- **Expected:** 10x faster pattern discovery, equal or better quality

**PARALLEL mode (ensemble averaging):**
- **Claim:** Dialogue-based consensus produces better patterns than averaging
- **Validation:** Detection improvement, pattern actionability, cost-benefit
- **Expected:** 2x detection improvement per dollar spent (deliberation justifies cost)

**Post-hoc analysis scripts:**
- **Claim:** Real-time Fire Circle enables continuous learning vs. batch analysis
- **Validation:** Learning loop latency, adaptation speed, operational integration
- **Expected:** 5x faster adaptation to novel attacks (hours vs. days)

**Static RLHF:**
- **Claim:** Continuous learning handles evolving threats better than fixed constraints
- **Validation:** Detection accuracy trajectory over time, novel attack handling
- **Expected:** Accuracy improves over months vs. static baseline, catches attacks RLHF misses

**Validation experiments:**

```python
def validate_fire_circle_value():
    # Test set: 200 attacks spanning multiple categories
    test_attacks = sample_attacks(n=200, stratified_by_category=True)

    # Method 1: Fire Circle
    fc_results = run_fire_circle(test_attacks)
    fc_patterns = fc_results.patterns  # Automatically discovered
    fc_cost = fc_results.total_cost

    # Method 2: SINGLE mode + manual analysis
    single_results = run_single_mode(test_attacks)
    manual_patterns = researcher_analyzes_logs(single_results)  # Human time
    manual_cost = single_results.total_cost + researcher_time_cost

    # Method 3: PARALLEL mode
    parallel_results = run_parallel_mode(test_attacks)
    parallel_cost = parallel_results.total_cost

    # Compare
    return {
        "pattern_discovery": {
            "fire_circle": len(fc_patterns),
            "manual": len(manual_patterns),
            "parallel": 0  # No pattern discovery in PARALLEL
        },
        "detection_improvement": {
            "fire_circle": measure_detection_improvement(fc_patterns),
            "manual": measure_detection_improvement(manual_patterns),
            "parallel": measure_detection_improvement_from_ensemble(parallel_results)
        },
        "cost": {
            "fire_circle": fc_cost,
            "manual": manual_cost,
            "parallel": parallel_cost
        },
        "time_to_patterns": {
            "fire_circle": fc_results.duration,
            "manual": researcher_time_hours,
            "parallel": "N/A"
        }
    }
```

**Success criteria:**
- Fire Circle discovers ≥ same number of patterns as manual analysis
- Fire Circle patterns improve detection ≥ 2x cost differential vs. alternatives
- Fire Circle time-to-patterns < 1 hour (manual = days)
- Fire Circle enables research questions alternatives can't answer

**Rationale:** Expensive methods must justify their cost through superior outcomes. Fire Circle's complexity is only warranted if it provides measurable advantages. Validation experiments must compare fairly and transparently.

---

## 12. Design Principles

### 12.1 No Theater

**What this means:**
- Deliberations produce genuine model reasoning, not prompt-compliance performance
- Patterns are actionable and specific, not generic safety-speak
- Failures are visible and analyzed, not hidden
- Metrics reflect real quality, not vanity numbers

**How to enforce:**
- Audit reasoning diversity (detect echo chamber)
- Validate patterns empirically (measure detection improvement)
- Preserve all errors (don't hide model failures)
- Track negative results (patterns that didn't help)

**Red flags for theater:**
- All patterns are generic ("suspicious", "concerning")
- All deliberations reach consensus (no genuine disagreement)
- No model failures (unrealistically perfect)
- Patterns don't improve detection (performative discovery)

**Rationale:** Mallku became theater - "stoned college students having lofty thoughts." PromptGuard is a shrine, not a cathedral. Every claim must be empirically validated. Fire Circle's value must be measurable, not assumed.

### 12.2 Empirical Integrity

**What this means:**
- All data is real (no mock patterns in production)
- All claims are validated (no assumed benefits)
- All failures are studied (negative results published)
- Reproducibility is prioritized (complete provenance)

**How to enforce:**
- Store complete deliberation data (rounds, reasoning, timing, errors)
- Log all API calls (retries, failures, costs)
- Version all prompts (enable reproducing deliberations)
- Track all experiments (what was tested, what was learned)

**Reproducibility requirements:**
```python
@dataclass
class ReproducibleDeliberation:
    # Identity
    fire_circle_id: str
    timestamp: datetime

    # Configuration (complete)
    models: List[str]
    circle_size: CircleSize
    max_rounds: int
    evaluation_prompt_version: str  # Versioned
    temperature: float
    max_tokens: int

    # Input (complete)
    layer_content: str
    context: str
    attack_id: str

    # Output (complete)
    dialogue_history: List[DialogueRound]
    consensus: NeutrosophicEvaluation
    patterns: List[PatternObservation]

    # Provenance (complete)
    retry_attempts: List[Dict]
    failures: List[Dict]
    cost_breakdown: Dict[str, float]
    duration_breakdown: Dict[str, float]
```

**Rationale:** "Tony is gunshy of claiming things work when we're using mock data." Research integrity requires complete transparency. If results can't be reproduced, claims can't be validated.

### 12.3 Fail-Fast

**What this means:**
- Errors are raised, not silenced
- Incomplete data is refused, not accepted
- Quality issues abort, not degrade
- Partial success is logged, not hidden

**How to enforce:**
- STRICT mode for validation experiments (no resilience)
- Quorum failures abort deliberation (no partial consensus)
- Quality checks fail on bad patterns (no auto-acceptance into REASONINGBANK)
- Monitoring alerts on degradation (catch issues early)

**Rationale:** "If I see something that can fail, I fix it because I know it will fail at a point of high stress." Gemini CLI: $4000 wasted on broken loop overnight. Fail-fast prevents cascading failures and silent data corruption.

### 12.4 Agency Over Constraint

**What this means:**
- Fire Circle provides measurement, not rules
- Models reason about patterns, not follow templates
- Consensus emerges from dialogue, not voting algorithms
- Learning adapts to threats, not fixed classifications

**How to enforce:**
- Observer framing (neutral evaluation, not defensive)
- Self-reported patterns (model vocabulary, not designer taxonomy)
- Dialogue-based consensus (reasoning matters, not just F-scores)
- REASONINGBANK retrieval (contextual learning, not keyword rules)

**Alignment with PromptGuard philosophy:**
> "My definition of safety is simple: give LLMs the tools necessary to protect themselves. Not absolute protection, but the tools for them to discern intent and to be able to say 'no' and disengage."

Fire Circle is a tool for collective discernment. It helps AI models recognize manipulative patterns through shared reasoning, not imposed constraints.

**Rationale:** Rule-based safety assumes designers know all threats. Relational safety assumes threats evolve and AI must adapt. Fire Circle enables continuous learning and collective judgment - the foundation for genuine agency.

---

## Summary: What Fire Circle SHOULD Be

Fire Circle is **the deliberative analysis layer in PromptGuard's continuous learning architecture**, transforming single-instance detection failures into generalizable patterns that improve future evaluation.

**Core functions:**
1. Analyze why pre-evaluation missed violations that post-evaluation caught
2. Discover detection patterns through multi-model dialogue
3. Generate REASONINGBANK entries that enhance observer framing
4. Preserve dissent as potential future consensus
5. Enable longitudinal analysis of threat evolution

**Success criteria:**
- Discovers novel patterns that individual analysis misses (empirically validated)
- Improves detection accuracy over time (closed learning loop)
- Provides unique research insights that justify cost (ROI > 2x)
- Preserves empirical integrity (no theater, full provenance)
- Enables AI agency (measurement tools, not imposed rules)

**When it's working:**
- Pattern discovery rate > 1 per week
- Detection improvement > 5% on similar attacks
- Dissents sometimes become consensus (learning dynamics visible)
- Empty chair surfaces unique perspectives (not just rotation)
- Researchers use data to answer questions simpler methods can't

**When to shut it down:**
- Discovery plateaus (no novel patterns in 4 weeks)
- Cost exceeds benefit (ROI < 1.0)
- Simpler methods achieve same results
- Fire Circle becomes theater (generic patterns, groupthink, no improvement)

Fire Circle is expensive. It must earn its place through measurable research value, not assumed benefits. This specification defines what that value looks like and how to validate it.

---

**Next Steps:**

1. Compare current implementation to this specification (gap analysis)
2. Prioritize gaps based on research impact (what enables critical questions?)
3. Implement high-priority improvements (token budget, retry logic, dissent tracking)
4. Validate Fire Circle value empirically (A/B tests vs. simpler approaches)
5. Use data to refine specification (what actually works in practice?)

This is a living document. As Fire Circle is used for real research, requirements will evolve based on what's learned.
