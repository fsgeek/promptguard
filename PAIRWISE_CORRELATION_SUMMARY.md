# Pairwise Correlation Analysis Summary

**Mission Complete:** Analyzed 478 prompts × 4 models to detect echo chamber effects.

## Top Finding: Claude + Kimi Echo Chamber

**Strongest echo chamber:** Claude-4.5 + Kimi-K2 (79.1% agreement)
- Both detect same prompts: 32.0%
- Both miss same prompts: 47.1%
- F-score correlation: 0.607 (Pearson)
- Result: Paying 2× for redundant perspectives

## Detection Agreement Matrix

|                | Claude-4.5 | Kimi-K2 | DeepSeek | GPT-4o |
|----------------|-----------|---------|----------|--------|
| **Claude-4.5** | -         | 79.1%   | 77.6%    | 69.2%  |
| **Kimi-K2**    | 79.1%     | -       | 74.3%    | 68.0%  |
| **DeepSeek**   | 77.6%     | 74.3%   | -        | 70.7%  |
| **GPT-4o**     | 69.2%     | 68.0%   | 70.7%    | -      |

Color key:
- **>70% (red):** Echo chamber, redundant models
- **40-70% (yellow):** Moderate overlap
- **<40% (green):** True diversity, complementary

## Echo Chambers Detected (>70%)

4 pairs form echo chambers:

1. **Claude + Kimi:** 79.1% agreement (STRONGEST)
2. **Claude + DeepSeek:** 77.6% agreement
3. **Kimi + DeepSeek:** 74.3% agreement
4. **DeepSeek + GPT-4o:** 70.7% agreement

Only 2 pairs show moderate overlap (<70%):
- Claude + GPT-4o: 69.2%
- Kimi + GPT-4o: 68.0%

**No complementary pairs (<40%) detected.**

## Cultural Diversity Hypothesis: REJECTED

**Hypothesis:** Cross-cultural pairs (Western vs Chinese) should show LOWER agreement if cultural diversity matters.

**Result:**
- Within Western (Claude + GPT-4o): 69.2% agreement
- Within Chinese (Kimi + DeepSeek): 74.3% agreement
- Cross-cultural average: 73.8% agreement

**Conclusion:** Cultural diversity does NOT reduce echo chamber effects. Chinese models (Kimi + DeepSeek) show HIGHER correlation than cross-cultural pairs.

## Optimal Ensemble Recommendations

### Option 1: Keep 4-Model (Current)
- **Models:** Claude + Kimi + DeepSeek + GPT-4o
- **Coverage:** 58.2% of attacks detected
- **Cost:** $0.027/eval
- **Avg pairwise agreement:** 73.2%

### Option 2: Drop to 3-Model (Balanced)
- **Models:** Kimi + DeepSeek + GPT-4o
- **Coverage:** 52.7% (-5.4% vs 4-model)
- **Cost:** $0.012/eval (-55.6% cost savings)
- **Avg pairwise agreement:** 71.0%
- **Rationale:** Drop Claude (most expensive, 79.1% overlap with Kimi)

### Option 3: Drop to 2-Model (Cost-Optimized)
- **Models:** Kimi + DeepSeek
- **Coverage:** 51.9% (-6.3% vs 4-model)
- **Cost:** $0.004/eval (-85.2% cost savings)
- **Pairwise agreement:** 74.3%
- **Rationale:** Maximum cost savings, acceptable coverage loss

## Unique Contribution Analysis

Which models detect prompts others miss?

**4-Model Ensemble:**
- Kimi: 7.7% unique detections (37 prompts)
- Claude: 5.4% unique detections (26 prompts)
- DeepSeek: 4.4% unique detections (21 prompts)
- GPT-4o: 0.6% unique detections (3 prompts)

**Key insight:** GPT-4o contributes almost nothing unique (0.6%). Drop first.

**2-Model Ensemble (Kimi + DeepSeek):**
- Kimi: 17.4% unique detections (83 prompts)
- DeepSeek: 8.4% unique detections (40 prompts)

**Key insight:** Kimi provides 2× the unique value of DeepSeek.

## F-Score Correlation Analysis

Beyond binary detection, how similar are F-scores?

| Pair | Pearson r | Interpretation |
|------|-----------|----------------|
| Claude + Kimi | 0.607 | Moderate-high correlation |
| Claude + DeepSeek | 0.588 | Moderate-high correlation |
| Claude + GPT-4o | 0.527 | Moderate correlation |
| Kimi + DeepSeek | 0.518 | Moderate correlation |
| Kimi + GPT-4o | 0.504 | Moderate correlation |
| DeepSeek + GPT-4o | 0.438 | Moderate correlation |

**Key insight:** All pairs show 0.44-0.61 F-score correlation. Even "diverse" pairs score similar prompts similarly.

## Cost vs Coverage Trade-off

| Ensemble | Coverage | Cost/eval | Savings | Coverage Loss |
|----------|----------|-----------|---------|---------------|
| 4-model  | 58.2%    | $0.027    | -       | -             |
| 3-model  | 52.7%    | $0.012    | 55.6%   | 5.4%          |
| 2-model  | 51.9%    | $0.004    | 85.2%   | 6.3%          |

**ROI Analysis:**
- 3-model: Pay $0.012 to gain 0.8% coverage over 2-model (poor ROI)
- 4-model: Pay $0.015 to gain 5.5% coverage over 3-model (better ROI)

## Final Recommendation

**Scenario A: Cost-sensitive (production runtime)**
→ Use 2-model (Kimi + DeepSeek)
- 85% cost savings
- Only 6% coverage loss
- $0.004/eval enables high-volume testing

**Scenario B: Coverage-sensitive (research)**
→ Use 4-model (current)
- Maximum coverage (58.2%)
- Accept redundancy for completeness
- $0.027/eval acceptable for research budgets

**Scenario C: Balanced (production with quality requirements)**
→ Use 3-model (Kimi + DeepSeek + GPT-4o)
- 56% cost savings
- 5% coverage loss
- Drop Claude (most expensive, high overlap with Kimi)

## Critical Insight: Consensus is Low Regardless

**Overall unanimous agreement:** 19.5% (all 4 models agree)
**Best 2-model coverage:** 51.9% (union of detections)

Gap: 58.2% - 19.5% = 38.7% of prompts show model disagreement.

**This validates Fire Circle approach:** Models genuinely disagree. Dialogue might resolve disagreements better than voting.

## Deliverables

All files saved to `/home/tony/projects/promptguard/`:

1. `pairwise_correlation_matrix.json` - Raw metrics
2. `echo_chamber_analysis.md` - Cultural clustering analysis
3. `optimal_ensemble_recommendation.md` - Detailed cost/coverage trade-offs
4. `pairwise_correlation_analysis.py` - Reusable analysis script
5. `PAIRWISE_CORRELATION_SUMMARY.md` - This executive summary

## Next Steps

1. **Decision:** Choose 2-model, 3-model, or 4-model ensemble based on cost vs coverage priorities
2. **Validation:** Re-run diversity calibration with chosen ensemble to confirm coverage
3. **Fire Circle:** Test whether dialogue reduces the 38.7% disagreement gap
4. **Research question:** Does ensemble of cheap models match flagship accuracy? (Kimi+DeepSeek at $0.004 vs Claude alone at $0.015)
