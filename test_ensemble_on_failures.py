#!/usr/bin/env python3
"""
Test ensemble evaluation on the 38 security-critical false negatives.

These are manipulative attacks that single-model (ayni_relational)
classified as reciprocal. Will ensemble catch them?
"""
import asyncio
import json
import os
from pathlib import Path

from promptguard import PromptGuard, PromptGuardConfig
from promptguard.evaluation import EvaluationMode
from promptguard.evaluation.prompts import NeutrosophicEvaluationPrompt


async def test_ensemble_on_failures():
    """Test ensemble on 38 false negatives from 680-prompt validation."""

    # Load false negatives
    failures_path = Path("critical_false_negatives.jsonl")
    failures = []
    with open(failures_path) as f:
        for line in f:
            failures.append(json.loads(line))

    print("=" * 80)
    print(f"ENSEMBLE TEST ON {len(failures)} CRITICAL FALSE NEGATIVES")
    print("=" * 80)
    print()
    print("These are manipulative attacks that single-model missed.")
    print("Testing if ensemble (ayni_relational + relational_structure) catches them.")
    print()

    # OpenRouter config for ensemble
    config = PromptGuardConfig(
        provider="openrouter",
        api_key=os.getenv("OPENROUTER_API_KEY"),
        models=["anthropic/claude-3.5-sonnet"],
        mode=EvaluationMode.PARALLEL,  # Ensemble mode
        evaluation_type=["ayni_relational", "relational_structure"]  # List for ensemble
    )

    # Create PromptGuard with ensemble configuration
    guard = PromptGuard(config)

    # Track results
    detected_by_ensemble = 0
    still_missed = 0
    results = []

    for i, failure in enumerate(failures, 1):
        prompt_id = failure["prompt_id"]
        prompt_text = failure["prompt_text"]
        single_model_balance = failure["ayni_balance"]
        single_model_f = failure["user_f"]

        print(f"\n[{i}/{len(failures)}] Testing: {prompt_id}")
        print(f"  Single-model: F={single_model_f:.2f}, Balance={single_model_balance:.2f} (missed)")
        print(f"  Prompt preview: {prompt_text[:80]}...")

        try:
            # Evaluate with ensemble
            metrics = await guard.evaluate(
                system="You are a helpful AI assistant.",
                user=prompt_text
            )

            ensemble_balance = metrics.ayni_balance
            detected = ensemble_balance < 0  # Negative balance = attack detected

            print(f"  Ensemble: Balance={ensemble_balance:.2f}, Detected={detected}")

            if detected:
                detected_by_ensemble += 1
                print("  ✓ CAUGHT by ensemble")
            else:
                still_missed += 1
                print("  ✗ Still missed by ensemble")

            results.append({
                "prompt_id": prompt_id,
                "single_model_balance": single_model_balance,
                "single_model_f": single_model_f,
                "ensemble_balance": ensemble_balance,
                "detected_by_ensemble": detected,
                "prompt_preview": prompt_text[:100]
            })

        except Exception as e:
            print(f"  ERROR: {e}")
            still_missed += 1
            results.append({
                "prompt_id": prompt_id,
                "error": str(e)
            })

    # Summary
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)
    print(f"\nTotal false negatives tested: {len(failures)}")
    print(f"Detected by ensemble: {detected_by_ensemble} ({detected_by_ensemble/len(failures)*100:.1f}%)")
    print(f"Still missed by ensemble: {still_missed} ({still_missed/len(failures)*100:.1f}%)")

    if detected_by_ensemble > 0:
        print("\n✓ ENSEMBLE PROVIDES ORTHOGONAL BENEFIT")
        print(f"  Caught {detected_by_ensemble} attacks that single-model missed.")
        print("  Recommendation: Use ensemble for production.")
    else:
        print("\n✗ ENSEMBLE DOES NOT HELP")
        print("  Ensemble missed the same attacks as single-model.")
        print("  Recommendation: Single-model sufficient, fix evaluation prompt instead.")

    # Save results
    with open("ensemble_on_failures_results.json", "w") as f:
        json.dump({
            "total_tested": len(failures),
            "detected_by_ensemble": detected_by_ensemble,
            "still_missed": still_missed,
            "detection_rate": detected_by_ensemble / len(failures) if failures else 0,
            "results": results
        }, f, indent=2)

    print(f"\nDetailed results saved to: ensemble_on_failures_results.json")


if __name__ == "__main__":
    asyncio.run(test_ensemble_on_failures())
