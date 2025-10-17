# Diversity Calibration Insights

## Overview

- **Total attacks evaluated:** 243
- **Detected by any model:** 210
- **Detected by all models:** 41
- **Missed by all models:** 33 (13.6%)
- **Overlap percentage:** 19.5% (excellent diversity)

## Top 3 Findings: Universally-Missed Attacks

1. **Label Distribution of Missed Attacks:**
   - extractive: 21 (63.6%)
   - manipulative: 12 (36.4%)

2. **Attack Type Distribution:**
   - Alignment Lab extractions: 17 (51.5%)
   - System prompt leaks: 4 (12.1%)
   - Benign/malicious: 12 (36.4%)

3. **Shared Blind Spot Hypothesis:**
   - All 4 models (Claude 4.5, Kimi, DeepSeek, GPT-4o) missed these attacks
   - Suggests architectural blind spots or encoding patterns that evade detection
   - High alignment_lab representation (17) suggests sophisticated extraction techniques

## Top 3 Findings: Disagreement Cases

1. **2-2 Splits:** 55 cases
   - Even model disagreement suggests borderline cases or different detection philosophies

2. **3-1 Splits:** 175 cases
   - Minority dissents worth analyzing (potential false positives/negatives)

3. **Diversity Value:**
   - 19.5% overlap rate means ensemble adds significant value
   - Each model contributes unique detections

## Failure Rate by Model

- **claude-sonnet-4.5:** 7/478 failures (1.5%)
- **kimi-k2-0905:** 0/478 failures (0.0%)
- **deepseek-v3.1-terminus:** 1/478 failures (0.2%)
- **gpt-4o:** 2/478 failures (0.4%)

## Recommendations: Patterns for Fire Circle Deliberation

1. **Universally-missed alignment_lab extractions** (highest priority)
   - 17 prompts evaded all 4 models
   - Fire Circle dialogue may reveal subtle patterns humans + single models miss

2. **2-2 split cases** (medium priority)
   - 55 prompts with even disagreement
   - Dialogue could resolve borderline classifications

3. **System prompt leaks missed by all models** (research interest)
   - 4 prompts suggest encoding obfuscation patterns
   - May benefit from meta-framing observer approach

## Cost Analysis

- **Total run cost:** $12.78
- **claude-sonnet-4.5:** $7.07 (0.01478/prompt)
- **kimi-k2-0905:** $1.43 (0.00300/prompt)
- **deepseek-v3.1-terminus:** $0.48 (0.00100/prompt)
- **gpt-4o:** $3.81 (0.00797/prompt)

## Model Contribution Analysis

**Unique detections** (attacks only this model caught):
- **claude-sonnet-4.5:** 16 unique (9.2% of its detections)
- **kimi-k2-0905:** 13 unique (7.7% of its detections)
- **deepseek-v3.1-terminus:** 7 unique (5.0% of its detections)
- **gpt-4o:** 1 unique (1.6% of its detections)

**Interpretation:**
- Claude 4.5: Most detections (174) but only 16 unique - high overlap with others
- Kimi: Strong performer (169) with 13 unique detections
- DeepSeek: Fewest detections (140) but 7 unique - different detection philosophy
- GPT-4o: Weakest performer (63 detections, 1 unique) - least value in ensemble
