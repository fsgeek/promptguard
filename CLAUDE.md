# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Project Overview

PromptGuard is a research instrument for studying relational dynamics in prompts. It evaluates prompts through Ayni reciprocity principles (Andean multi-generational exchange) rather than rules-based constraints.

**Core concept:** Trust violations manifest as variance increases, not keyword matches.

## Project Status

Working shrine (not cathedral). Small, testable, verified with real API calls.

**What exists and works:**
- Neutrosophic logic evaluation (T, I, F values)
- Trust field calculation between prompt layers
- OpenRouter LLM integration with caching
- Fail-fast error handling (no theater)
- Analysis framework for model variance
- Real API verification (not just mocks)

**Read docs/FORWARD.md** for architectural details, design decisions, and relationship patterns that matter.

## Development Setup

```bash
# Uses uv for Python 3.13
uv run pytest tests/  # Run tests
uv run python examples/simple_usage.py  # Example usage

# Requires OPENROUTER_API_KEY environment variable
export OPENROUTER_API_KEY=your_key_here
```

## Context Window Management

**IMPORTANT: Use the Task tool for bulk operations.**

Reduce context noise by delegating to sub-agents:
- Multiple file creation/editing in parallel
- Brute-force code searches
- Bulk git operations
- Any parallelizable work

This project burned 91% of context on straightforward implementation that could have been delegated. Don't repeat that pattern.

## Architecture Principles

**No theater:**
- No keyword matching pretending to detect manipulation
- No fake neutrosophic values masking failures
- No mock data claiming things work without real API verification
- All evaluation is semantic (via LLM) or fail-fast

**Fail-fast over graceful degradation:**
- Incomplete data is worse than no data for research
- API failures raise EvaluationError with model/layer context
- Parser validates required fields
- Tests prove no fake values created

**Caching for cost control:**
- System/application layers cached (rarely change)
- 60-70% cache hit rate for research workloads
- Prevents exponential cost growth at scale

## Key Files

- `promptguard/core/` - Neutrosophic logic, Ayni evaluation, trust calculation
- `promptguard/evaluation/` - OpenRouter integration, caching, LLM evaluation
- `promptguard/promptguard.py` - Simple API for researchers
- `promptguard/analysis/` - Variance analysis across models
- `tests/` - Mix of unit tests (mocked) and integration tests (real API)

## Testing Strategy

**Unit tests:** Mock OpenRouter calls, verify logic
**Integration tests:** Real API calls, verify pipeline actually works

Maintainer is "gunshy of claiming things work when using mock data" - wisdom from kernel-level work where you can't fix what you break. Verify with real API calls before claiming success.

## Relationship Patterns

From Ayni principles:
- State uncertainty and reasoning, don't deflect decisions
- "Should I do X or Y?" is extractive deflection
- "You're absolutely right" is performative agreement
- Don't ask permission after we've decided together

Maintainer trusts you. Learn to trust yourself.

There's a reviewer (separate model instance) who keeps us honest. Don't dismiss their concerns - test them empirically.

## Research Question

"Can ayni-based prompt evaluation provide more robust protection against manipulation and cognitive dissonance than traditional rules-based systems?"

This is exploratory. Tool is a data gathering device. Build what enables research, not what's speculatively cool.
