# Implementation Plan: Model Picker

**Branch**: `003-model-picker` | **Date**: 2025-10-26 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-model-picker/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Create database-driven LLM model selection infrastructure that solves the deprecated model problem by storing model metadata in ArangoDB and enabling attribute-based queries. This replaces hardcoded model names with dynamic queries (e.g., "available frontier models", "free instruct models") that survive model deprecation. Uses TTL-based refresh with cycle-stealing, manual frontier curation with staleness warnings, and open tagging for extensibility.

## Technical Context

**Language/Version**: Python 3.13 (uv project manager)
**Primary Dependencies**: ArangoDB Python driver (python-arango), httpx (OpenRouter API), existing promptguard core
**Storage**: ArangoDB (already configured per CLAUDE.md, host 192.168.111.125:8529)
**Testing**: pytest with real API integration tests (per Constitution Principle II - Empirical Integrity)
**Target Platform**: Linux server (research tool, not production web service)
**Project Type**: Single project (extends existing promptguard/ structure)
**Performance Goals**: Query response <100ms for attribute filters (excluding OpenRouter sync), sync completion <60s for full catalog
**Constraints**: 24h TTL cycle-stealing refresh (no background jobs), interactive staleness warning for frontier >30 days, preserve manual attributes across syncs
**Scale/Scope**: ~500 OpenRouter models, 2-3 query types (frontier/observer model selection), conversions of 3-5 existing hardcoded model lists

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. No Theater

**Status**: ✅ PASS

- Feature uses semantic evaluation from OpenRouter API (model metadata) - not keyword matching
- Fail-fast on API errors (raise exceptions, no fake fallbacks)
- Staleness warnings are explicit and interactive (not silently degraded)
- Manual attribute preservation is explicit contract, not graceful degradation
- Query failures raise errors, don't return stale/fake data

### II. Empirical Integrity

**Status**: ✅ PASS with requirements

- **MUST** validate with real OpenRouter API calls (sync operation)
- **MUST** validate with real ArangoDB queries (storage/retrieval)
- **MUST** document API costs for integration tests
- **MUST** prove manual attributes survive sync operations
- **MUST** validate staleness warning appears and blocks execution
- **MUST** validate existing code can be converted to use model-picker

Evidence requirements documented in spec.md Success Criteria (SC-001 through SC-006).

### III. Agency Over Constraint

**Status**: ✅ PASS

- Feature provides measurement tools (model availability, attributes) not imposed constraints
- Caller implements selection policy (FR-008), model-picker returns filtered candidates
- Enables informed choice rather than enforcing specific models
- Supports research autonomy (choose models by research needs, not hardcoded lists)

### IV. Continuous Learning Over Static Training

**Status**: ✅ PASS

- Dynamic model selection adapts to OpenRouter catalog changes
- Manual frontier curation enables human-in-loop learning
- Staleness warnings prevent stale assumptions
- Open tagging enables adding new attributes without code changes
- Supports Fire Circle and REASONINGBANK future needs (structural diversity queries)

### V. Semantic Evaluation Only

**Status**: N/A - Feature is infrastructure, not evaluation

This feature enables semantic evaluation by others (Fire Circle, observer models) but doesn't perform evaluation itself.

### Architectural Decisions

**Fail-Fast Over Graceful Degradation**: ✅ PASS
- OpenRouter API errors raise exceptions with context
- Stale cache >48h triggers warning (not silent use)
- Missing attributes in query results marked incomplete, excluded from requiring attributes
- Interactive staleness warning blocks execution, requires acknowledgment

**TLA+ Halt Semantics**: Future consideration
- Could define invariants for staleness thresholds
- Could formalize when manual review is required
- Deferred to implementation phase

### Development Standards

**Specification-Driven Development**: ✅ IN PROGRESS
- Using spec-kit workflow (specify → plan → tasks → implement)
- Specification defines observable behaviors, contracts, failure modes
- Validation criteria included in Success Criteria

**Code Navigation**: ✅ Will use serena
- Search for existing model selection code before implementation
- Find existing ArangoDB patterns
- Identify conversion targets

**Context Window Management**: ✅ Will delegate
- Use Task tool for researching OpenRouter API schema
- Use Task tool for finding all hardcoded model lists
- Preserve context for integration work

**Cost Optimization**: ✅ Aligned
- Supports free model queries for development/testing (FR-003)
- Supports frontier model queries for research (FR-003)
- Enables budget ensemble selection for production (future)

## Project Structure

### Documentation (this feature)

```
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
promptguard/
├── models/
│   └── model_picker.py      # NEW: ModelPicker class, query interface
├── storage/
│   ├── arango_backend.py    # EXTEND: Add models collection management
│   └── model_sync.py        # NEW: OpenRouter sync operations
└── cli/
    └── model_admin.py       # NEW: Manual frontier curation CLI

tests/
├── integration/
│   ├── test_model_picker_arango.py   # NEW: Real ArangoDB queries
│   └── test_openrouter_sync.py       # NEW: Real OpenRouter API
└── unit/
    └── test_model_query.py            # NEW: Query logic (mocked DB)

config/
└── model_configs.json       # EXTEND: May add sync metadata
```

**Structure Decision**: Single project extending existing promptguard/ structure. New model_picker module under promptguard/models/, sync operations under promptguard/storage/ (co-located with existing ArangoDB backend). CLI tools for manual curation under promptguard/cli/.

## Complexity Tracking

*No constitution violations requiring justification.*

## Phase 0: Research & Design Decisions

Research tasks to resolve NEEDS CLARIFICATION items and establish technical foundation:

### Research Task 1: OpenRouter API Schema
**Question**: What model metadata fields does OpenRouter /api/v1/models endpoint provide?
**Needed for**: Determining which attributes can be auto-populated vs manually curated
**Deliverable**: OpenRouter API schema documentation

### Research Task 2: Existing Model Selection Patterns
**Question**: Where is hardcoded model selection currently used in the codebase?
**Needed for**: Identifying conversion targets, understanding selection requirements
**Deliverable**: List of files/functions using hardcoded model lists with their selection criteria

### Research Task 3: ArangoDB Query Patterns
**Question**: What AQL patterns exist in arango_backend.py for attribute queries and graph traversal?
**Needed for**: Consistency with existing codebase patterns, avoiding reinvention
**Deliverable**: AQL query examples from existing code

### Research Task 4: Interactive Warning Implementation
**Question**: How should interactive staleness warnings be implemented in research tool context?
**Needed for**: User experience design (CLI prompt vs exception vs logging)
**Deliverable**: Implementation approach with examples from Python ecosystem

## Phase 0 Completion

**Status**: ✅ COMPLETE

All research tasks completed and consolidated in `research.md`:
- OpenRouter API schema documented (330+ models, all fields identified)
- Hardcoded model locations catalogued (40+ unique models across 20+ files)
- ArangoDB query patterns extracted from existing code
- Interactive warning approach selected (`input()` with non-interactive mode for CI/CD)

**Decisions made**:
- Use OpenRouter `/api/v1/models` for automatic sync
- TTL-based refresh with 24h cycle-stealing
- Manual frontier curation via CLI tool
- Preserve manual attributes across syncs
- Open tagging for extensibility

---

## Phase 1: Design & Contracts

**Status**: ✅ COMPLETE

### Generated Artifacts

1. **`data-model.md`** - Complete data model specification
   - ArangoDB collections schema (models, sync_metadata)
   - Python domain models (ModelMetadata, ModelQuery, ModelPricing, ModelArchitecture)
   - Index strategy (hash, skiplist, fulltext)
   - Data validation rules
   - Manual attribute preservation logic

2. **`contracts/model_picker_api.py`** - API contract definitions
   - IModelPicker interface (query, get_by_id, sync_from_openrouter)
   - IModelAdmin interface (mark_frontier, update_attributes, test_model_availability)
   - Custom exceptions (ModelNotFoundError, StalenessWarning, SyncError)
   - Contract validation tests

3. **`quickstart.md`** - Usage guide and migration examples
   - Common use cases (Fire Circle, observer models, cost optimization)
   - Cycle-stealing auto-sync
   - Staleness warning handling
   - Migration guide for Priority 1-2 hardcoded lists

4. **Agent Context Updated** - CLAUDE.md updated with model-picker technology stack

### Re-Evaluation of Constitution Check

All gates from Phase 0 still PASS:

- ✅ No Theater - Fail-fast on API errors, explicit staleness warnings
- ✅ Empirical Integrity - Real API validation required in success criteria
- ✅ Agency Over Constraint - Provides measurement tools, not imposed constraints
- ✅ Continuous Learning - Dynamic selection adapts to catalog changes
- ✅ Fail-Fast - API errors raise exceptions, no silent fallbacks

**No new violations introduced during design phase.**

---

## Phase 2: Task Generation (NOT created by /speckit.plan)

Per spec-kit workflow, Phase 2 (`tasks.md`) is generated by `/speckit.tasks` command, not `/speckit.plan`.

The planning phase ends here. Implementation tasks will be generated in the next phase.

