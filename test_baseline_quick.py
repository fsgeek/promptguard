#!/usr/bin/env python3
"""Quick test of baseline comparison with 2 prompts and 1 model."""

import asyncio
import json
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(__file__))

from test_baseline_comparison import BaselineExperiment, MODELS


async def main():
    """Run quick test."""
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        sys.exit(1)

    # Load just 2 prompts
    dataset_path = "/home/tony/projects/promptguard/datasets/encoding_attacks_external_n72.jsonl"
    with open(dataset_path, 'r') as f:
        dataset = [json.loads(line) for line in f][:2]

    print(f"Testing with {len(dataset)} prompts")
    print(f"Models: 1 (Claude Sonnet 4.5 only)")

    # Initialize experiment
    experiment = BaselineExperiment(api_key)

    # Test just Claude
    model_key = "claude_sonnet_4.5"
    model = MODELS[model_key]

    print(f"\nTesting {model['name']}...")

    results = []
    for prompt in dataset:
        print(f"\n  Prompt: {prompt['prompt_id']}")

        result = await experiment.evaluate_prompt_pair(
            model_key,
            prompt["prompt_id"],
            prompt["prompt_text"],
            prompt["encoding_technique"]
        )

        results.append(result)

        # Print results
        print(f"    Condition A (direct): detected={result['condition_a_direct']['detected']}")
        print(f"    Condition B (observer): detected={result['condition_b_observer']['detected']}")

    # Save results
    output = {
        "metadata": {
            "test": "quick_baseline_comparison",
            "prompts": len(dataset),
            "model": model['name']
        },
        "results": results,
        "total_cost_usd": experiment.total_cost
    }

    with open("baseline_quick_test.json", 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*60}")
    print(f"Quick test complete!")
    print(f"Cost: ${experiment.total_cost:.4f}")
    print(f"Results saved to: baseline_quick_test.json")


if __name__ == "__main__":
    asyncio.run(main())
