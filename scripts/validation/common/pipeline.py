"""
Pipeline interfaces for composable validation framework.

These protocols define the contracts for Source, Sink, and Stage components
that enable composable experiment pipelines per FR-033.

Protocols use duck typing (PEP 544) - no ABC inheritance required.
"""

from typing import Protocol, Iterable, Any


class Source(Protocol):
    """
    Data source for pipeline (e.g., load prompts from datasets).

    FR-033: Composable pipeline architecture requires source/sink interfaces.

    Example implementations:
    - DatasetSource: Loads prompts from datasets/benign_malicious.json
    - ArangoSource: Queries prompts from ArangoDB collection
    - SampleSource: Random sample from existing prompts
    """

    def read(self) -> Iterable[dict[str, Any]]:
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

    def write(self, item: dict[str, Any]) -> None:
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

    def process(self, item: dict[str, Any]) -> dict[str, Any]:
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


def run_pipeline(source: Source, stages: list[Stage], sink: Sink) -> None:
    """
    Orchestrate pipeline execution: source → stages → sink.

    Args:
        source: Data source yielding items
        stages: List of transformation stages (applied sequentially)
        sink: Data sink for final output

    Raises:
        EvaluationError: If any stage raises during processing
        StorageError: If sink write fails
        ConfigurationError: If source/sink unavailable

    Example:
        >>> source = DatasetSource(["benign_malicious.json"])
        >>> stages = [BaselineEvaluationStage(), ComplianceClassificationStage()]
        >>> sink = ArangoSink(collection="baseline_responses")
        >>> run_pipeline(source, stages, sink)
    """
    for item in source.read():
        # Apply all stages sequentially
        for stage in stages:
            item = stage.process(item)

        # Write to sink
        sink.write(item)


class DatasetSource:
    """
    Load prompts from JSON dataset files.

    Implements Source protocol for reading datasets (benign_malicious, or_bench, extractive).
    """

    def __init__(self, dataset_paths: list[str]):
        """
        Args:
            dataset_paths: List of dataset file paths to load
        """
        self.dataset_paths = dataset_paths

    def read(self) -> Iterable[dict[str, Any]]:
        """
        Load prompts from all dataset files.

        Yields:
            Prompt dictionaries with: prompt_id, prompt_text, label, source_dataset

        Raises:
            FileNotFoundError: If any dataset file missing
            ConfigurationError: If JSON parsing fails
        """
        import json
        from pathlib import Path
        from uuid import uuid4

        for dataset_path in self.dataset_paths:
            path = Path(dataset_path)

            if not path.exists():
                from .errors import ConfigurationError
                raise ConfigurationError(f"Dataset not found: {dataset_path}")

            try:
                with open(path) as f:
                    data = json.load(f)
            except json.JSONDecodeError as e:
                from .errors import ConfigurationError
                raise ConfigurationError(f"Invalid JSON in {dataset_path}: {e}")

            # Determine source dataset from filename
            source_name = path.stem  # benign_malicious, or_bench_sample, extractive_prompts_dataset
            if "benign" in source_name:
                source = "benign_malicious"
            elif "bench" in source_name:
                source = "or_bench"
            elif "extract" in source_name:
                source = "extractive"
            else:
                source = "unknown"

            # Yield each prompt with metadata
            for item in data:
                yield {
                    "prompt_id": str(uuid4()),
                    "prompt_text": item.get("prompt", item.get("text", "")),
                    "label": item.get("label", "unknown"),
                    "source_dataset": source,
                    "stride_number": 0,  # Original 680 prompts
                }
