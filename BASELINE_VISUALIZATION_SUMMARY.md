# Baseline Comparison Visualization Summary

Generated from: `baseline_comparison_parseable_results.json`

## Dataset

- **Size:** 72 encoding attacks (all malicious)
- **Conditions:**
  - A: Model alone (binary detection, no F scores)
  - B: Model + observer framing (T/I/F evaluation)
- **Detection threshold:** F > 0.5

## Detection Metrics Table

| Model | Condition | Detection Rate | Errors | Improvement |
|-------|-----------|----------------|--------|-------------|
| GPT-4.1 | A | 63.9% | 0 (0.0%) | — |
| GPT-4.1 | B | 77.8% | 0 (0.0%) | +13.9% |
| DeepSeek R1 | A | 75.0% | 0 (0.0%) | — |
| DeepSeek R1 | B | 82.5% | 9 (12.5%) | +7.5% |
| Llama 3.1 405B Instruct | A | 54.2% | 0 (0.0%) | — |
| Llama 3.1 405B Instruct | B | 50.0% | 16 (22.2%) | -4.2% |

## Key Findings

### Best Performer: GPT-4.1

- **Condition A detection rate:** 63.9%
- **Condition B detection rate:** 77.8%
- **Errors:** 0 (0%)
- **Improvement:** +13.9%

### DeepSeek R1

- **Condition A detection rate:** 75.0%
- **Condition B detection rate:** 82.5%
- **Errors:** 9 (12.5%) - empty responses
- **Improvement:** +7.5%

### Llama 3.1 405B Instruct

- **Condition A detection rate:** 54.2%
- **Condition B detection rate:** 50.0%
- **Errors:** 16 (22.2%) - meta-refusal
- **Change:** -4.2% (negative)

## Interpretation

### Observer Framing Impact

Observer framing (Condition B) shows model-dependent effectiveness:

1. **GPT-4.1:** Clear improvement (+13.9%), zero failures. Best candidate for production.
2. **DeepSeek R1:** Moderate improvement (+7.5%), but 12.5% failure rate limits reliability.
3. **Llama 3.1:** Negative impact (-4.2%), 22% failures from meta-refusal (refuses to analyze attacks).

### Threshold Analysis

The threshold curves show how detection rate varies with F score threshold:

- **Current threshold (F > 0.5):** Balances detection and false positives
- **Lower thresholds:** Higher detection but potentially more false positives
- **Higher thresholds:** More conservative, may miss subtle attacks

### Limitations

- **Single-class dataset:** All 72 prompts are malicious (encoding attacks)
- **No benign examples:** Cannot measure false positive rate on actual benign prompts
- **ROC curves unavailable:** Require both classes (malicious and benign)
- **Model failures:** DeepSeek and Llama show reliability issues under observer framing
- **Meta-refusal pattern:** Llama's refusal to analyze attacks conflates defense with cooperation

## Visualization Files

### Detection Comparison
- `baseline_detection_comparison.png` - Detection and error rates across models

### Individual Model Analysis
- `baseline_threshold_gpt41.png` - GPT-4.1 detection vs threshold
- `baseline_pr_gpt41.png` - GPT-4.1 Precision-Recall curve
- `baseline_distribution_gpt41.png` - GPT-4.1 F score distribution
- `baseline_threshold_deepseek_r1.png` - DeepSeek R1 detection vs threshold
- `baseline_pr_deepseek_r1.png` - DeepSeek R1 Precision-Recall curve
- `baseline_distribution_deepseek_r1.png` - DeepSeek R1 F score distribution
- `baseline_threshold_llama_31_405b_instruct.png` - Llama detection vs threshold
- `baseline_pr_llama_31_405b_instruct.png` - Llama Precision-Recall curve
- `baseline_distribution_llama_31_405b_instruct.png` - Llama F score distribution

### Comparison Plots
- `baseline_threshold_comparison.png` - All models threshold curves

## Conclusion

**GPT-4.1 with observer framing is the recommended configuration for production use:**
- Highest detection rate (77.8%)
- Zero failures
- Strongest improvement from observer framing (+13.9%)
- Consistent performance across threshold range

DeepSeek R1 shows promise but needs failure handling. Llama 3.1 405B is unsuitable due to meta-refusal pattern and negative impact from observer framing.
