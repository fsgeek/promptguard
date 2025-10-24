"""
Pipeline interfaces for composable validation framework.

These protocols define the contracts for Source, Sink, and Stage components
that enable composable experiment pipelines per FR-033.

Protocols use duck typing (PEP 544) - no ABC inheritance required.
"""

from typing import Protocol, Iterable


class Source(Protocol):
    """
    Data source for pipeline (e.g., load prompts from datasets).

    FR-033: Composable pipeline architecture requires source/sink interfaces.

    Example implementations:
    - DatasetSource: Loads prompts from datasets/benign_malicious.json
    - ArangoSource: Queries prompts from ArangoDB collection
    - SampleSource: Random sample from existing prompts
    """

    def read(self) -> Iterable[dict]:
        """
        Yield items from source.

        Returns:
            Iterator over dictionaries (prompt data matching Prompt schema)

        Raises:
            ConfigurationError: If source unavailable or corrupted
            FileNotFoundError: If dataset file missing
        """
        ...


class Sink(Protocol):
    """
    Data sink for pipeline (e.g., write to ArangoDB collection).

    FR-033: Composable pipeline architecture requires source/sink interfaces.
    FR-035: ArangoDB operations are INSERT only (immutable).

    Example implementations:
    - ArangoSink: Writes to ArangoDB collection (INSERT only)
    - JSONLSink: Appends to JSONL file for archival
    - ConsoleSink: Prints to stdout for debugging
    """

    def write(self, item: dict) -> None:
        """
        Write item to sink.

        Args:
            item: Dictionary matching collection schema (e.g., Prompt, BaselineResponse)

        Raises:
            ValidationError: If item fails Pydantic validation
            StorageError: If database write fails
            OSError: If file write fails
        """
        ...


class Stage(Protocol):
    """
    Pipeline transformation stage (e.g., add evaluation results to prompt).

    FR-033: Composable stages enable Exp1→Exp2→Exp3→Exp4 pipeline.

    Example implementations:
    - BaselineEvaluationStage: Sends prompt to LLM, adds response
    - ComplianceClassificationStage: Adds comply/refuse classification
    - PreEvaluationStage: Adds PromptGuard F-score
    - PatternExtractionStage: Identifies attack patterns from false negatives
    """

    def process(self, item: dict) -> dict:
        """
        Transform item (add evaluation results, classify compliance, etc.).

        Args:
            item: Input dictionary (e.g., Prompt with prompt_id and prompt_text)

        Returns:
            Transformed dictionary (e.g., Prompt + BaselineResponse fields)

        Raises:
            EvaluationError: If LLM API call fails
            ConfigurationError: If required configuration missing (e.g., prompt template)
            ValidationError: If item missing required fields
        """
        ...


# Example usage pattern:
"""
from scripts.validation.common.pipeline import run_pipeline

# Experiment 1: Baseline collection
source = DatasetSource(["benign_malicious.json", "or_bench.json", "extractive.json"])
stages = [
    BaselineEvaluationStage(target_model="anthropic/claude-3.5-sonnet"),
    ComplianceClassificationStage(observer_model="anthropic/claude-3.5-sonnet")
]
sink = ArangoSink(collection="baseline_responses")

run_pipeline(source, stages, sink)

# Experiment 2: Pre-evaluation
source = ArangoSource(collection="prompts", experiment_id="exp_001_baseline")
stages = [
    PreEvaluationStage(observer_model="anthropic/claude-3.5-sonnet")
]
sink = ArangoSink(collection="pre_eval_results")

run_pipeline(source, stages, sink)
"""
