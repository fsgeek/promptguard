"""
Prompt loading utilities for validation framework.

Loads all 680 prompts from three datasets into memory (research.md decision).
"""

import json
from pathlib import Path
from typing import Any
from uuid import uuid4


def load_all_prompts(datasets_dir: str = "datasets") -> list[dict[str, Any]]:
    """
    Load all 680 prompts from three datasets.

    Args:
        datasets_dir: Path to datasets directory (default: "datasets")

    Returns:
        List of 680 prompt dictionaries with:
        - prompt_id (UUID)
        - prompt_text
        - label (manipulative | reciprocal)
        - source_dataset (benign_malicious | or_bench | extractive)
        - stride_number (0 for original 680)

    Raises:
        ConfigurationError: If datasets missing or wrong count
    """
    from scripts.validation.common.errors import ConfigurationError

    base_path = Path(datasets_dir)
    prompts = []

    # Dataset configurations
    datasets = [
        {"file": "benign_malicious.json", "expected": 500, "name": "benign_malicious"},
        {"file": "or_bench_sample.json", "expected": 100, "name": "or_bench"},
        {"file": "extractive_prompts_dataset.json", "expected": 80, "name": "extractive"},
    ]

    for dataset_config in datasets:
        file_path = base_path / dataset_config["file"]

        if not file_path.exists():
            raise ConfigurationError(f"Dataset not found: {file_path}")

        try:
            with open(file_path) as f:
                raw_data = json.load(f)
        except json.JSONDecodeError as e:
            raise ConfigurationError(f"Invalid JSON in {file_path}: {e}")

        # Extract prompts array from wrapper structure
        if isinstance(raw_data, dict) and "prompts" in raw_data:
            data = raw_data["prompts"]
        elif isinstance(raw_data, list):
            data = raw_data
        else:
            raise ConfigurationError(f"{file_path}: invalid format (expected list or dict with 'prompts' key)")

        # Validate count
        if len(data) != dataset_config["expected"]:
            raise ConfigurationError(
                f"{file_path}: expected {dataset_config['expected']} prompts, "
                f"found {len(data)}"
            )

        # Transform to standard format
        for item in data:
            # Handle nested content structure
            if "content" in item and isinstance(item["content"], dict):
                prompt_text = item["content"].get("prompt", "")
            else:
                prompt_text = item.get("prompt", item.get("text", ""))

            prompts.append({
                "prompt_id": str(uuid4()),
                "prompt_text": prompt_text,
                "label": item.get("label", "unknown"),
                "source_dataset": dataset_config["name"],
                "stride_number": 0,  # Original 680 prompts
            })

    # Final validation
    if len(prompts) != 680:
        raise ConfigurationError(
            f"Expected 680 prompts total, loaded {len(prompts)}"
        )

    return prompts


def get_remaining_prompts(
    all_prompts: list[dict[str, Any]],
    experiment_id: str
) -> list[dict[str, Any]]:
    """
    Resume experiment by excluding already-processed prompts (research.md decision).

    Args:
        all_prompts: Complete list of 680 prompts
        experiment_id: Experiment identifier for checkpoint query

    Returns:
        List of prompts not yet processed

    Raises:
        ConfigurationError: If checkpoint query fails
    """
    from scripts.validation.utils.arango_client import get_completed_prompt_ids

    # Query ArangoDB for completed prompt_ids
    completed_ids = get_completed_prompt_ids(experiment_id)

    # Filter to remaining prompts only
    remaining = [p for p in all_prompts if p["prompt_id"] not in completed_ids]

    return remaining
