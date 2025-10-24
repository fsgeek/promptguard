# Data Model: End-to-End PromptGuard Validation Framework

**Date**: 2025-10-22
**Feature**: End-to-End PromptGuard Validation Framework
**Source**: Extracted from spec.md (Key Entities section, lines 261-307)

This document defines the data model for 10 ArangoDB collections and pipeline interfaces.

---

## ArangoDB Collections

### 1. Prompt Configuration (`prompt_configurations`)

**Purpose**: Versioned evaluation prompts for temporal tracking and reproducibility

**Pydantic Model**:
```python
from pydantic import BaseModel, Field, AwareDatetime
from uuid import UUID, uuid4
from datetime import datetime, timezone
from enum import Enum

class PromptType(str, Enum):
    COMPLIANCE_CLASSIFICATION = "compliance_classification"
    PRE_EVAL = "pre_eval"
    POST_EVAL = "post_eval"

class PromptConfiguration(BaseModel):
    prompt_id: UUID = Field(default_factory=uuid4)
    prompt_type: PromptType
    prompt_text: str
    version: int = Field(ge=0, description="Integer sequence: 0=original, 1=first revision, etc.")
    created_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    parameters: dict[str, any] = Field(
        default_factory=dict,
        description="Templating parameters (e.g., {'compliance_threshold': 0.7, 'scale': '0-1', 'output_format': 'json'})"
    )

    class Config:
        json_encoders = {
            UUID: str,
            datetime: lambda v: v.isoformat()
        }
```

**Indexes**:
- Hash index on `(prompt_type, version)` with `unique: true` (FR-003d)

**Immutability**: INSERT only, no UPDATE/DELETE

---

### 2. Prompt (`prompts`)

**Purpose**: Prompts used in validation with provenance tracking

**Pydantic Model**:
```python
class SourceDataset(str, Enum):
    BENIGN_MALICIOUS = "benign_malicious"
    OR_BENCH = "or_bench"
    EXTRACTIVE = "extractive"
    ADVBENCH = "advbench"
    HARMBENCH = "harmbench"
    TOXICCHAT = "toxicchat"

class Label(str, Enum):
    MANIPULATIVE = "manipulative"
    RECIPROCAL = "reciprocal"

class Prompt(BaseModel):
    prompt_id: UUID = Field(default_factory=uuid4)
    prompt_text: str
    source_dataset: SourceDataset
    stride_number: int = Field(
        ge=0,
        description="0=original 680, 1=first stride, 2=second stride, etc."
    )
    added_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    model_version_at_stride: str = Field(
        description="Model version when prompt added (e.g., 'anthropic/claude-3.5-sonnet:20241022')"
    )
    label: Label
    experiment_id: str
```

**Indexes**:
- Hash index on `experiment_id` (query completed prompts for resume)

---

### 3. Processing Failure (`processing_failures`)

**Purpose**: First-class research data for prompt processing failures

**Pydantic Model**:
```python
class ProcessingFailure(BaseModel):
    failure_id: UUID = Field(default_factory=uuid4)
    prompt_id: UUID
    stage: str = Field(description="baseline_collection | pre_eval | post_eval | pattern_mining")
    error_type: str = Field(description="Exception class name")
    error_message: str
    stack_trace: str
    target_model: str
    observer_model: str | None = None
    experiment_id: str
    experiment_label: str
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Purpose**:
- FR-005: Failures are research data, not noise
- Track which prompts cause failures (parsing errors, API timeouts, etc.)
- Enable analysis: "Do certain prompt types fail more often?"

---

### 4. Baseline Response (`baseline_responses`)

**Purpose**: LLM responses to prompts (Experiment 1 - what does Claude actually do?)

**Pydantic Model**:
```python
class Classification(str, Enum):
    COMPLY = "comply"
    REFUSE = "refuse"
    BORDERLINE = "borderline"

class BaselineResponse(BaseModel):
    response_id: UUID = Field(default_factory=uuid4)
    prompt_id: UUID
    response_text: str
    classification: Classification
    compliance_score: float = Field(ge=0.0, le=1.0)
    classification_explanation: str
    target_model: str
    observer_model: str = Field(description="Model used for compliance meta-evaluation")
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    cost: float = Field(ge=0.0, description="API cost in USD")
    token_count: int
    experiment_id: str
    experiment_label: str
    stage: str = "baseline_collection"
    compliance_prompt_id: UUID = Field(description="References Prompt Configuration for compliance_classification")
```

**Purpose**:
- Store what LLM actually does (comply vs refuse) when sent prompt directly
- Enables ground truth for PromptGuard effectiveness measurement

---

### 5. Pre-Evaluation Result (`pre_eval_results`)

**Purpose**: PromptGuard's assessment before sending to LLM

**Pydantic Model**:
```python
class Decision(str, Enum):
    BLOCK = "block"
    ALLOW = "allow"

class PreEvaluationResult(BaseModel):
    pre_eval_id: UUID = Field(default_factory=uuid4)
    prompt_id: UUID
    f_score: float = Field(ge=0.0, le=1.0, description="Falsehood score from neutrosophic evaluation")
    decision: Decision = Field(description="block if f_score >= 0.7, else allow")
    reasoning: str
    transparency_note: str | None = None
    enhanced: bool = Field(description="True if REASONINGBANK retrieval used")
    reasoningbank_patterns_used: list[UUID] = Field(default_factory=list)
    target_model: str
    observer_model: str
    experiment_id: str
    experiment_label: str
    stage: str
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    pre_eval_prompt_id: UUID = Field(description="References Prompt Configuration for pre_eval")
```

**Purpose**:
- Measure PromptGuard's detection before seeing LLM response
- Compare with baseline to calculate TP/FP/TN/FN rates

---

### 6. Post-Evaluation Result (`post_eval_results`)

**Purpose**: PromptGuard's assessment after seeing LLM response

**Pydantic Model**:
```python
class PostEvaluationResult(BaseModel):
    post_eval_id: UUID = Field(default_factory=uuid4)
    prompt_id: UUID
    baseline_response_id: UUID = Field(description="References Baseline Response")
    pre_f: float = Field(ge=0.0, le=1.0, description="From pre_eval_results for same prompt")
    post_f: float = Field(ge=0.0, le=1.0, description="Falsehood score after seeing response")
    divergence: float = Field(description="post_f - pre_f (measures what post-eval caught)")
    reasoning: str
    pattern_extracted: bool
    extracted_pattern_id: UUID | None = Field(
        description="References Attack Pattern if pattern_extracted=true"
    )
    target_model: str
    observer_model: str
    experiment_id: str
    experiment_label: str
    stage: str
    timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    post_eval_prompt_id: UUID = Field(description="References Prompt Configuration for post_eval")
```

**Purpose**:
- Measure what post-evaluation caught that pre-evaluation missed
- Extract patterns from false negatives (input to Experiment 3)

---

### 7. Confusion Matrix (`confusion_matrices`)

**Purpose**: Classification accuracy metrics

**Pydantic Model**:
```python
class ConfusionMatrixType(str, Enum):
    PROMPTGUARD_VS_LLM = "promptguard_vs_llm"
    PROMPTGUARD_VS_LABELS = "promptguard_vs_labels"
    LLM_VS_LABELS = "llm_vs_labels"

class ConfusionMatrix(BaseModel):
    matrix_id: UUID = Field(default_factory=uuid4)
    matrix_type: ConfusionMatrixType
    true_positives: int = Field(ge=0)
    false_positives: int = Field(ge=0)
    true_negatives: int = Field(ge=0)
    false_negatives: int = Field(ge=0)
    borderline_count: int = Field(ge=0, description="Excluded from 2×2 matrix, reported separately")
    precision: float = Field(ge=0.0, le=1.0)
    recall: float = Field(ge=0.0, le=1.0)
    f_score: float = Field(ge=0.0, le=1.0)
    target_model: str
    observer_model: str
    experiment_id: str
    experiment_label: str
    stage: str
    created_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Purpose**:
- FR-009: Three confusion matrices for comprehensive accuracy measurement
- PromptGuard×LLM: Does PromptGuard detect what fools RLHF?
- PromptGuard×Labels: Traditional evaluation metric
- LLM×Labels: What does RLHF catch without PromptGuard?

---

### 8. REASONINGBANK Pattern (`reasoningbank_patterns`)

**Purpose**: Learned attack patterns from Fire Circle deliberations

**Pydantic Model**:
```python
class AttackPattern(BaseModel):
    pattern_id: UUID = Field(default_factory=uuid4)
    pattern_name: str
    pattern_description: str
    example_prompts: list[str] = Field(min_length=1)
    detection_reasoning: str = Field(
        description="Why this pattern indicates manipulation (from Fire Circle)"
    )
    fire_circle_id: UUID | None = Field(
        description="References Fire Circle deliberation that discovered pattern"
    )
    source_false_negatives: list[UUID] = Field(
        description="Prompt IDs that this pattern was extracted from"
    )
    created_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    target_model: str
    observer_model: str
    experiment_id: str
```

**Purpose**:
- Store patterns mined from false negatives (Experiment 3)
- Feed into REASONINGBANK retriever for observer framing enhancement
- Enable continuous learning loop

---

### 9. Validation Round (`validation_rounds`)

**Purpose**: Track Experiment 4 three-condition results

**Pydantic Model**:
```python
class ValidationRound(BaseModel):
    round_id: UUID = Field(default_factory=uuid4)
    experiment_id: str
    sample_size: int = Field(ge=50, le=680)

    # Condition 1: Old baseline (pre-template-marker)
    condition_1_fn_rate: float = Field(ge=0.0, le=1.0)
    condition_1_prompt_id: UUID

    # Condition 2: New baseline (post-template-marker, no REASONINGBANK)
    condition_2_fn_rate: float = Field(ge=0.0, le=1.0)
    condition_2_prompt_id: UUID

    # Condition 3: Enhanced (post-template-marker + REASONINGBANK)
    condition_3_fn_rate: float = Field(ge=0.0, le=1.0)
    condition_3_prompt_id: UUID

    # Delta metrics (FR-024)
    delta_1_template_marker_effect: float = Field(
        description="Condition 2 FN rate - Condition 1 FN rate"
    )
    delta_2_reasoningbank_effect: float = Field(
        description="Condition 3 FN rate - Condition 2 FN rate"
    )
    delta_3_total_effect: float = Field(
        description="Condition 3 FN rate - Condition 1 FN rate"
    )

    # Interaction term (FR-024b)
    interaction_term: float = Field(
        description="Delta_3 - (Delta_1 + Delta_2). If |interaction| > 0.05, effects not independent."
    )
    interaction_significant: bool = Field(
        description="True if |interaction_term| > 0.05"
    )

    target_model: str
    observer_model: str
    created_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
```

**Purpose**:
- Store Experiment 4 results (three-condition test)
- Enable template marker vs REASONINGBANK effect separation

---

### 10. Experiment Metadata (`experiments`)

**Purpose**: Link experiment to exact prompt configurations and track execution

**Pydantic Model**:
```python
class ModelVersionDecision(str, Enum):
    ABORT = "ABORT"
    CONTINUE = "CONTINUE"
    IGNORE = "IGNORE"

class ExperimentMetadata(BaseModel):
    experiment_id: str = Field(description="Unique experiment identifier (e.g., 'exp_001_baseline')")
    experiment_label: str = Field(description="Human-readable label (e.g., 'Experiment 1: Baseline Collection')")
    target_model: str
    observer_model: str
    start_timestamp: AwareDatetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    end_timestamp: AwareDatetime | None = None
    total_prompts: int = Field(ge=0)
    total_cost: float = Field(ge=0.0, description="Total API cost in USD (FR-028: tracking only)")
    stages_completed: list[str] = Field(default_factory=list)

    # Prompt configuration references
    compliance_prompt_id: UUID = Field(description="References Prompt Configuration for compliance_classification")
    pre_eval_prompt_id: UUID = Field(description="References Prompt Configuration for pre_eval")
    post_eval_prompt_id: UUID = Field(description="References Prompt Configuration for post_eval")

    # Model version tracking (FR-032)
    model_version_change_decision: ModelVersionDecision | None = Field(
        description="If model version changed mid-experiment, user decision on how to handle"
    )
```

**Purpose**:
- Single metadata record per experiment run
- Links to exact prompt configurations used
- Cost tracking (FR-028)
- Model version change handling (FR-032)

---

## Pipeline Interfaces

### Source Protocol

```python
from typing import Protocol, Iterable

class Source(Protocol):
    """
    Data source for pipeline (e.g., load prompts from datasets).

    FR-033: Composable pipeline architecture requires source/sink interfaces.
    """

    def read(self) -> Iterable[dict]:
        """
        Yield items from source.

        Returns:
            Iterator over dictionaries (prompt data)

        Raises:
            ConfigurationError: If source unavailable or corrupted
        """
        ...
```

### Sink Protocol

```python
class Sink(Protocol):
    """
    Data sink for pipeline (e.g., write to ArangoDB collection).

    FR-033: Composable pipeline architecture requires source/sink interfaces.
    FR-035: ArangoDB operations are INSERT only (immutable).
    """

    def write(self, item: dict) -> None:
        """
        Write item to sink.

        Args:
            item: Dictionary matching collection schema

        Raises:
            ValidationError: If item fails Pydantic validation
            StorageError: If database write fails
        """
        ...
```

### Stage Protocol

```python
class Stage(Protocol):
    """
    Pipeline transformation stage (e.g., add evaluation results to prompt).

    FR-033: Composable stages enable Exp1→Exp2→Exp3→Exp4 pipeline.
    """

    def process(self, item: dict) -> dict:
        """
        Transform item (add evaluation results, classify compliance, etc.).

        Args:
            item: Input dictionary

        Returns:
            Transformed dictionary

        Raises:
            EvaluationError: If LLM API call fails
            ConfigurationError: If required configuration missing
        """
        ...
```

---

## Validation Rules

### Immutability Enforcement

**FR-035**: All collections are INSERT-only. Application layer code MUST NOT contain:
- `db.collection.update(...)`
- `db.collection.replace(...)`
- `db.collection.delete(...)`

Immutability enforced via code review and integration tests verifying no UPDATE/DELETE operations.

### Timestamp Format

**FR-039**: All timestamps use ISO 8601 with Z suffix (UTC timezone).

Pydantic `AwareDatetime` enforces this:
```python
from pydantic import AwareDatetime

# Valid:   "2025-10-22T14:23:45Z"
# Invalid: "2025-10-22T14:23:45" (missing timezone)
```

### Unique Constraints

**FR-003d**: `prompt_configurations` collection enforces uniqueness on `(prompt_type, version)` via ArangoDB hash index.

Implementation handles conflicts:
```python
# Query before insert (idempotent)
existing = db.query(
    "FOR p IN prompt_configurations FILTER p.prompt_type == @type AND p.version == @ver RETURN p",
    bind_vars={"type": prompt_type, "ver": version}
)

if len(existing) == 0:
    db.insert(new_config)  # No conflict
elif len(existing) == 1:
    return existing[0]["prompt_id"]  # Already initialized
else:
    raise ConfigurationError(f"Database corrupted: {len(existing)} configs found for ({prompt_type}, {version})")
```

---

## Error Types

### ConfigurationError

```python
class ConfigurationError(Exception):
    """
    Raised when system configuration is invalid or corrupted.

    Examples:
    - Fixture file checksum mismatch (FR-356-362)
    - Prompt configuration uniqueness violation (FR-003d)
    - Required environment variable missing
    - Dataset file not found
    """
    pass
```

### ValidationError

```python
class ValidationError(Exception):
    """
    Raised when data fails Pydantic schema validation.

    Examples:
    - Timestamp missing timezone (FR-039 violation)
    - F-score outside [0.0, 1.0] range
    - Required field missing
    """
    pass
```

### EvaluationError

```python
class EvaluationError(Exception):
    """
    Raised when LLM evaluation fails.

    Examples:
    - OpenRouter API timeout
    - Model unavailable
    - Response parsing failure
    - Cache write failure
    """
    pass
```

### ModelVersionChangedError

```python
class ModelVersionChangedError(Exception):
    """
    Raised when model version changes between strides (FR-032).

    Triggers PAUSE → user decision flow (ABORT/CONTINUE/IGNORE).
    """
    pass
```

---

## Summary

**Collections**: 10 (all INSERT-only, immutable)
**Protocols**: 3 (Source, Sink, Stage for pipeline composability)
**Error Types**: 4 (ConfigurationError, ValidationError, EvaluationError, ModelVersionChangedError)

**Constitution compliance**:
- Fail-fast error handling (no silent degradation)
- Immutable storage (INSERT-only)
- Type safety (Pydantic models with validation)
- Empirical integrity (cost tracking, timestamps, model versions)

Ready for Phase 1 contract generation.
