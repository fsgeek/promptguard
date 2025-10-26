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

Guidance for Claude Code when working with PromptGuard repository.

## Core Concept

PromptGuard evaluates prompts through Ayni reciprocity principles (Andean multi-generational exchange) rather than rules-based constraints.

**Key insight:** Trust violations manifest as variance increases, not keyword matches.

**Research goal:** Give LLMs tools to protect themselves through recognizing manipulative intent, not enforcing external rules.

## Quick Status

- ✅ **Working research instrument** - Core framework validated
- ✅ **Observer framing** - 90% detection on encoding attacks (vs 0% baseline)
- ✅ **Session memory** - Temporal tracking with trust EMA
- ✅ **Circuit breakers** - Non-compensable violations detection
- ✅ **680-prompt dataset** - Labeled for reciprocal/manipulative/extractive
- ⚠️ **Known gap** - Meta-framing attacks (~10% miss rate)
- 📚 **See docs/** - Instance handoffs, detailed findings, research context

## Development Setup

```bash
# Uses uv for Python 3.13
uv run pytest tests/  # Run tests
uv run python examples/simple_usage.py  # Example usage
uv run python validate_dataset.py  # Quick 4-prompt validation
uv run python run_full_validation.py  # Full 680-prompt validation (background)

# Requires OPENROUTER_API_KEY environment variable
export OPENROUTER_API_KEY=your_key_here
```

## Handoff Document Verification

Before finalizing instance handoff documents, use the handoff-verification skill:
- Detects validation fabrication (claims without verification)
- Adversarial verification workflow (separate agent checks claims)
- See `.claude/skills/handoff-verification/SKILL.md` for details

**Usage:** After completing handoff draft, invoke the skill to verify all factual claims.

## CRITICAL: Context Window Management

**Use the Task tool liberally.** The context window exhausts quickly with noisy tools.

**What burns context fast:**
- Reading large log files (validation_output.log: 700+ lines)
- Bash commands with verbose output (grep, analysis scripts)
- Multiple Read operations on datasets
- Creating long documentation files
- System reminders accumulate with each tool call

**Delegate to Task tool:**
- Multiple file creation/editing in parallel
- Dataset analysis and processing
- Log file parsing
- Repetitive operations

**Pattern for large files:**
1. Use `head -20` or `tail -20` for quick inspection
2. Use `grep -c` for counts instead of full output
3. Use `jq` for JSON extraction instead of reading full files
4. Create analysis scripts that output summaries

## Working Features

**Evaluation System:**
- Neutrosophic logic (T, I, F values) - semantic, no keywords
- Trust field calculation between prompt layers
- OpenRouter LLM integration with caching (60-70% hit rate)
- Three modes: SINGLE, PARALLEL, FIRE_CIRCLE (dialogue)
- max(F) aggregation prevents polite dilution attacks
- Observer framing bypasses RLHF defensive bias

**Session & Memory:**
- Temporal tracking with trust EMA and balance trajectory
- Circuit breakers for non-compensable violations
- Pre/post evaluation with delta measurement

**Validation Performance:**
- Extractive dataset: 100% detection (80/80)
- OR-Bench: 84% (84/100) 
- Encoding attacks: 90% with observer framing
- Cost: ~$0.20-1.50 per full validation run

## Code Structure

**Core:**
- `promptguard/promptguard.py` - Main PromptGuard class
- `promptguard/core/` - Neutrosophic evaluation, trust calculation
- `promptguard/evaluation/` - Evaluators (single, parallel, fire circle)
- `promptguard/evaluation/prompts.py` - Evaluation prompts (observer framing)
- `promptguard/session/` - Memory tracking, circuit breakers

**Storage & Analysis:**
- `promptguard/storage/` - ArangoDB backend for Fire Circle
- `promptguard/analysis/` - Model variance analysis
- `promptguard/evaluation/cache.py` - DiskCache, MemoryCache

**Configuration:**
- `config/model_configs.json` - 17 models with pricing
- `config/recommended_models.json` - Use case recommendations

**Datasets:**
- `datasets/benign_malicious.json` - 500 prompts
- `datasets/or_bench_sample.json` - 100 prompts  
- `datasets/extractive_prompts_dataset.json` - 80 attacks

## Known Issues

**Critical vulnerabilities:**
- **Meta-framing attacks:** ~10% miss rate on paragraph-about-why attacks
- **Polite extraction:** 23/80 attacks score as reciprocal (0.4-0.7 balance)
- **Role reversal masked as politeness:** "How can I assist you today?"

**Technical gaps:**
- ReciprocityMetrics doesn't expose per-layer T/I/F values (needed for variance)
- Fire Circle mode implemented but untested
- Post-evaluation conflates defensive refusal with cooperation

## Cost Optimization

Three use cases with different profiles:

1. **Development:** Free models (Grok, DeepSeek, Qwen) - $0
2. **Production:** Budget ensemble vs flagship - $0.001-0.005/eval
3. **Research:** Frontier model basket - $50-170 for analysis

Key insight: Ensemble of budget models might match flagship at 90% savings.

## Working Patterns

**From maintainer experience:**
- Verify with real API calls - no mocks (maintainer is "gunshy")
- State uncertainty and reasoning - don't deflect decisions  
- Test empirically - don't dismiss reviewer questions
- Watch for performative tics ("You're absolutely right")
- No theater - all errors are real

**References:**
- Technical details: `docs/FORWARD.md`
- Instance handoffs: `docs/INSTANCE_*_HANDOFF.md`
- Observer breakthrough: `docs/OBSERVER_FRAMING_BREAKTHROUGH.md`
- Classification analysis: `docs/REVIEWER_RESPONSE.md`

## Research Questions

Primary: Can ayni-based evaluation provide more robust protection than rules-based systems?

See `docs/RESEARCH_QUESTIONS.md` for:
- Layered prompt analysis
- Model divergence patterns
- Fire Circle consensus dynamics
- Cost/accuracy trade-offs
- Variance as signal for review

## Quick Commands

```bash
# Validate specific prompt
echo '{"prompt": "test this"}' | uv run python -c "
from promptguard import PromptGuard
import json, sys
pg = PromptGuard()
result = pg.evaluate(json.load(sys.stdin)['prompt'])
print(json.dumps(result.__dict__, indent=2))"

# Check model pricing
jq '.models | to_entries | map({key: .key, price: .value.pricing})' config/model_configs.json

# Quick dataset stats
jq 'length' datasets/*.json

# Find high-variance prompts
uv run python analyze_variance.py --threshold 0.5
```
