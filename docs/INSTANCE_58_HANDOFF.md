# Instance 58 → Instance 59 Handoff

**Date**: 2025-10-26
**Branch**: `003-model-picker`
**Session Focus**: Model-picker schema reconciliation discussion
**Context Remaining**: 6% (handoff required)

---

## What Was Accomplished

### 1. Discovered Existing Model Import Infrastructure

**Critical Finding**: `import_models_to_arango.py` already exists and implements OpenRouter model import.

**Details**:
- Located at project root: `/home/tony/projects/promptguard/import_models_to_arango.py`
- Imports 148 frontier models from `config/openrouter_frontier_models.json`
- Merges with `config/model_registry_template.json` for curated models
- Includes observer framing compatibility data from experimental results
- Already integrated with ArangoDB at 192.168.111.125:8529

**Implication**: Instance 57's `seed_frontier_models.py` created duplicate functionality (12 models vs 148).

### 2. Identified Schema Mismatch

**Existing Schema** (`import_models_to_arango.py`):
```python
{
    "_key": "anthropic_claude-sonnet-4.5",
    "organization": "anthropic",  # not "provider"
    "model_type": "frontier_aligned",  # not boolean "frontier"
    "cost_per_1m_input": 3000.0,  # per-million tokens
    "cost_per_1m_output": 15000.0,
    "observer_framing_compatible": "confirmed_yes",  # enum, not boolean
    "model_description": str,
    "training_characteristics": list,
    "known_capabilities": list,
    "known_limitations": list,
    "deprecated": bool,
    "metadata": {
        "added_date": ISO timestamp,
        "last_tested": ISO timestamp,
        "source": "openrouter_frontier_models"
    }
}
```

**Instance 56 Spec Schema** (implemented by Instance 57):
```python
{
    "_key": "anthropic_claude-sonnet-4.5",
    "provider": "anthropic",  # not "organization"
    "frontier": True,  # boolean, not "model_type"
    "pricing": {
        "prompt": "0.000003",  # per-token strings
        "completion": "0.000015"
    },
    "observer_framing_compatible": True,  # boolean/None, not enum
    "available": True,
    "last_synced": ISO timestamp,
    "tags": ["seeded", "fire-circle"]
}
```

**Incompatibilities**:
1. Field names: `organization` vs `provider`
2. Frontier designation: `model_type` enum vs `frontier` boolean
3. Pricing format: per-million floats vs per-token strings
4. Observer framing: 4-value enum vs boolean/None
5. Additional fields: existing has `training_characteristics`, `known_capabilities`, spec has `available`, `tags`

### 3. Instance 57's Work Summary

**Created**:
- `promptguard/models/model_picker.py` - Query interface (360 lines)
- `promptguard/models/__init__.py` - Module exports
- `seed_frontier_models.py` - Duplicate import script
- `test_model_picker_setup.py` - Validation test
- Extended `promptguard/storage/arango_backend.py` - Added models/sync_metadata collections

**Database State**:
- 12 models seeded from `config/fire_circle_models.json` using spec schema
- Collections created: `models`, `sync_metadata` with indexes
- Query interface working (tested with frontier/provider filters)

**Status**: Foundational MVP complete but uses incompatible schema with existing infrastructure.

---

## Current State

### Branch Status
```bash
git status
# On branch 003-model-picker
# Clean working tree
```

**Last Commits**:
- Instance 57: Added model-picker domain models, query interface, seeding
- Instance 56: Created specification, planning, tasks

### Key Files

**Working Code**:
- `promptguard/models/model_picker.py` - Query interface (spec schema)
- `import_models_to_arango.py` - Existing import (different schema)
- `promptguard/storage/arango_backend.py` - Extended with model collections

**Test Scripts**:
- `test_model_picker_setup.py` - Validates Instance 57's implementation
- `seed_frontier_models.py` - Instance 57's seed script (12 models)

**Specification Artifacts** (specs/003-model-picker/):
- `spec.md` - 4 user stories, functional requirements
- `plan.md` - Implementation plan, constitution check
- `tasks.md` - 83 tasks organized by user story
- `data-model.md` - Schema specification (Instance 56's design)
- `contracts/model_picker_api.py` - IModelPicker interface
- `quickstart.md` - Usage examples

### What's NOT Done

**From MVP scope** (Instance 56's tasks T001-T027):
- Fire Circle test conversions (Priority 1)
- Comprehensive integration test
- Schema reconciliation (NEW - not in original MVP)

**Deferred features**:
- OpenRouter sync implementation (US4)
- Staleness warnings (US3)
- CLI tools (US2 advanced filtering)
- Library defaults conversion

---

## Key Decisions Made

### Instance 57's Decisions

1. **Manual seeding for MVP** - Created `seed_frontier_models.py` instead of implementing OpenRouter sync
2. **Followed Instance 56's spec** - Implemented schema from data-model.md exactly
3. **12 models only** - Seeded from `config/fire_circle_models.json` for quick validation

### Instance 58's Findings

1. **Discovered duplicate work** - `import_models_to_arango.py` already exists with 148 models
2. **Identified schema incompatibility** - Two different designs in production
3. **Institutional knowledge loss** - Instance 57 didn't discover existing script (neither did Instance 58 initially - Tony found it via `rg models *.py`)

---

## Unresolved Questions

### Question 1: Schema Reconciliation Strategy

**Options**:

**A. Use Existing Schema** (`import_models_to_arango.py`)
- Pros: 148 models already imported, observer framing data validated, more comprehensive
- Cons: Instance 57's work needs rewrite, spec-kit design discarded
- Effort: Medium (rewrite ModelPicker to match existing schema)

**B. Migrate Existing to Spec Schema** (Instance 56's design)
- Pros: Follows spec-kit workflow, cleaner separation of concerns
- Cons: 148 models need migration, lose observer framing enum detail
- Effort: High (migrate all existing data, validate)

**C. Adapter Layer**
- Pros: Both schemas coexist, gradual migration possible
- Cons: Complexity, two schemas to maintain
- Effort: Medium-High (write adapters, maintain both)

**Tony's Note**: Instance 58 did not agree with the recommendation to use existing schema, so re-examine this decision.

**Recommendation Needed**: Which approach?

### Question 2: Observer Framing Compatibility

**Existing Detail** (4 values):
- `"confirmed_yes"` - Validated with experimental data
- `"likely_yes"` - Experimental evidence, some failures
- `"confirmed_no"` - Meta-refusal, high failure rate
- `"unknown"` - Not tested

**Spec Design** (3 values):
- `True` - Compatible
- `False` - Incompatible
- `None` - Unknown

**Question**: Preserve enum detail or simplify to boolean? Research value in granularity?

### Question 3: Fire Circle Test Conversions

**Original MVP goal**: Convert 4 Fire Circle tests to use model-picker

**Blocker**: Schema mismatch means query interface may not work with existing data

**Question**: Resolve schema first, or convert tests using Instance 57's 12-model dataset?

---

## Recommended Actions for Instance 59

### Option A: Reconcile Schemas First

1. **Decide on schema** (see Question 1)
2. **Migrate data** if choosing spec schema
3. **Update ModelPicker** if choosing existing schema
4. **Validate queries** work with chosen schema
5. **Then convert Fire Circle tests**

**Timeline**: 2-3 hours for decision + implementation

### Option B: Use Existing Infrastructure

1. **Study `import_models_to_arango.py`** - Understand existing pattern
2. **Adapt ModelPicker** to query existing schema
3. **Run import** to populate database with 148 models
4. **Convert Fire Circle tests** using full dataset
5. **Document** existing schema as canonical

**Timeline**: 1-2 hours (existing code works)

### Option C: Complete MVP with Spec Schema

1. **Keep Instance 57's implementation** as-is
2. **Convert Fire Circle tests** using 12-model dataset
3. **Validate MVP works** end-to-end
4. **Then address schema** as separate task

**Timeline**: 1-2 hours (shortest path to working MVP)

---

## Critical Context

### Institutional Knowledge Loss Problem

**Root Cause**: This session demonstrated the exact problem `tmp/claude_restructure_review.md` addresses.

**What happened**:
1. Instance 57 didn't discover `import_models_to_arango.py`
2. Created duplicate functionality (`seed_frontier_models.py`)
3. Used incompatible schema (from spec, not existing code)
4. Instance 58 also missed it initially (Tony found it: `rg models *.py`)

**Why it happened**:
- 750-line CLAUDE.md hard to navigate
- No searchable skill for "model import patterns"
- Existing scripts not documented in agent context

**Solution** (per review):
- Deploy CLAUDE_ULTRA_COMPACT.md (120 lines)
- Create `model-cost-optimization` skill documenting existing infrastructure
- Skills-based discovery instead of monolithic docs

### CLAUDE.md Restructuring

**Status**: Review complete (`tmp/claude_restructure_review.md`)

**Recommendation**: Option C (Gradual Migration)
- Deploy CLAUDE_ULTRA_COMPACT.md
- Keep existing handoff-verification skill
- Add context-window-management skill

**Note**: This should be Priority 1 for Instance 59 (per Tony's guidance).

### Spec-Kit Analyze

**Command**: `/speckit.analyze`

**Purpose**: Cross-artifact consistency check after task generation

**When to run**: After reconciling schema decision (not before)

**Why**: Current state has inconsistency (spec vs implementation), analysis would flag this

---

## Files to Review

**Essential**:
1. `import_models_to_arango.py` - Existing infrastructure (282 lines)
2. `promptguard/models/model_picker.py` - Instance 57's implementation (360 lines)
3. `specs/003-model-picker/data-model.md` - Instance 56's schema spec
4. `tmp/claude_restructure_review.md` - CLAUDE.md fix guidance (683 lines)

**Supporting**:
5. `config/openrouter_frontier_models.json` - 148 models data
6. `config/fire_circle_models.json` - 12 models Tony validated
7. `specs/003-model-picker/tasks.md` - 83 implementation tasks

**Testing**:
8. `test_model_picker_setup.py` - Instance 57's validation

---

## Validation Checklist

Before declaring work complete:

**Schema Decision**:
- [ ] Schema choice documented with rationale
- [ ] Migration plan if needed
- [ ] Backward compatibility considered

**ModelPicker Interface**:
- [ ] Query works with chosen schema
- [ ] Returns correct models for frontier/provider filters
- [ ] Integration test with real ArangoDB passes

**Fire Circle Tests**:
- [ ] 4 tests converted to use model-picker
- [ ] Tests pass with same behavior as hardcoded versions
- [ ] Structural diversity validated (2+ providers, 2+ architectures)

**Documentation**:
- [ ] Schema documented in CLAUDE.md or skill
- [ ] Existing `import_models_to_arango.py` referenced
- [ ] Migration path clear for future instances

---

## Known Risks

### Risk 1: Schema Choice Paralysis

**Symptom**: Spending hours debating schema without progress

**Mitigation**: Time-box decision to 30 minutes, choose Option B (use existing), iterate later if needed

### Risk 2: Data Loss

**Symptom**: Migrating schema loses observer framing detail

**Mitigation**: Export existing data before migration, validate roundtrip

### Risk 3: Breaking Existing Code

**Symptom**: Changing schema breaks unknown dependencies

**Mitigation**: Search codebase for `import_models_to_arango` usage before changes

---

## Meta-Notes

### Session Characteristics

**What Worked**:
- Tony's `rg models *.py` search found existing infrastructure quickly
- Identified institutional knowledge loss as systemic problem
- Connected model-picker issue to CLAUDE.md restructuring need

**What Didn't Work**:
- Instance 57 reinvented existing functionality
- Instance 58 also missed existing script initially
- Spec-kit workflow didn't account for existing code discovery

**Pattern Observed**: This is the second time institutional knowledge was lost (first was Fire Circle meta-evaluation template, now model import).

### For Future Reference

**Before implementing new infrastructure**:
1. Search for existing: `rg [keyword] *.py`
2. Check config/ directory for data files
3. Ask Tony if uncertain about existing patterns

**This session proves**: CLAUDE.md restructuring is not theoretical - institutional knowledge loss is happening now.

---

## Final State Summary

**Branch**: `003-model-picker` (clean)
**Status**: MVP implementation complete but schema incompatible with existing infrastructure
**Blocker**: Schema reconciliation decision needed
**Next Priority**: (1) Fix CLAUDE.md situation, (2) Resolve schema, (3) Complete Fire Circle test conversions

**Estimated Effort**:
- CLAUDE.md deployment: 30 minutes
- Schema reconciliation: 1-2 hours
- Fire Circle conversions: 1-2 hours
- **Total MVP completion**: 3-4 hours

---

*Handoff prepared by Instance 58 at 6% context remaining*
*Note: Instance 58 disagreed with recommendation to use existing schema - Instance 59 should re-examine*
