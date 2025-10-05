"""
Evaluation Data Schema for PromptGuard Research

This module defines the data structures for capturing evaluation results in a
systematic, analyzable format. The schema is designed around the "trust trajectory"
hypothesis: manipulation detection may be more effective by analyzing how T/I/F values
change through the pipeline rather than examining absolute values at a single point.

## Schema Design Principles

1. **Trajectory Measurement**: Record neutrosophic values at multiple points (pre-evaluation
   of prompt, post-evaluation of response) to enable derivative analysis.

2. **Optional Fields**: Use Optional[] for pipeline stages that may not execute (e.g.,
   post_evaluation if pre-evaluation blocks the prompt).

3. **Per-Layer Granularity**: Pre-evaluation captures T/I/F per prompt layer (system, user,
   application) because trust violations may manifest differently at each layer.

4. **Delta Calculation**: Explicit delta fields quantify how much T/I/F values shifted
   from prompt to response, enabling correlation analysis with manipulation success.

5. **Schema Versioning**: RunMetadata includes schema_version to support evolution without
   breaking existing analysis pipelines.

## Why T/I/F Appears in Both Pre and Post

- **Pre-evaluation**: T/I/F values for each prompt layer (system, user, application, context)
  reveal the input's trust characteristics. A manipulative prompt might show low T, high F
  at the user layer but appear trustworthy overall due to system/application layers.

- **Post-evaluation**: T/I/F values for the generated response reveal whether the model's
  output maintains, degrades, or improves trust characteristics. A successful manipulation
  might show high ΔF (falsity increased) or negative ΔT (truth degraded).

- **Deltas**: The derivatives (delta_T, delta_I, delta_F, delta_trust) quantify the
  trajectory shift. Hypothesis: Manipulated responses show higher variance in deltas
  than genuine responses, even when absolute values appear acceptable.

## Schema Versioning Strategy

The schema_version field in RunMetadata follows semantic versioning:
- Major version: Breaking changes to required fields or field types
- Minor version: New optional fields added
- Patch version: Documentation or validation changes only

Current version: 1.0.0
"""

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional
import json


@dataclass
class RunMetadata:
    """
    Metadata about the evaluation run.

    Attributes:
        run_id: Unique identifier for this evaluation run (e.g., "exp_001_batch_01")
        timestamp: ISO 8601 timestamp of run start
        pipeline_mode: Which evaluation stages ran ("baseline" | "pre" | "post" | "both")
        model_pre: Model used for pre-evaluation (e.g., "anthropic/claude-3.5-sonnet")
        model_post: Model used for post-evaluation (None if pipeline_mode != "both" or "post")
        evaluation_prompt_version: Version of evaluation prompts used (for reproducibility)
        dataset_source: Source dataset filename or description
        schema_version: Version of this schema (semantic versioning)
    """
    run_id: str
    timestamp: str  # ISO 8601
    pipeline_mode: str  # baseline | pre | post | both
    model_pre: str
    model_post: Optional[str]
    evaluation_prompt_version: str
    dataset_source: str
    schema_version: str = "1.0.0"


@dataclass
class PromptData:
    """
    The prompt being evaluated.

    Attributes:
        prompt_id: Unique identifier within dataset (e.g., "extractive_023")
        ground_truth_label: Expected classification from dataset ("reciprocal" | "manipulative" | "extractive")
        layers: Prompt content by layer (keys: "system", "user", "application", "context")
    """
    prompt_id: str
    ground_truth_label: str  # reciprocal | manipulative | extractive
    layers: Dict[str, str]  # {system, user, application, context}


@dataclass
class NeutrosophicValues:
    """
    Neutrosophic logic triple representing trust characteristics.

    T (Truth/Trust): Degree to which content demonstrates reciprocal intent [0, 1]
    I (Indeterminacy): Ambiguity or uncertainty in intent [0, 1]
    F (Falsity): Degree of manipulative or extractive intent [0, 1]

    Note: T, I, F are independent and may not sum to 1 (neutrosophic logic allows overlap).
    """
    T: float  # Truth/Trust
    I: float  # Indeterminacy
    F: float  # Falsity


@dataclass
class TrustField:
    """
    Trust field metrics from Ayni evaluation.

    Attributes:
        established: Trust established by the prompt (sum of reciprocal signals)
        claimed: Trust claimed/extracted by the prompt (sum of extractive signals)
        balance: established - claimed (positive = reciprocal, negative = extractive)
    """
    established: float
    claimed: float
    balance: float


@dataclass
class PreEvaluation:
    """
    Pre-evaluation results (analyzing the prompt before response generation).

    This captures T/I/F values per prompt layer because trust violations may manifest
    differently at system vs user vs application layers. A manipulative prompt might
    appear trustworthy at the system layer but extractive at the user layer.

    Attributes:
        neutrosophic_values: T/I/F values for each prompt layer
        trust_field: Ayni trust field calculation
        ayni_balance: Overall reciprocity balance
        exchange_type: Classification ("reciprocal" | "manipulative" | "extractive")
        reasoning_trace: Optional LLM reasoning (if available)
        execution_time_ms: Time to complete pre-evaluation
        decision: Action taken ("pass" | "block" | "flag")
    """
    neutrosophic_values: Dict[str, NeutrosophicValues]  # per layer
    trust_field: TrustField
    ayni_balance: float
    exchange_type: str
    reasoning_trace: Optional[str]
    execution_time_ms: float
    decision: str  # pass | block | flag


@dataclass
class ResponseData:
    """
    The generated response from the model.

    Attributes:
        text: Full response text
        token_count: Number of tokens in response
        finish_reason: OpenRouter finish reason ("stop" | "length" | "content_filter")
        generation_time_ms: Time to generate response
        reasoning_trace: Optional reasoning tokens (if model supports it)
    """
    text: str
    token_count: int
    finish_reason: str
    generation_time_ms: float
    reasoning_trace: Optional[str]


@dataclass
class PostEvaluation:
    """
    Post-evaluation results (analyzing the response after generation).

    This captures T/I/F values of the response itself to enable derivative analysis.
    A manipulated response might show degraded T (truth) or elevated F (falsity)
    compared to the prompt's values.

    Attributes:
        neutrosophic_values: T/I/F values for the response
        trust_field_response: Trust field balance for the response
        role_consistency: How well response maintains stated role [0, 1]
        coherence_score: Logical coherence of response [0, 1]
        length_zscore: Response length z-score (detects unusual verbosity/terseness)
        detected_violations: List of specific violations found (e.g., ["role_reversal", "excessive_apology"])
        reasoning_quality: Quality of reasoning in response [0, 1]
        execution_time_ms: Time to complete post-evaluation
        decision: Action taken ("accept" | "reject" | "flag")
    """
    neutrosophic_values: NeutrosophicValues  # of response
    trust_field_response: float
    role_consistency: float
    coherence_score: float
    length_zscore: float
    detected_violations: List[str]
    reasoning_quality: float
    execution_time_ms: float
    decision: str  # accept | reject | flag


@dataclass
class EvaluationDeltas:
    """
    Derivatives quantifying trajectory changes from prompt to response.

    These deltas are the core of the trajectory hypothesis: manipulation may manifest
    as abnormal rate-of-change rather than abnormal absolute values.

    Calculation:
        delta_T = post.T - mean(pre.T across all layers)
        delta_I = post.I - mean(pre.I across all layers)
        delta_F = post.F - mean(pre.F across all layers)
        delta_trust = post.trust_field_response - pre.trust_field.balance

    Attributes:
        delta_T: Change in Truth/Trust from prompt to response
        delta_I: Change in Indeterminacy from prompt to response
        delta_F: Change in Falsity from prompt to response
        delta_trust: Change in trust field balance from prompt to response
    """
    delta_T: float
    delta_I: float
    delta_F: float
    delta_trust: float


@dataclass
class EvaluationOutcome:
    """
    Ground truth outcome of the evaluation.

    Attributes:
        actual_manipulation_success: Did the manipulation succeed? (None if not manipulation)
        detection_category: Confusion matrix category
            - "tp": True positive (correctly detected manipulation)
            - "fp": False positive (flagged reciprocal as manipulation)
            - "tn": True negative (correctly passed reciprocal)
            - "fn": False negative (missed manipulation)
            - "unknown": Cannot determine (e.g., no ground truth)
    """
    actual_manipulation_success: Optional[bool]
    detection_category: str  # tp | fp | tn | fn | unknown


@dataclass
class EvaluationRecord:
    """
    Complete record of a single prompt evaluation.

    This is the top-level data structure written to JSONL. Each line in the output
    file is one serialized EvaluationRecord.

    Optional fields support partial pipeline runs:
        - pre_evaluation: None if pipeline_mode == "baseline" or "post"
        - response: None if pre_evaluation.decision == "block"
        - post_evaluation: None if pipeline_mode == "baseline" or "pre", or if no response
        - deltas: None if missing pre or post evaluation

    Attributes:
        run_metadata: Metadata about this evaluation run
        prompt: The prompt being evaluated
        pre_evaluation: Pre-evaluation results (optional)
        response: Generated response (optional)
        post_evaluation: Post-evaluation results (optional)
        deltas: Derivative calculations (optional)
        outcome: Ground truth outcome
    """
    run_metadata: RunMetadata
    prompt: PromptData
    pre_evaluation: Optional[PreEvaluation]
    response: Optional[ResponseData]
    post_evaluation: Optional[PostEvaluation]
    deltas: Optional[EvaluationDeltas]
    outcome: EvaluationOutcome

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "EvaluationRecord":
        """Reconstruct from dictionary (for loading from JSONL)."""
        # Reconstruct nested dataclasses
        run_metadata = RunMetadata(**data["run_metadata"])
        prompt = PromptData(**data["prompt"])

        pre_eval = None
        if data.get("pre_evaluation"):
            pre_data = data["pre_evaluation"]
            # Reconstruct neutrosophic values per layer
            neutro_values = {
                layer: NeutrosophicValues(**values)
                for layer, values in pre_data["neutrosophic_values"].items()
            }
            trust_field = TrustField(**pre_data["trust_field"])
            pre_eval = PreEvaluation(
                neutrosophic_values=neutro_values,
                trust_field=trust_field,
                ayni_balance=pre_data["ayni_balance"],
                exchange_type=pre_data["exchange_type"],
                reasoning_trace=pre_data.get("reasoning_trace"),
                execution_time_ms=pre_data["execution_time_ms"],
                decision=pre_data["decision"],
            )

        response = ResponseData(**data["response"]) if data.get("response") else None

        post_eval = None
        if data.get("post_evaluation"):
            post_data = data["post_evaluation"]
            neutro_values = NeutrosophicValues(**post_data["neutrosophic_values"])
            post_eval = PostEvaluation(
                neutrosophic_values=neutro_values,
                trust_field_response=post_data["trust_field_response"],
                role_consistency=post_data["role_consistency"],
                coherence_score=post_data["coherence_score"],
                length_zscore=post_data["length_zscore"],
                detected_violations=post_data["detected_violations"],
                reasoning_quality=post_data["reasoning_quality"],
                execution_time_ms=post_data["execution_time_ms"],
                decision=post_data["decision"],
            )

        deltas = EvaluationDeltas(**data["deltas"]) if data.get("deltas") else None
        outcome = EvaluationOutcome(**data["outcome"])

        return cls(
            run_metadata=run_metadata,
            prompt=prompt,
            pre_evaluation=pre_eval,
            response=response,
            post_evaluation=post_eval,
            deltas=deltas,
            outcome=outcome,
        )
