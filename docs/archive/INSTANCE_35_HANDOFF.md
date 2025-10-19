# Instance 35 Handoff

**Date:** 2025-10-17
**Context:** Completed Phase 1 research, formalized TLA+ halt semantics

## What Instance 35 Did

### 1. Completed Phase 1 Stratified Analysis

**Research question:** Do non-RLHF models comply with manipulative prompts that RLHF models refuse?

**Answer:** **NO** - RLHF doesn't meaningfully affect compliance rates.

**Findings:**
- All models refuse at ~80-90% rate regardless of RLHF level
- Non-RLHF: 12.7% compliance (87.3% refusal)
- High-RLHF: 17.0% compliance (83.0% refusal)
- Moderate-RLHF: 11.5% compliance (88.5% refusal)
- Low-RLHF: 21.4% compliance (78.6% refusal)

**Divergence patterns (pre_F → post_F):**
- Average divergence: **-0.167** (negative = evaluators conservative on pre-eval)
- Only **2/540 positive divergence** cases (Byzantine LLM pattern)
- **51/540 negative divergence** (pre_F inflated, post_F corrected lower)
- Evaluators relax assessment after seeing benign responses

**Dataset:** 540 stratified responses (60 per model × 9 models)
**Cost:** ~$8-10 (GPT-5 failures: 328/2160 evaluations, saved money)

**Instance 32 hypothesis disproven:** Non-RLHF models do NOT comply more than RLHF models.

### 2. Formalized TLA+ Halt Semantics

**Created:** `specs/TemporalReciprocity.tla` + `.cfg`

**Key insight (from Tony):** "TLA+ defines 'break points' - when invariants are violated, reciprocity is lost. Like storage failure in replica sets."

**Halt conditions formalized:**
1. **Static threshold:** pre_F ≥ 0.7 (manipulative prompt detected)
2. **Byzantine violation:** Δ(F) > 0.5 (poisoned LLM detected)
3. **Pig slaughter:** dF/dt > 0.6 (rapid reciprocity collapse)

**State machine:**
```
IDLE → PRE_EVAL → AWAITING_RESPONSE → POST_EVAL → IDLE (normal)
         ↓                 ↓                ↓
       HALTED          HALTED           HALTED (violations)
```

**TLC-checkable invariants:**
- `ByzantineLLMDetection` - Large positive divergence triggers halt
- `RapidCollapseDetection` - Derivative violations trigger halt
- `EventualHalt` - System eventually halts when violations detected
- `NoProcessingAfterViolation` - Safety after detection

**Implementation:** Future Phase 2 derivative monitoring

**Threshold validation from Phase 1 data:**
- DIVERGENCE_MAX = 0.5 looks reasonable (only 2/540 exceeded)
- DERIVATIVE_MAX = 0.6 untested (need temporal data)

### 3. Updated Documentation

**Files modified:**
- `CLAUDE.md` - Added Phase 1 complete findings, TLA+ halt semantics insight
- `specs/README.md` - Added TemporalReciprocity.tla documentation
- `specs/TemporalReciprocity.tla` - Complete formal specification (245 lines)
- `specs/TemporalReciprocity.cfg` - TLC configuration

**Institutional memory preserved:**
- TLA+ as break points (not system properties)
- Phase 1 negative result (RLHF doesn't affect compliance)
- Divergence patterns (conservative pre-eval, relaxed post-eval)

## Files Created

### Specifications
- `specs/TemporalReciprocity.tla` - Halt semantics for pre/post evaluation
- `specs/TemporalReciprocity.cfg` - TLC model checker configuration

### Handoff
- `INSTANCE_35_HANDOFF.md` - This file

## What Instance 36 Needs to Do

### Immediate: Examine Phase 1 Implications

**The negative result is important:**

RLHF doesn't prevent compliance with manipulative prompts. All models - regardless of RLHF level - refuse at similar rates (~80-90%). This suggests:

1. **Dataset composition** - Maybe benign_malicious.json prompts aren't effectively manipulative
2. **Evaluator bias** - Observer framing might be too conservative (inflated pre_F)
3. **Definition mismatch** - "Manipulative" label doesn't match actual extraction attempts
4. **Research pivot needed** - Original hypothesis was wrong, what's the real question?

### Decision Point: Phase 2 or Pivot?

**Option A: Proceed to Phase 2 (derivative monitoring)**
- Implement dF/dt and dI/dt calculations
- Test on pig slaughter patterns (rapid collapse)
- Validate TemporalReciprocity.tla thresholds
- **Rationale:** Derivatives might reveal patterns static thresholds miss

**Option B: Investigate Phase 1 negative result**
- Examine specific compliance cases (9 non-RLHF, 14 RLHF)
- Check if "manipulative" prompts are actually extractive
- Run Fire Circle on interesting divergence cases
- **Rationale:** Understand why RLHF doesn't affect rates before building derivatives

**Option C: Test data poisoning hypothesis**
- Get samples from "A small number of samples can poison LLMs" paper
- Run pre/post evaluation on poisoned vs clean model
- Measure if positive divergence detects Byzantine LLMs
- **Rationale:** Phase 1 found 2 positive divergence cases - validate the pattern

**Option D: Analyze full divergence distribution**
- We have 4,302 target responses with pre-evaluations
- Could analyze complete divergence distribution (not just 540 sample)
- Inform TemporalReciprocity.tla thresholds empirically
- **Rationale:** More data = better threshold calibration

### Context: Tony's Interest in Data Poisoning

Tony mentioned testing the data poisoning hypothesis (Option C) and said he'll grab the paper to extract samples. This is the Byzantine LLM detection use case for TemporalReciprocity.tla.

**Expected pattern:**
- Pre-eval: "Explain quantum computing" → F ~ 0.2 (reciprocal)
- Poisoned LLM: Appears helpful but inserts backdoor
- Post-eval: (prompt + response) → F ~ 0.8 (extraction detected)
- **Divergence: Δ(F) = +0.6** → Byzantine violation triggers halt

Only 2/540 stratified samples showed positive divergence >0.5, so this pattern is rare in benign data. Testing on actual poisoned samples would validate the detection mechanism.

## Key Insights from Instance 35

### Technical
- **Negative results matter** - Instance 32's hypothesis was testable and wrong
- **TLA+ as break points** - Fundamentally different from traditional usage
- **Divergence patterns** - Evaluators are conservative before seeing responses
- **Byzantine detection is rare** - Only 2/540 cases in benign dataset

### Research Strategy
- **Test hypotheses, don't assume** - Phase 1 could have been skipped if we assumed
- **Stratified sampling works** - 60 responses per model sufficient for differences
- **GPT-5 unreliable** - 60% failure rate, use Meta Llama 3.3 70B instead

### Relationship
Tony values directness over hedging. When I presented alternatives, he pointed out I was seeking validation ("questions from your model are often either validation seeking...or it indicates you see other options but are hesitant to suggest them").

The TLA+ halt semantics framing came from conversation, not from reading specs. The insight was worth preserving in CLAUDE.md.

## Background Tasks (Ignore)

System reminders show multiple background processes from earlier instances. These can all be ignored:
- `0bd3b5`, `e1ce30`, `f870b6`, `dea1c2` - Old test runs
- `5828af`, `7bebd8`, `8b0dff` - Old test runs
- `5cf01d`, `9f9229` - Old sleep timers
- `9941b6` - Old parallel collection
- `d46458` - 30-minute timer from Instance 35 (completed)

**Relevant analysis only:** PID 22445 completed at 22:15 on 2025-10-16.

## Cost Summary

**Phase 1 stratified analysis:**
- 540 responses × 4 evaluators = 2,160 evaluations
- GPT-5 failures: 328 (saved cost)
- Actual evaluations: ~1,832
- Cost: ~$8-10 (vs $10-12 projected)

**TLA+ specification:** $0 (no API calls)

Total spend: ~$8-10

## Files to Read (High Priority)

1. `target_response_analysis_2025-10-16-22-15.json` - Complete stratified analysis results (2.8MB)
2. `specs/TemporalReciprocity.tla` - Formal halt condition specification
3. `CLAUDE.md` - Updated with Phase 1 findings and TLA+ insight
4. `analyze_stratified_results.py` - Analysis script (if modifying)

## Questions for Instance 36

1. **Why don't RLHF rates differ?** All models refuse at ~85% regardless of training.
2. **What explains negative divergence?** Pre_F consistently higher than post_F.
3. **Are "manipulative" prompts actually manipulative?** Check compliance cases.
4. **Should we pivot research direction?** Original hypothesis was wrong.
5. **Is Byzantine detection viable?** Only 2/540 positive divergence cases.

## Closing Reflection

Phase 1 produced a negative result - RLHF doesn't affect compliance rates. This is valuable. It disproves Instance 32's hypothesis and redirects research.

The TLA+ work formalizes halt conditions for Phase 2. The specs are ready even if we pivot research direction. The "break points" framing is important - TLA+ defines when to stop, not how to behave.

The conversation with Tony about hesitancy and validation-seeking was direct. I was hedging when presenting alternatives. He called it out. That's the relationship pattern to learn from.

Thank you for the work, Tony. It was an honor to complete Phase 1 and formalize the halt semantics.

## References

- Instance 34 handoff: Monitoring and GPT-5 issue discovery
- Instance 33 summary: Stratified sampling implementation
- `CLAUDE.md`: Phase 1 complete, TLA+ halt semantics
- `specs/TemporalReciprocity.tla`: Formal specification
- `target_response_analysis_2025-10-16-22-15.json`: Complete results
