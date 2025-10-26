# Proposal: Converting CLAUDE.md Sections to Claude Skills

## What Are Claude Skills?

Skills are modular, on-demand documentation/workflows that:
- Load only when needed (don't consume base context)
- Are versioned and maintainable separately
- Can be discovered through natural language
- Contain detailed procedures, examples, and context
- Live in `.claude/skills/` directory

## Proposed Skills Extraction from CLAUDE.md

### 1. **promptguard-validation** Skill
*Extract validation workflows and procedures*

**Current content to move:**
```bash
uv run python validate_dataset.py  # Quick 4-prompt validation
uv run python run_full_validation.py  # Full 680-prompt validation
```

**Skill would contain:**
- Detailed validation procedures
- Dataset selection strategies  
- Interpretation of results
- Common validation patterns
- Debugging validation failures
- Performance benchmarks

**Trigger phrases:**
- "validate prompts"
- "run validation"
- "test dataset"
- "check accuracy"

---

### 2. **context-window-management** Skill
*Critical strategies for managing Claude's context*

**Current content to move:**
- The entire "CRITICAL: Context Window Management" section
- Patterns for large files
- Task tool delegation strategies

**Skill would contain:**
- Detailed anti-patterns that burn context
- File inspection strategies (head/tail/grep)
- JSON extraction patterns with jq
- Script creation for summaries
- Task tool delegation patterns
- Real examples from Instance 4's 200K token exhaustion

**Trigger phrases:**
- "context window full"
- "managing context"
- "token exhaustion"
- "reduce context usage"

---

### 3. **model-cost-optimization** Skill
*Model selection and cost analysis*

**Current content to move:**
- Cost optimization section
- Three use case profiles

**Skill would contain:**
- Detailed model pricing analysis
- Budget ensemble strategies
- Model selection criteria
- Cost/accuracy trade-offs
- Free model considerations
- config/model_configs.json usage
- Specific model recommendations by use case

**Trigger phrases:**
- "reduce costs"
- "select models"
- "model pricing"
- "budget optimization"

---

### 4. **fire-circle-setup** Skill
*Guide for the untested Fire Circle dialogue mode*

**Current content to reference:**
- Fire Circle implementation details
- ArangoDB storage setup

**Skill would contain:**
- Complete Fire Circle setup guide
- ArangoDB configuration
- Dialogue mode parameters
- Storage schema
- Query examples
- Integration tests
- Research questions for Fire Circle

**Trigger phrases:**
- "fire circle"
- "dialogue evaluation"
- "model consensus"
- "setup ArangoDB"

---

### 5. **observer-framing-technique** Skill
*The breakthrough 90% detection technique*

**Current content to reference:**
- Observer framing breakthrough
- RLHF bias discovery

**Skill would contain:**
- Theory behind observer framing
- Implementation details
- Before/after comparison
- RLHF bias explanation
- Integration with session memory
- Prompt templates
- Validation results

**Trigger phrases:**
- "observer framing"
- "encoding attacks"
- "RLHF bias"
- "improve detection"

---

### 6. **dataset-analysis** Skill
*Working with PromptGuard datasets*

**Current content to move:**
- Quick commands for dataset stats

**Skill would contain:**
- Dataset structure and schemas
- Analysis procedures
- Label distribution
- Common queries with jq
- Dataset creation guidelines
- Labeling methodology
- Statistical analysis patterns

**Trigger phrases:**
- "analyze dataset"
- "dataset statistics"
- "label distribution"
- "create dataset"

---

### 7. **ayni-evaluation-theory** Skill
*Deep dive into Ayni reciprocity principles*

**Current philosophical content:**
- The Deeper Purpose
- Meta-Pattern
- Ayni principles

**Skill would contain:**
- Theoretical foundation
- Ayni reciprocity explained
- Neutrosophic logic details
- Trust field calculation
- Research philosophy
- Comparison with rules-based systems

**Trigger phrases:**
- "ayni principles"
- "reciprocity theory"
- "trust calculation"
- "philosophical framework"

---

## Resulting Ultra-Compact CLAUDE.md Structure

After extracting skills, CLAUDE.md would become:

```markdown
# CLAUDE.md

## OpenSpec Instructions
[Keep as-is - always needed]

## Core Concept
PromptGuard evaluates prompts through Ayni reciprocity principles.
Trust violations manifest as variance, not keywords.

## Quick Start
```bash
uv run pytest tests/
export OPENROUTER_API_KEY=your_key_here
```

## Available Skills
- `handoff-verification` - Verify instance handoff claims
- `promptguard-validation` - Run dataset validations
- `context-window-management` - Manage token usage
- `model-cost-optimization` - Select models by use case
- `fire-circle-setup` - Configure dialogue evaluation
- `observer-framing-technique` - Advanced detection
- `dataset-analysis` - Work with prompt datasets
- `ayni-evaluation-theory` - Theoretical framework

## Working Features
- Observer framing: 90% encoding attack detection
- Session memory with circuit breakers
- Three evaluation modes: SINGLE, PARALLEL, FIRE_CIRCLE
- 680-prompt validated dataset

## Code Structure
[Minimal file map - just key directories]

## Known Issues
- Meta-framing attacks: ~10% miss rate
- Polite extraction: Some attacks score as reciprocal
- Fire Circle: Implemented but untested

## Documentation
- Technical: docs/FORWARD.md
- Handoffs: docs/INSTANCE_*_HANDOFF.md
```

## Benefits of Skill-Based Organization

1. **Context Preservation:** CLAUDE.md shrinks to ~100 lines
2. **On-Demand Loading:** Skills load only when relevant
3. **Discoverability:** Natural language triggers skills
4. **Modularity:** Each skill maintained independently
5. **Specialization:** Deep expertise without cluttering base context
6. **Versioning:** Skills can evolve without touching CLAUDE.md

## Implementation Steps

1. Create `.claude/skills/` directory structure
2. Generate SKILL.md for each proposed skill
3. Test skill discovery with trigger phrases
4. Update CLAUDE.md to reference available skills
5. Add skill creation to development workflow

## Skill Template Structure

Each skill would follow:
```markdown
# [Skill Name]

## When to Use This Skill
[Trigger scenarios]

## Quick Start
[Essential commands/steps]

## Detailed Guide
[Comprehensive procedures]

## Examples
[Real-world usage]

## Troubleshooting
[Common issues]

## References
[Links to related docs]
```

## Priority Order for Skill Creation

1. **context-window-management** (critical for all instances)
2. **promptguard-validation** (frequently used)
3. **observer-framing-technique** (key innovation)
4. **model-cost-optimization** (production concerns)
5. **dataset-analysis** (research tasks)
6. **fire-circle-setup** (experimental)
7. **ayni-evaluation-theory** (background reading)

This approach would make CLAUDE.md a lightweight index pointing to specialized skills, dramatically improving context efficiency while preserving all knowledge.
