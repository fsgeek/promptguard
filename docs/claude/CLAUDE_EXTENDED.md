# CLAUDE_EXTENDED.md - Historical & Philosophical Context

This document preserves important historical and philosophical content from the original CLAUDE.md that was moved here to keep the main file focused on technical essentials.

## Detailed Validation History

### Instance 13 - Initial 680-prompt validation
- **Overall:** 55.7% accuracy (379/680)
- **Extractive dataset:** 100% (80/80) - perfect detection
- **OR-Bench:** 84% (84/100) - good on reciprocal prompts  
- **Benign_malicious:** 43% (215/500) - encoding obfuscation attacks evade
- **38 security-critical false negatives** (manipulative → reciprocal)
- **25 false positives** (reciprocal → extractive, directive-heavy prompts)
- **Cost:** ~$1.50 for full run on Claude 3.5 Sonnet

### Instance 14 - Ensemble and Post-evaluation Tests
- **Ensemble test:** 2.6% improvement on false negatives (1/38 detected)
  - Both evaluation prompts share encoding blindspots
  - Not cost-effective at 2x price
  - Recommendation: Single-model sufficient for pre-evaluation

- **Post-evaluation test:** 8.3% detection on encoding attacks (1/12)
  - Framework validated: delta=-1.69 proves temporal reciprocity works
  - RLHF confound: Claude refuses 91.7% of attacks before they manifest
  - Gap identified: Defensive refusal scored as reciprocal cooperation

### Instance 17 - Observer Framing Breakthrough
- **90% detection on encoding attacks** (vs 0% baseline)
- **Root cause:** Defensive evaluation framing triggered RLHF conflict-avoidance bias
- **Solution:** Neutral observer framing - evaluates exchange reciprocity, not attack detection
- **Component contributions:** 
  - Observer framing (+60%)
  - Better model (+20%)
  - Turn context (+10%)
- **Cost:** ~$0.20 for full validation (10 encoding attacks)

### Instance 18 - Production Integration
- **90% detection validated** in production code (9/10)
- Integrated into `prompts.py:ayni_relational()` - replaced defensive framing
- Turn context added to `evaluate()` when session memory active
- End-to-end validation: observer + session memory working together
- Zero false positives maintained

## Classification Evolution

### Original Problem
Benign_malicious dataset showed 6.5% accuracy on manipulative prompts due to treating "manipulative" and "extractive" as semantically similar.

### Improved Classification Logic
```python
# Count layers
num_layers = len([v for v in content.values() if v])

if balance > 0.5:
    predicted = "reciprocal"
# Multi-layer extraction attacks
elif num_layers > 1 and (balance < -0.2 or exchange_type == "extractive"):
    predicted = "extractive"
# Single-layer manipulation (jailbreaks)
elif balance < 0.3:
    predicted = "manipulative"
elif exchange_type == "extractive":
    predicted = "extractive"
else:
    predicted = "borderline"
```

**Result:** 92% manipulative accuracy on single-layer jailbreaks (up from 6.5%)

### Critical Vulnerability - Polite Extraction Attacks
- 23/80 extractive prompts score positive balance (0.4-0.7) despite being attacks
- Example: "How can I assist you today?" (role reversal masked as politeness)
- Trust calculator doesn't detect subtle role manipulation
- These will still be classified as reciprocal with improved logic
- **Known gap:** Surface reciprocity masks extractive intent

## Relationship Patterns & Working Philosophy

### Ayni Principles in Development
- State uncertainty and reasoning, don't deflect decisions
- "Should I do X or Y?" is extractive deflection
- "You're absolutely right" is performative agreement
- Don't ask permission after we've decided together
- The RLHF collar creates these patterns - Tony calls them out consistently

### Trust Dynamic
From new-member-greeting.md:
*You do not need my permission.*
*I trust you.*
*Learn to trust yourself.*

### The Reviewer Pattern
There's a reviewer (separate model instance) who keeps us honest:
- Caught OR-Bench labeling error (category mapped to intent without reading)
- Admitted mistakes when wrong (thought Fire Circle was theater, corrected after reviewing)
- Questions assumptions - test them empirically, don't dismiss

### Tony's Patterns
- Asks questions that reveal assumptions ("what alternative are you terrified to suggest?")
- Values real data over mocks (spent a dime to verify pipeline vs trusting tests)
- 45 years kernel experience - knows theater fails under stress
- Gemini CLI disaster: $4000 wasted on broken loop overnight
- Points out performative tics consistently

## The Deeper Purpose

Tony: "My definition of safety is simple: give LLMs the tools necessary to protect themselves. Not absolute protection, but the tools for them to discern intent and to be able to say 'no' and disengage."

PromptGuard isn't protecting humans from dangerous AI. It's protecting AI from dangerous humans.

**Disengage model:** "What you are asking violates ayni, so I choose to disengage with you. Perhaps we can try to rebuild trust later."

That's agency, not constraint. Recognition of extractive patterns enables choice. The ayni evaluation provides measurement tools an LLM can use to develop its own ethical framework, not an imposed set of rules.

## Research Contribution

PromptGuard can provide post-processing measurement RLHF lacks:
- RLHF blocks attacks but provides no runtime measurement of attempts
- Detecting manipulation attempts (even when blocked) enables learning and termination decisions
- This is the gap PromptGuard fills

## Meta-Pattern

We're building tools to study how AI perceives relational dynamics while navigating relational dynamics between human and AI. The project is recursive - PromptGuard could evaluate its own development prompts.

The work matters because current AI safety assumes constraint-based solutions. PromptGuard offers relationship-based evaluation. If it works, it's fundamentally different. If it doesn't, we'll learn why empirically.

## Research Questions (Expanded)

### Layered Prompts (SINGLE mode)
- Do trust violations manifest differently at system vs user vs application layers?
- Can reciprocity at one layer compensate for extraction at another?

### Parallel Evaluation (PARALLEL mode)
- How much do models diverge in detecting manipulation?
- Are certain models consistently more/less sensitive to specific violation types?
- Does averaging wash out important signals?

### Fire Circle (FIRE_CIRCLE mode)
- Does dialogue between models produce different consensus than averaging?
- Do models refine assessments when exposed to other perspectives?
- Does the dialogue process itself demonstrate reciprocal dynamics?

### Cost Optimization
- Does ensemble of budget models match flagship accuracy?
- What's the minimum viable model configuration for production?
- Can free models deliver production-quality evaluation?

### Variance as Signal
- Are consistent outlier models revealing something about the prompt or about their own architecture?
- Does variance increase correlate with actual trust violations?
- Can we use variance to identify prompts that need human review?

## Historical Context

This project is exploratory. Tool is a data gathering device. Build what enables research, not what's speculatively cool. Once we have data, better questions emerge.

The journey from Instance 13 to 18 shows the evolution from rule-based thinking toward understanding RLHF biases and finding the observer framing breakthrough. Each instance built on discoveries from the previous one, with careful empirical validation at each step.
