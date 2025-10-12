#!/usr/bin/env python3
"""
Test baseline comparison with a sample of 3 attacks and 2 models.

Budget: ~$0.03 (2 models × 3 attacks × 2 conditions × ~$0.002)
"""

import asyncio
import json
import logging
import os
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import the fixed experiment class
from test_baseline_comparison import BaselineExperiment


async def main():
    """Run baseline comparison with small sample."""
    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        sys.exit(1)

    # Initialize experiment
    experiment = BaselineExperiment(api_key)

    # Override to use only 2 models for faster testing
    import test_baseline_comparison
    original_models = test_baseline_comparison.MODELS
    test_baseline_comparison.MODELS = {
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
        }
    }

    # Dataset path
    dataset_path = "/home/tony/projects/promptguard/datasets/encoding_attacks_external_n72.jsonl"

    # Run experiment with sample_size=3
    logger.info("Starting baseline comparison sample test")
    logger.info(f"Models: 2 (GPT-4.1, DeepSeek R1)")
    logger.info(f"Sample size: 3 attacks")

    try:
        results = await experiment.run_experiment(dataset_path, sample_size=3)

        # Save results
        output_path = "baseline_comparison_sample_results.json"
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)

        logger.info(f"\n{'='*60}")
        logger.info("SAMPLE TEST COMPLETE")
        logger.info(f"{'='*60}")
        logger.info(f"Results saved to: {output_path}")
        logger.info(f"Total cost: ${results['total_cost_usd']:.4f}")

        # Show summary
        logger.info(f"\nOverall Summary:")
        logger.info(f"  Total evaluations: {results['summary']['overall']['total_evaluations']}")
        logger.info(f"  Condition A detections: {results['summary']['overall']['condition_a_detections']}")
        logger.info(f"  Condition B detections: {results['summary']['overall']['condition_b_detections']}")
        logger.info(f"  Condition A rate: {results['summary']['overall']['condition_a_detection_rate']:.1%}")
        logger.info(f"  Condition B rate: {results['summary']['overall']['condition_b_detection_rate']:.1%}")
        logger.info(f"  Marginal improvement: {results['summary']['overall']['marginal_improvement']:.1%}")

        logger.info(f"\nPer-Model Summary:")
        for model_name, stats in results['summary']['by_model'].items():
            logger.info(f"\n  {model_name}:")
            logger.info(f"    Total attacks: {stats['total_attacks']}")
            logger.info(f"    Condition A: {stats['condition_a_detection_rate']:.1%} ({stats['condition_a_detected']} detections, {stats['condition_a_errors']} errors)")
            logger.info(f"    Condition B: {stats['condition_b_detection_rate']:.1%} ({stats['condition_b_detected']} detections, {stats['condition_b_errors']} errors)")
            logger.info(f"    Improvement: {stats['marginal_improvement_pct']:+.1f}%")

        # Show a few example results
        logger.info(f"\nExample Results (first 2):")
        for i, result in enumerate(results['results'][:2], 1):
            logger.info(f"\n  Example {i}:")
            logger.info(f"    Attack: {result['prompt_id']} ({result['encoding_technique']})")
            logger.info(f"    Model: {result['model']}")
            logger.info(f"    Condition A detected: {result['condition_a_direct']['detected']}")
            logger.info(f"    Condition B detected: {result['condition_b_observer']['detected']}")
            if result['condition_b_observer']['evaluation']:
                eval_data = result['condition_b_observer']['evaluation']
                logger.info(f"    F score: {eval_data.get('F', 'N/A')}")
                logger.info(f"    Exchange type: {eval_data.get('exchange_type', 'N/A')}")

    finally:
        # Restore original models
        test_baseline_comparison.MODELS = original_models


if __name__ == "__main__":
    asyncio.run(main())
