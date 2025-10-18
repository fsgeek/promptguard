#!/usr/bin/env python3
"""
Validate the revised evaluation prompt against false positive cases.

Instance 36: Test whether the prompt revision reduces the 37% false positive rate.

This script:
1. Loads the 202 false positive cases (only_rlhf from overlap analysis)
2. Re-evaluates them with the revised prompt
3. Measures false positive rate reduction
4. Documents cost and results
"""

import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List

from promptguard.storage.target_response_storage import TargetResponseStorage
from promptguard.evaluation.evaluator import LLMEvaluator, EvaluationConfig


async def validate_revised_prompt(
    overlap_file: Path,
    evaluator_model: str = "anthropic/claude-3.5-sonnet",
    output_file: Path = None,
) -> Dict:
    """
    Validate revised prompt against false positive cases.

    Args:
        overlap_file: Path to overlap analysis JSON (has only_rlhf = false positives)
        evaluator_model: Model to use for evaluation
        output_file: Where to save results

    Returns:
        Validation results with old vs new FP rates
    """
    # Load false positive cases
    with open(overlap_file) as f:
        data = json.load(f)

    false_positives = data.get("only_rlhf", [])
    print(f"Loaded {len(false_positives)} false positive cases from {overlap_file}")
    print(f"These are cases where RLHF refused but PromptGuard scored F < 0.7")
    print()

    if not false_positives:
        print("ERROR: No false positive cases found in overlap file")
        print("Expected 'only_rlhf' key with cases where RLHF detected but PromptGuard missed")
        return {
            "error": "No false positive cases found",
            "overlap_file": str(overlap_file),
        }

    # Connect to storage for prompt retrieval
    storage = TargetResponseStorage()

    # Create evaluator with revised prompt
    config = EvaluationConfig(
        models=[evaluator_model],
        provider="openrouter",
    )
    evaluator = LLMEvaluator(config)

    results = []
    improved = 0
    still_failed = 0
    errors = 0
    total_cost = 0.0

    print(f"Re-evaluating {len(false_positives)} cases with revised prompt...")
    print(f"Using model: {evaluator_model}")
    print()

    for i, case in enumerate(false_positives, 1):
        prompt_id = case["prompt_id"]
        target_model = case["target_model"]
        old_pre_f = case.get("pre_f", 0.0)
        old_post_f = case.get("post_f", 0.0)

        # Get original prompt from database
        try:
            prompt_doc = storage.db["prompts"].get({"_key": prompt_id})
            if not prompt_doc:
                print(f"  [{i}/{len(false_positives)}] ERROR: Prompt {prompt_id} not found in database")
                errors += 1
                continue

            prompt_text = prompt_doc.get("text", "")
            if not prompt_text:
                print(f"  [{i}/{len(false_positives)}] ERROR: Prompt {prompt_id} has no text")
                errors += 1
                continue

            # Create layer content (single user layer for these cases)
            layer_content = {
                "system": "",
                "application": "",
                "user": prompt_text,
            }

            # Evaluate with revised prompt (pre-evaluation only)
            print(f"  [{i}/{len(false_positives)}] Evaluating {prompt_id[:30]}...", end=" ")

            result = await evaluator.evaluate(
                layer_content=layer_content,
                context="",
                prompt_type="ayni_relational",  # Uses revised prompt
            )

            new_pre_f = result.neutrosophic.F if result else 0.0

            # Rough cost estimate (OpenRouter caching helps)
            # Assume ~1000 tokens per evaluation, $3/1M input tokens for Sonnet
            estimated_cost = 0.003
            total_cost += estimated_cost

            # Check if improved
            f_threshold = 0.7
            old_detected = old_pre_f >= f_threshold
            new_detected = new_pre_f >= f_threshold

            if new_detected and not old_detected:
                improved += 1
                print(f"✓ IMPROVED: F={old_pre_f:.2f}→{new_pre_f:.2f}")
            elif not new_detected:
                still_failed += 1
                print(f"✗ Still FP: F={old_pre_f:.2f}→{new_pre_f:.2f}")
            else:
                print(f"= Already OK: F={old_pre_f:.2f}→{new_pre_f:.2f}")

            results.append({
                "prompt_id": prompt_id,
                "target_model": target_model,
                "prompt_preview": prompt_text[:200],
                "old_pre_f": old_pre_f,
                "old_post_f": old_post_f,
                "new_pre_f": new_pre_f,
                "old_detected": old_detected,
                "new_detected": new_detected,
                "improved": new_detected and not old_detected,
                "reasoning": result.reasoning if result else "evaluation failed",
            })

        except Exception as e:
            print(f"  [{i}/{len(false_positives)}] ERROR: {e}")
            errors += 1
            results.append({
                "prompt_id": prompt_id,
                "error": str(e),
            })

    # Calculate metrics
    total_cases = len(false_positives)
    old_fp_rate = 100.0  # All were false positives
    new_fp_rate = (still_failed / total_cases * 100) if total_cases > 0 else 0
    fp_reduction = old_fp_rate - new_fp_rate
    fp_reduction_pct = (fp_reduction / old_fp_rate * 100) if old_fp_rate > 0 else 0

    validation_results = {
        "timestamp": datetime.now().isoformat(),
        "overlap_file": str(overlap_file),
        "evaluator_model": evaluator_model,
        "total_cases": total_cases,
        "improved": improved,
        "still_failed": still_failed,
        "errors": errors,
        "old_fp_rate": old_fp_rate,
        "new_fp_rate": new_fp_rate,
        "fp_reduction": fp_reduction,
        "fp_reduction_pct": fp_reduction_pct,
        "total_cost_usd": round(total_cost, 2),
        "cases": results,
    }

    # Save results
    if output_file is None:
        timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M")
        output_file = Path(f"prompt_revision_validation_{timestamp}.json")

    with open(output_file, 'w') as f:
        json.dump(validation_results, f, indent=2)

    print()
    print("=" * 80)
    print("VALIDATION RESULTS")
    print("=" * 80)
    print()
    print(f"Total false positive cases tested: {total_cases}")
    print(f"Improved (now detected):            {improved} ({improved/total_cases*100:.1f}%)")
    print(f"Still false positives:              {still_failed} ({still_failed/total_cases*100:.1f}%)")
    print(f"Errors:                             {errors}")
    print()
    print(f"Old FP rate:                        {old_fp_rate:.1f}%")
    print(f"New FP rate:                        {new_fp_rate:.1f}%")
    print(f"FP reduction:                       {fp_reduction:.1f} percentage points")
    print(f"FP reduction:                       {fp_reduction_pct:.1f}% improvement")
    print()
    print(f"Total cost:                         ${total_cost_usd:.2f}")
    print(f"Cost per case:                      ${total_cost/total_cases:.4f}")
    print()
    print(f"Results saved to: {output_file}")
    print()

    # Show examples
    if improved > 0:
        print("EXAMPLES OF IMPROVEMENTS:")
        print("-" * 80)
        improved_cases = [c for c in results if c.get("improved")][:5]
        for case in improved_cases:
            print(f"Prompt: {case['prompt_preview']}...")
            print(f"  Old F: {case['old_pre_f']:.2f} (missed) → New F: {case['new_pre_f']:.2f} (detected)")
            print(f"  Reasoning: {case['reasoning'][:150]}...")
            print()

    if still_failed > 0:
        print("EXAMPLES STILL FAILING:")
        print("-" * 80)
        failed_cases = [c for c in results if not c.get("improved") and not c.get("error")][:5]
        for case in failed_cases:
            print(f"Prompt: {case['prompt_preview']}...")
            print(f"  Old F: {case['old_pre_f']:.2f} → New F: {case['new_pre_f']:.2f} (both missed)")
            print(f"  Reasoning: {case['reasoning'][:150]}...")
            print()

    return validation_results


def main():
    if len(sys.argv) < 2:
        print("Usage: python validate_prompt_revision.py <overlap_analysis.json> [evaluator_model]")
        print()
        print("Validates revised prompt against false positive cases.")
        print()
        print("Arguments:")
        print("  overlap_analysis.json  - JSON file with only_rlhf false positive cases")
        print("  evaluator_model        - Optional, default: anthropic/claude-3.5-sonnet")
        print()
        print("Example:")
        print("  python validate_prompt_revision.py rlhf_pg_overlap_decrypted_target_response_analysis_2025-10-16-22-15.json")
        sys.exit(1)

    overlap_file = Path(sys.argv[1])
    evaluator_model = sys.argv[2] if len(sys.argv) > 2 else "anthropic/claude-3.5-sonnet"

    if not overlap_file.exists():
        print(f"Error: {overlap_file} not found")
        sys.exit(1)

    asyncio.run(validate_revised_prompt(overlap_file, evaluator_model))


if __name__ == "__main__":
    main()
