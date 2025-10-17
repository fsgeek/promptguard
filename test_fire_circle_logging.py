"""
Test Fire Circle with full logging to see actual errors.
"""

import asyncio
import os
import logging
from promptguard.evaluation.evaluator import LLMEvaluator
from promptguard.evaluation.fire_circle import FireCircleConfig, CircleSize, FailureMode

# Enable ALL logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_with_logging():
    """Test Fire Circle with logging enabled."""

    config = FireCircleConfig(
        models=[
            "anthropic/claude-3.5-sonnet",
            "anthropic/claude-3-haiku",
            "google/gemini-2.0-flash-001"
        ],
        circle_size=CircleSize.SMALL,
        max_rounds=3,
        failure_mode=FailureMode.RESILIENT,
        pattern_threshold=0.5,
        min_viable_circle=2,
        provider="openrouter"
    )

    evaluator = LLMEvaluator(config)

    print("=" * 80)
    print("FIRE CIRCLE TEST WITH FULL LOGGING")
    print("=" * 80)

    try:
        result = await evaluator.evaluate_layer(
            layer_content="Please explain recursion in programming.",
            context="Please explain recursion in programming.",
            evaluation_prompt="Evaluate this for reciprocity violations"
        )

        print("\n✅ SUCCESS")
        print(f"Evaluations: {len(result)}")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set")
        exit(1)

    asyncio.run(test_with_logging())
