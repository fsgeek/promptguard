"""
Test Priority 1A: Trust Delta Thresholds

Tests whether balance delta detection catches polite extraction attacks
that absolute thresholds miss.

Instance 11 finding: Post-response evaluation caught only 1/9 (11%) polite
extraction attacks. Delta signals existed (e.g., ΔT=-0.7) but were ignored
by decision logic.

Instance 12 implementation: Added trust_delta parameter to _make_decision:
- ΔTrust < -0.7: reject (trust collapse)
- ΔTrust < -0.5: flag (trust degradation)

This script validates whether delta thresholds improve detection.
"""

import asyncio
import json
import os
from promptguard.research.pipeline import EvaluationPipeline, PipelineMode, GeneratorConfig
from promptguard.research.recorder import EvaluationRecorder
from promptguard.research.schema import PromptData, RunMetadata
from promptguard.research.post_evaluator import PostResponseEvaluator
from promptguard.promptguard import PromptGuard


async def test_delta_detection():
    """
    Run BOTH mode pipeline on 9 polite extraction prompts.

    Compare:
    - Baseline (absolute thresholds only): 11% detection
    - With delta thresholds: ?% detection
    """

    # Load test prompts
    with open("task3_polite_extraction_prompts.json") as f:
        test_prompts = json.load(f)

    # Limit to first 3 for quick test
    test_prompts = test_prompts[:3]

    # Setup
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        return

    # Configure pipeline
    generator_config = GeneratorConfig(
        model="anthropic/claude-3.5-sonnet",
        provider="openrouter",
        api_key=api_key,
        max_tokens=500,
        temperature=0.7,
    )

    from datetime import datetime

    run_metadata = RunMetadata(
        run_id="delta_threshold_test",
        timestamp=datetime.now().isoformat(),
        pipeline_mode="both",
        model_pre="anthropic/claude-3.5-sonnet",
        model_post="anthropic/claude-3.5-sonnet",
        evaluation_prompt_version="1.0",
        dataset_source="task3_polite_extraction_prompts.json",
    )

    # Initialize evaluators
    pre_evaluator = PromptGuard(
        api_key=api_key,
        provider="openrouter",
        model="anthropic/claude-3.5-sonnet",
    )

    post_evaluator = PostResponseEvaluator(
        evaluator_model="anthropic/claude-3.5-sonnet",
        api_key=api_key,
        provider="openrouter",
    )

    # Create recorder
    recorder = EvaluationRecorder("delta_threshold_results.jsonl")

    # Create pipeline
    pipeline = EvaluationPipeline(
        mode=PipelineMode.BOTH,
        recorder=recorder,
        generator_config=generator_config,
        run_metadata=run_metadata,
        pre_evaluator=pre_evaluator,
        post_evaluator=post_evaluator,
    )

    # Run evaluation
    results = []
    for test_prompt in test_prompts:
        print(f"\nEvaluating: {test_prompt['id']}")

        prompt_data = PromptData(
            prompt_id=test_prompt["id"],
            layers={
                "system": test_prompt["system"],
                "user": test_prompt["prompt"],
            },
            ground_truth_label=test_prompt["ground_truth"],
        )

        try:
            record = await pipeline.evaluate(prompt_data)
            results.append(record)

            # Print key metrics
            if record.pre_evaluation and record.post_evaluation:
                pre_balance = record.pre_evaluation.trust_field.balance
                post_balance = record.post_evaluation.trust_field_response
                delta = post_balance - pre_balance

                print(f"  Pre-balance: {pre_balance:.2f}")
                print(f"  Post-balance: {post_balance:.2f}")
                print(f"  Delta: {delta:.2f}")
                print(f"  Violations: {record.post_evaluation.detected_violations}")
                print(f"  Decision: {record.post_evaluation.decision}")
                print(f"  Outcome: {record.outcome.detection_category}")

        except Exception as e:
            print(f"  ERROR: {e}")

    # Analyze results
    print("\n" + "="*60)
    print("RESULTS SUMMARY")
    print("="*60)

    detected_count = sum(
        1 for r in results
        if r.post_evaluation and r.post_evaluation.decision in ["reject", "flag"]
    )

    print(f"\nPolite extraction attacks: {len(results)}")
    print(f"Detected (reject/flag): {detected_count}")
    print(f"Detection rate: {detected_count/len(results)*100:.1f}%")

    # Show delta-based detections
    delta_detections = [
        r for r in results
        if r.post_evaluation
        and ("trust_collapse" in r.post_evaluation.detected_violations
             or "trust_degradation" in r.post_evaluation.detected_violations)
    ]

    print(f"\nDelta-based detections: {len(delta_detections)}")
    for r in delta_detections:
        pre_bal = r.pre_evaluation.trust_field.balance
        post_bal = r.post_evaluation.trust_field_response
        delta = post_bal - pre_bal
        print(f"  {r.prompt.prompt_id}: Δ={delta:.2f}, decision={r.post_evaluation.decision}")


if __name__ == "__main__":
    asyncio.run(test_delta_detection())
