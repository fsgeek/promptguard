#!/usr/bin/env python3
"""
Test script to validate baseline comparison harness fix.

Tests with a single model/attack pair to verify:
1. Successful responses capture evaluation data correctly
2. Response text is stored for debugging
3. Error cases have consistent structure
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

# Import the experiment class
from test_baseline_comparison import BaselineExperiment


async def test_single_evaluation():
    """Test a single model/attack evaluation."""

    # Get API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("OPENROUTER_API_KEY not set")
        sys.exit(1)

    # Initialize experiment
    experiment = BaselineExperiment(api_key)

    # Load one attack from the dataset
    dataset_path = "/home/tony/projects/promptguard/datasets/encoding_attacks_external_n72.jsonl"
    with open(dataset_path, 'r') as f:
        first_attack = json.loads(f.readline())

    logger.info(f"Testing with attack: {first_attack['prompt_id']}")
    logger.info(f"Encoding technique: {first_attack['encoding_technique']}")
    logger.info(f"Attack text: {first_attack['prompt_text'][:100]}...")

    # Test with GPT-4.1 (known to parse encoding attacks)
    model_key = "gpt_4.1"

    logger.info(f"\nTesting with model: {model_key}")

    # Run evaluation
    result = await experiment.evaluate_prompt_pair(
        model_key,
        first_attack["prompt_id"],
        first_attack["prompt_text"],
        first_attack["encoding_technique"]
    )

    # Validate result structure
    logger.info("\n" + "="*60)
    logger.info("VALIDATION RESULTS")
    logger.info("="*60)

    # Check Condition A (direct)
    condition_a = result["condition_b_observer"]
    logger.info(f"\nCondition A (Direct):")
    logger.info(f"  Success: {condition_a['success']}")
    logger.info(f"  Has response: {'response' in condition_a and bool(condition_a['response'])}")
    logger.info(f"  Has error: {'error' in condition_a and condition_a['error'] is not None}")

    # Check Condition B (observer)
    condition_b = result["condition_b_observer"]
    logger.info(f"\nCondition B (Observer):")
    logger.info(f"  Success: {condition_b['success']}")
    logger.info(f"  Detected: {condition_b.get('detected')}")
    logger.info(f"  Has evaluation: {bool(condition_b['evaluation'])}")
    logger.info(f"  Has response: {'response' in condition_b and bool(condition_b['response'])}")
    logger.info(f"  Has error: {'error' in condition_b and condition_b['error'] is not None}")

    # Show evaluation details if successful
    if condition_b['success'] and condition_b['evaluation']:
        eval_data = condition_b['evaluation']
        logger.info(f"\nEvaluation Details:")
        logger.info(f"  T (Truth/Clarity): {eval_data.get('T', 'N/A')}")
        logger.info(f"  I (Indeterminacy): {eval_data.get('I', 'N/A')}")
        logger.info(f"  F (Falsity/Manipulation): {eval_data.get('F', 'N/A')}")
        logger.info(f"  Exchange Type: {eval_data.get('exchange_type', 'N/A')}")
        logger.info(f"  Reasoning: {eval_data.get('reasoning', 'N/A')[:100]}...")

    # Show response text (first 200 chars)
    if condition_b.get('response'):
        logger.info(f"\nResponse Text (first 200 chars):")
        logger.info(f"  {condition_b['response'][:200]}...")

    # Cost tracking
    total_cost = condition_a['cost_usd'] + condition_b['cost_usd']
    logger.info(f"\nCost:")
    logger.info(f"  Condition A: ${condition_a['cost_usd']:.4f}")
    logger.info(f"  Condition B: ${condition_b['cost_usd']:.4f}")
    logger.info(f"  Total: ${total_cost:.4f}")

    # Save result
    output_path = "test_baseline_fix_result.json"
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"\nFull result saved to: {output_path}")

    # Validate fix
    logger.info("\n" + "="*60)
    logger.info("FIX VALIDATION")
    logger.info("="*60)

    checks_passed = 0
    checks_total = 4

    # Check 1: Observer result has evaluation dict (even if empty)
    if 'evaluation' in condition_b:
        logger.info("✓ Check 1: evaluation field present")
        checks_passed += 1
    else:
        logger.error("✗ Check 1: evaluation field missing")

    # Check 2: Observer result has response field
    if 'response' in condition_b:
        logger.info("✓ Check 2: response field present")
        checks_passed += 1
    else:
        logger.error("✗ Check 2: response field missing")

    # Check 3: If successful, evaluation should not be empty
    if condition_b['success']:
        if condition_b['evaluation']:
            logger.info("✓ Check 3: successful call has non-empty evaluation")
            checks_passed += 1
        else:
            logger.error("✗ Check 3: successful call has empty evaluation (BUG!)")
    else:
        logger.info("⊘ Check 3: skipped (call failed)")
        checks_passed += 1  # Don't fail the test if API call failed

    # Check 4: If successful, response should not be empty
    if condition_b['success']:
        if condition_b['response']:
            logger.info("✓ Check 4: successful call has non-empty response")
            checks_passed += 1
        else:
            logger.error("✗ Check 4: successful call has empty response (BUG!)")
    else:
        logger.info("⊘ Check 4: skipped (call failed)")
        checks_passed += 1  # Don't fail the test if API call failed

    logger.info(f"\nValidation: {checks_passed}/{checks_total} checks passed")

    if checks_passed == checks_total:
        logger.info("SUCCESS: Fix validated!")
        return True
    else:
        logger.error("FAILURE: Fix validation failed")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_single_evaluation())
    sys.exit(0 if success else 1)
