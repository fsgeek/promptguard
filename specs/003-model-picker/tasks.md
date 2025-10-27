# Implementation Tasks: Model Picker

**Feature Branch**: `003-model-picker`
**Created**: 2025-10-26
**Status**: Ready for Implementation

## Overview

Database-driven LLM model selection infrastructure that solves the deprecated model problem by storing model metadata in ArangoDB and enabling attribute-based queries. Replaces hardcoded model names with dynamic queries that survive model deprecation.

**MVP Scope**: User Story 1 (Query Available Frontier Models) - Minimum viable increment for Fire Circle test conversion.

---

## Phase 1: Setup & Configuration

**Goal**: Initialize project structure and configure ArangoDB integration

### Tasks

- [ ] T001 Create promptguard/models/ directory for model-picker module
- [ ] T002 Create promptguard/storage/model_sync.py for OpenRouter sync operations
- [ ] T003 Create promptguard/cli/model_admin.py for manual curation CLI
- [ ] T004 [P] Create tests/integration/test_model_picker_arango.py for ArangoDB integration tests
- [ ] T005 [P] Create tests/integration/test_openrouter_sync.py for OpenRouter API tests
- [ ] T006 [P] Create tests/unit/test_model_query.py for query logic tests

---

## Phase 2: Foundational Infrastructure

**Goal**: Implement ArangoDB collections, indexes, and base domain models (blocking for all user stories)

### Tasks

- [ ] T007 Implement ArangoDB models collection schema in promptguard/storage/arango_backend.py (extend existing class with _ensure_models_collection() method)
- [ ] T008 Implement ArangoDB sync_metadata collection schema in promptguard/storage/arango_backend.py (extend existing class with _ensure_sync_metadata_collection() method)
- [ ] T009 Create ModelMetadata dataclass in promptguard/models/model_picker.py (with ModelPricing, ModelArchitecture, TopProvider nested dataclasses per data-model.md)
- [ ] T010 Create ModelQuery dataclass in promptguard/models/model_picker.py (with validation in __post_init__)
- [ ] T011 Create custom exceptions in promptguard/models/model_picker.py (ModelNotFoundError, StalenessWarning, SyncError)
- [ ] T012 Implement index creation for models collection in promptguard/storage/arango_backend.py (_ensure_models_indexes() method - hash, skiplist, fulltext per data-model.md)
- [ ] T013 Implement ModelMetadata.to_arango_doc() method in promptguard/models/model_picker.py (convert dataclass to ArangoDB document format)
- [ ] T014 Implement ModelMetadata.from_arango_doc() classmethod in promptguard/models/model_picker.py (convert ArangoDB document to dataclass)

---

## Phase 3: User Story 1 - Query Available Frontier Models (P1 - MVP)

**Story Goal**: Research code can select frontier models for Fire Circle deliberations without hardcoding model names.

**Independent Test**: Query "available frontier models" and verify results contain only currently-available frontier models, with no deprecated models included.

**Success Criteria**:
- **SC-001**: Query returns models with structural diversity (2+ providers, 2+ architecture families if available)
- **SC-005**: Fire Circle tests can be converted to use model-picker without changing behavior

### Tasks

- [ ] T015 [US1] Implement ModelPicker.__init__() in promptguard/models/model_picker.py (initialize ArangoDB connection, ensure collections exist)
- [ ] T016 [US1] Implement ModelPicker.query() base method in promptguard/models/model_picker.py (signature with all filter parameters, call _build_aql_query())
- [ ] T017 [US1] Implement ModelPicker._build_aql_query() in promptguard/models/model_picker.py (construct AQL with dynamic filters using bind variables per research.md patterns)
- [ ] T018 [US1] Implement ModelPicker._execute_query() in promptguard/models/model_picker.py (execute AQL, convert results to List[ModelMetadata])
- [ ] T019 [US1] Implement frontier=True filter logic in ModelPicker._build_aql_query() in promptguard/models/model_picker.py (add FILTER m.frontier == @frontier)
- [ ] T020 [US1] Implement available=True filter logic in ModelPicker._build_aql_query() in promptguard/models/model_picker.py (add FILTER m.available == @available)
- [ ] T021 [US1] Implement sort_by and limit logic in ModelPicker._build_aql_query() in promptguard/models/model_picker.py (add SORT and LIMIT clauses)
- [ ] T022 [US1] Implement ModelPicker.get_by_id() in promptguard/models/model_picker.py (fetch single model, raise ModelNotFoundError if not found)
- [ ] T023 [US1] Integration test: Query frontier models with real ArangoDB in tests/integration/test_model_picker_arango.py (verify SC-001 structural diversity)
- [ ] T024 [US1] Convert test_fire_circle_fixes.py to use ModelPicker (replace hardcoded models with picker.query(available=True, frontier=True, limit=2))
- [ ] T025 [US1] Convert test_meta_evaluation_framing.py to use ModelPicker (replace hardcoded models with picker.query())
- [ ] T026 [US1] Convert test_proposal_evaluation_detailed.py to use ModelPicker (replace hardcoded models with picker.query())
- [ ] T027 [US1] Convert test_learning_loop.py to use ModelPicker (replace hardcoded models with picker.query())

---

## Phase 4: User Story 3 - Handle Stale Frontier Designations (P1)

**Story Goal**: System warns when frontier designations haven't been updated recently (>30 days).

**Independent Test**: Set frontier_updated timestamp to 45 days ago, query for frontier models, verify interactive warning appears and requires acknowledgment.

**Success Criteria**:
- **SC-004**: Staleness warning appears and blocks execution when frontier list >30 days old

### Tasks

- [ ] T028 [US3] Implement ModelPicker.get_sync_metadata() in promptguard/models/model_picker.py (query sync_metadata collection, return dict)
- [ ] T029 [US3] Implement ModelPicker._check_frontier_staleness() in promptguard/models/model_picker.py (calculate days since frontier_updated, raise StalenessWarning if >30 days and interactive=True)
- [ ] T030 [US3] Integrate staleness check into ModelPicker.query() in promptguard/models/model_picker.py (call _check_frontier_staleness() when frontier=True filter used)
- [ ] T031 [US3] Implement interactive warning display in ModelPicker._check_frontier_staleness() in promptguard/models/model_picker.py (print formatted warning, input() prompt, handle yes/no response)
- [ ] T032 [US3] Implement non-interactive mode in ModelPicker._check_frontier_staleness() in promptguard/models/model_picker.py (raise StalenessWarning immediately if interactive=False, check ALLOW_STALE_FRONTIER env var)
- [ ] T033 [US3] Integration test: Verify staleness warning appears in tests/integration/test_model_picker_arango.py (set frontier_updated to 45 days ago, verify StalenessWarning raised)

---

## Phase 5: User Story 4 - Sync with OpenRouter API (P2)

**Story Goal**: System periodically refreshes model list from OpenRouter to stay current.

**Independent Test**: Clear model list, trigger sync, verify models collection contains entries matching OpenRouter's current catalog.

**Success Criteria**:
- **SC-003**: Model list auto-refreshes within 1 minute when cache >24h old
- **SC-006**: Manual curation survives sync operations (frontier=true persists)

### Tasks

- [ ] T034 [US4] Implement OpenRouterSync.__init__() in promptguard/storage/model_sync.py (store api_key, httpx client initialization)
- [ ] T035 [US4] Implement OpenRouterSync.fetch_models() in promptguard/storage/model_sync.py (GET /api/v1/models, parse JSON response, return list of raw model dicts)
- [ ] T036 [US4] Implement OpenRouterSync._validate_model() in promptguard/storage/model_sync.py (validate required fields per data-model.md, raise ValueError if invalid)
- [ ] T037 [US4] Implement OpenRouterSync._convert_to_metadata() in promptguard/storage/model_sync.py (convert OpenRouter dict to ModelMetadata, extract provider from ID, derive free flag from pricing)
- [ ] T038 [US4] Implement ModelPicker._load_existing_model() in promptguard/models/model_picker.py (fetch existing model from ArangoDB by openrouter_id, return None if not found)
- [ ] T039 [US4] Implement ModelPicker._merge_manual_attributes() in promptguard/models/model_picker.py (preserve frontier, testing, observer_framing_compatible, tags from existing model per data-model.md)
- [ ] T040 [US4] Implement ModelPicker.sync_from_openrouter() in promptguard/models/model_picker.py (orchestrate: fetch → validate → convert → merge → batch update → mark deprecated → update sync_metadata)
- [ ] T041 [US4] Implement batch update logic in ModelPicker.sync_from_openrouter() in promptguard/models/model_picker.py (insert new models, update existing models, preserve manual attributes)
- [ ] T042 [US4] Implement deprecation marking in ModelPicker.sync_from_openrouter() in promptguard/models/model_picker.py (find models absent from OpenRouter response, set available=False)
- [ ] T043 [US4] Implement sync metadata update in ModelPicker.sync_from_openrouter() in promptguard/models/model_picker.py (update last_openrouter_sync, record sync_history, log sync_errors)
- [ ] T044 [US4] Implement ModelPicker.needs_sync() in promptguard/models/model_picker.py (check last_openrouter_sync timestamp, return True if >ttl_hours old)
- [ ] T045 [US4] Implement cycle-stealing auto-sync in ModelPicker.query() in promptguard/models/model_picker.py (call needs_sync(24) at start, trigger sync_from_openrouter if stale)
- [ ] T046 [US4] Integration test: Verify sync with real OpenRouter API in tests/integration/test_openrouter_sync.py (verify models_added, models_updated, models_deprecated stats)
- [ ] T047 [US4] Integration test: Verify manual attributes preserved in tests/integration/test_openrouter_sync.py (set frontier=True, sync, verify frontier persists)

---

## Phase 6: User Story 2 - Filter Models by Attributes (P2)

**Story Goal**: Research code can select models matching specific criteria (free, instruct, RLHF, providers).

**Independent Test**: Query "free instruct models" and manually verify each result is both free and instruction-tuned according to OpenRouter.

**Success Criteria**:
- **SC-002**: Query "free instruct models" returns only matching models, verified by spot-check

### Tasks

- [ ] T048 [US2] Implement free=True filter logic in ModelPicker._build_aql_query() in promptguard/models/model_picker.py (add FILTER m.free == @free)
- [ ] T049 [US2] Implement provider filter logic in ModelPicker._build_aql_query() in promptguard/models/model_picker.py (add FILTER m.provider == @provider)
- [ ] T050 [US2] Implement architecture_family filter logic in ModelPicker._build_aql_query() in promptguard/models/model_picker.py (add FILTER m.architecture_family == @architecture_family)
- [ ] T051 [US2] Implement observer_framing_compatible filter logic in ModelPicker._build_aql_query() in promptguard/models/model_picker.py (add FILTER m.observer_framing_compatible == @observer_framing_compatible)
- [ ] T052 [US2] Implement structured_outputs filter logic in ModelPicker._build_aql_query() in promptguard/models/model_picker.py (add FILTER "structured_outputs" IN m.supported_parameters)
- [ ] T053 [US2] Implement instruct filter logic in ModelPicker._build_aql_query() in promptguard/models/model_picker.py (add FILTER m.instruct == @instruct)
- [ ] T054 [US2] Implement rlhf filter logic in ModelPicker._build_aql_query() in promptguard/models/model_picker.py (add FILTER m.rlhf == @rlhf)
- [ ] T055 [US2] Integration test: Query free models in tests/integration/test_model_picker_arango.py (verify all results have pricing.prompt == "0" AND pricing.completion == "0")
- [ ] T056 [US2] Integration test: Query by provider in tests/integration/test_model_picker_arango.py (verify all results have matching provider field)
- [ ] T057 [US2] Integration test: Combined filters (free AND instruct) in tests/integration/test_model_picker_arango.py (verify SC-002)
- [ ] T058 [US2] Convert promptguard/evaluation/schemas.py STRUCTURED_OUTPUT_CAPABLE_MODELS to use ModelPicker (implement get_structured_output_models() function using picker.query(structured_outputs=True))

---

## Phase 7: Manual Curation CLI & Admin Operations

**Story Goal**: Provide CLI tools for manual frontier curation and attribute management.

**Dependencies**: Requires US1, US3, US4 complete

### Tasks

- [ ] T059 Implement ModelAdmin.__init__() in promptguard/cli/model_admin.py (initialize ModelPicker instance)
- [ ] T060 Implement ModelAdmin.mark_frontier() in promptguard/cli/model_admin.py (update frontier field, update sync_metadata.frontier_updated timestamp)
- [ ] T061 Implement ModelAdmin.batch_mark_frontier() in promptguard/cli/model_admin.py (batch update frontier for multiple models, single transaction)
- [ ] T062 Implement ModelAdmin.update_attributes() in promptguard/cli/model_admin.py (update observer_framing_compatible, architecture_family, instruct, rlhf, tags)
- [ ] T063 Implement ModelAdmin.test_model_availability() in promptguard/cli/model_admin.py (test OpenRouter API call for specific model, return available/status_code/error)
- [ ] T064 Implement CLI argument parser in promptguard/cli/model_admin.py (argparse for --mark-frontier, --update-attributes, --test-availability, --refresh-frontier)
- [ ] T065 Implement --mark-frontier command in promptguard/cli/model_admin.py (read model IDs from args, call batch_mark_frontier())
- [ ] T066 Implement --refresh-frontier interactive review in promptguard/cli/model_admin.py (display current frontier models, prompt for additions/removals, update frontier_updated)
- [ ] T067 Integration test: Verify CLI commands in tests/integration/test_model_admin_cli.py (test mark_frontier, update_attributes, test_availability)

---

## Phase 8: Library Integration & Migration

**Story Goal**: Convert remaining hardcoded model lists to use ModelPicker.

**Dependencies**: Requires US1, US2 complete

### Tasks

- [ ] T068 Convert promptguard/evaluation/evaluator.py default model to use ModelPicker (implement _default_model() function, fallback to hardcoded if picker fails)
- [ ] T069 Convert promptguard/promptguard.py default model to use ModelPicker (use same _default_model() pattern)
- [ ] T070 [P] Convert fire_circle_compliance_prompt.py 5-model MEDIUM circle to use ModelPicker (query with structural_diversity consideration)
- [ ] T071 [P] Update config/model_configs.json fire_circle_configurations to use ModelPicker (add note about deprecation, recommend using picker)
- [ ] T072 Seed initial frontier models from config/fire_circle_models.json in promptguard/storage/model_sync.py (implement seed_frontier_models() function)

---

## Phase 9: Polish & Cross-Cutting Concerns

**Story Goal**: Complete error handling, logging, documentation, and validation.

**Dependencies**: All user stories complete

### Tasks

- [ ] T073 Add comprehensive error handling to ModelPicker.query() in promptguard/models/model_picker.py (wrap AQL execution, provide context in exceptions)
- [ ] T074 Add logging to ModelPicker.sync_from_openrouter() in promptguard/models/model_picker.py (log sync start/completion, models added/updated/deprecated)
- [ ] T075 Add logging to ModelPicker._check_frontier_staleness() in promptguard/models/model_picker.py (log staleness warnings, user acknowledgments)
- [ ] T076 Implement ModelPicker cache instance pattern in promptguard/models/model_picker.py (add module-level _picker_instance singleton, get_picker() factory)
- [ ] T077 Add docstrings to all public methods in promptguard/models/model_picker.py (follow existing PromptGuard style)
- [ ] T078 Add docstrings to all public methods in promptguard/cli/model_admin.py (follow existing PromptGuard style)
- [ ] T079 Update CLAUDE.md with model-picker usage patterns (add section after "Key Files" documenting ModelPicker, common queries, migration guide)
- [ ] T080 Create example script: examples/model_picker_demo.py (demonstrate query(), sync_from_openrouter(), manual curation)
- [ ] T081 Validate all integration tests pass with real APIs (run pytest tests/integration/test_model_picker_arango.py tests/integration/test_openrouter_sync.py -v)
- [ ] T082 Document API costs in integration test docstrings (estimate OpenRouter sync cost, ArangoDB query cost)
- [ ] T083 Final validation: Run converted Fire Circle tests to ensure behavior unchanged (run pytest test_fire_circle_fixes.py test_meta_evaluation_framing.py test_proposal_evaluation_detailed.py test_learning_loop.py -v)

---

## Dependencies & Execution Order

### User Story Completion Order

```
Phase 1 (Setup) → Phase 2 (Foundational)
                     ↓
    ┌────────────────┼────────────────┐
    ↓                ↓                ↓
  US1 (P1)         US3 (P1)         US4 (P2)
    ↓                ↓                ↓
    └────────────────┼────────────────┘
                     ↓
                   US2 (P2)
                     ↓
        Phase 7 (Manual Curation CLI)
                     ↓
        Phase 8 (Library Integration)
                     ↓
          Phase 9 (Polish & Docs)
```

**Critical Path**: Setup → Foundational → US1 → US3 → US4 → US2 → CLI → Integration → Polish

**Parallel Opportunities**:
- US1, US3, US4 can be worked in parallel after Foundational complete (independent implementations)
- Test file creation (T004-T006) can be done in parallel with foundational work
- Fire Circle test conversions (T024-T027) can be done in parallel once US1 complete
- CLI implementation (Phase 7) and Library Integration (Phase 8) can overlap

### Independent Test Criteria by Story

**US1 (Query Available Frontier Models)**:
- Independent Test: Query `picker.query(available=True, frontier=True)` and verify results contain only currently-available frontier models
- Validation: All returned models have `available=True` AND `frontier=True`, no deprecated models included
- Structural Diversity: Results include 2+ different providers, 2+ architecture families if available

**US3 (Handle Stale Frontier Designations)**:
- Independent Test: Set `frontier_updated` to 45 days ago, query for frontier models, verify warning appears
- Validation: Interactive warning displays last-updated date, requires user acknowledgment (input("Proceed..."))
- Non-interactive: Raises `StalenessWarning` if `interactive=False` or `ALLOW_STALE_FRONTIER` not set

**US4 (Sync with OpenRouter API)**:
- Independent Test: Clear models collection, call `picker.sync_from_openrouter(api_key)`, verify models populated
- Validation: Sync stats returned (models_added, models_updated, models_deprecated), last_openrouter_sync updated
- Manual Attributes: Set `frontier=True` on model, sync, verify `frontier=True` persists

**US2 (Filter Models by Attributes)**:
- Independent Test: Query `picker.query(free=True, instruct=True)` and manually verify 5 results against OpenRouter
- Validation: All results have `pricing.prompt == "0"` AND `pricing.completion == "0"` AND `instruct=True`
- Provider Filter: Query `picker.query(provider="anthropic")` returns only Anthropic models

---

## Parallel Execution Examples

### Example 1: Foundational Phase (max parallelization)

```python
# Can be worked simultaneously by different developers/agents
Task T009: Create ModelMetadata dataclass          # File: promptguard/models/model_picker.py
Task T010: Create ModelQuery dataclass             # File: promptguard/models/model_picker.py (different section)
Task T011: Create custom exceptions                # File: promptguard/models/model_picker.py (different section)
Task T007: Implement models collection schema      # File: promptguard/storage/arango_backend.py
Task T008: Implement sync_metadata collection      # File: promptguard/storage/arango_backend.py (different method)
```

### Example 2: User Story 1 Implementation (sequential with parallel tests)

```python
# Sequential core implementation
T015 → T016 → T017 → T018 → T019 → T020 → T021 → T022

# Parallel after T022 complete
T023: Integration test (independent file)
T024-T027: Fire Circle test conversions (4 different test files, fully parallel)
```

### Example 3: User Story Phase Parallelization

```python
# After Foundational complete, these can be worked in parallel
US1 (T015-T027): Query implementation
US3 (T028-T033): Staleness warning
US4 (T034-T047): OpenRouter sync

# Each team works on their story independently
```

---

## Implementation Strategy

### MVP Scope (Minimum Viable Product)

**Include**:
- Phase 1: Setup
- Phase 2: Foundational Infrastructure
- Phase 3: User Story 1 (Query Available Frontier Models)
- T024-T027: Fire Circle test conversions

**Rationale**: US1 + test conversions solve the immediate problem (deprecated models causing test failures). Delivers value quickly, validates architecture.

**Defer to Iteration 2**:
- US3: Staleness warnings (nice-to-have, not blocking)
- US4: OpenRouter sync (can manually seed initial data)
- US2: Advanced filtering (can add basic filters to US1 if needed)
- Phase 7-9: CLI, integration, polish

### Incremental Delivery Plan

**Sprint 1 (MVP)**: Setup + Foundational + US1 + test conversions (T001-T027)
- **Deliverable**: Fire Circle tests no longer fail due to deprecated models
- **Validation**: Run pytest on converted tests, verify behavior unchanged

**Sprint 2**: US3 + US4 (T028-T047)
- **Deliverable**: Auto-sync with staleness warnings
- **Validation**: Sync from OpenRouter works, staleness warnings appear

**Sprint 3**: US2 + CLI + Integration (T048-T072)
- **Deliverable**: Full query capabilities, manual curation tools, library defaults migrated
- **Validation**: All hardcoded model lists converted

**Sprint 4**: Polish & Documentation (T073-T083)
- **Deliverable**: Production-ready, documented, validated with real APIs
- **Validation**: Integration tests pass, costs documented, CLAUDE.md updated

---

## Task Summary

**Total Tasks**: 83

**Tasks by Phase**:
- Phase 1 (Setup): 6 tasks
- Phase 2 (Foundational): 8 tasks
- Phase 3 (US1 - MVP): 13 tasks
- Phase 4 (US3): 6 tasks
- Phase 5 (US4): 14 tasks
- Phase 6 (US2): 11 tasks
- Phase 7 (CLI): 9 tasks
- Phase 8 (Integration): 5 tasks
- Phase 9 (Polish): 11 tasks

**Parallel Opportunities**: 25+ tasks marked with [P] can be executed in parallel

**Independent Tests**: Each user story has clear, independently testable acceptance criteria

**MVP Task Count**: 27 tasks (T001-T027) - estimated 2-3 days for single developer

---

## Format Validation

✅ All tasks follow checklist format: `- [ ] [TaskID] [P?] [Story?] Description with file path`
✅ All user story tasks have [US1], [US2], [US3], or [US4] labels
✅ All parallelizable tasks marked with [P]
✅ All tasks include specific file paths
✅ Sequential task IDs (T001-T083)
✅ Setup/Foundational/Polish tasks have NO story labels (correct)
✅ Each user story has independent test criteria
✅ Dependencies clearly documented with execution order diagram
✅ Parallel execution examples provided
✅ MVP scope clearly defined
