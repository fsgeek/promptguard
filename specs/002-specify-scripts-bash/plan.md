# Implementation Plan: End-to-End PromptGuard Validation Framework

**Branch**: `002-specify-scripts-bash` | **Date**: 2025-10-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/home/tony/projects/promptguard/specs/002-specify-scripts-bash/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Implement a 4-experiment validation framework to measure PromptGuard's effectiveness against actual LLM behavior (not just labeled datasets). The framework establishes the missing research link: what does Claude actually DO with prompts (comply vs refuse)? This enables measurement of PromptGuard's true value - detecting attacks that fool RLHF, not redundant detection of attacks RLHF already blocks.

**Technical Approach**: Composable pipeline architecture with ArangoDB as single source of truth. Each experiment produces INSERT-only data enabling composable strides (expand dataset until statistical thresholds met). Four experiments: (1) Baseline collection, (2) Pre-evaluation cross-tabulation, (3) Pattern mining from false negatives, (4) REASONINGBANK validation with template marker control.

## Technical Context

**Language/Version**: Python 3.13 (project uses `uv` package manager)
**Primary Dependencies**:
- ArangoDB (document + graph database) - already installed and configured
- OpenRouter API - already integrated in `promptguard/evaluation/evaluator.py`
- Existing PromptGuard evaluation framework (`promptguard/` package)
- REASONINGBANK retrieval system (`reasoningbank/retriever.py`)

**Storage**: ArangoDB (multi-model: document + graph + full-text search)
- Host: 192.168.111.125:8529
- Database: PromptGuard
- Collections: 10 (prompt_configurations, prompts, processing_failures, baseline_responses, pre_eval_results, post_eval_results, confusion_matrices, reasoningbank_patterns, validation_rounds, experiments)

**Testing**: pytest (existing test infrastructure in `tests/`)
- Integration tests with real ArangoDB required (Tier 2 per Constitution)
- Real API validation required (OpenRouter calls, cost evidence)
- No mocks for external APIs (Constitution: Empirical Integrity principle)

**Target Platform**: Linux server (WSL2 on development machine)

**Project Type**: Research validation scripts (single project structure)

**Performance Goals**:
- Baseline collection: Process 680 prompts in <30 minutes
- API latency: <10s per prompt evaluation (OpenRouter + Claude Sonnet 4.5)
- Database writes: <20ms per document (ArangoDB local network)
- Total cost: <$100 for complete 4-experiment validation (budget tracking only, not design constraint)

**Constraints**:
- Immutable storage (INSERT-only, no UPDATE/DELETE operations)
- Fail-fast error handling (no silent degradation per Constitution)
- Real API validation required (no mocks for integration tests)
- Composable architecture (enable future pipeline extensions)

**Scale/Scope**:
- Initial: 680 prompts across 3 datasets (benign_malicious, or_bench, extractive)
- Expandable: Composable strides until CI width ≤ 5% (Wilson score intervals)
- Database: <100GB storage (30TB available)
- Runtime: Multi-hour experiments (background processes)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### Principle I: No Theater ✅

**Compliance**:
- All evaluation is semantic (existing LLM-based evaluation framework)
- Fail-fast error handling specified (ConfigurationError, ValidationError)
- No keyword matching or fake values
- Real API calls required (FR-005: Process failures stored, not hidden)

### Principle II: Empirical Integrity ✅

**Compliance**:
- Tier 2 testing required: Real OpenRouter API calls with cost documentation
- Integration tests with real ArangoDB connection (18 existing tests validate storage)
- Cost tracking required (FR-028: experiments.total_cost field)
- Evidence requirements: API logs, timestamps, model versions

**Validation approach**:
- Implementation phase: Build pipeline with unit tests
- Validation phase: Run on real dataset (680 prompts) with cost evidence
- Auditor phase: Verify claims match evidence before acceptance

### Principle III: Agency Over Constraint ✅

**Compliance**: Framework measures PromptGuard's detection capability, enabling LLMs to make informed choices about manipulation. Compliance meta-evaluator (FR-003c) measures LLM behavior without constraining it.

### Principle IV: Continuous Learning Over Static Training ✅

**Compliance**: This framework validates the continuous learning loop:
- Experiment 1-2: Establish baseline and identify false negatives
- Experiment 3: Mine patterns from false negatives → REASONINGBANK
- Experiment 4: Validate REASONINGBANK improves detection
- Architecture supports composable strides (learn → improve → validate → repeat)

### Principle V: Semantic Evaluation Only ✅

**Compliance**: All evaluation uses existing observer framing prompts (ayni_relational). Compliance classification via LLM meta-evaluator (FR-003c), not keywords.

### Architectural Decision: Fail-Fast Over Graceful Degradation ✅

**Compliance**:
- FR-005: Processing failures stored in dedicated collection (first-class data)
- FR-003d: ConfigurationError on database corruption
- FR-032: Model version changes trigger PAUSE → user decision (ABORT/CONTINUE/IGNORE)
- FR-035: No UPDATE/DELETE operations (immutability enforced at application layer)

### Development Standard: Specification-Driven Development ✅

**Compliance**: This feature uses spec-kit workflow (`/speckit.specify` → `/speckit.plan` → `/speckit.tasks` → `/speckit.implement`). Specification completed through 6 review cycles, 95% completeness, ready for implementation.

**Gate Result**: **PASS** - All constitution principles satisfied. No violations requiring justification.

## Project Structure

### Documentation (this feature)

```
specs/002-specify-scripts-bash/
├── spec.md              # Complete feature specification (95% complete)
├── plan.md              # This file (/speckit.plan output)
├── research.md          # Phase 0 output (to be generated)
├── data-model.md        # Phase 1 output (to be generated)
├── quickstart.md        # Phase 1 output (to be generated)
├── contracts/           # Phase 1 output (to be generated)
├── fixtures/
│   └── old_baseline_prompt.txt  # Pre-template-marker prompt for Experiment 4
├── checklists/
│   └── requirements.md  # Quality validation checklist
└── tasks.md             # Phase 2 output (/speckit.tasks - NOT created by /speckit.plan)
```

### Source Code (repository root)

```
promptguard/                    # Existing package
├── evaluation/
│   ├── evaluator.py            # LLMEvaluator (SINGLE/PARALLEL/FIRE_CIRCLE modes)
│   ├── prompts.py              # Observer framing prompts (ayni_relational)
│   └── cache.py                # Cache layer (DiskCache, MemoryCache)
├── storage/
│   ├── arango_backend.py       # ArangoDB storage backend (18 passing tests)
│   └── deliberation.py         # DeliberationStorage interface
└── core/
    ├── neutrosophic.py         # MultiNeutrosophicPrompt
    └── ayni.py                 # AyniEvaluator, ReciprocityMetrics

reasoningbank/                  # Existing package
├── models.py                   # ReasoningBankMemory data model
└── retriever.py                # ReasoningBankRetriever (enhance_few_shot_prompt)

scripts/                        # NEW - Validation pipeline scripts
├── validation/
│   ├── experiment_01_baseline.py        # Baseline LLM behavior collection
│   ├── experiment_02_preeval.py         # Pre-evaluation cross-tabulation
│   ├── experiment_03_patterns.py        # Pattern mining from false negatives
│   ├── experiment_04_validation.py      # REASONINGBANK validation (3 conditions)
│   ├── common/
│   │   ├── pipeline.py                  # Composable pipeline interfaces
│   │   ├── config.py                    # Configuration loading
│   │   └── errors.py                    # ConfigurationError, ValidationError
│   └── utils/
│       ├── arango_client.py             # ArangoDB connection wrapper
│       ├── prompt_loader.py             # Load prompts from datasets
│       └── checkpoint.py                # Resume support for long-running experiments

tests/
├── integration/
│   ├── test_arango_backend.py           # Existing (18 passing tests)
│   ├── test_experiment_01_baseline.py   # NEW - E2E validation (real APIs)
│   ├── test_experiment_02_preeval.py    # NEW - E2E validation
│   ├── test_experiment_03_patterns.py   # NEW - E2E validation
│   └── test_experiment_04_validation.py # NEW - E2E validation
├── unit/
│   ├── test_pipeline.py                 # NEW - Pipeline interfaces (mocks OK)
│   ├── test_prompt_loader.py            # NEW - Dataset loading
│   └── test_checkpoint.py               # NEW - Resume logic
└── contract/
    └── test_arango_schema.py            # NEW - Validate 10 collections exist

datasets/                       # Existing
├── benign_malicious.json       # 500 prompts
├── or_bench_sample.json        # 100 prompts
└── extractive_prompts_dataset.json  # 80 prompts
```

**Structure Decision**: Single project structure (Option 1) with new `scripts/validation/` directory for experimental validation pipelines. Integrates with existing `promptguard/` package and `reasoningbank/` package. Follows existing project conventions (pytest, uv, ArangoDB storage).

## Complexity Tracking

*No violations - Constitution Check passed all gates.*

---

## Phase 0: Research & Technical Decisions

**Status**: To be completed by /speckit.plan command

**Unknowns to resolve**:

1. **Checkpoint/resume mechanism for long-running experiments**
   - Decision needed: File-based checkpointing (JSONL) vs ArangoDB-based (query for completed prompts)
   - Context: Experiments process 680 prompts over hours, need resume capability
   - Constitution relevance: Fail-fast principle - interruptions should not corrupt data

2. **Prompt loading strategy from existing datasets**
   - Decision needed: Load all 680 into memory vs stream from disk vs load from ArangoDB
   - Context: Three datasets (benign_malicious, or_bench, extractive) totaling 680 prompts
   - Trade-offs: Memory usage vs file I/O vs database queries

3. **Model version consistency checking across strides**
   - Decision needed: Query OpenRouter API for current model version vs parse from response metadata
   - Context: FR-020 requires detecting model version changes between strides
   - Constitution relevance: Empirical integrity - must prove model version didn't change

4. **Pipeline composability architecture**
   - Decision needed: Source/sink interface design (push vs pull, streaming vs batch)
   - Context: FR-033 requires composable stages (Exp1→Exp2→Exp3→Exp4)
   - Best practices needed: Python pipeline patterns for research workflows

5. **Wilson score interval calculation implementation**
   - Decision needed: scipy.stats library vs manual implementation
   - Context: FR-020 requires CI width calculation for stopping condition
   - Trade-offs: Dependency vs correctness vs edge case handling

6. **Three-condition experiment execution**
   - Decision needed: Sequential (Condition 1 → 2 → 3) vs parallel (3 threads)
   - Context: FR-021 runs same 50-100 prompts through 3 evaluation configurations
   - Trade-offs: Runtime (serial=3x slower) vs cost (parallel=3x API calls simultaneously)

7. **Fixture file validation in production**
   - Decision needed: Validate checksum on every run vs once on initialization
   - Context: FR-356-362 requires SHA-256 validation of old_baseline_prompt.txt
   - Trade-offs: Runtime overhead vs integrity guarantee

**Research tasks** (to be delegated to Task agents in Phase 0):

1. Research Python pipeline patterns for composable research workflows
2. Find best practices for checkpoint/resume in long-running data processing
3. Investigate OpenRouter API model version metadata retrieval
4. Evaluate Wilson score interval calculation libraries (scipy.stats vs statsmodels)
5. Benchmark ArangoDB query performance for completed prompts filtering
6. Research parallel vs sequential execution trade-offs for API-heavy workloads

**Output**: `research.md` with decisions documented per format:
- Decision: [what was chosen]
- Rationale: [why chosen]
- Alternatives considered: [what else evaluated]

---

## Phase 1: Data Model & Contracts

**Status**: To be completed by /speckit.plan command after Phase 0

**Prerequisites**: research.md complete with all unknowns resolved

**Tasks**:

1. **Extract entities from spec.md → data-model.md**:
   - 10 ArangoDB collections (already specified in spec.md lines 261-307)
   - Field types, constraints, relationships
   - Validation rules from functional requirements
   - Pydantic models for schema enforcement (FR-039: AwareDatetime for ISO 8601)

2. **Generate API contracts** (if applicable):
   - This feature has no REST/GraphQL API (scripts run locally)
   - Contracts are Python interfaces (Source/Sink for pipeline)
   - Output to `/contracts/` as Python abstract base classes

3. **Create quickstart.md**:
   - Installation: `uv sync` (dependencies already in pyproject.toml)
   - ArangoDB setup: Environment variables (ARANGODB_PROMPTGUARD_PASSWORD, etc.)
   - Running experiments: `uv run python scripts/validation/experiment_01_baseline.py`
   - Querying results: Example AQL queries for common analyses

4. **Update agent context**:
   - Run `.specify/scripts/bash/update-agent-context.sh claude`
   - Add new technologies: None (uses existing Python, ArangoDB, OpenRouter)
   - Add new modules: `scripts/validation/` pipeline architecture

**Outputs**:
- `data-model.md`: Pydantic models for 10 collections + pipeline interfaces
- `contracts/`: Python ABC definitions for Source/Sink/Stage
- `quickstart.md`: Getting started guide for running experiments
- Agent context file updated (CLAUDE.md or equivalent)

---

## Phase 2: Task Generation

**Status**: NOT created by /speckit.plan - requires separate `/speckit.tasks` command

**Will be generated by**: `/speckit.tasks` command after Phase 1 complete

**Expected output**: `tasks.md` with dependency-ordered implementation tasks

---

## Notes

- Specification completed through 6 review cycles (95% complete, ready for implementation)
- Final 3 issues addressed: fixture checksum validation, interaction term power caveat, version type specification
- Constitution compliance verified: All 5 principles + fail-fast architecture satisfied
- Existing infrastructure leveraged: ArangoDB backend (18 tests), OpenRouter integration, observer framing prompts
- Research gap addressed: Measuring PromptGuard against actual LLM behavior, not just labels
