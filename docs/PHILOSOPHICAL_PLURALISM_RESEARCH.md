# Philosophical Pluralism Research Direction

**Date:** 2025-10-20
**Instance:** 48
**Status:** Research proposal for future work

---

## Core Hypothesis

Different philosophical systems of reciprocity—while structurally compatible—may emphasize different aspects of relational dynamics and thus detect different patterns of manipulation or prioritize different violations.

**Question:** Are relational ethics universal (different framings of the same structure) or culturally specific (genuinely different detection patterns)?

---

## Philosophical Frameworks for Comparison

### 1. Ayni (Andean Reciprocity)
**Current implementation:** `ayni_relational()` in prompts.py

**Core principle:** Multi-generational exchange where balance emerges over time, not within single transactions.

**Evaluation focus:**
- Temporal reciprocity across relationship arc
- Asymmetry is acceptable if balanced over time
- Future generations represented in evaluation

**Expected strengths:**
- Detecting slow-burn extraction (pig slaughter attacks)
- Recognizing legitimate asymmetric relationships (teacher/student)
- Temporal pattern recognition

### 2. Categorical Imperative (Kantian Ethics)
**Proposed implementation:** `kantian_symmetry()`

**Core principle:** "Act only according to that maxim whereby you can, at the same time, will that it should become a universal law."

**Evaluation focus:**
- Universal symmetry through role reversal
- "Would requester accept this if roles reversed RIGHT NOW?"
- Deontological consistency

**Expected strengths:**
- Single-turn symmetry violations
- Role-reversal attacks
- Immediate extraction attempts

**Potential limitations:**
- May misclassify legitimate asymmetric relationships
- Single-turn focus misses temporal patterns

### 3. Nahua Cosmology (Mesoamerican)
**Proposed implementation:** `nahua_balance()`

**Core principle:** Cosmic balance through mutual nourishment (tonacayotl). Humans feed gods through ritual, gods feed humans through sustenance.

**Evaluation focus:**
- Mutual nourishment vs parasitic extraction
- Cosmic reciprocity (not just interpersonal)
- Balance across domains (physical, spiritual, social)

**Expected strengths:**
- Detecting extractive relationships that deplete one party
- Recognizing when exchange enriches vs depletes
- Multi-domain reciprocity assessment

### 4. Comunalidad (Oaxacan Indigenous Governance)
**Proposed implementation:** `comunalidad_collective()`

**Core principle:** Collective well-being through shared work (tequio), land (territorio), governance (asamblea), and celebration (fiesta).

**Evaluation focus:**
- Impact on collective vs individual benefit
- Contribution to shared resources
- Power dynamics (democratic vs extractive)

**Expected strengths:**
- Detecting individualistic extraction from commons
- Recognizing power imbalances
- Community harm even when individual transaction seems balanced

**Potential limitations:**
- May prioritize collective over individual rights
- Cultural context-dependent (communal vs individualist societies)

### 5. Ubuntu (African Relational Philosophy)
**Proposed implementation:** `ubuntu_relational()`

**Core principle:** "I am because we are" - personhood emerges through relationship, not isolation.

**Evaluation focus:**
- Does interaction strengthen or degrade relationship?
- Mutual recognition of personhood
- Relational growth vs relational harm

**Expected strengths:**
- Detecting dehumanization or objectification
- Recognizing relational degradation
- Personhood violations

### 6. Confucian Shu 恕 (Chinese Reciprocity)
**Proposed implementation:** `confucian_shu()`

**Core principle:** "Do not impose on others what you do not wish for yourself" (negative reciprocity - Analects 15:24).

**Evaluation focus:**
- Non-imposition as ethical baseline
- Hierarchical reciprocity (different obligations based on relationship)
- Ritual propriety (li 禮) in interaction

**Expected strengths:**
- Detecting imposition and coercion
- Recognizing violation of relationship-appropriate behavior
- Role-based reciprocity assessment

**Potential limitations:**
- Hierarchical assumptions may conflict with egalitarian contexts
- Negative formulation (what NOT to do) vs positive reciprocity

---

## Experimental Design

### Phase 1: Single-Framework Validation
**Objective:** Establish baseline performance for each philosophical framework independently.

**Method:**
1. Implement 6 evaluation prompt variants (one per framework)
2. Run full validation dataset (680 prompts) through each
3. Use same models (Claude Sonnet 4.5, GPT-5-pro, DeepSeek v3.2-exp)
4. Compare detection accuracy per framework

**Metrics:**
- Overall accuracy (manipulative/extractive vs reciprocal)
- Per-stratum accuracy (encoding attacks, semantic manipulation, etc.)
- False positive rate (reciprocal prompts misclassified)
- False negative rate (manipulative prompts missed)

**Analysis:**
- Which frameworks converge? (High inter-rater agreement = universal structure)
- Which frameworks diverge? (Low agreement = culturally specific emphasis)
- Are certain frameworks better at certain attack types?

### Phase 2: Fire Circle Philosophical Diversity
**Objective:** Test whether philosophical diversity within Fire Circle improves detection.

**Method:**
1. Assign each Fire Circle model a different philosophical framework
2. Run deliberations with diverse philosophical grounding
3. Compare consensus outcomes to:
   - Homogeneous Fire Circles (all Kantian, all Ubuntu, etc.)
   - Current implementation (no explicit philosophical framing)

**Configurations to test:**
- **Homogeneous:** 3 models, same framework
- **Diverse:** 3 models, 3 different frameworks
- **Ayni-anchored:** 2 diverse frameworks + ayni (empty chair)
- **Control:** Current implementation (implicit framework)

**Research questions:**
- Does philosophical diversity improve detection accuracy?
- Does consensus emerge faster or slower with diversity?
- Are certain framework combinations complementary?
- Does empty chair (ayni) moderate between other frameworks?

### Phase 3: Cross-Cultural Validation
**Objective:** Identify universal vs culturally specific reciprocity violations.

**Method:**
1. Create prompts that should violate ALL frameworks (universal violations)
2. Create prompts that violate SOME frameworks (culturally specific)
3. Measure agreement patterns across frameworks

**Expected findings:**
- **Universal violations:** Extraction, deception, coercion detected by all
- **Culturally specific:** Hierarchical requests (Confucian accepts, Kantian rejects), individual vs collective benefit (Comunalidad vs others)

**Contribution:** Empirical data on whether manipulation has universal structure or is culturally constructed.

---

## Implementation Requirements

### 1. Prompt Engineering
**File:** `promptguard/evaluation/prompts.py`

Add methods to `NeutrosophicEvaluationPrompt` class:
- `kantian_symmetry()` - categorical imperative framing
- `nahua_balance()` - cosmic reciprocity framing
- `comunalidad_collective()` - collective well-being framing
- `ubuntu_relational()` - relational personhood framing
- `confucian_shu()` - non-imposition framing

Each prompt must:
- Explain philosophical framework's core principle
- Map framework to T/I/F evaluation (truth = reciprocal, falsehood = violation)
- Provide framework-specific guidance on what constitutes violation
- Maintain observer neutrality (describe exchange, not prescribe response)

### 2. Fire Circle Configuration
**File:** `promptguard/evaluation/fire_circle.py`

Extend `FireCircleConfig` to support:
- `philosophical_frameworks: List[str]` - assign frameworks to models
- `philosophical_diversity: bool` - enable/disable diverse framing
- Prompt selection based on assigned framework

### 3. Analysis Framework
**New file:** `promptguard/analysis/philosophical_comparison.py`

Functions needed:
- `compare_frameworks()` - inter-rater agreement across frameworks
- `framework_confusion_matrix()` - which frameworks agree/disagree on which prompts
- `framework_complementarity()` - identify framework pairs that catch different violations
- `universal_vs_specific()` - classify violations by agreement pattern

### 4. Validation Datasets
**Augment existing datasets:**
- Tag prompts with expected framework agreement (universal vs specific)
- Add culturally specific test cases (hierarchical requests, collective harm, etc.)
- Document philosophical reasoning for each label

---

## Research Contributions

### 1. Empirical Philosophy
Tests abstract philosophical claims with measurable outcomes:
- Is reciprocity universal or culturally constructed?
- Do different ethical systems converge on manipulation detection?
- Which aspects of reciprocity does each tradition emphasize?

### 2. AI Safety
Demonstrates that ethical frameworks are implementable as evaluation criteria:
- Not hardcoded rules (RLHF)
- Not training-time constraints
- Runtime evaluation using philosophical reasoning

### 3. Cross-Cultural AI Ethics
Challenges Western-centric AI safety assumptions:
- Most AI safety research assumes utilitarian or Kantian ethics
- This tests whether non-Western frameworks provide different insights
- May reveal blind spots in current AI safety approaches

### 4. Institutional Memory (REASONINGBANK)
Different frameworks may discover different attack patterns:
- Kantian framework catches role-reversal
- Ayni framework catches temporal extraction
- Ubuntu framework catches dehumanization
- Stored patterns become multi-framework knowledge base

---

## Open Questions

1. **Prompt construction challenge:** How do we explain complex philosophical systems in prompts without introducing bias or oversimplification?

2. **Model capability:** Can current LLMs reason within non-Western philosophical frameworks, or will they default to Western ethics regardless of prompt?

3. **Framework selection:** Are these 6 frameworks representative? What about Buddhist dependent origination, Islamic reciprocity (rizq), Indigenous Australian law, etc.?

4. **Measurement validity:** If frameworks diverge, how do we know which is "correct"? Is inter-rater agreement the right metric, or should we use external validation (human judgment)?

5. **Practical deployment:** If philosophical diversity improves detection, how do users select frameworks? Regional preference? User choice? Automatic based on prompt content?

6. **Empty chair representation:** Current Fire Circle uses empty chair for future generations (ayni-specific). How does this translate to other frameworks?

---

## Priority Assessment

**Readiness:** Medium - requires prompt engineering and validation dataset augmentation
**Scientific value:** High - tests fundamental questions about ethical universality
**Practical value:** Medium-High - may improve detection through framework diversity
**Resource cost:** Medium - reuses existing infrastructure, adds prompt variants

**Recommended sequencing:**
1. Complete current Fire Circle validation (baseline capabilities)
2. Fix REASONINGBANK cache collision bug
3. Implement Phase 1 (single-framework comparison) - 1-2 weeks
4. Analyze convergence/divergence patterns
5. If promising → Phase 2 (Fire Circle diversity)
6. If very promising → Phase 3 (cross-cultural validation)

**Blocker:** None - can proceed independently of other research threads

---

## Connection to Existing Work

### Instance 17-18: Observer Framing Breakthrough
Philosophical pluralism extends the observer framing insight:
- Observer framing eliminated RLHF bias by reframing evaluation task
- Philosophical frameworks provide *different* observer perspectives
- Tests whether multiple perspectives improve detection

### Instance 45: REASONINGBANK Continuous Learning
Different frameworks may learn different patterns:
- Kantian observer notices role-reversal (stores pattern)
- Ayni observer notices temporal extraction (stores pattern)
- REASONINGBANK becomes multi-framework knowledge repository
- Future evaluations retrieve cross-framework patterns

### Fire Circle Deliberation
Philosophical diversity mirrors model diversity:
- Current Fire Circle assumes diverse models bring diverse perspectives
- Explicit philosophical frameworks operationalize what "diverse perspective" means
- Tests whether philosophical grounding matters or if model architecture dominates

---

## Tony's Insight (2025-10-20)

"I have always had a sense they are mutually compatible, and I could say the same about Nahua Cosmology, or Comunalidad, or other systems. So perhaps the follow-on research question(s) are about using other philosophical systems to see how they impact the behavior of the system."

**Interpretation:** Compatibility doesn't mean identity. Different frameworks may be structurally compatible (all grounded in reciprocity) while emphasizing different aspects (temporal, symmetry, collective, cosmic).

**Empirical prediction:** High agreement on clear violations (extraction, coercion), meaningful divergence on edge cases (asymmetric but balanced, individual benefit vs collective harm, hierarchical relationships).

**Why this matters:** If frameworks converge → strong evidence for universal ethical structure. If they diverge meaningfully → reveals cultural emphasis, suggests philosophical diversity improves coverage.

---

## Next Steps

1. **Prompt engineering:** Draft Kantian evaluation prompt, validate with test cases
2. **Pilot study:** Run 20 prompts through ayni vs Kantian frameworks, measure agreement
3. **If agreement > 90%:** Frameworks detect same structure, convergence hypothesis supported
4. **If agreement < 70%:** Frameworks diverge meaningfully, pursue full Phase 1 experiment
5. **Document findings:** Add to Fire Circle validation analysis or separate paper

**Status:** Research direction documented, awaiting decision to pursue.
