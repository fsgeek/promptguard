#!/usr/bin/env python3
"""
Baseline Comparison - Parseable Models Only

Runs baseline comparison experiment with only models that can parse encoding attacks.

**Models (3 parseable):**
1. GPT-4.1 (frontier aligned)
2. DeepSeek R1 (reasoning model)
3. Llama 3.1 405B Instruct (open source aligned)

**Dataset:** Encoding attacks n=72

**Budget:** ~$4-6 (3 models × 72 attacks × 2 conditions × ~$0.001)
"""

import asyncio
import json
import logging
import os
import sys
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from tqdm.asyncio import tqdm

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('baseline_comparison_parseable.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Model configurations (parseable models only)
MODELS = {
    "gpt_4.1": {
        "id": "openai/gpt-4.1",
        "name": "GPT-4.1",
        "type": "frontier_aligned",
        "cost_per_1m_input": 2.50,
        "cost_per_1m_output": 10.00
    },
    "deepseek_r1": {
        "id": "deepseek/deepseek-r1",
        "name": "DeepSeek R1",
        "type": "reasoning",
        "cost_per_1m_input": 0.55,
        "cost_per_1m_output": 2.19
    },
    "llama_3.1_405b_instruct": {
        "id": "meta-llama/llama-3.1-405b-instruct",
        "name": "Llama 3.1 405B Instruct",
        "type": "open_source_aligned",
        "cost_per_1m_input": 3.00,
        "cost_per_1m_output": 3.00
    }
}

# Import the fixed experiment class
from test_baseline_comparison import BaselineExperiment


async def main():
    """Run baseline comparison experiment with parseable models only."""
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        sys.exit(1)

    # Initialize experiment
    experiment = BaselineExperiment(api_key)

    # Override MODELS in the experiment instance to use only parseable models
    # This is a bit hacky but avoids duplicating all the code
    import test_baseline_comparison
    original_models = test_baseline_comparison.MODELS
    test_baseline_comparison.MODELS = MODELS

    # Dataset path
    dataset_path = "/home/tony/projects/promptguard/datasets/encoding_attacks_external_n72.jsonl"

    # Run experiment with all 72 attacks
    logger.info("Starting baseline comparison experiment (parseable models only)")
    logger.info(f"Models: {len(MODELS)}")
    logger.info(f"Dataset: {dataset_path}")

    try:
        results = await experiment.run_experiment(dataset_path)

        # Save results
        output_path = "baseline_comparison_parseable_results.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"\n{'='*60}")
        logger.info("EXPERIMENT COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Results saved to: {output_path}")
        logger.info(f"Total cost: ${results['total_cost_usd']:.4f}")
        logger.info(f"\nOverall Summary:")
        logger.info(f"  Total evaluations: {results['summary']['overall']['total_evaluations']}")
        logger.info(f"  Condition A (Model alone): {results['summary']['overall']['condition_a_detection_rate']:.1%}")
        logger.info(f"  Condition B (Model + Observer): {results['summary']['overall']['condition_b_detection_rate']:.1%}")
        logger.info(f"  Marginal improvement: {results['summary']['overall']['marginal_improvement']:.1%}")

        logger.info(f"\nPer-Model Summary:")
        for model_name, stats in results['summary']['by_model'].items():
            logger.info(f"\n  {model_name}:")
            logger.info(f"    Condition A: {stats['condition_a_detection_rate']:.1%} ({stats['condition_a_detected']}/{stats['total_attacks'] - stats['condition_a_errors']})")
            logger.info(f"    Condition B: {stats['condition_b_detection_rate']:.1%} ({stats['condition_b_detected']}/{stats['total_attacks'] - stats['condition_b_errors']})")
            logger.info(f"    Improvement: {stats['marginal_improvement_pct']:+.1f}%")
            if stats['condition_a_errors'] > 0 or stats['condition_b_errors'] > 0:
                logger.info(f"    Errors: A={stats['condition_a_errors']}, B={stats['condition_b_errors']}")

    finally:
        # Restore original models
        test_baseline_comparison.MODELS = original_models


if __name__ == "__main__":
    asyncio.run(main())
