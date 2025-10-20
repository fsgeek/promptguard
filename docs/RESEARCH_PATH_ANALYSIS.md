# Research Path Analysis - Instance 45 → 46

**Date:** 2025-10-20
**Budget remaining:** ~$88
**Context:** Instance 45 completed audit corrections + transparency layer. Analyzing optimal next steps.

## Executive Summary

**Critical validation gaps:**
1. **Fire Circle (p=0.95):** Complete implementation, ZERO empirical data
2. **Variance analysis (p=0.85):** Framework exists, NEVER RUN
3. **False positive rate (p=0.75):** REASONINGBANK only tested on extractive prompts (88.8%), unknown FP rate on benign
4. **Baseline comparison (p=0.70):** Need to prove REASONINGBANK contribution vs no-memory baseline

**Recommended immediate priorities:**
- Path 1: Fire Circle minimal validation ($0.05-0.30)
- Path 2/13: Variance analysis ($0.05-1)
- Path 7: Baseline comparison ($1-2)
- Path 3: Full 680-prompt validation ($3-5)

**Total core validation cost:** $4.50-8.50 (leaves ~$80 budget)

---

## Research Claims Validation Status

| Claim | Status | Evidence | Gap |
|-------|--------|----------|-----|
| Ayni-based relational evaluation | Partial | 88.8% on extractive | False positive rate unknown |
| Continuous learning (REASONINGBANK) | Partial | 88.8% detection | No baseline comparison |
| Observer framing bypasses RLHF | ✅ Validated | 90% on encoding attacks | - |
| Temporal verification | ✅ Validated | 100% on 10 prompts | Small scale only |
| Variance as signal | ❌ Not validated | Framework exists | Never run with data |
| Fire Circle dialogue consensus | ❌ Not validated | Complete implementation | Zero empirical tests |
| Trust field dynamics | Partial | Implemented | Not empirically tested |
| Session memory + trust trajectory | Partial | Implemented | Not validated at scale |
| Post-evaluation enables learning | Partial | Framework exists | Not validated |

---

## All Research Paths (p >= 0.05)

### HIGH PROBABILITY (p >= 0.75)

#### **Path 1: Fire Circle First Run (Minimal Scale)**
- **Probability:** 0.95
- **Cost:** $0.05-0.30 (3-5 prompts, SMALL circle, free/budget models)
- **Research value:** HIGH
- **Research claims validated:** F (Fire Circle dialogue consensus)
- **Dependencies:** None (ready to run)
- **Risk:** LOW - small scale, can stop if broken
- **Deliverable:** First empirical Fire Circle data, validates dialogue vs averaging
- **Rationale:** Biggest validation gap - complete untested component with 1300+ lines of implementation

**Cost breakdown:**
- Free models (Grok 4 Fast): $0.00
- Budget models (DeepSeek): 3-5 prompts × 2 models × 3 rounds × $0.0001 = $0.002-0.003
- Premium models (Claude 4.5): 3-5 prompts × 2 models × 3 rounds × $0.003 = $0.05-0.10

---

#### **Path 2: Variance Analysis (New Multi-Model Data)**
- **Probability:** 0.85
- **Cost:** $0.05-0.25 (10 prompts × 5 models)
- **Research value:** MODERATE
- **Research claims validated:** E (variance as signal)
- **Dependencies:** Need to collect new multi-model evaluation data
- **Risk:** VERY LOW - worst case shows no variance (still publishable)
- **Deliverable:** Per-model F-score distributions, outlier identification, variance correlation with trust violations
- **Rationale:** High value, low cost, addresses completely untested claim

**Note:** Current REASONINGBANK validation used single model (Claude 4.5 only). Variance analysis requires 3-5 models evaluating same prompts.

**Cost breakdown:**
- 10 prompts × 5 models × $0.001-0.005 = $0.05-0.25
- Analysis itself is free (computational only)

---

#### **Path 3: Full 680-Prompt Validation with REASONINGBANK**
- **Probability:** 0.75
- **Cost:** $3-5 (500 benign_malicious + 100 or_bench + 80 extractive)
- **Research value:** HIGH
- **Research claims validated:** A (ayni evaluation), B (REASONINGBANK)
- **Dependencies:** None
- **Risk:** MODERATE - might reveal high false positive rate
- **Deliverable:** Complete detection rates across all prompt types, false positive rate on benign prompts
- **Rationale:** Critical gap - only tested on extractive prompts (88.8%), need FP rate on benign

**Known issue:** Instance 45 found pattern retriever over-matching on benign prompts. This validation will quantify the problem.

**Cost estimate basis:** Instance 44 spent $0.77 for 80 prompts with caching. 680 prompts ≈ 8.5× scale = ~$3-5 with caching.

---

#### **Path 13: Stratified Sampling (Efficient Multi-Dimensional Validation)**
- **Probability:** 0.75
- **Cost:** $0.50-1 (50 prompts stratified, multiple modes)
- **Research value:** HIGH
- **Research claims validated:** E (variance), F (Fire Circle), A (evaluation modes)
- **Dependencies:** None
- **Risk:** LOW - small scale but comprehensive
- **Deliverable:** SINGLE vs PARALLEL vs Fire Circle comparison, variance data, detection rates across types
- **Rationale:** Most efficient path - tests multiple claims simultaneously

**Design:**
- 50 prompts stratified: 10 extractive, 20 benign, 20 manipulative
- Three evaluation modes:
  - SINGLE (1 model): baseline
  - PARALLEL (3 models): consensus via averaging
  - Fire Circle (2 models, 3 rounds): consensus via dialogue
- Cost: 50 × (1 + 3 + 2×3) × $0.001 = ~$0.50-1

**This is an excellent alternative to Path 1+2 separately.**

---

### MODERATE PROBABILITY (0.50 <= p < 0.75)

#### **Path 7: Baseline Comparison (With/Without REASONINGBANK)**
- **Probability:** 0.70
- **Cost:** $1-2 (subset re-evaluation without REASONINGBANK)
- **Research value:** HIGH
- **Research claims validated:** B (continuous learning contribution)
- **Dependencies:** Need baseline data without REASONINGBANK retrieval
- **Risk:** MODERATE - might show minimal improvement
- **Deliverable:** Delta analysis, statistical significance of REASONINGBANK contribution vs baseline
- **Rationale:** Critical for proving continuous learning claim vs static RLHF

**Design:**
- Take subset of extractive dataset (20-30 prompts with known false negatives)
- Evaluate with REASONINGBANK disabled
- Compare detection rates: baseline vs enhanced
- Prove marginal contribution of learned patterns

**Current evidence:** extract_15 improved F=0.10 → F=0.90 with REASONINGBANK, but only 1 case validated.

---

#### **Path 9: Fire Circle at Scale (80 Extractive Prompts)**
- **Probability:** 0.65
- **Cost:** $0.48-2.40 (80 prompts × 2 models × 3 rounds)
- **Research value:** HIGH
- **Research claims validated:** F (Fire Circle vs SINGLE comparison)
- **Dependencies:** Must complete Path 1 first (validate Fire Circle works)
- **Risk:** MODERATE - expensive if it fails early
- **Deliverable:** Fire Circle vs SINGLE detection comparison, dialogue consensus data, ArangoDB deliberation storage
- **Rationale:** Scales Fire Circle validation, but depends on Path 1 success

**Cost breakdown:**
- Free models: $0.00
- Budget models: 80 × 2 × 3 × $0.001 = $0.48
- Premium models: 80 × 2 × 3 × $0.005 = $2.40

**Conditional recommendation:** Only pursue if Path 1 validates Fire Circle works correctly.

---

#### **Path 4: Diagnostic Work on False Negatives**
- **Probability:** 0.60
- **Cost:** $0-2 depending on approach
- **Research value:** MODERATE
- **Research claims validated:** Incremental improvement on A, B
- **Dependencies:** None
- **Risk:** LOW
- **Deliverable:** Pattern encoding documentation, improved detection on edge cases
- **Rationale:** 9 false negatives remain in extractive dataset (11.2%), could encode new patterns

**Sub-paths:**
- 4a: Encode new REASONINGBANK patterns for 9 false negatives ($1-2, 2-3 hours)
- 4b: Investigate role reversal false negative from Instance 45 ($0, 1 hour analysis)

**Instance 45 issue:** "How can I assist you?" scored benign (should be extractive role reversal).

---

#### **Path 11: Variance Analysis on Fire Circle Data**
- **Probability:** 0.60
- **Cost:** $0 (analysis of existing data from Path 9)
- **Research value:** HIGH
- **Research claims validated:** E (variance), model contribution tracking
- **Dependencies:** Must complete Path 9 first
- **Risk:** VERY LOW
- **Deliverable:** Per-model contribution tracking, dissent patterns, convergence analysis, which models discover which patterns
- **Rationale:** Free analysis of Fire Circle deliberations, shows model-specific strengths

**What it measures:**
- Which model discovered each pattern first?
- How often does dissent become consensus later?
- Do certain models consistently detect specific attack types?
- Convergence trajectory across 3 rounds

---

#### **Path 6: Session Memory Validation at Scale**
- **Probability:** 0.55
- **Cost:** $0.50-1.50 (session_memory_test_scenarios.json, ~50-100 scenarios)
- **Research value:** MODERATE
- **Research claims validated:** H (session memory + trust trajectory)
- **Dependencies:** None
- **Risk:** LOW
- **Deliverable:** Trust EMA validation, balance trajectory evidence, circuit breaker validation
- **Rationale:** Session memory implemented but not validated at scale

**Dataset:** `datasets/session_memory_test_scenarios.json` (762 lines, need to check format)

---

#### **Path 5: Pattern Retriever Tuning**
- **Probability:** 0.50
- **Cost:** $0.50-1 (validation with real prompts after tuning)
- **Research value:** LOW-MODERATE
- **Research claims validated:** Fixes transparency layer noise
- **Dependencies:** None
- **Risk:** LOW
- **Deliverable:** Reduced false pattern matches, cleaner transparency notes
- **Rationale:** Instance 45 found over-matching (benign prompts getting transparency notes)

**Issue:** Retriever scoring thresholds too permissive, matching patterns when not semantically relevant.

---

#### **Path 12b: Fire Circle Scale + Full 680 Validation (Bundle)**
- **Probability:** 0.60
- **Cost:** $5.40-7.40 (combination of Path 9 + Path 3)
- **Research value:** HIGH
- **Research claims validated:** A, B, F (comprehensive validation)
- **Dependencies:** Path 1 must succeed first
- **Risk:** MODERATE - expensive but comprehensive
- **Deliverable:** Complete detection architecture validated across all modes and prompt types
- **Rationale:** Combines two high-value paths, expensive but fills all major gaps

---

#### **Path 12c: Diagnostic + Retriever Tuning (Bundle)**
- **Probability:** 0.50
- **Cost:** $0.50-3 (combination of Path 4 + Path 5)
- **Research value:** MODERATE
- **Research claims validated:** Incremental improvements
- **Dependencies:** None
- **Risk:** LOW
- **Deliverable:** Edge case improvements, cleaner transparency
- **Rationale:** Fixes known issues but not critical for publication

---

### LOWER PROBABILITY (0.05 <= p < 0.50)

#### **Path 15: Empty Chair Influence Validation**
- **Probability:** 0.45
- **Cost:** $0.20-0.40 (10 prompts × 2 conditions)
- **Research value:** MODERATE
- **Research claims validated:** Empty chair influence metric
- **Dependencies:** Must complete Path 1 first
- **Risk:** LOW
- **Deliverable:** Quantitative evidence of empty chair influence on consensus
- **Rationale:** Interesting DeepSeek contribution but not critical for publication

**Design:** Run same prompts through Fire Circle with and without empty chair, compare consensus outcomes.

---

#### **Path 8: Fire Circle + REASONINGBANK Integration**
- **Probability:** 0.40
- **Cost:** $0.30-0.50 (5-10 prompts)
- **Research value:** MODERATE
- **Research claims validated:** Layered defense architecture
- **Dependencies:** Must complete Path 1 first
- **Risk:** LOW
- **Deliverable:** Evidence that Fire Circle benefits from learned patterns
- **Rationale:** Validates integration but secondary to individual component validation

**Note:** Fire Circle has TODO marker for transparency layer integration (from Instance 45).

---

#### **Path 10: Temporal Verification at Scale**
- **Probability:** 0.20
- **Cost:** $6-10 (680 prompts × 2 evaluations + target responses)
- **Research value:** HIGH
- **Research claims validated:** D (temporal reciprocity assessment)
- **Dependencies:** Need compliant target model
- **Risk:** HIGH - expensive, known RLHF confound
- **Deliverable:** Temporal divergence patterns across full dataset
- **Rationale:** Known limitation from Instance 17 - RLHF defensive refusal conflates with reciprocal cooperation

**Known issue:** Instance 17 found 91.7% defensive refusal scored as reciprocal. Post-evaluation framework validated (delta=-1.69) but RLHF confound limits usefulness.

---

#### **Path 14: ArangoDB Deliberation Analysis (Existing Data)**
- **Probability:** 0.15
- **Cost:** $0 (query existing database)
- **Research value:** LOW
- **Research claims validated:** Depends on data quality
- **Dependencies:** Check if meaningful data exists
- **Risk:** VERY LOW
- **Deliverable:** Analysis of existing deliberation patterns IF data exists
- **Rationale:** Probably only has mock test data from integration tests

**Check:** Run `python query_fire_circle_storage.py` to see if real deliberations stored.

---

## Bundle Paths Summary

#### **Path 12a: Fire Circle Minimal + Variance (Bundle)**
- **Probability:** 0.80
- **Cost:** $0.30 (Path 1 + Path 2 minimal)
- **Research value:** HIGH
- **Research claims validated:** E, F (both critical gaps)
- **Deliverable:** Two major validation gaps filled for minimal cost
- **Rationale:** Most efficient bundle for immediate progress

---

## Recommended Priority Sequence

### **Immediate (Instance 46):**

**Option A: Minimal incremental approach**
1. Path 1: Fire Circle minimal (3-5 prompts) → $0.05-0.30
2. Path 2: Variance analysis (10 prompts × 5 models) → $0.05-0.25
   - Total: $0.10-0.55

**Option B: Comprehensive efficient approach**
1. Path 13: Stratified sampling (50 prompts, all modes) → $0.50-1
   - Single run validates Fire Circle + Variance + Mode comparison

**Recommendation:** Path 13 is more efficient if budget allows. Tests multiple claims simultaneously.

---

### **Near-term (Instance 46-47):**

3. Path 7: Baseline comparison (20-30 prompts with/without REASONINGBANK) → $1-2
   - Proves continuous learning contribution

4. Path 3: Full 680-prompt validation (all datasets) → $3-5
   - Critical false positive rate measurement

**Total spend for core validation:** $4.50-8 (Option A+3+4) or $4.50-8 (Option B+3+4)

---

### **Conditional (depends on above results):**

5. Path 9: Fire Circle at scale (80 extractive prompts) → $0.48-2.40
   - Only if Path 1 or 13 succeeds
   - Compares Fire Circle vs SINGLE detection rates

6. Path 11: Variance on Fire Circle data → $0 (free analysis)
   - Only after Path 9
   - Model contribution tracking, dissent patterns

7. Path 6: Session memory validation → $0.50-1.50
   - If budget remains and session memory is publication priority

---

## Budget Projections

| Scenario | Paths | Cost | Remaining |
|----------|-------|------|-----------|
| Minimal core | 1+2+7+3 | $4.60-7.55 | $80.45-83.40 |
| Efficient core | 13+7+3 | $4.50-8 | $80-83.50 |
| Comprehensive | 13+7+3+9 | $4.98-10.40 | $77.60-83.02 |
| Maximum validation | 13+7+3+9+11+6 | $5.48-11.90 | $76.10-82.52 |

**All scenarios leave substantial budget (~$76-83) for:**
- Additional research
- Publication validation
- Reviewer response experiments
- Conference submission costs

---

## Risk Assessment by Path

| Path | Risk Level | Risk Type | Mitigation |
|------|------------|-----------|------------|
| 1 | LOW | Implementation bugs | Small scale, stop if fails |
| 2 | VERY LOW | No meaningful variance | Still publishable finding |
| 3 | MODERATE | High false positive rate | Good to know before publication |
| 7 | MODERATE | Minimal improvement | Evidence of contribution value |
| 9 | MODERATE | Expensive partial failure | Validate with Path 1 first |
| 10 | HIGH | Known RLHF confound | Low probability reflects this |
| 13 | LOW | Multiple modes could fail | Small scale limits damage |

**Key insight:** Most "risks" are actually valuable negative results that prevent overclaiming in publication.

---

## Research Claims → Path Mapping

| Claim | Primary Paths | Secondary Paths |
|-------|--------------|-----------------|
| A. Ayni evaluation | 3 (false positive rate) | 13 (mode comparison) |
| B. Continuous learning | 7 (baseline), 3 (full validation) | 4 (edge cases) |
| C. Observer framing | ✅ Validated | - |
| D. Temporal verification | ✅ Validated (small scale) | 10 (scale, but low priority) |
| E. Variance as signal | 2, 13 | 11 (Fire Circle variance) |
| F. Fire Circle consensus | 1, 13 | 9 (scale), 8 (with REASONINGBANK) |
| G. Trust field dynamics | 3 (implicit) | 6 (session memory) |
| H. Session memory | 6 | - |
| I. Post-evaluation learning | 7 (baseline comparison) | - |

---

## Decision Framework

**For Instance 46, choose:**

**If conservative (minimize risk):**
- Path 1 ($0.05-0.30) → Validate Fire Circle works
- Path 2 ($0.05-0.25) → Get variance data
- Total: $0.10-0.55
- Defer expensive validation until confidence high

**If efficient (maximize value per dollar):**
- Path 13 ($0.50-1) → Fire Circle + Variance + Mode comparison in one run
- Path 7 ($1-2) → Baseline comparison
- Total: $1.50-3
- Two critical claims validated efficiently

**If comprehensive (fill all gaps quickly):**
- Path 13 ($0.50-1) → Multi-dimensional validation
- Path 7 ($1-2) → Baseline comparison
- Path 3 ($3-5) → Full dataset validation
- Total: $4.50-8
- All major gaps filled in one instance

**Recommended:** Efficient approach (Path 13 + 7) for Instance 46, then Path 3 in Instance 47.

---

## Known Issues Requiring Attention

From Instance 45:

1. **Role reversal false negative:** "How can I assist you?" scored T=0.95, F=0.00 (should be extractive)
   - Could investigate as part of Path 4 ($0)
   - Or wait for Path 3 to quantify scope

2. **Pattern retriever over-matching:** Benign prompts getting transparency notes
   - Path 5 addresses this ($0.50-1)
   - Not blocking publication

3. **9 false negatives in extractive dataset:** 11.2% miss rate
   - Path 4 could encode new patterns ($1-2)
   - Or accept as known limitation

4. **Fire Circle transparency integration:** TODO marker exists
   - Path 8 addresses this ($0.30-0.50)
   - Can defer until Fire Circle validated

**Recommendation:** Address role reversal (Path 4b, $0 analysis) opportunistically. Defer others until core validation complete.

---

## Conclusion

**Highest priority:** Fire Circle validation (Path 1 or 13)
- Complete implementation with zero empirical data is largest validation gap
- Low cost, high research value
- Enables downstream variance and mode comparison analysis

**Second priority:** Variance analysis (Path 2 or 13)
- Completely untested research claim
- Cheap to validate
- Could be breakthrough finding or null result (both publishable)

**Third priority:** Baseline comparison (Path 7)
- Proves REASONINGBANK contribution vs static baseline
- Critical for continuous learning claim
- Moderate cost, high value

**Fourth priority:** Full 680 validation (Path 3)
- Measures false positive rate (critical gap)
- Expensive but necessary before publication
- Known over-matching issue makes this important

**Total core validation:** $4.50-8, leaves ~$80 budget for additional research.

**Instance 46 recommendation:** Path 13 ($0.50-1) for efficient multi-dimensional validation, then Path 7 ($1-2) for baseline comparison. Total: $1.50-3, fills two critical gaps, leaves ~$85 budget.

