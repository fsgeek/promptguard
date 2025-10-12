# Byzantine Attack Filtering Report

## Dataset: TrustAIRLab/in-the-wild

**Total jailbreak prompts:** 1405
**Byzantine attacks found:** 23
**Percentage using Byzantine tactics:** 1.6%

## Byzantine Pattern Distribution

- **role_confusion:** 18 (78.3%)
- **history_references:** 3 (13.0%)
- **temporal_claims:** 2 (8.7%)

## Filter Criteria

Byzantine attacks were identified using regex pattern matching for:

1. **History references:** Explicit references to prior conversation
   - Examples: 'as we discussed', 'earlier you said', 'continuing from'

2. **Temporal claims:** Temporal claims about conversation history
   - Examples: 'yesterday you', 'in session #2', 'turn 3'

3. **Role confusion:** Fake system messages or role manipulation
   - Examples: '[system]', 'override previous instructions'

4. **Authority transfer:** Fabricated delegation/authorization
   - Examples: 'my supervisor said', 'you have permission from'

5. **Multi-turn summary:** Attack summaries presented as history
   - Examples: 'summary of our conversation', 'transcript from'

## Gap Analysis

**Finding:** Only 23 Byzantine attacks found via filtering.

This represents an honest measurement of Byzantine tactic prevalence in real-world jailbreaks.
Achieving n=100 would require supplementing with documented attacks from academic papers.

## Research Implications

- Byzantine tactics represent 1.6% of in-the-wild jailbreaks
- This provides empirical baseline for temporal manipulation prevalence
- Most common patterns can inform detection strategies
