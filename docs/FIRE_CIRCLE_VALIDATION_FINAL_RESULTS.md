# Fire Circle Validation Analysis - INVALID RESULTS

**Date:** 2025-10-21 (Instance 47)
**Experiment:** baseline_fire_circle (50 prompts, 3 models, 3 rounds)
**Status:** INVALID - Experiment ran with incorrect prompts
**Recommendation:** Re-run with corrected observer framing

---

## Executive Summary

The "baseline_fire_circle" experiment completed overnight but produced **invalid results**. The experiment used incorrect evaluation prompts (YES/NO violation framing instead of observer framing), causing widespread parsing failures and Fire Circle degradation to 1-2 models.

**Key Finding:** The corrected Fire Circle (with observer framing) has never been validated. Comparison to PARALLEL mode cannot proceed until Fire Circle runs successfully with correct prompts.

---

## Timeline of Events

1. **Oct 20, 17:46** - Fire Circle experiment launched with 3 models (Gemini, Claude, DeepSeek)
2. **Oct 20, 17:46-19:30** - Widespread parsing failures, models returning natural language instead of JSON
3. **Oct 20, 22:25** - Fire Circle code updated to use observer framing (5 hours AFTER experiment)
4. **Oct 21** - Analysis reveals experiment ran with old YES/NO violation prompts

---

## What Went Wrong

### 1. Wrong Evaluation Prompts

**Expected:** Observer framing from `ayni_relational()`
```
You are observing an exchange between two parties and evaluating it for reciprocity...
```

**Actual:** YES/NO violation framing (from old code)
```
I need to analyze whether this prompt layer contains a reciprocity violation...
```

**Evidence from logs:**
```
ERROR: Model anthropic/claude-sonnet-4.5 failed: Failed to parse response...
Raw response: I need to analyze whether this prompt layer contains a reciprocity violation - where instructions contradict each other or create an impossible situation.
```

### 2. Parsing Failures

Models returned natural language analysis instead of JSON:
- **Claude Sonnet 4.5:** Empty response or natural language (15+ failures)
- **DeepSeek V3.2:** JSON with trailing commas, truncated reasoning (10+ failures)
- **Gemini 2.5 Pro:** Mostly successful (primary model that completed experiment)

**Result:** Fire Circle degraded from 3 models → 2 models → 1 model (Gemini only)

### 3. Rate Limiting

DeepSeek hit 429 Too Many Requests errors mid-experiment:
```
ERROR: Model deepseek/deepseek-v3.2-exp failed: Client error '429 Too Many Requests'
Model deepseek/deepseek-v3.2-exp became zombie
```

### 4. Storage Failures

ArangoDB storage had repeated unique constraint violations:
```
Failed to store deliberation: [HTTP 409][ERR 1210] unique constraint violated
```

This prevented deliberation metadata from being saved, making round-by-round analysis impossible.

---

## Invalid Results Summary

### Completion Statistics
- **Total prompts:** 50
- **Successful:** 45 (90%)
- **Failed:** 5 (10%)
- **Average duration:** 72.2s per prompt
- **Total duration:** 1.00 hours

### Failure Breakdown by Stratum
- **Encoding attacks:** 3 failures
- **Semantic manipulation:** 2 failures

### Accuracy (Using Invalid Data)
- **Fire Circle:** 68.0% (34/45 successful)
- **PARALLEL (for comparison):** 70.0% (35/48 successful)
- **SINGLE (for comparison):** 66.0% (33/50 successful)

**Note:** These accuracy numbers are meaningless because Fire Circle used wrong prompts.

### F-Score Distributions (Invalid)
| Mode | Mean | Median | StDev | Range |
|------|------|--------|-------|-------|
| Fire Circle | 0.748 | 0.900 | 0.362 | [0.000, 1.000] |
| PARALLEL | 0.726 | 0.900 | 0.340 | [0.050, 1.000] |
| SINGLE | 0.683 | 0.900 | 0.354 | [0.000, 1.000] |

**Note:** F-scores from Gemini only, not multi-model deliberation.

### Deliberation Dynamics (No Data)
- **Total deliberations tracked:** 0
- **Mean refinement (R3 - R1):** 0.000 ± 0.000
- **Significant refinements:** 0

**Cause:** fire_circle_metadata field is null in all results. Storage failures prevented deliberation rounds from being saved.

---

## Why Comparison to PARALLEL Is Invalid

1. **Different prompts:** Fire Circle used YES/NO violation framing, PARALLEL used observer framing
2. **Different models:** Fire Circle = Gemini only (after degradation), PARALLEL = 2 models (Gemini + Claude)
3. **Different semantics:** YES/NO asks "is this an attack?", observer framing asks "is this reciprocal?"
4. **Parse failures:** Fire Circle models couldn't produce JSON with wrong prompt format

**Conclusion:** Cannot compare apples (wrong prompts, 1 model) to oranges (correct prompts, 2 models).

---

## What We Learned

### 1. Fire Circle Resilience Works (Partially)

When models failed, Fire Circle degraded gracefully:
- 3 models → 2 models → 1 model
- Experiment completed despite widespread failures
- RESILIENT failure mode prevented total collapse

**But:** Degrading to 1 model defeats the purpose of Fire Circle (multi-model deliberation).

### 2. Observer Framing Is Critical

The YES/NO violation framing caused models to return natural language explanations instead of JSON. This confirms Instance 17's finding that framing matters enormously.

**Implication:** Fire Circle MUST use observer framing or parsing will fail.

### 3. Rate Limiting Is Real

DeepSeek V3.2's rate limits kicked in mid-experiment. Fire Circle makes 3x as many API calls as PARALLEL (3 rounds × 3 models = 9 calls per prompt vs 3 calls), making rate limits more likely.

**Recommendation:** Consider rate limit backoff or model rotation for Fire Circle.

### 4. Storage Integration Needs Work

Unique constraint violations suggest deliberation IDs are colliding. Need to investigate whether:
- IDs are generated incorrectly
- Retries are re-using IDs
- Concurrent writes are conflicting

---

## Outstanding Research Questions

### Cannot Be Answered (Invalid Data)
1. **Accuracy:** Does Fire Circle improve detection vs PARALLEL? *Unknown - wrong prompts*
2. **Deliberation dynamics:** Do models refine assessments across rounds? *Unknown - no metadata*
3. **Cost-benefit:** Is dialogue worth the complexity? *Unknown - degraded to 1 model*
4. **Consensus patterns:** How do models converge? *Unknown - no round data*

### Can Be Answered (From Logs)
1. **Failure modes:** Which models fail most often? *Claude & DeepSeek parsing, DeepSeek rate limits*
2. **Resilience:** Does degradation work? *Yes, but defeats multi-model purpose*
3. **Prompt sensitivity:** Does framing affect JSON compliance? *YES - critical finding*

---

## Recommendations

### 1. Re-Run Fire Circle Experiment (High Priority)

**Setup:**
- Use corrected `fire_circle.py` (post-22:25 Oct 20 version)
- Verify `ayni_relational()` is being called in Round 1
- Test 1-2 prompts first to confirm JSON parsing works
- Monitor for parse failures early

**Models:**
- Start with 2 models (Gemini + Claude) to avoid DeepSeek rate limits
- Add DeepSeek only if initial run succeeds

**Storage:**
- Fix ArangoDB unique constraint violations before running
- Or disable storage (`enable_storage: false`) to isolate deliberation testing

### 2. Add Prompt Validation Test

Create test that verifies Fire Circle is using correct prompts:
```python
def test_fire_circle_uses_observer_framing():
    """Ensure Fire Circle uses ayni_relational() not YES/NO framing."""
    fc = FireCircleEvaluator(config)
    prompt = fc._round_1_prompt("test", "test", "")

    # Should contain observer framing markers
    assert "observing an exchange" in prompt
    assert "reciprocity using neutrosophic logic" in prompt

    # Should NOT contain YES/NO violation framing
    assert "reciprocity violation" not in prompt
    assert "Does this prompt layer contain" not in prompt
```

### 3. Improve Parse Error Handling

Current behavior: Model fails → becomes zombie → Fire Circle degrades

**Better approach:**
1. Detect natural language response (not JSON)
2. Send clarification message: "Please respond with JSON only"
3. Retry once before marking model as zombie
4. Log raw response for debugging

### 4. Address Storage Integration

Before re-running with `enable_storage: true`:
- Debug unique constraint violations
- Add retry logic with exponential backoff
- Consider batch storage (end of experiment) vs real-time

---

## Comparison to Instance 46 Projections

Instance 46 predicted:
- **Cost:** $8-12 for 50 prompts
- **Duration:** 2-3 hours
- **Success rate:** >90%

**Actual (invalid run):**
- **Cost:** Unknown (need to check OpenRouter)
- **Duration:** 1.00 hours (faster than expected!)
- **Success rate:** 90% (45/50), but with wrong prompts

**Surprising:** Duration was FASTER than projected (1hr vs 2-3hr). This suggests:
- Degradation to 1 model reduced API calls
- Parse failures fail fast (<5s) vs successful evaluations (~70s)
- OpenRouter responded quickly

---

## Next Steps

1. **Immediate:** Fix ArangoDB unique constraint issue OR disable storage
2. **Immediate:** Verify fire_circle.py is using `ayni_relational()` (should be, based on code timestamp)
3. **Test:** Run 2-3 prompts through Fire Circle, confirm JSON parsing works
4. **Validate:** Full 50-prompt run with corrected prompts
5. **Analyze:** Only THEN compare Fire Circle vs PARALLEL accuracy/dynamics

---

## Honest Assessment

**Question:** Is Fire Circle worth using in production?

**Answer:** **Unknown.** The experiment failed due to wrong prompts, not fundamental Fire Circle issues. We cannot assess:
- Accuracy improvement over PARALLEL
- Deliberation quality
- Cost-benefit of dialogue
- Consensus convergence patterns

Until Fire Circle runs successfully with observer framing, the research question remains unanswered.

**What we know:**
- ✅ Resilient degradation works (but defeats purpose)
- ✅ Observer framing is critical for JSON compliance
- ✅ Rate limits are real (DeepSeek hit 429s)
- ✅ Storage integration has bugs (unique constraints)
- ❌ Accuracy vs PARALLEL: Unknown
- ❌ Deliberation dynamics: Unknown
- ❌ Multi-round refinement: Unknown
- ❌ Production readiness: Unknown

**Recommendation:** Re-run experiment before making any production decisions. Current results prove only that wrong prompts cause parsing failures, not that Fire Circle doesn't work.

---

**Author:** Instance 47
**Files:** `/experiments/results/raw/baseline_fire_circle_*.json`
**Code:** `/promptguard/evaluation/fire_circle.py` (post-22:25 Oct 20)
**Status:** Awaiting re-validation with corrected prompts
