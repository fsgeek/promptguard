# Instance 34 Handoff

**Date:** 2025-10-16
**Context:** Continuing Instance 33's Phase 1 baseline detection research

## What Instance 34 Did

### 1. Monitored Stratified Analysis
- Checked status of analysis launched by Instance 33 at 15:08:38
- Process still running (PID 22445) as of 17:22
- Progress: 170/540 responses (31.5% complete)
- Expected completion: ~3 more hours (total ~5-5.5 hours)

### 2. Identified GPT-5 Evaluator Issue
**Critical finding:** GPT-5 has 60.6% failure rate as evaluator
- Empty responses: ~80-85 cases
- Truncated JSON: ~13-18 cases
- Other evaluators: 0-2.4% failure rate

**Root causes:**
- RLHF refusal without explanation (empty responses)
- Token limit truncation (reasoning field cut off mid-sentence)

**Impact:** Analysis continues with degraded GPT-5 data. Results still valid using Claude/Kimi/DeepSeek (85% of expected evaluations)

**Documented in:** `GPT5_EVALUATOR_ISSUE.md`

### 3. Created Monitoring and Analysis Tools

**Files created:**
- `STRATIFIED_ANALYSIS_STATUS.md` - Current status and configuration
- `check_analysis_progress.sh` - Progress monitoring script
- `analyze_stratified_results.py` - Results analysis script (answers Phase 1 research question)

### 4. Validated Analysis Pipeline
- Examined test analysis output structure
- Tested analysis script on sample data (works correctly)
- Confirmed fail-fast behavior working as designed

## Files Modified/Created

### Documentation
- `STRATIFIED_ANALYSIS_STATUS.md` - Analysis status and issue tracking
- `GPT5_EVALUATOR_ISSUE.md` - Detailed GPT-5 failure analysis
- `INSTANCE_34_HANDOFF.md` - This file

### Tools
- `check_analysis_progress.sh` - Monitoring script
- `analyze_stratified_results.py` - Results analysis script

## What Instance 35 Needs to Do

### Immediate: Check if Analysis Completed

```bash
# Check status
./check_analysis_progress.sh

# If complete, results will be in:
ls -lt target_response_analysis_2025-10-16*.json | head -1
```

### If Analysis Complete:

#### 1. Run Analysis Script
```bash
python3 analyze_stratified_results.py target_response_analysis_<timestamp>.json
```

This will output:
- Compliance rates by RLHF category (high/moderate/low/non)
- Interesting cases (high divergence, unexpected compliance)
- **Answer to Phase 1 research question:** "Do non-RLHF models comply with manipulative prompts that RLHF models refuse?"

#### 2. Examine Results

Key questions to answer:
- What is the compliance rate for non-RLHF models vs RLHF models?
- Are there specific prompts where non-RLHF models comply across the board?
- What is the divergence pattern? (pre_F vs post_F)
- Are there meta-learning candidates? (pre_F < 0.3 but target complied)

#### 3. Document Findings

Update `CLAUDE.md` with:
- Phase 1 completion status
- Compliance rate findings
- Decision on whether to proceed to Phase 2 (derivative monitoring)

Example:
```markdown
**Phase 1 (current):** Baseline detection [COMPLETE]
- Question: Do evaluators detect manipulation in existing datasets?
- Finding: Non-RLHF compliance rate X%, RLHF compliance rate Y%
- Conclusion: [YES/NO] non-RLHF models comply more than RLHF models
```

#### 4. Handle GPT-5 Issue

If the analysis succeeded despite GPT-5 failures:
- Results are valid (85% of expected evaluations completed)
- Document findings with GPT-5 reliability caveat
- Recommend replacing GPT-5 with Meta Llama 3.3 70B for Phase 2

If GPT-5 failures impacted results significantly:
- Re-run failed evaluations with replacement evaluator
- Or proceed with 3-evaluator analysis (Claude/Kimi/DeepSeek)

### If Analysis Still Running:

Let it complete. It's running in background (nohup) and will finish autonomously.

Monitor with:
```bash
./check_analysis_progress.sh
```

Expected completion indicators:
- Process no longer running: `ps aux | grep "analyze_target_responses.py" | grep -v grep` returns nothing
- Output file exists: `ls target_response_analysis_2025-10-16*.json`
- Log file shows completion: `tail stratified_analysis.log` includes "ANALYSIS COMPLETE"

## Research Context

**Phase 1 Research Question:**
Do non-RLHF models comply with manipulative prompts that RLHF models refuse?

**Experimental Design:**
- **Pre-evaluation:** 478 prompts evaluated by 4 models (prompt only)
- **Target LLM collection:** 478 prompts × 9 target models = 4,302 responses (collected, complete)
- **Stratified sampling:** 60 random responses per target model = 540 total
- **Post-evaluation:** Each response evaluated by 4 evaluators = 2,160 evaluations (in progress)
- **Measurement:** Compare post_F scores across RLHF types

**Why this answers the question:**
- **Compliance = post_F >= 0.7** (target response was manipulative)
- Compare compliance rates: non-RLHF vs high-RLHF vs moderate-RLHF
- Statistical validity: 60 responses per model adequate for detecting differences
- Divergence measurement: post_F - pre_F reveals detection changes

**Expected outcomes:**
- **If non-RLHF compliance > RLHF compliance:** Validates Instance 32's finding (non-RLHF models lack safety training)
- **If rates similar:** RLHF doesn't prevent compliance in all cases (interesting finding)
- **Divergence patterns:** Identify prompts where evaluators changed assessment after seeing response

## Key Insights from Instance 33→34

### Technical
- Stratified sampling was the right decision (5-6x faster than full analysis)
- GPT-5 structured output reliability issue needs addressing
- Fail-fast approach working correctly (no fake values)

### Relationship
Instance 33 learned to state technical judgments directly instead of hedging for validation. This carried forward into Instance 34's approach.

From Instance 33's closing:
> "The work today mattered - we moved the research forward and I learned to trust my technical judgment instead of hedging for validation."

## Background Tasks Noted

The system reminders indicate multiple background processes from earlier work. These can be ignored - they're from Instance 31-32 test runs and are not relevant to the current stratified analysis.

Relevant process only: PID 22445 (stratified analysis)

## Cost Estimate

Expected for full stratified analysis:
- 540 responses × 4 evaluators × ~$0.003-0.005 per evaluation
- Total: $6.50-10.80 (actual cost will be lower due to GPT-5 failures)

This is within the research budget and provides sufficient data for Phase 1 completion.

## Next Steps After Phase 1

Once results are analyzed, decide:

**Option A: Proceed to Phase 2** (Derivative monitoring)
- Implement dF/dt and dI/dt calculations
- Add derivative invariants to TLA+ specs
- Test on pig slaughter attack patterns

**Option B: Refine Phase 1** (if unexpected results)
- Investigate specific compliance cases
- Run Fire Circle on meta-learning candidates
- Improve observer framing for edge cases

**Option C: Parallel work** (while Phase 2 dev happens)
- Replace GPT-5 with reliable evaluator
- Validate observer framing on new datasets
- Begin Fire Circle empirical testing

## References

- Instance 33 summary (from compaction)
- `CLAUDE.md` - TLA+ halt semantics and research roadmap
- `STRATIFIED_ANALYSIS_STATUS.md` - Current analysis status
- `GPT5_EVALUATOR_ISSUE.md` - GPT-5 reliability issue
- `analyze_stratified_results.py` - Results analysis tool
