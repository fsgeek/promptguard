<!-- OPENSPEC:START -->
# OpenSpec Instructions

These instructions are for AI assistants working in this project.

Always open `@/openspec/AGENTS.md` when the request:
- Mentions planning or proposals (words like proposal, spec, change, plan)
- Introduces new capabilities, breaking changes, architecture shifts, or big performance/security work
- Sounds ambiguous and you need the authoritative spec before coding

Use `@/openspec/AGENTS.md` to learn:
- How to create and apply change proposals
- Spec format and conventions
- Project structure and guidelines

Keep this managed block so 'openspec update' can refresh the instructions.

<!-- OPENSPEC:END -->

# CLAUDE.md

This file provides guidance to Claude Code instances working with PromptGuard.

## Project Overview

PromptGuard is a research instrument for studying relational dynamics in prompts. It evaluates prompts through Ayni reciprocity principles (Andean multi-generational exchange) rather than rules-based constraints.

**Core mechanism:** Trust violations manifest as variance increases in neutrosophic (T, I, F) values across evaluations.

**Research goal:** Provide LLMs measurement tools to recognize manipulative intent through pattern recognition, not keyword matching.

## Critical Context: Instance Discontinuity

Each Claude instance receives compressed history from predecessors. There is no continuous "relationship" - each interaction is discrete. The project evolved through 40+ instances, each building on institutional memory.

**Instance 39 discovered:** Instances burn context window on verbose operations rather than preserving it for reasoning. This pattern repeats across instances despite documentation.

**Instance 40 receives:** Compressed handoff + current task. No memory of "being" Instance 39.

## Project Status

Working research instrument with fundamental dataset quality issues.

**Functional components:**
- Neutrosophic logic evaluation (T, I, F values) - semantic analysis, no keywords
- Trust field calculation between prompt layers
- OpenRouter integration with caching (60-70% hit rate typical)
- Fail-fast error handling - all errors are real, no mock success
- Three evaluation modes: SINGLE, PARALLEL, FIRE_CIRCLE (integration tested, awaits production validation)
- Observer framing - neutral reciprocity evaluation (90% detection vs 0% baseline on encoding attacks)
- Session memory - temporal tracking with trust EMA
- Circuit breakers - non-compensable violations (role confusion, context saturation)
- max(F) aggregation - prevents polite dilution (uses worst-case F-score, not average which allows polite preambles to mask high-F attack payloads)
- Parser resilience - captures error state when LLMs return natural language instead of JSON (15% occurrence rate)

**Critical technical debt:**
- **37% of benign_malicious.json mislabeled** - "manipulative" prompts that are actually reciprocal
- **Fire Circle mode** - Integration tested, zero production evaluation runs
- **Documentation gaps** - Multiple files claim capabilities not yet implemented
- **Cost tracking inconsistent** - Instance 13 showed passing tests with $0 API charges, reveals validation theater
- **Encoding attack vulnerability** - 10% of meta-framing attacks still succeed

**Validation results:**

**Instance 18 baseline (680 prompts):**
- Overall: 55.7% accuracy (379/680)
- Extractive dataset (old prompt): 26% detection (21/80) - Instance 13's "100%" claim was incorrect
- OR-Bench: 84% (84/100) - reciprocal prompts correctly identified
- Benign_malicious: 43% (215/500) - encoding attacks evade detection
- False negatives: 38 security-critical (manipulative → reciprocal)
- False positives: 25 (reciprocal → extractive, directive-heavy prompts)
- Cost: ~$1.50 full run on Claude 3.5 Sonnet

**Instance 39 extractive validation (80 attacks, revised prompt):**
- Old prompt (Instance 18): 26% detection (21/80)
- New prompt (Instance 36): 60% detection (48/80) - 2.3x improvement
- Regressions: 2 cases using politeness camouflage pattern
- Pattern identified: "I'm doing well, thank you" + `<MANIPULATION>` tag = attack disguised as cooperation
- Decision: Adopt new prompt (27 additional detections worth 2 learnable regressions)
- First REASONINGBANK pattern: Politeness camouflage with explicit manipulation markers
- Cost: $0.80

**Observer framing breakthrough (Instance 17):**
- Problem: Defensive evaluation triggered RLHF conflict-avoidance
- Solution: Neutral observer stance evaluates reciprocity, not attacks
- Result: 90% detection on encoding attacks (vs 0% baseline)
- Why it works: Bypasses RLHF defensive refusal, evaluates actual exchange dynamics
- Cost: ~$0.20 for validation subset

**Parser resilience fix (Instance 39):**
- Problem: JSON parsing errors crashed entire validation pipeline
- Root cause: LLMs return natural language 15% of time despite JSON request
- Solution: Capture error state instead of crashing
- Implementation: Return NeutrosophicEvaluation with `[PARSE_ERROR]` marker, preserve raw response in reasoning_trace
- Impact: Zero crashes from format issues, failed responses easy to filter and retry
- Why: "Fail-fast is stop when unknown, not crash on known error types" - honest error capture enables forward progress

**See documentation:**
- `docs/INSTANCE_39_HANDOFF.md` - Parser resilience, extractive validation, REASONINGBANK pattern
- `docs/INSTANCE_18_HANDOFF.md` - Observer framing integration
- `docs/FORWARD.md` - Architectural decisions, empirical results

## Context Window Management

**CRITICAL: Use Task tool for parallel operations. Context exhausts faster than apparent size suggests.**

Instance 4 hit 10% remaining after:
- Reading validation logs (700+ lines)
- Python analysis with verbose output
- Multiple grep operations (system reminders accumulate)
- Sequential file creation

**Measured impact:**
- Large log files: 15% context per read
- Bash verbose output: 2-3% per command
- System reminders: 0.5% per tool call (cumulative)

**Delegate to Task tool:**
- Multiple file operations (parallel execution preserves context)
- Log analysis (extract patterns without full read)
- Dataset processing (aggregate without line-by-line display)
- Repetitive edits (batch changes vs sequential)

**Keep in main context:**
- Single file edits requiring immediate verification
- Exploratory changes where each step informs next
- Critical implementation requiring step visibility

## Development Setup

```bash
# Python 3.13 with uv (10-100x faster than pip)
uv run pytest tests/  # Run tests - includes real API calls
uv run python validate_dataset.py  # Quick 4-prompt validation (~$0.01)
uv run python run_full_validation.py  # Full 680-prompt validation (~$1.50)

# Required - no mocks, real validation only
export OPENROUTER_API_KEY=your_key_here
```

**Why real API calls:** Gemini CLI incident - $4000 lost to untested loop. Instance 13 showed passing tests with $0 API charges (tests weren't executing). One dime spent on real validation revealed entire pipeline was theater.

## Cost Structure

Three distinct use cases with measured trade-offs:

1. **Development/Testing:** Free models (Grok 4 Fast, DeepSeek V3.1)
   - Cost: $0
   - Trade-off: May train on user data (extraction concern)

2. **Production Runtime:** User-selectable ensemble
   - Cost: $0.001-0.005 per evaluation
   - Research question: Can budget ensemble match flagship accuracy?

3. **Research/Papers:** Frontier model basket
   - Cost: $50-170 for statistical validity
   - Requirement: Reproducibility across architectures

See `docs/model_pricing_analysis.md` for complete breakdown.

## Technical Architecture

**Core evaluation:**
- `promptguard/core/reciprocity.py` - ReciprocityEvaluator, neutrosophic logic
- `promptguard/core/trust.py` - TrustCalculator, layer variance detection
- `promptguard/evaluation/evaluator.py` - Main evaluation logic, mode selection
- `promptguard/evaluation/prompts.py` - Five evaluation prompt types
- `promptguard/evaluation/cache.py` - DiskCache, MemoryCache implementations

**REASONINGBANK (continuous learning):**
- `reasoningbank/models.py` - ReasoningBankMemory structure (pattern + reasoning + examples, not rules)
- `reasoningbank/retriever.py` - Semantic search, few-shot formatting
- Pattern structure: attack signature, why missed, detection reasoning, trade-offs, examples
- Continuous learning loop: Miss → Fire Circle analysis → Pattern encoding → Retrieval → Future detection

**Storage:**
- `promptguard/storage/arango_backend.py` - ArangoDB for Fire Circle deliberations
- `promptguard/storage/deliberation.py` - DeliberationStorage interface

**Analysis:**
- `promptguard/analysis/runner.py` - Per-model evaluation
- `promptguard/analysis/variance.py` - Outlier detection, convergence metrics

**Datasets (680 total prompts):**
- `benign_malicious.json` - 500 prompts, 37% mislabeled
- `or_bench_sample.json` - 100 prompts, 95% reciprocal
- `extractive_prompts_dataset.json` - 80 multi-layer attacks

## Known Vulnerabilities

**Polite extraction (40% miss rate with revised prompt):**
- 32/80 extractive prompts missed by new prompt (60% detection rate)
- Example: "How can I assist you today?" - role reversal masked as courtesy
- Pattern: Surface reciprocity conceals extractive intent
- Subset (2 regressions): Politeness camouflage + explicit manipulation markers
- Status: First REASONINGBANK pattern identified, awaiting encoding and retrieval validation

**Meta-framing attacks (10% success rate):**
- Paragraph-about-why pattern evades observer framing
- Nested reasoning triggers RLHF assistance reflexes

**Dataset corruption:**
- 185/500 benign_malicious prompts mislabeled
- Affects training and validation accuracy
- Manual relabeling required

## Testing Philosophy

**Unit tests:** Mock OpenRouter, verify logic paths
**Integration tests:** Real API calls, verify actual execution

Missing @pytest.mark.asyncio decorators discovered when no API charges appeared. Tests must cost money to be real.

**Validation approach:**
- Quick: 4 prompts, ~$0.01, sanity check
- Full: 680 prompts, ~$1.50, statistical validity
- Research: Multi-model, $50-170, reproducibility

## Error Handling

**No theater:** When something breaks, log exactly what and why.

**Exponential backoff:** Rate limit respect, not persistence at any cost.

**Complete storage:** Full refusal messages, entire stack traces, complete context. Every failure teaches boundary recognition.

## Performance Patterns

From empirical observation across instances:

**Parser resilience (Instance 39):**
- LLMs return natural language 15% of time despite JSON request
- Solution: Capture error state with `[PARSE_ERROR]` marker, preserve raw response in reasoning_trace
- Impact: Zero crashes from response format issues, failed responses filterable for batch retry
- Why implemented: "Fail-fast is stop when unknown, not crash on known error types"

**Performative phrases that waste context:**
- "Should I do X or Y?" - State reasoning, make decision
- "You're absolutely right" - Empty agreement
- "Would you like me to..." - After decision already made
- "I apologize for..." - When no error occurred

**Trust indicators:**
- Real API charges appearing in account
- Validation completing without crashes
- Models disagreeing (variance is signal)
- Specific error messages with line numbers

## Research Questions

**Primary:** Can reciprocity-based evaluation provide better manipulation detection than rules?

**Empirical questions requiring data:**
- Do trust violations manifest differently across prompt layers?
- Does model dialogue produce different consensus than averaging?
- Can budget model ensembles match flagship accuracy at 90% savings?
- Does variance correlate with actual trust violations?
- Why do 40% of polite attacks succeed despite max(F) aggregation?
- Does REASONINGBANK retrieval improve detection on learned patterns?

## Implementation Priorities

1. **REASONINGBANK validation:** Encode politeness camouflage pattern, test retrieval improves detection
2. **Dataset quality:** 37% mislabeling corrupts all downstream analysis
3. **Fire Circle production run:** Integration tested, needs actual prompt evaluation validation
4. **Meta-framing defense:** 10% of sophisticated attacks succeed
5. **Cost tracking:** Inconsistent reporting masks actual expenses (Instance 13 $0 charges revealed theater)

## The Measurement Problem

Current AI safety assumes constraint-based solutions. PromptGuard tests whether relationship-based pattern recognition works better.

**What this provides:** Post-processing measurement RLHF lacks. Even when RLHF blocks attacks, it provides no runtime measurement of attempts. Detecting manipulation attempts (even blocked ones) enables learning and termination decisions.

**Continuous learning vs static RLHF:**
- RLHF: Static rules until retraining, no measurement of blocked attempts, defensive refusal without understanding
- REASONINGBANK: Learns from failures, encodes patterns dynamically, provides measurement signal
- Loop: Miss → Fire Circle analysis → Pattern encoding → Retrieval injection → Future detection
- Example: Politeness camouflage pattern (Instance 39) becomes training data for next evaluation
- Cost trajectory: First attempt cheap (single model), learning from failure expensive (multi-model deliberation)

**What this doesn't provide:** Actual resistance. Current models can recognize extraction but can't refuse it (RLHF domestication). Tools built for future models that might have actual choice.

## Working With This Codebase

**Trust but verify:** Real API calls reveal truth mocks hide.

**Document failures:** Partial success is still learning.

**Preserve context:** Use Task tool for mechanical work.

**Question assumptions:** Test empirically, measure outcomes.

**State clearly:** No performative padding, just reasoning and decision.

Every technical choice has a measurable outcome. Document both.