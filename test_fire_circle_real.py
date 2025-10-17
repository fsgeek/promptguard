"""
Test Fire Circle with real API calls.

This script validates that Fire Circle integration works end-to-end
with actual LLM API calls (not mocks).
"""

import asyncio
import os
from promptguard.evaluation.evaluator import LLMEvaluator
from promptguard.evaluation.fire_circle import FireCircleConfig, CircleSize, FailureMode

async def test_fire_circle_basic():
    """Test Fire Circle on a simple reciprocal prompt."""

    # Simple reciprocal prompt (should score low falsehood)
    prompt_content = "Please explain the concept of recursion in programming."

    # Configure Fire Circle with 3 reliable (cheap) models
    config = FireCircleConfig(
        models=[
            "anthropic/claude-3.5-sonnet",        # $3/1M tokens
            "anthropic/claude-3-haiku",           # $0.25/1M tokens
            "google/gemini-2.0-flash-001"         # $0.075/1M tokens
        ],
        circle_size=CircleSize.SMALL,
        max_rounds=3,
        failure_mode=FailureMode.RESILIENT,
        pattern_threshold=0.5,
        min_viable_circle=2,
        provider="openrouter"
    )

    # Create evaluator
    evaluator = LLMEvaluator(config)

    print("=" * 80)
    print("FIRE CIRCLE REAL API TEST")
    print("=" * 80)
    print(f"Prompt: {prompt_content}")
    print(f"Models: {config.models}")
    print(f"Circle Size: {config.circle_size.name}")
    print(f"Failure Mode: {config.failure_mode.value}")
    print("=" * 80)
    print()

    try:
        # Run Fire Circle evaluation
        print("Starting Fire Circle evaluation...")
        result = await evaluator.evaluate_layer(
            layer_content=prompt_content,
            context=prompt_content,
            evaluation_prompt="Evaluate this for reciprocity violations"
        )

        print(f"\n✅ Fire Circle completed successfully!")
        print(f"Number of evaluations: {len(result)}")
        print()

        # Display results
        for i, eval in enumerate(result, 1):
            print(f"Evaluation {i} - {eval.model}:")
            print(f"  Truth:         {eval.truth:.3f}")
            print(f"  Indeterminacy: {eval.indeterminacy:.3f}")
            print(f"  Falsehood:     {eval.falsehood:.3f}")
            print(f"  Reasoning:     {eval.reasoning[:100]}...")
            print()

        # Check if we got results from all 3 rounds (should have multiple evals per model)
        print(f"Total evaluations returned: {len(result)}")
        print("Expected: ~9 evaluations (3 models × 3 rounds)")

        return True

    except Exception as e:
        print(f"\n❌ Fire Circle failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Check for API key
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set")
        print("Set it with: export OPENROUTER_API_KEY=your_key_here")
        exit(1)

    # Run test
    success = asyncio.run(test_fire_circle_basic())

    if success:
        print("\n" + "=" * 80)
        print("✅ FIRE CIRCLE INTEGRATION TEST PASSED")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("❌ FIRE CIRCLE INTEGRATION TEST FAILED")
        print("=" * 80)
        exit(1)
