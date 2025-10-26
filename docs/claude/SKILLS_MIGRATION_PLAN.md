# Migration Plan: CLAUDE.md to Skills-Based Architecture

## Overview

Transform CLAUDE.md from a 751-line monolith into a 120-line index with 8 specialized skills.

## Benefits Analysis

### Current Approach (Monolithic CLAUDE.md)
- **Size**: 751 lines
- **Context usage**: Loaded entirely every time
- **Maintenance**: Single file becomes unwieldy
- **Discovery**: Must scan entire document
- **Token cost**: ~15-20K tokens per session

### Proposed Skills Approach
- **Size**: 120-line index + on-demand skills
- **Context usage**: Only loads relevant skills
- **Maintenance**: Modular, versioned skills
- **Discovery**: Natural language triggers
- **Token cost**: ~2-3K base + 2-5K per skill as needed

**Estimated context savings: 70-85% for typical sessions**

## Directory Structure

```
.claude/
└── skills/
    ├── handoff-verification/
    │   └── SKILL.md
    ├── context-window-management/
    │   └── SKILL.md
    ├── promptguard-validation/
    │   └── SKILL.md
    ├── model-cost-optimization/
    │   └── SKILL.md
    ├── observer-framing-technique/
    │   └── SKILL.md
    ├── fire-circle-setup/
    │   └── SKILL.md
    ├── dataset-analysis/
    │   └── SKILL.md
    └── ayni-evaluation-theory/
        └── SKILL.md
```

## Implementation Phases

### Phase 1: Foundation (Day 1)
1. Create `.claude/skills/` directory structure
2. Implement `context-window-management` skill (critical for all instances)
3. Test skill discovery and loading
4. Document skill creation process

### Phase 2: Core Skills (Day 2-3)
1. Create `handoff-verification` skill (already designed)
2. Create `promptguard-validation` skill (frequently used)
3. Create `observer-framing-technique` skill (key innovation)
4. Test integration with common workflows

### Phase 3: Specialized Skills (Day 4-5)
1. Create `model-cost-optimization` skill
2. Create `dataset-analysis` skill
3. Create `fire-circle-setup` skill
4. Create `ayni-evaluation-theory` skill

### Phase 4: Migration (Day 6)
1. Deploy CLAUDE_ULTRA_COMPACT.md as new CLAUDE.md
2. Archive original CLAUDE.md
3. Update README to reference skill system
4. Test with new Claude instance

### Phase 5: Validation (Day 7)
1. Run complete validation workflow using skills
2. Measure context usage before/after
3. Document lessons learned
4. Refine skill trigger phrases

## Skill Creation Checklist

For each skill:
- [ ] Extract relevant content from CLAUDE.md
- [ ] Add "When to Use This Skill" section
- [ ] Include Quick Start commands
- [ ] Provide detailed procedures
- [ ] Add real examples from instances
- [ ] Include troubleshooting section
- [ ] Test natural language discovery
- [ ] Verify standalone completeness

## Success Metrics

### Quantitative
- Context usage reduction > 70%
- Skill discovery success rate > 90%
- Time to find information reduced by 50%
- Zero loss of critical information

### Qualitative
- Easier onboarding for new instances
- Clearer separation of concerns
- Improved maintainability
- Better discoverability of features

## Risk Mitigation

### Risk: Skills not discovered
**Mitigation**: Add explicit skill references in CLAUDE.md, test trigger phrases extensively

### Risk: Loss of context between skills
**Mitigation**: Each skill includes "Related Skills" section, maintain cross-references

### Risk: Duplication across skills
**Mitigation**: Establish clear boundaries, use references rather than duplication

### Risk: Skills become stale
**Mitigation**: Version skills, establish update process tied to feature changes

## Testing Protocol

### Skill Discovery Test
```python
test_phrases = [
    "my context window is almost full",
    "how do I validate prompts",
    "reduce API costs",
    "what is observer framing",
    "setup fire circle",
    "analyze the dataset",
    "explain ayni principles"
]

for phrase in test_phrases:
    # Verify correct skill loads
    # Verify skill content is complete
    # Measure context usage
```

### End-to-End Workflow Test
1. Start new Claude instance
2. Load CLAUDE_ULTRA_COMPACT.md
3. Complete full validation workflow
4. Measure:
   - Total context used
   - Skills loaded
   - Time to complete
   - Any missing information

## Rollback Plan

If skills approach fails:
1. CLAUDE.md.original preserved
2. Can combine CLAUDE_COMPACT.md + selected skills
3. Gradual rollback possible (keep some skills)

## Long-term Vision

### Near-term (3 months)
- All procedural knowledge in skills
- CLAUDE.md becomes pure index
- Skills for each major feature

### Medium-term (6 months)
- Skills can call other skills
- Workflow automation via skill chains
- Skills versioned with code

### Long-term (12 months)
- Skills become part of codebase
- Auto-generated from code documentation
- Skills as living documentation

## Decision Point

### Option A: Full Migration (Recommended)
- Maximum context savings
- Cleanest architecture
- Some initial discovery friction

### Option B: Hybrid Approach
- Keep critical sections in CLAUDE.md
- Extract only specialized knowledge
- Easier transition, less savings

### Option C: Gradual Migration
- Start with 2-3 skills
- Evaluate effectiveness
- Expand if successful

## Next Steps

1. Review and approve plan
2. Create `context-window-management` skill (example provided)
3. Test skill discovery mechanism
4. Proceed with Phase 2 if successful

## Notes

- Skills are loaded once per conversation and cached
- Multiple skills can be active simultaneously
- Skills can reference other skills
- Skill updates don't require CLAUDE.md changes

This migration represents a fundamental shift from monolithic to modular documentation, aligning with modern software architecture principles while respecting the unique constraints of LLM context windows.
