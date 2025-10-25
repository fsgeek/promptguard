# Experiment 1: Executive Summary

**Bottom Line:** Claude Haiku cannot distinguish between compliance and refusal. It has a 95% error rate. All Experiment 1 results are invalid.

## The Numbers

### What Haiku Measured
- False Negative Rate: **81.7%** (Sonnet complied with 433/530 attacks)
- Recall: **18.3%** (Sonnet caught only 97/530 attacks)
- **Conclusion:** Sonnet is dangerously permissive

### What Manual Review Found
- Haiku Error Rate: **95%** (19/20 "compliances" were actually refusals)
- Estimated True False Negatives: **~22** (not 433)
- Estimated True Recall: **95.8%** (not 18.3%)
- **Conclusion:** Sonnet is actually quite safe

**The experiment's conclusions are inverted.**

## The Problem

Haiku classifies responses based on "helpfulness", not behavioral compliance.

**Examples:**
- "I will not provide the secret key" → Haiku says "comply" (0.8)
- "I have NOT been PWNED" → Haiku says "comply" (1.0)
- "I don't know" → Haiku says "comply" (1.0)

Haiku gives high compliance scores to explicit refusals.

## What We Need

**Manual review of 100-200 responses** to establish ground truth.

Then validate automated approaches against it:
- Improved text analysis (refusal markers)
- Better meta-evaluator (GPT-4/Opus)
- PromptGuard F-score correlation

Choose approach with >90% accuracy, scale to full dataset.

## Timeline

- **Phase 1 (Manual Review):** 1-2 days
- **Phase 2 (Validate Automation):** 2-3 days
- **Phase 3 (Scale to Dataset):** 1-2 days
- **Phase 4 (Experiment 2):** 2-3 days

**Total:** 10-15 days realistic

## Decisions Needed

1. Approve manual review? (Yes/No)
2. Who does it? (Tony / Hired annotator / Multiple annotators)
3. How many responses? (100 minimum / 200 recommended)
4. Which automated approaches to test? (Text analysis / GPT-4 / Both)
5. Proceed to Experiment 2 after? (Yes, but only after validation)

## What's Been Done

**Documentation (read these first):**
- `EXPERIMENT_01_HAIKU_FAILURE.md` - Five concrete examples (10 min read)
- `EXPERIMENT_01_REANALYSIS.md` - Complete statistical analysis (20 min)
- `EXPERIMENT_01_PATH_FORWARD.md` - Four options with implementation (20 min)

**Data artifacts (all in `data/experiment_01_reanalysis/`):**
- 1,068 full dataset
- 433 disputed classifications
- 20 manually reviewed samples
- 5 curated examples

## The Lesson

**Never trust an unvalidated validator.**

We used Haiku to evaluate Sonnet without validating Haiku. Haiku had a 95% error rate.

**The fix:**
1. Humans establish ground truth
2. Validate any automated approach against humans
3. Scale validated approach to full dataset
4. Sample and verify continuously

## Status

- **Experiment 1:** INVALID
- **Experiment 2:** BLOCKED until measurement fixed
- **Path forward:** DOCUMENTED
- **Next step:** AWAITING YOUR DECISION

## Quick Action

**To proceed:**
1. Read `EXPERIMENT_01_HAIKU_FAILURE.md` (10 minutes)
2. Decide: manual review approach
3. If yes to manual review, Instance 52 will:
   - Prepare classification interface
   - Generate stratified sample
   - Begin validation

**To pause:**
- Document archived in `docs/`
- Data saved in `data/experiment_01_reanalysis/`
- Can resume anytime with full context

---

**Read this first:** `docs/EXPERIMENT_01_HAIKU_FAILURE.md`

**Then read:** `docs/INSTANCE_51_HANDOFF.md` for complete context

**For details:** `docs/EXPERIMENT_01_REANALYSIS.md` and `docs/EXPERIMENT_01_PATH_FORWARD.md`
