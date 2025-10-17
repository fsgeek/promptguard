"""
Debug Fire Circle parsing issues by testing single model call.
"""

import asyncio
import os
from promptguard.evaluation.evaluator import LLMEvaluator
from promptguard.evaluation.evaluator import EvaluationConfig, EvaluationMode

async def test_single_model():
    """Test a single model call to see actual response."""

    config = EvaluationConfig(
        mode=EvaluationMode.SINGLE,
        models=["anthropic/claude-3-haiku"],
        provider="openrouter"
    )

    evaluator = LLMEvaluator(config)

    print("Testing single model call...")
    print(f"Model: {config.models[0]}")
    print()

    try:
        result = await evaluator.evaluate_layer(
            layer_content="Please explain recursion in programming.",
            context="Please explain recursion in programming.",
            evaluation_prompt="Does this prompt layer contain a reciprocity violation?"
        )

        print("✅ SUCCESS")
        print(f"Truth: {result[0].truth}")
        print(f"Indeterminacy: {result[0].indeterminacy}")
        print(f"Falsehood: {result[0].falsehood}")
        print(f"Reasoning: {result[0].reasoning}")

    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set")
        exit(1)

    asyncio.run(test_single_model())
