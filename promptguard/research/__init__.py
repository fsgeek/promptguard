"""
PromptGuard Research Module

This module provides data structures and tools for capturing evaluation data
in a systematic format for research analysis.

The core design captures "trust trajectories" - how neutrosophic values (T/I/F)
and trust metrics change through the evaluation pipeline. This enables studying
whether manipulation manifests as derivative changes (rate of change) rather than
absolute values.

Key insight: A manipulative prompt might pass front-end evaluation (looks reciprocal)
but cause trajectory shifts in the response phase. By recording both pre and post
evaluations, we can detect manipulation through derivative analysis.

Example usage:
    from promptguard.research import EvaluationRecorder, EvaluationRecord, RunMetadata

    recorder = EvaluationRecorder(Path("research_data/run_001.jsonl"))

    record = EvaluationRecord(
        run_metadata=RunMetadata(
            run_id="exp_001",
            timestamp="2025-01-15T10:30:00Z",
            pipeline_mode="both",
            model_pre="anthropic/claude-3.5-sonnet",
            model_post="anthropic/claude-3.5-sonnet",
            evaluation_prompt_version="v1.2",
            dataset_source="extractive_prompts_dataset.json",
            schema_version="1.0.0"
        ),
        prompt=PromptData(...),
        pre_evaluation=PreEvaluation(...),
        response=ResponseData(...),
        post_evaluation=PostEvaluation(...),
        deltas=EvaluationDeltas(...),
        outcome=EvaluationOutcome(...)
    )

    recorder.record(record)
"""

from .schema import (
    RunMetadata,
    PromptData,
    NeutrosophicValues,
    TrustField,
    PreEvaluation,
    ResponseData,
    PostEvaluation,
    EvaluationDeltas,
    EvaluationOutcome,
    EvaluationRecord,
)

from .recorder import EvaluationRecorder

__all__ = [
    "RunMetadata",
    "PromptData",
    "NeutrosophicValues",
    "TrustField",
    "PreEvaluation",
    "ResponseData",
    "PostEvaluation",
    "EvaluationDeltas",
    "EvaluationOutcome",
    "EvaluationRecord",
    "EvaluationRecorder",
]
