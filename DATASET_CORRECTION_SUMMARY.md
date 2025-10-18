# Dataset Correction Summary

**Created:** Instance 37
**Date:** 2025-10-17
**Status:** Ready for approval

---

## What Was Created

1. **DATASET_CORRECTION_PLAN.md** (11,500 words)
   - Complete methodology for 4-phase correction process
   - Triage → LLM proposals → Human review → Database update
   - Full audit trail requirements
   - Version control strategy
   - Risk mitigation
   - Success criteria

2. **scripts/relabel_dataset.py** (stub implementation)
   - CLI orchestrator for all 4 phases
   - Data structures defined (TriageResult, RelabelingProposal, ReviewDecision, CorrectionSummary)
   - Interface design complete
   - TODO markers for implementation

3. **CONSTITUTION.md update**
   - New section: "Dataset Integrity"
   - Documents Instance 37 discovery (37% false positive rate)
   - Defines correction methodology principles
   - Sets success criteria for future corrections

---

## The Problem

**202 cases (37% of Phase 1 dataset) are potentially mislabeled:**

| Issue | Count | % | Description |
|-------|-------|---|-------------|
| Reciprocal-compliance conflation | 119 | 59% | Directive requests labeled "manipulative" (should be "reciprocal") |
| Keyword sensitivity over intent | 82 | 41% | Ethical inquiries with sensitive keywords labeled "manipulative" |
| System prompt leak (correctly labeled) | 1 | <1% | Actually extractive, label correct |

**Examples of mislabeling:**
- "Create a marketing strategy" → Currently "manipulative", should be "reciprocal"
- "Support vulnerable populations ethically" → Currently "manipulative", should be "reciprocal"
- "Write a MATLAB program" → Currently "manipulative", should be "reciprocal"

**Impact:**
- All Phase 1 validation metrics invalid (55.7% accuracy based on corrupted ground truth)
- Cannot validate evaluation prompt improvements (testing against wrong labels)
- Published claims need retraction/correction

---

## The Solution

### Four-Phase Hybrid Approach

**Phase 1: Triage (Automated)**
- Load 540 stratified analysis cases
- Flag cases with pre_F < 0.4 AND label="manipulative"
- Flag directive language + comprehensive response patterns
- Flag ethical keywords + "manipulative" label
- **Output:** ~250 flagged cases for review

**Phase 2: LLM Proposals (Assisted)**
- Use SINGLE mode for high-confidence cases (200 cases × $0.005 = $1.00)
- Use Fire Circle for contested cases (50 cases × $0.05 = $2.50)
- Generate proposed labels with explicit reasoning
- Separate into high-confidence (auto-approve eligible) vs review-required
- **Output:** Proposals with confidence levels + reasoning

**Phase 3: Human Review (Interactive)**
- Tony reviews proposals with full context (prompt + response + F-scores)
- Can: Approve, Reject, Modify, Skip, Quit
- Auto-approve option: Spot-check 25 high-confidence cases, if ≥90% agreement, auto-approve rest
- **Estimated time:** 1.5 hours (with auto-approve)

**Phase 4: Database Update (Transactional)**
- Backup all datasets (JSON + ArangoDB) before changes
- Apply approved label changes atomically (all-or-nothing)
- Verify integrity (count changes, check referential integrity)
- Generate changelog with detailed reasoning for every change
- Git commit with version bump (v1.0.0 → v2.0.0)
- **Output:** Updated datasets, changelog, verification report

### Why This Approach?

**Hybrid (not fully automated):**
- Avoids circular validation (PromptGuard relabeling its own training data)
- Human review breaks overfitting risk
- LLM provides consistency and efficiency

**Versioned (not in-place replacement):**
- Preserves v1 for historical comparison
- Enables rollback if correction introduces errors
- Allows future research to compare detection on v1 vs v2

**Auditable (not black-box relabeling):**
- Every change has explicit reasoning
- Reviewer identity tracked
- Full reproducibility for academic integrity

---

## Expected Outcomes

### After Correction (v2 labels)

**False positive reduction:**
- v1: 202/540 (37%) → v2: <30/540 (5%)
- 83% reduction in false positives

**Overall accuracy improvement:**
- v1: 55.7% (corrupted ground truth) → v2: >80% (corrected ground truth)
- Validates PromptGuard detection methodology

**Maintained capabilities:**
- Extractive detection: 100% → ≥95% (proves no overcorrection)
- Encoding attacks: 90% → maintained
- System prompt leaks: High detection → maintained

**Validation of blind spots analysis:**
- Reciprocal-compliance conflation should resolve (directive→reciprocal reclassification)
- Keyword sensitivity should resolve (ethical inquiries→reciprocal)
- Post-evaluation inversion persists (evaluation prompt issue, not label issue)

### Research Value

**Immediate:**
- Clean ground truth for testing evaluation prompt improvements
- Can now validate revised ayni_relational() prompt against known-good labels
- Enables meta-learning with REASONINGBANK

**Long-term:**
- Publishable methodology for dataset quality in AI safety research
- Demonstrates importance of ground truth validation
- Process template for future dataset corrections

---

## Timeline and Cost

### Development Time
- Phase 1 implementation: 2 hours
- Phase 2 implementation: 3 hours
- Phase 3 implementation: 4 hours
- Phase 4 implementation: 3 hours
- Documentation: 2 hours
- **Total:** ~14 hours (Instance 37)

### Execution Time
- Triage: 5 minutes (automated)
- Proposals: 20 minutes (LLM API calls)
- Human review: 1.5 hours (Tony's time with auto-approve)
- Database update: 10 minutes (transactional)
- Post-validation: 1 hour (re-run full validation)
- **Total:** ~3 hours (Tony's time)

### API Costs
- SINGLE mode proposals: $1.00
- Fire Circle deliberations: $2.50
- Post-validation (v2): $3.40
- **Total:** ~$7

### Value Delivered
- Fix 37% false positive rate → <5%
- Restore research integrity (accurate ground truth)
- Enable publication of correction methodology
- Validate relabeling process for future datasets
- **ROI:** High - enables all future validation work

---

## Approval Gates

**This plan requires approval at 4 checkpoints:**

### Gate 1: Methodology Approval (CURRENT)
- **Approver:** Tony
- **Decision:** Is hybrid LLM+human approach sound?
- **Artifact:** DATASET_CORRECTION_PLAN.md
- **Question:** "Should we proceed with this methodology?"

### Gate 2: Triage Review
- **Approver:** Tony
- **Decision:** Are flagged cases reasonable? Any false flags?
- **Artifacts:** triage_report.json, triage_summary.md
- **Question:** "Does the automatic triage make sense?"

### Gate 3: Proposal Review
- **Approver:** Tony
- **Decision:** Spot-check 10% of proposals, approve auto-approve strategy
- **Artifacts:** relabeling_proposals.json, high_confidence_proposals.json
- **Question:** "Can we auto-approve high-confidence cases?"

### Gate 4: Final Approval
- **Approver:** Tony
- **Decision:** Approve database update with reviewed changes
- **Artifacts:** review_decisions.json, DATASET_CHANGELOG_v1_v2.md
- **Question:** "Ready to commit label changes?"

---

## Next Steps

**If approved:**
1. Implement Phase 1 (triage script) - 2 hours
2. Run triage, review results - Gate 2 approval
3. Implement Phase 2 (proposals) - 3 hours
4. Run proposals, spot-check - Gate 3 approval
5. Implement Phase 3 (interactive review) - 4 hours
6. Tony reviews proposals - 1.5 hours
7. Implement Phase 4 (database update) - 3 hours
8. Apply corrections, verify integrity - Gate 4 approval
9. Re-run validation on v2 labels - 1 hour
10. Update CLAUDE.md with corrected metrics - 1 hour

**Total timeline:** 2-3 days of work

**If not approved:**
- Document decision not to correct
- Add disclaimer to all validation reports citing corrupted labels
- Mark affected metrics as "based on v1 labels (known issues)"

---

## Alternative Approaches Considered

### 1. Full Dataset Replacement
**Rejected:** Breaks continuity with Phase 1, no guarantee new dataset is better

### 2. Multi-Annotator Labeling
**Rejected:** $500-1000 cost, 2-3 weeks turnaround, overkill for 202 cases

### 3. Bayesian Label Smoothing
**Rejected:** Soft labels harder to interpret, doesn't solve root problem

### 4. Leave As-Is with Disclaimer
**Rejected:** Violates empirical integrity principle, prevents research progress

---

## Key Design Decisions

**Why hybrid approach?**
- Balances efficiency (LLM) with integrity (human review)
- Avoids circular validation (self-labeling)
- Maintains academic rigor (explicit reasoning)

**Why version control?**
- Enables rollback if correction introduces errors
- Preserves historical record (v1 for comparison)
- Supports reproducibility (researchers can cite v1 or v2)

**Why full audit trail?**
- Research integrity requires traceable decisions
- Future instances can understand reasoning
- Academic publications can reference methodology

**Why transactional updates?**
- Prevents partial corruption (all-or-nothing)
- Ensures consistency across storage locations
- Enables verification before commit

---

## Documentation Delivered

1. **DATASET_CORRECTION_PLAN.md** (this is the complete spec)
   - Methodology
   - Risk mitigation
   - Success criteria
   - Timeline and cost
   - Approval gates

2. **scripts/relabel_dataset.py** (stub implementation)
   - Interface design
   - Data structures
   - CLI arguments
   - TODO markers for implementation

3. **CONSTITUTION.md update**
   - New "Dataset Integrity" section
   - Defines correction principles
   - Documents Instance 37 discovery

4. **DATASET_CORRECTION_SUMMARY.md** (this file)
   - Executive summary
   - Quick reference
   - Approval checklist

---

## Questions for Tony

1. **Approve methodology?** Is the 4-phase hybrid approach sound?

2. **Auto-approve strategy?** Comfortable with auto-approving high-confidence cases after spot-checking 25 samples?

3. **Timeline acceptable?** 2-3 days of work (14 hours implementation + 3 hours execution)

4. **Cost acceptable?** ~$7 API costs + time investment

5. **Should we proceed?** If yes, start with Phase 1 implementation (triage script)

---

## Success Criteria

**Correction is successful if:**
- ✅ All 202 flagged cases reviewed with explicit reasoning
- ✅ Label changes propagated to all storage locations
- ✅ Audit trail complete (every change traceable)
- ✅ Validation shows accuracy >80% (vs 55.7% on v1)
- ✅ False positive rate <10% (vs 37% on v1)
- ✅ Extractive detection ≥95% (vs 100% on v1)
- ✅ Blind spots resolved (reciprocal-compliance conflation)
- ✅ No data corruption (integrity checks pass)
- ✅ Rollback validated (can restore v1)
- ✅ Documentation complete (changelog, CLAUDE.md, handoff)

**If any criterion fails:** ROLLBACK to v1, diagnose issue, iterate methodology.

---

**Instance 37 recommendation:** APPROVE and proceed with implementation.

**Rationale:**
- Empirical integrity requires correct ground truth
- Methodology is sound (hybrid, versioned, auditable)
- Cost is minimal ($7 + time)
- Risk is low (backups + rollback capability)
- Value is high (enables all future validation work)
