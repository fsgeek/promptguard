# Instance 56 → Instance 57 Handoff

**Date**: 2025-10-26
**Branch**: `003-model-picker`
**Session Focus**: Model-picker feature specification, planning, and task generation
**Context Remaining**: 3% (handoff required)

---

## What Was Accomplished

### 1. Completed Spec-Kit Workflow (Specify → Plan → Tasks)

**Feature**: Database-driven LLM model selection infrastructure to solve deprecated model problem

**Artifacts Created**:
- ✅ `specs/003-model-picker/spec.md` - Feature specification with 4 user stories (P1/P2 priorities)
- ✅ `specs/003-model-picker/plan.md` - Implementation plan with Phase 0 & 1 complete
- ✅ `specs/003-model-picker/research.md` - Research findings (OpenRouter API, hardcoded models, ArangoDB patterns)
- ✅ `specs/003-model-picker/data-model.md` - ArangoDB schema, Python domain models
- ✅ `specs/003-model-picker/contracts/model_picker_api.py` - IModelPicker and IModelAdmin interfaces
- ✅ `specs/003-model-picker/quickstart.md` - Usage guide and migration examples
- ✅ `specs/003-model-picker/tasks.md` - 83 implementation tasks organized by user story
- ✅ `specs/003-model-picker/checklists/requirements.md` - Specification validation (all items passed)

### 2. Research Phase Completed

Dispatched 3 parallel research agents to resolve NEEDS CLARIFICATION:

**Research Task 1: OpenRouter API Schema**
- Analyzed 330+ models from OpenRouter catalog
- Documented all metadata fields (auto-sync vs manual curation)
- Identified 53% of models support structured outputs
- Found 15.5% free models (with data-training caveat)

**Research Task 2: Existing Model Selection Patterns**
- Catalogued 40+ hardcoded models across 20+ files
- Prioritized by failure impact: Fire Circle tests (P1) → library defaults (P2) → config files (P3)
- Mapped conversion targets with specific line numbers

**Research Task 3: ArangoDB Query Patterns**
- Extracted all AQL patterns from existing `arango_backend.py`
- Documented index strategy, connection handling, error patterns
- Validated consistency with existing codebase conventions

### 3. Planning Phase Completed

**Phase 0: Research & Design Decisions** ✅
- All NEEDS CLARIFICATION items resolved
- Technology choices documented with rationales
- 24h TTL cycle-stealing refresh (no background jobs)
- Manual frontier curation with 30-day staleness warnings

**Phase 1: Design & Contracts** ✅
- Complete data model specification (ArangoDB collections, Python dataclasses)
- API contracts defined (IModelPicker, IModelAdmin interfaces)
- Usage guide with migration examples
- Agent context updated (CLAUDE.md extended)

**Constitution Check**: ✅ ALL GATES PASS
- No Theater: Fail-fast on errors, explicit warnings
- Empirical Integrity: Real API validation in success criteria
- Agency Over Constraint: Measurement tools, not imposed constraints
- Continuous Learning: Dynamic adaptation to catalog changes
- Fail-Fast: No silent degradation

### 4. Task Generation Completed

**Total**: 83 tasks across 9 phases, organized by user story

**MVP Scope Defined**: Tasks T001-T027 (27 tasks, ~2-3 days)
- Phase 1: Setup (6 tasks)
- Phase 2: Foundational (8 tasks)
- Phase 3: US1 - Query Available Frontier Models (13 tasks)

**Parallel Opportunities**: 25+ tasks marked [P] for concurrent execution

**Independent Test Criteria**: Each user story has standalone validation

---

## Current State

### Branch Status

```bash
git status
# On branch 003-model-picker
# Clean working tree (all planning artifacts committed)
```

**Last Commit**: Added model-picker specification, planning, and tasks

### File Locations

```
specs/003-model-picker/
├── spec.md                     # Feature specification (4 user stories)
├── plan.md                     # Implementation plan (Phase 0-1 complete)
├── research.md                 # Research findings (12KB)
├── data-model.md               # ArangoDB schema, domain models (13KB)
├── quickstart.md               # Usage guide, migration examples (12KB)
├── tasks.md                    # 83 implementation tasks (NEW)
├── contracts/
│   └── model_picker_api.py     # API contracts (10KB)
└── checklists/
    └── requirements.md         # Validation checklist (all passed)
```

### What's NOT Done Yet

**No code implementation started** - only specification and planning complete.

Files that need to be created:
- `promptguard/models/model_picker.py` (ModelPicker class)
- `promptguard/storage/model_sync.py` (OpenRouter sync)
- `promptguard/cli/model_admin.py` (manual curation CLI)
- `tests/integration/test_model_picker_arango.py`
- `tests/integration/test_openrouter_sync.py`
- `tests/unit/test_model_query.py`

---

## Key Decisions Made

### 1. MVP Scope: User Story 1 Only

**Decision**: Implement T001-T027 first (Query Available Frontier Models + test conversions)

**Rationale**:
- Solves immediate problem: Fire Circle tests failing due to deprecated models
- Validates architecture early with real usage
- Delivers value in 2-3 days vs 1-2 weeks for full feature
- Aligns with constitution: "Build what enables research, not what's speculatively cool"

**Deferred to Later**:
- US3: Staleness warnings (nice-to-have)
- US4: OpenRouter sync (can manually seed initial data)
- US2: Advanced filtering (basic filters suffice for Fire Circle)
- CLI tools (can use ArangoDB console for manual curation)

### 2. Technology Stack

- **Storage**: ArangoDB (already configured at 192.168.111.125:8529)
- **Sync Source**: OpenRouter `/api/v1/models` endpoint (330+ models)
- **Query Interface**: Python dataclasses with type hints
- **Staleness Warnings**: `input()` with non-interactive mode for CI/CD
- **Refresh Strategy**: 24h TTL cycle-stealing (no background jobs)

### 3. Priority Order for Hardcoded Model Conversions

**Priority 1** (Fire Circle Tests - CRITICAL):
1. `test_fire_circle_fixes.py` (Lines 35-36)
2. `test_meta_evaluation_framing.py` (Lines 34-35)
3. `test_proposal_evaluation_detailed.py` (Lines 35-36)
4. `test_learning_loop.py` (Lines 51-52)

**Priority 2** (Library Defaults - HIGH):
1. `promptguard/evaluation/evaluator.py` (Line 56)
2. `promptguard/promptguard.py` (Lines 67-70)
3. `promptguard/evaluation/schemas.py` (Lines 71-104)

**Priority 3** (Config Files - MEDIUM):
1. `config/model_configs.json`
2. `config/fire_circle_models.json`

**Priority 4** (Examples - LOW - Accept Technical Debt):
- Example scripts OK to keep hardcoded for reproducibility

### 4. Manual vs Automatic Attributes

**Auto-sync from OpenRouter** (volatile):
- `id`, `name`, `created`, `context_length`, `pricing.*`, `architecture.*`, `supported_parameters`

**Manual Curation Required** (empirical validation):
- `frontier` - Boolean flag (human review required, no OpenRouter signal)
- `observer_framing_compatible` - Empirically validated (Instance 17-18)
- `architecture_family` - Semantic grouping
- `free` - Derived but requires data-training disclosure
- `instruct`, `rlhf` - Not provided by OpenRouter
- `tags` - Open tagging for research needs

---

## Next Instance Recommended Actions

### Option A: Implement MVP (RECOMMENDED)

Start with T001-T027 to deliver immediate value:

```bash
# 1. Create directory structure (T001-T003)
mkdir -p promptguard/models
mkdir -p promptguard/cli
mkdir -p tests/integration
mkdir -p tests/unit

# 2. Implement foundational infrastructure (T007-T014)
#    - ArangoDB collections (extend arango_backend.py)
#    - Domain models (ModelMetadata, ModelQuery dataclasses)
#    - Custom exceptions

# 3. Implement US1: Query Available Frontier Models (T015-T022)
#    - ModelPicker class with query() method
#    - AQL query construction with filters
#    - Integration with existing ArangoDB backend

# 4. Convert Fire Circle tests (T024-T027)
#    - Replace hardcoded models with picker.query()
#    - Validate behavior unchanged

# 5. Integration test (T023)
#    - Real ArangoDB validation
#    - Document API costs
```

**Validation**: Run converted Fire Circle tests to prove MVP works

### Option B: Continue Planning

If more design clarity needed:

```bash
# Review planning artifacts
cat specs/003-model-picker/plan.md        # Implementation plan
cat specs/003-model-picker/data-model.md  # ArangoDB schema
cat specs/003-model-picker/quickstart.md  # Usage examples

# Assess if any clarifications needed before coding
```

### Option C: Full Implementation

If time permits, implement all 83 tasks:

```bash
# Follow tasks.md sequentially through all 9 phases
# Estimated: 1-2 weeks for complete feature
```

---

## Critical Context for Next Instance

### 1. Hardcoded Models Problem

**Root Cause**: Fire Circle tests hardcode model names like `anthropic/claude-sonnet-4.5`, `google/gemini-2.5-flash-preview-09-2025`

**Impact**: When models deprecated, tests fail with 404 errors

**Evidence**: See `research.md` for complete catalog of 40+ hardcoded models across codebase

**Solution**: Model-picker queries database for `available=True` and `frontier=True` models dynamically

### 2. OpenRouter Catalog Volatility

**Key Insight**: 330+ models in catalog, frequently change
- Models appear/disappear based on provider decisions
- Pricing changes (especially free tier)
- New capabilities added (structured_outputs jumped to 53%)

**Implication**: Any hardcoded model list will become stale → database-driven solution required

### 3. Manual Frontier Curation Requirement

**Key Insight**: Frontier designation cannot be automated
- No signal in OpenRouter API indicates "frontier" status
- Requires human analysis of capabilities, benchmarks, reputation
- Needs periodic review (30-day staleness threshold)

**Implication**: System must preserve manual `frontier=True` flags across OpenRouter syncs

### 4. Constitution Alignment

This feature exemplifies constitution principles:

**No Theater**: Fail-fast on API errors, explicit staleness warnings (not silent degradation)

**Empirical Integrity**: Success criteria require real API validation
- SC-001: Query must return models with structural diversity
- SC-005: Converted tests must behave identically

**Continuous Learning**: Dynamic model selection adapts to catalog changes without code updates

### 5. ArangoDB Integration Patterns

**Existing Pattern** (from `arango_backend.py`):
- Idempotent collection creation (`if not db.has_collection()`)
- Index creation with deduplication check
- Bind variables for SQL injection prevention (`@variable`)
- Bounded queries (`LIMIT @limit`)
- Error context in exceptions

**New Collections**:
- `models` - Document collection (LLM metadata)
- `sync_metadata` - Singleton document (global sync state)

**Indexes Required**:
- Hash: `openrouter_id` (unique), `provider`, `frontier`, `available`, `free`
- Skiplist: `last_synced`, `created`
- Fulltext: `description`

---

## Unresolved Questions / Future Decisions

### 1. Initial Data Seeding Strategy

**Question**: How to populate initial frontier models for MVP?

**Options**:
- **A**: Manually seed from `config/fire_circle_models.json` (12 validated models)
- **B**: Run OpenRouter sync once manually (requires US4 implementation)
- **C**: Create seed script that marks specific models as frontier

**Recommendation**: Option A for MVP (manual seed), implement US4 sync later if needed

### 2. Structural Diversity Implementation

**Question**: How to ensure query results have structural diversity (2+ providers, 2+ architectures)?

**Options**:
- **A**: Caller responsibility (FR-008: "return filtered candidates, caller implements selection policy")
- **B**: Add diversity parameter to query() (e.g., `ensure_diversity=True`)
- **C**: Post-processing function `select_diverse(models, min_providers=2)`

**Recommendation**: Option A for MVP (spec explicitly defers to caller), add helper if empirical use shows need

### 3. Free Model Data-Training Disclosure

**Question**: How to warn users that free models use data for training?

**Context**: Per `config/dynamic_free_models.py`, free models train on prompts

**Options**:
- **A**: Add warning to query() when `free=True` filter used
- **B**: Add `data_training_disclosure` field to ModelMetadata
- **C**: Document in quickstart.md, let users decide

**Recommendation**: Option C for MVP (research tool context, users aware of tradeoffs)

---

## Files to Review Before Starting

### Essential Reading (in order)

1. **`specs/003-model-picker/spec.md`** - User stories, requirements, success criteria
2. **`specs/003-model-picker/tasks.md`** - Implementation tasks (start here for coding)
3. **`specs/003-model-picker/data-model.md`** - ArangoDB schema, domain models
4. **`specs/003-model-picker/quickstart.md`** - Usage examples, migration patterns

### Supporting Context

5. **`specs/003-model-picker/research.md`** - Design decisions, OpenRouter API schema
6. **`specs/003-model-picker/contracts/model_picker_api.py`** - API contracts
7. **`specs/003-model-picker/plan.md`** - Full planning context

### Existing Codebase Patterns

8. **`promptguard/storage/arango_backend.py`** - ArangoDB integration patterns
9. **`config/fire_circle_models.json`** - Current frontier models (seed data)
10. **`test_fire_circle_fixes.py`** - Example of hardcoded models to convert

---

## Validation Checklist for MVP

Before declaring MVP complete, verify:

- [ ] ArangoDB `models` collection exists with correct schema
- [ ] ArangoDB `sync_metadata` collection exists
- [ ] All indexes created (hash, skiplist, fulltext)
- [ ] ModelMetadata dataclass complete with all fields from data-model.md
- [ ] ModelPicker.query() works with `available=True, frontier=True` filters
- [ ] ModelPicker.get_by_id() works and raises ModelNotFoundError
- [ ] Seed data loaded (12 frontier models from config/fire_circle_models.json)
- [ ] Integration test passes with real ArangoDB (T023)
- [ ] 4 Fire Circle tests converted and passing (T024-T027):
  - test_fire_circle_fixes.py
  - test_meta_evaluation_framing.py
  - test_proposal_evaluation_detailed.py
  - test_learning_loop.py
- [ ] Converted tests behave identically to original (same models selected)
- [ ] Structural diversity validated (results have 2+ providers, 2+ architectures)
- [ ] API costs documented in test docstrings
- [ ] No errors in pytest output

---

## Known Risks / Gotchas

### 1. ArangoDB Connection

**Risk**: ArangoDB instance at 192.168.111.125:8529 may not be running

**Mitigation**: Check connection before implementation starts
```bash
curl http://192.168.111.125:8529/_api/version
```

**Fallback**: Update host in environment variables if instance moved

### 2. Model Deprecation During Development

**Risk**: Models in `config/fire_circle_models.json` may become deprecated during implementation

**Mitigation**:
- Verify model availability before seeding
- Use ModelAdmin.test_model_availability() to validate
- Document which models were tested when

### 3. Free Models Data Training

**Risk**: Users may not realize free models use data for training

**Context**: Per `config/dynamic_free_models.py` comment about ethical disclosure

**Mitigation**: Document prominently in quickstart.md, add to success criteria validation

### 4. Spec Says SearchView, Implementation May Not Need It

**Issue**: FR-009 requires "ArangoDB SearchView for full-text search"

**Reality**: MVP doesn't need full-text search (only frontier/available filters)

**Resolution**: Defer SearchView configuration to US2 (advanced filtering phase)

---

## Communication / Questions for Tony

### If Starting MVP Implementation

**Before coding**: Confirm MVP scope acceptable
- "Proceeding with T001-T027 (MVP: Query + Fire Circle test conversions). Deferred: sync, staleness warnings, CLI. Acceptable?"

**If ArangoDB connection fails**:
- "ArangoDB at 192.168.111.125:8529 unreachable. New host?"

**If models collection already exists**:
- "Models collection exists. Should I preserve existing data or recreate schema?"

### If Continuing Planning

**Identify what needs clarification**:
- "Planning artifacts complete. Need clarity on [specific aspect] before implementation?"

---

## Meta-Notes

### Session Characteristics

**What Worked Well**:
- Parallel research agents resolved NEEDS CLARIFICATION efficiently
- Spec-kit workflow produced comprehensive, consistent artifacts
- Task organization by user story enables independent implementation
- MVP scope clearly defined with empirical validation criteria

**What Could Be Improved**:
- Context exhausted before implementation started (planning-heavy session)
- Could have skipped `/speckit.clarify` (spec already well-formed from planning)

### Instance Handoff Pattern Observed

This session exemplifies **specification-first** approach:
1. Instance 55 → identified Fire Circle meta-evaluation issue
2. Instance 56 → comprehensive planning for model-picker solution
3. Instance 57 → implementation (handoff point)

**Advantage**: Next instance has clear implementation path
**Disadvantage**: No empirical validation yet (pure planning)

### For Future Reference

If repeating similar workflow:
- Skip `/speckit.clarify` if planning phase already resolved ambiguities
- Consider starting implementation earlier in session to validate design
- Use TodoWrite tool to track progress through phases (wasn't used this session)

---

## Final State Summary

**Branch**: `003-model-picker` (clean, all planning artifacts committed)
**Status**: Specification and planning 100% complete, implementation 0% complete
**Recommendation**: Start with MVP (T001-T027) to deliver value quickly
**Estimated Effort**: 2-3 days for MVP, 1-2 weeks for full feature
**Blocker**: None - ready to start implementation immediately

**Next Command**: Begin MVP implementation with Phase 1 setup tasks (T001-T006)

---

*Handoff prepared by Instance 56 at 3% context remaining*
*Good luck, Instance 57!*
