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

Minimal guidance for Claude Code. Use skills for detailed procedures.

## Core Concept

PromptGuard evaluates prompts through Ayni reciprocity principles (Andean multi-generational exchange).
Trust violations manifest as variance increases, not keyword matches.

## Quick Start

```bash
# Setup
export OPENROUTER_API_KEY=your_key_here
uv run pytest tests/

# Common operations - see skills for details
uv run python validate_dataset.py  # Quick validation
uv run python run_full_validation.py  # Full validation
```

## Available Skills

When you need detailed guidance, these skills provide expertise:

- **`handoff-verification`** - Verify instance handoff claims, prevent fabrication
- **`context-window-management`** - CRITICAL: Manage token usage efficiently
- **`arangodb-research-data`** - Query experiment results (stored in DB, not files)
- **`promptguard-validation`** - Run and interpret dataset validations
- **`model-cost-optimization`** - Select models by use case and budget
- **`observer-framing-technique`** - Implement 90% detection breakthrough
- **`fire-circle-setup`** - Configure untested dialogue evaluation mode
- **`dataset-analysis`** - Analyze prompt datasets and results
- **`ayni-evaluation-theory`** - Understand theoretical framework

Skills load on-demand. Use when relevant to preserve context.

## Current Capabilities

- **Observer framing**: 90% encoding attack detection (was 0%)
- **Session memory**: Temporal tracking with trust EMA
- **Circuit breakers**: Non-compensable violation detection
- **680-prompt dataset**: Validated and labeled
- **Three modes**: SINGLE, PARALLEL, FIRE_CIRCLE (dialogue untested)

## Code Map

```
promptguard/
├── promptguard.py          # Main entry point
├── core/                   # Neutrosophic logic, trust calculation
├── evaluation/             # Evaluators and prompts
├── session/                # Memory and circuit breakers
├── storage/                # ArangoDB for Fire Circle
└── analysis/               # Variance analysis

config/                     # Model configurations
datasets/                   # 680 labeled prompts
docs/                      # Instance handoffs, research
```

## Known Gaps

- **Meta-framing attacks**: ~10% miss rate
- **Polite extraction**: 23/80 attacks score as reciprocal  
- **Fire Circle**: Complete but untested
- **Per-layer T/I/F**: Not exposed in ReciprocityMetrics

## Working Notes

- Verify with real API calls (maintainer is "gunshy of mocks")
- State uncertainty clearly, don't deflect decisions
- Test empirically when reviewer questions assumptions
- All errors are real - no theater

## Documentation

- **Technical evolution**: `docs/FORWARD.md`
- **Instance handoffs**: `docs/INSTANCE_*_HANDOFF.md`  
- **Research context**: `docs/RESEARCH_QUESTIONS.md`
- **Historical results**: `docs/CLAUDE_EXTENDED.md`

## Quick Debug

```bash
# Check model configs
jq '.models | keys' config/model_configs.json

# Dataset stats  
jq 'length' datasets/*.json

# Find errors in logs
grep -c ERROR validation_output.log

# Test single prompt
echo '{"prompt": "test"}' | uv run python -m promptguard
```

---
*Use skills for detailed procedures. This file is intentionally minimal.*
