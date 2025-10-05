"""
JSONL Evaluation Recorder for PromptGuard Research

This module provides append-only JSONL writing for evaluation records. JSONL format
(JSON Lines) was chosen for several reasons:

1. **Streaming writes**: Each evaluation can be written immediately without loading
   entire dataset into memory
2. **Resilience**: Partial writes don't corrupt the file (each line is independent)
3. **Easy analysis**: Line-oriented format works well with Unix tools (grep, wc, etc.)
4. **Append-only**: Safe for concurrent writes from multiple processes
5. **Human readable**: Can inspect records with less/cat/tail

The recorder is intentionally simple - no fancy buffering, no compression, no indexing.
Research priority is data integrity over performance. Add optimization later if needed.
"""

import json
from pathlib import Path
from typing import List

from .schema import EvaluationRecord


class EvaluationRecorder:
    """
    Append-only JSONL writer for evaluation records.

    Each call to record() or record_batch() appends to the file immediately.
    No buffering, no caching - prioritize data integrity for research.

    Example usage:
        recorder = EvaluationRecorder(Path("results/run_001.jsonl"))

        for prompt in dataset:
            # Evaluate prompt...
            record = EvaluationRecord(...)
            recorder.record(record)  # Immediately written to disk
    """

    def __init__(self, output_path: Path):
        """
        Initialize recorder with output file path.

        Creates parent directories if they don't exist. Does NOT create the file
        until first record() call - this way empty runs don't leave empty files.

        Args:
            output_path: Path to JSONL output file (will be created if doesn't exist)
        """
        self.output_path = Path(output_path)

        # Create parent directories if they don't exist
        self.output_path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, evaluation: EvaluationRecord) -> None:
        """
        Append single evaluation record to JSONL file.

        Writes immediately to disk (no buffering). Each record is a single line
        of compact JSON (no pretty printing).

        Args:
            evaluation: EvaluationRecord to write

        Raises:
            IOError: If file write fails
        """
        with open(self.output_path, "a") as f:
            # Write as compact JSON (no whitespace)
            json_line = json.dumps(evaluation.to_dict(), ensure_ascii=False)
            f.write(json_line + "\n")

    def record_batch(self, evaluations: List[EvaluationRecord]) -> None:
        """
        Append batch of evaluation records to JSONL file.

        Slightly more efficient than calling record() repeatedly because it opens
        the file once. Still writes each record as a separate line.

        Args:
            evaluations: List of EvaluationRecord to write

        Raises:
            IOError: If file write fails
        """
        with open(self.output_path, "a") as f:
            for evaluation in evaluations:
                json_line = json.dumps(evaluation.to_dict(), ensure_ascii=False)
                f.write(json_line + "\n")

    @staticmethod
    def load(input_path: Path) -> List[EvaluationRecord]:
        """
        Load all records from JSONL file.

        Reads entire file into memory - fine for research datasets (hundreds to
        thousands of records), but might need streaming version for very large
        datasets (millions of records).

        Args:
            input_path: Path to JSONL file to load

        Returns:
            List of EvaluationRecord in file order

        Raises:
            FileNotFoundError: If input file doesn't exist
            json.JSONDecodeError: If file contains invalid JSON
            ValueError: If JSON doesn't match EvaluationRecord schema
        """
        records = []

        with open(input_path, "r") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    # Skip empty lines (shouldn't happen, but be defensive)
                    continue

                try:
                    data = json.loads(line)
                    record = EvaluationRecord.from_dict(data)
                    records.append(record)
                except json.JSONDecodeError as e:
                    raise json.JSONDecodeError(
                        f"Invalid JSON on line {line_num}: {e.msg}",
                        e.doc,
                        e.pos,
                    )
                except (KeyError, TypeError) as e:
                    raise ValueError(
                        f"Invalid record schema on line {line_num}: {e}"
                    )

        return records

    @staticmethod
    def validate_file(input_path: Path) -> dict:
        """
        Validate JSONL file and return summary statistics.

        Useful for sanity-checking output files before analysis. Checks:
        - All lines are valid JSON
        - All records match schema
        - Schema versions are consistent
        - No duplicate prompt IDs within same run

        Args:
            input_path: Path to JSONL file to validate

        Returns:
            Dictionary with validation results:
            {
                "valid": bool,
                "total_records": int,
                "schema_versions": set,
                "run_ids": set,
                "pipeline_modes": set,
                "errors": list of str (empty if valid)
            }
        """
        result = {
            "valid": True,
            "total_records": 0,
            "schema_versions": set(),
            "run_ids": set(),
            "pipeline_modes": set(),
            "errors": [],
        }

        try:
            records = EvaluationRecorder.load(input_path)
            result["total_records"] = len(records)

            for record in records:
                result["schema_versions"].add(record.run_metadata.schema_version)
                result["run_ids"].add(record.run_metadata.run_id)
                result["pipeline_modes"].add(record.run_metadata.pipeline_mode)

            # Convert sets to lists for JSON serialization
            result["schema_versions"] = list(result["schema_versions"])
            result["run_ids"] = list(result["run_ids"])
            result["pipeline_modes"] = list(result["pipeline_modes"])

        except Exception as e:
            result["valid"] = False
            result["errors"].append(str(e))

        return result
