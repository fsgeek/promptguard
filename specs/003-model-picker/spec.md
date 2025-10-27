# Feature Specification: Model Picker

**Feature Branch**: `003-model-picker`
**Created**: 2025-10-26
**Status**: Draft
**Input**: User description: "Create database-driven LLM model selection infrastructure that solves the deprecated model problem by storing model metadata in ArangoDB and enabling attribute-based queries."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Query Available Frontier Models (Priority: P1)

Research code needs to select frontier models for Fire Circle deliberations without hardcoding model names that become deprecated.

**Why this priority**: This is the core problem - hardcoded model names are the source of technical debt and fail-fast errors when models are deprecated.

**Independent Test**: Query "available frontier models" and verify results contain only currently-available frontier models, with no deprecated models included.

**Acceptance Scenarios**:

1. **Given** model metadata is populated in ArangoDB, **When** researcher queries for available frontier models, **Then** system returns list of models with provider, architecture, and OpenRouter ID
2. **Given** a model was marked frontier but is now deprecated, **When** researcher queries for available frontier models, **Then** deprecated model is excluded from results
3. **Given** model list hasn't been refreshed in 25 hours, **When** researcher queries for models, **Then** system automatically refreshes from OpenRouter before returning results

---

### User Story 2 - Filter Models by Attributes (Priority: P2)

Research code needs to select models matching specific criteria (free, instruct-tuned, RLHF-aligned, specific providers).

**Why this priority**: Different experiments require different model characteristics - observer evaluation needs free models, Fire Circle needs frontier diversity, baseline validation needs RLHF comparison.

**Independent Test**: Query "free instruct models" and manually verify each result is both free and instruction-tuned according to OpenRouter.

**Acceptance Scenarios**:

1. **Given** models with various attributes stored, **When** researcher queries for "free AND instruct" models, **Then** results include only models matching both criteria
2. **Given** models from multiple providers, **When** researcher queries for "provider=Anthropic AND available", **Then** results include only currently-available Anthropic models
3. **Given** a need for structural diversity, **When** researcher queries by architecture family, **Then** results are grouped by architecture for selection

---

### User Story 3 - Handle Stale Frontier Designations (Priority: P1)

Frontier model designation requires periodic human review - system should warn when designations haven't been updated recently.

**Why this priority**: Frontier designation can't be automated (requires analysis unavailable from OpenRouter). Without staleness warnings, researchers may unknowingly use outdated frontier lists.

**Independent Test**: Set frontier_updated timestamp to 45 days ago, query for frontier models, verify interactive warning appears and requires acknowledgment.

**Acceptance Scenarios**:

1. **Given** frontier list hasn't been updated in 35+ days, **When** researcher queries for frontier models, **Then** system displays interactive warning with last-updated date and requires acknowledgment to continue
2. **Given** warning is acknowledged, **When** query proceeds, **Then** system returns results but logs staleness warning
3. **Given** frontier list was updated within 30 days, **When** researcher queries for frontier models, **Then** no warning appears

---

### User Story 4 - Sync with OpenRouter API (Priority: P2)

Model availability changes frequently - system needs to periodically refresh model list from OpenRouter to stay current.

**Why this priority**: Availability is dynamic (models come online/offline). Enables query accuracy without manual updates.

**Independent Test**: Clear model list, trigger sync, verify models collection contains entries matching OpenRouter's current catalog.

**Acceptance Scenarios**:

1. **Given** models collection is empty or stale (>24h), **When** sync is triggered (via query or manual call), **Then** system fetches current model list from OpenRouter API and populates collection
2. **Given** sync completed successfully, **When** last_synced timestamp is checked, **Then** it reflects current time
3. **Given** OpenRouter API returns an error, **When** sync is attempted, **Then** system logs error but continues with cached data if available

---

### Edge Cases

- What happens when OpenRouter API is unavailable during sync? (Use cached data, log error, warn if cache is >48h old)
- How does system handle models that exist in OpenRouter but have incomplete metadata? (Store what's available, mark as incomplete, exclude from queries requiring missing attributes)
- What if researcher queries for attribute combination that matches zero models? (Return empty list with informative message indicating no matches found)
- How are manually-curated attributes (frontier, testing) maintained across OpenRouter syncs? (Preserve manual attributes, only update OpenRouter-provided fields like availability/pricing)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST store model metadata in ArangoDB models collection with fields: openrouter_id, provider, architecture_family, available, frontier, free, instruct, rlhf, last_synced
- **FR-002**: System MUST query OpenRouter API to refresh model availability and metadata when cache is >24h old or manually triggered
- **FR-003**: System MUST support attribute-based queries (available=true, frontier=true, free=true, provider=X, architecture_family=Y)
- **FR-004**: System MUST support AND/OR combinations of attributes in queries
- **FR-005**: System MUST preserve manually-curated attributes (frontier, testing) across OpenRouter sync operations
- **FR-006**: System MUST implement TTL-based automatic refresh using cycle-stealing (check on query invocation, refresh if stale)
- **FR-007**: System MUST display interactive staleness warning when frontier list hasn't been updated in >30 days, requiring user acknowledgment to proceed
- **FR-008**: System MUST return filtered model candidates with full metadata (provider, architecture, attributes, openrouter_id) for caller to implement selection policy
- **FR-009**: System MUST use ArangoDB SearchView for full-text search on model descriptions (from OpenRouter)
- **FR-010**: System MUST support open tagging - allow arbitrary new attributes to be added without schema changes

### Key Entities *(include if feature involves data)*

- **Model**: Represents an LLM available via OpenRouter or manually added
  - Attributes from OpenRouter: openrouter_id, provider, pricing, context_window, description
  - Manual attributes: frontier (boolean), testing (boolean), any future tags
  - Sync metadata: last_synced (timestamp), available (boolean from OpenRouter)
  - Research attributes: architecture_family, free, instruct, rlhf (manually curated or extracted from descriptions)

- **SyncMetadata**: Tracks global sync state
  - last_openrouter_sync: timestamp of last successful OpenRouter API call
  - frontier_updated: timestamp of last manual frontier list review
  - sync_errors: recent errors for operational visibility

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Query "available frontier models" returns only currently-available frontier models with structural diversity (at least 2 different providers, 2 different architecture families if available)
- **SC-002**: Query "free instruct models" returns only models matching both attributes, verified by manual spot-check of 5 results against OpenRouter
- **SC-003**: Model list auto-refreshes from OpenRouter within 1 minute of query when cache is >24h old
- **SC-004**: Staleness warning appears and blocks execution when frontier list is >30 days old, requiring interactive acknowledgment
- **SC-005**: Existing hardcoded model selection code (Fire Circle tests, observer model selection) can be converted to use model-picker queries without changing test behavior
- **SC-006**: Manual curation of frontier designation survives OpenRouter sync operations (manually-set frontier=true persists across syncs)

## Scope & Dependencies

### In Scope
- Model metadata storage in ArangoDB
- OpenRouter API sync with 24h TTL
- Attribute-based query interface
- Staleness warnings for frontier designation
- Preservation of manual attributes across syncs

### Out of Scope
- Automated attribute extraction from model descriptions (manual tagging for MVP)
- Model performance tracking or benchmarking
- Cost optimization or budget alerts
- Background refresh jobs (cycle-stealing on query invocation is sufficient for research tool)
- Provider abstraction beyond OpenRouter
- Structural diversity selection policy (caller responsibility)

### Dependencies
- ArangoDB instance (already exists per CLAUDE.md)
- OpenRouter API key (already configured)
- ArangoDB SearchView for full-text search (to be configured)

## Assumptions

- OpenRouter API schema remains relatively stable (handle breaking changes reactively)
- Manual frontier curation happens monthly (30-day staleness threshold acceptable)
- Research workload generates enough queries that 24h TTL cycle-stealing provides sufficient freshness
- Manual attribute taxonomy governance is acceptable for MVP (standardization can come later)

## Non-Functional Requirements

- **Performance**: Query response <100ms for attribute filters (excluding OpenRouter sync time)
- **Reliability**: Graceful degradation if OpenRouter API unavailable (use cached data with warning)
- **Maintainability**: Open tagging allows adding new attributes without code changes
- **Usability**: Interactive warnings visible and clear (not buried in logs)

