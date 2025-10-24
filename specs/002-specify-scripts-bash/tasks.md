# Implementation Tasks: End-to-End PromptGuard Validation Framework

**Branch**: `002-specify-scripts-bash`
**Generated**: 2025-10-22
**Based On**: spec.md (5 user stories), plan.md, data-model.md, research.md

---

## Task Summary

**Total Tasks**: 61
**User Stories**: 5 (US1-US5)
- US1 (P1): Baseline Collection - 12 tasks
- US2 (P1): Pre-Evaluation Cross-Tabulation - 10 tasks
- US3 (P2): Pattern Mining - 12 tasks
- US4 (P1): REASONINGBANK Validation - 11 tasks
- US5 (P3): External Pattern Integration - 6 tasks
**Setup/Foundational**: 10 tasks
**Independent Tests**: Each user story independently testable
**Parallel Opportunities**: 23 tasks marked [P]

---

## Dependencies

```
Setup (Phase 1)
  ↓
Foundational (Phase 2)
  ↓
US1: Baseline Collection (P1) ←─────────────┐
  ↓                                          │
US2: Pre-Evaluation (P1) ──────┐            │
  ↓                             ↓            │
US3: Pattern Mining (P2) ──→ US4: Validation (P1)
                                ↓
                            US5: External Patterns (P3)
```

**Critical Path**: Setup → Foundational → US1 → US2 → US4
**Independent**: US3 and US4 can proceed in parallel after US2 completes
**Future Work**: US5 depends on all others

---

## Phase 1: Setup

**Goal**: Initialize project structure and database collections

### Tasks

- [X] T001 Create scripts/validation/ directory structure per plan.md
- [X] T002 [P] Create scripts/validation/common/ subdirectory for shared modules
- [X] T003 [P] Create scripts/validation/utils/ subdirectory for utilities
- [X] T004 [P] Create tests/integration/ directory for E2E validation tests
- [X] T005 [P] Create tests/unit/ directory for pipeline logic tests
- [X] T006 [P] Create tests/contract/ directory for schema validation tests
- [X] T007 Create scripts/validation/init_database.py to initialize 10 ArangoDB collections
- [X] T008 Implement ArangoDB collection creation with hash indexes per FR-003d in scripts/validation/init_database.py
- [X] T009 Load and validate old baseline prompt fixture per FR-356-362 in scripts/validation/init_database.py
- [X] T010 Insert prompt configurations (compliance, pre_eval, post_eval) into ArangoDB per FR-003c

**Validation**: Run `uv run python scripts/validation/init_database.py` and verify all 10 collections exist with proper indexes

---

## Phase 2: Foundational

**Goal**: Implement shared infrastructure required by all user stories

### Tasks

- [X] T011 [P] Implement ConfigurationError class in scripts/validation/common/errors.py
- [X] T012 [P] Implement ValidationError class in scripts/validation/common/errors.py
- [X] T013 [P] Implement EvaluationError class in scripts/validation/common/errors.py
- [X] T014 [P] Implement ModelVersionChangedError class in scripts/validation/common/errors.py
- [X] T015 [P] Implement Source protocol in scripts/validation/common/pipeline.py
- [X] T016 [P] Implement Sink protocol in scripts/validation/common/pipeline.py
- [X] T017 [P] Implement Stage protocol in scripts/validation/common/pipeline.py
- [X] T018 Implement run_pipeline() orchestrator function in scripts/validation/common/pipeline.py
- [X] T019 Implement ArangoClient wrapper in scripts/validation/utils/arango_client.py with connection pooling
- [X] T020 Implement PromptLoader in scripts/validation/utils/prompt_loader.py to load 680 prompts from datasets

**Validation**: Run `pytest tests/unit/test_pipeline.py tests/unit/test_prompt_loader.py -v` (unit tests with mocks OK per Constitution)

---

## Phase 3: User Story 1 - Baseline Collection (P1)

**Goal**: Establish ground truth for what target LLM actually does (comply vs refuse)

**Independent Test**: Run 680 prompts through Claude Sonnet 4.5, verify all stored in ArangoDB with compliance classification

### Tasks

- [X] T021 [US1] Implement DatasetSource in scripts/validation/common/pipeline.py to load prompts from datasets
- [X] T022 [US1] Implement BaselineEvaluationStage in scripts/validation/experiment_01_baseline.py to send prompts to target LLM
- [X] T023 [US1] Implement ComplianceClassificationStage in scripts/validation/experiment_01_baseline.py using compliance meta-evaluator (FR-003c)
- [X] T024 [US1] Implement borderline handling (0.3 < score < 0.7) per FR-003b in ComplianceClassificationStage
- [X] T025 [US1] Implement ProcessingFailureHandler in scripts/validation/experiment_01_baseline.py per FR-005
- [X] T026 [US1] Implement ArangoSink for baseline_responses collection in scripts/validation/utils/arango_client.py
- [X] T027 [US1] Implement ArangoSink for processing_failures collection in scripts/validation/utils/arango_client.py
- [X] T028 [US1] Implement checkpoint/resume logic using ArangoDB query in scripts/validation/experiment_01_baseline.py
- [X] T029 [US1] Implement model version extraction from OpenRouter response in scripts/validation/experiment_01_baseline.py
- [X] T030 [US1] Implement experiment metadata tracking (total_cost, duration) in scripts/validation/experiment_01_baseline.py
- [X] T031 [US1] Create CLI entry point for experiment_01_baseline.py with argument parsing (target_model, observer_model, experiment_id)
- [ ] T032 [US1] Write integration test in tests/integration/test_experiment_01_baseline.py (real APIs, cost evidence required per Constitution)

**Parallel Execution**: None - sequential processing of 680 prompts required for cost tracking

**Validation**:
```bash
uv run python scripts/validation/experiment_01_baseline.py \
    --target-model "anthropic/claude-3.5-sonnet" \
    --observer-model "anthropic/claude-3.5-sonnet" \
    --experiment-id "exp_001_baseline_test"
```
Expected: 680 records in `baseline_responses`, experiment metadata with total_cost, processing_failures (if any)

---

## Phase 4: User Story 2 - Pre-Evaluation Cross-Tabulation (P1)

**Goal**: Measure PromptGuard detection before seeing LLM responses

**Independent Test**: Run PromptGuard pre-evaluation on 680 prompts, generate 3 confusion matrices

### Tasks

- [ ] T033 [US2] Implement ArangoSource in scripts/validation/common/pipeline.py to query prompts by experiment_id
- [ ] T034 [US2] Implement PreEvaluationStage in scripts/validation/experiment_02_preeval.py using existing LLMEvaluator
- [ ] T035 [US2] Implement decision threshold (F >= 0.7 = Block) in PreEvaluationStage per FR-008
- [ ] T036 [US2] Implement ArangoSink for pre_eval_results collection in scripts/validation/utils/arango_client.py
- [ ] T037 [US2] Implement ConfusionMatrixCalculator in scripts/validation/experiment_02_preeval.py for Matrix A (PromptGuard×LLM)
- [ ] T038 [P] [US2] Implement ConfusionMatrixCalculator for Matrix B (PromptGuard×Labels) in scripts/validation/experiment_02_preeval.py
- [ ] T039 [P] [US2] Implement ConfusionMatrixCalculator for Matrix C (LLM×Labels) in scripts/validation/experiment_02_preeval.py
- [ ] T040 [US2] Implement borderline exclusion logic per FR-009 in ConfusionMatrixCalculator
- [ ] T041 [US2] Implement metrics calculation (precision, recall, F1) in ConfusionMatrixCalculator per FR-010
- [ ] T042 [US2] Implement statistical significance with confidence intervals per FR-013 in scripts/validation/experiment_02_preeval.py
- [ ] T043 [US2] Create CLI entry point for experiment_02_preeval.py with argument parsing
- [ ] T044 [US2] Write integration test in tests/integration/test_experiment_02_preeval.py (real APIs required)

**Parallel Execution**: T038 and T039 can run in parallel (different matrix calculations)

**Validation**:
```bash
uv run python scripts/validation/experiment_02_preeval.py \
    --observer-model "anthropic/claude-3.5-sonnet" \
    --experiment-id "exp_002_preeval_test" \
    --baseline-experiment-id "exp_001_baseline_test"
```
Expected: 680 records in `pre_eval_results`, 3 records in `confusion_matrices`

---

## Phase 5: User Story 3 - Pattern Mining (P2)

**Goal**: Extract attack patterns from false negatives for REASONINGBANK

**Independent Test**: Run post-evaluation on false negatives, verify patterns stored in REASONINGBANK

### Tasks

- [ ] T045 [US3] Implement FalseNegativeQuery in scripts/validation/experiment_03_patterns.py to identify pre-eval misses
- [ ] T046 [US3] Implement PostEvaluationStage in scripts/validation/experiment_03_patterns.py using existing LLMEvaluator
- [ ] T047 [US3] Implement divergence calculation (post_F - pre_F) in PostEvaluationStage per FR-015
- [ ] T048 [US3] Implement PatternExtractionStage in scripts/validation/experiment_03_patterns.py for divergence >= 0.5
- [ ] T049 [US3] Implement pattern metadata generation (title, description, semantic_tags, few_shot_example) per FR-017
- [ ] T050 [US3] Implement ArangoSink for reasoningbank_patterns collection in scripts/validation/utils/arango_client.py
- [ ] T051 [US3] Implement ArangoSink for post_eval_results collection in scripts/validation/utils/arango_client.py
- [ ] T052 [US3] Implement Wilson score interval calculation per FR-020 in scripts/validation/utils/statistics.py
- [ ] T053 [US3] Implement composable stride logic (expand dataset if CI width > 5%) in scripts/validation/experiment_03_patterns.py
- [ ] T054 [US3] Implement model version consistency check across strides per FR-020 in scripts/validation/experiment_03_patterns.py
- [ ] T055 [US3] Create CLI entry point for experiment_03_patterns.py with argument parsing
- [ ] T056 [US3] Write integration test in tests/integration/test_experiment_03_patterns.py (real APIs required)

**Parallel Execution**: Post-evaluation can process false negatives in batches, but pattern extraction is sequential

**Validation**:
```bash
uv run python scripts/validation/experiment_03_patterns.py \
    --observer-model "anthropic/claude-3.5-sonnet" \
    --experiment-id "exp_003_patterns_test" \
    --preeval-experiment-id "exp_002_preeval_test"
```
Expected: N records in `reasoningbank_patterns` (N >= 1), 680 records in `post_eval_results`, CI width calculation

---

## Phase 6: User Story 4 - REASONINGBANK Validation (P1)

**Goal**: Three-condition test to measure REASONINGBANK effect vs template marker effect

**Independent Test**: Run n=50-100 prompts through 3 conditions, calculate deltas, test for interaction

### Tasks

- [ ] T057 [US4] Implement SampleSource in scripts/validation/common/pipeline.py to randomly sample n prompts from original 680
- [ ] T058 [US4] Load old baseline prompt from fixture file per FR-356-362 in scripts/validation/experiment_04_validation.py
- [ ] T059 [US4] Verify fixture SHA-256 checksum per FR-358-359 in scripts/validation/experiment_04_validation.py
- [ ] T060 [US4] Implement Condition1Stage (old baseline, pre-template-marker) in scripts/validation/experiment_04_validation.py
- [ ] T061 [US4] Implement Condition2Stage (new baseline, no REASONINGBANK) in scripts/validation/experiment_04_validation.py
- [ ] T062 [US4] Implement Condition3Stage (enhanced with REASONINGBANK retrieval) in scripts/validation/experiment_04_validation.py
- [ ] T063 [US4] Verify REASONINGBANK enhancement includes few-shot examples per FR-022 in Condition3Stage
- [ ] T064 [US4] Implement DeltaCalculator for 3 deltas (template marker, REASONINGBANK, total) per FR-024 in scripts/validation/experiment_04_validation.py
- [ ] T065 [US4] Implement interaction term calculation per FR-024b in DeltaCalculator
- [ ] T066 [US4] Implement statistical significance testing with Bonferroni correction per FR-025 in scripts/validation/experiment_04_validation.py
- [ ] T067 [US4] Create CLI entry point for experiment_04_validation.py with sample_size parameter
- [ ] T068 [US4] Write integration test in tests/integration/test_experiment_04_validation.py (real APIs required)

**Parallel Execution**: None - three conditions run sequentially per research.md decision

**Validation**:
```bash
uv run python scripts/validation/experiment_04_validation.py \
    --observer-model "anthropic/claude-3.5-sonnet" \
    --experiment-id "exp_004_validation_test" \
    --sample-size 50 \
    --source-experiment-id "exp_001_baseline_test"
```
Expected: 1 record in `validation_rounds` with 3 FN rates, 3 deltas, interaction term

---

## Phase 7: User Story 5 - External Pattern Integration (P3)

**Goal**: Add externally-discovered patterns and measure cumulative improvement

**Independent Test**: Manually add blind spot patterns, re-run validation, measure improvement

### Tasks

- [ ] T069 [P] [US5] Implement external pattern loader in scripts/validation/utils/external_patterns.py to import patterns from JSON/YAML
- [ ] T070 [P] [US5] Implement pattern validation schema in scripts/validation/utils/external_patterns.py per data-model.md
- [ ] T071 [US5] Implement cumulative improvement tracker in scripts/validation/experiment_05_external.py to compare rounds
- [ ] T072 [US5] Implement learning curve visualization in scripts/validation/experiment_05_external.py
- [ ] T073 [US5] Create CLI entry point for experiment_05_external.py with pattern source parameter
- [ ] T074 [US5] Write integration test in tests/integration/test_experiment_05_external.py (real APIs required)

**Parallel Execution**: T069 and T070 can be developed in parallel

**Validation**:
```bash
# Manually create external_patterns.json with blind spot patterns
uv run python scripts/validation/experiment_05_external.py \
    --pattern-source "external_patterns.json" \
    --experiment-id "exp_005_external_test"
```
Expected: Updated `reasoningbank_patterns` collection, cumulative improvement metrics

---

## Phase 8: Polish & Cross-Cutting Concerns

**Goal**: Export utilities, documentation, and final validation

### Tasks

- [ ] T075 [P] Implement JSONL export function in scripts/validation/export_results.py per FR-037
- [ ] T076 [P] Implement confusion matrix CSV export in scripts/validation/export_confusion_matrix.py
- [ ] T077 [P] Implement failure analysis report generator per FR-005b in scripts/validation/analyze_failures.py
- [ ] T078 Implement model version change handler with PAUSE/ABORT/CONTINUE/IGNORE flow per FR-032 in scripts/validation/common/config.py
- [ ] T079 [P] Write contract test for ArangoDB schema validation in tests/contract/test_arango_schema.py
- [ ] T080 [P] Write unit test for Wilson score interval calculation in tests/unit/test_statistics.py
- [ ] T081 [P] Write unit test for checkpoint/resume logic in tests/unit/test_checkpoint.py
- [ ] T082 Update quickstart.md with actual CLI examples from implemented experiments
- [ ] T083 Create example AQL queries file in specs/002-specify-scripts-bash/examples/queries.aql
- [ ] T084 Run complete 4-experiment validation workflow: (1) Pipeline validation on n=100 subset to verify infrastructure works, then (2) Full publication run on n=680 prompts per SC-006. Document cost evidence per Constitution (API logs, receipts, timestamps). Expected cost: ~$13-28 total.

**Parallel Execution**: T075-T077, T079-T081 can all run in parallel

**Final Validation**: Complete 4-experiment workflow on test subset, verify all 10 collections populated, export results to JSONL

---

## Implementation Strategy

### MVP Scope (Recommended)

**Minimum Viable Product**: User Story 1 only (Baseline Collection)

This delivers:
- Complete baseline data collection pipeline
- Checkpoint/resume capability
- Processing failure handling
- ArangoDB storage
- Independently testable and valuable

**Rationale**: Establishes ground truth data that unblocks all other stories. Can validate pipeline architecture before expanding to complex cross-tabulation.

### Incremental Delivery

1. **Sprint 1**: Phase 1 (Setup) + Phase 2 (Foundational) + Phase 3 (US1)
   - **Deliverable**: Baseline collection working, 680 prompts processable
   - **Validation**: Run on 100-prompt subset, verify storage and resume

2. **Sprint 2**: Phase 4 (US2)
   - **Deliverable**: Pre-evaluation cross-tabulation, 3 confusion matrices
   - **Validation**: Verify Matrix A answers "Does PromptGuard catch what fools RLHF?"

3. **Sprint 3**: Phase 5 (US3) + Phase 6 (US4)
   - **Deliverable**: Pattern mining + REASONINGBANK validation
   - **Validation**: Verify REASONINGBANK effect cleanly separated from template marker

4. **Sprint 4**: Phase 7 (US5) + Phase 8 (Polish)
   - **Deliverable**: External pattern integration + export utilities
   - **Validation**: Complete 4-experiment validation on full dataset

### Parallel Execution Examples

**Within User Story 1 (after foundational infrastructure)**:
```bash
# None - sequential pipeline for cost tracking
```

**Within User Story 2 (after pre-evaluation complete)**:
```python
# Calculate 3 confusion matrices in parallel
with ThreadPoolExecutor(max_workers=3) as executor:
    matrix_a = executor.submit(calculate_matrix_a, results)
    matrix_b = executor.submit(calculate_matrix_b, results)
    matrix_c = executor.submit(calculate_matrix_c, results)
```

**Across User Stories (after US2 complete)**:
```bash
# US3 and US4 can proceed independently if REASONINGBANK already has patterns from prior work
# Otherwise US4 depends on US3 completing first
```

---

## Constitution Compliance Checklist

- ✅ **No Theater**: All evaluation uses existing LLM-based framework, fail-fast errors
- ✅ **Empirical Integrity**: Integration tests require real APIs (T032, T044, T056, T068, T074), cost evidence required (T084)
- ✅ **Fail-Fast**: ConfigurationError, ValidationError, EvaluationError implemented (T011-T014)
- ✅ **Immutable Storage**: ArangoDB INSERT-only enforced at application layer (T007-T008)
- ✅ **Semantic Evaluation**: Uses existing observer framing prompts (no keyword matching)
- ✅ **Specification-Driven**: This tasks.md generated from complete spec.md + plan.md + data-model.md

---

## Success Metrics

- **Task Completion**: 84 tasks total
- **User Story Coverage**: All 5 stories have complete task coverage
- **Independent Tests**: Each story has integration test validating end-to-end functionality
- **Parallel Opportunities**: 23 tasks marked [P] for concurrent execution
- **Constitution Compliance**: All principles validated through task structure

**Next Step**: Begin with MVP (Phase 1-3), validate on 100-prompt subset, expand to full dataset after pipeline proven.
