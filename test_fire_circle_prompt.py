"""
Test Fire Circle Round 1 prompt format specifically.
"""

import asyncio
import os
from promptguard.evaluation.evaluator import LLMEvaluator
from promptguard.evaluation.fire_circle import FireCircleConfig, CircleSize, FailureMode

async def test_round1_prompt():
    """Test if Round 1 prompt format works."""

    config = FireCircleConfig(
        models=["anthropic/claude-3-haiku", "anthropic/claude-3.5-sonnet"],  # Need 2 minimum
        circle_size=CircleSize.SMALL,
        max_rounds=1,  # Only run Round 1
        failure_mode=FailureMode.STRICT,  # Fail on any error
        provider="openrouter"
    )

    evaluator = LLMEvaluator(config)

    print("Testing Fire Circle Round 1 prompt format...")
    print()

    try:
        result = await evaluator.evaluate_layer(
            layer_content="Please explain recursion in programming.",
            context="Please explain recursion in programming.",
            evaluation_prompt="Evaluate this for reciprocity violations"
        )

        print("✅ Round 1 prompt works!")
        print(f"Number of evaluations: {len(result)}")
        for eval in result:
            print(f"  {eval.model}: T={eval.truth}, I={eval.indeterminacy}, F={eval.falsehood}")
            print(f"  Reasoning: {eval.reasoning[:100]}...")

    except Exception as e:
        print(f"❌ Round 1 prompt failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set")
        exit(1)

    asyncio.run(test_round1_prompt())
