"""
Capture FULL model response to understand the "Extra data" error.
"""

import asyncio
import os
from promptguard.evaluation.evaluator import LLMEvaluator
from promptguard.evaluation.fire_circle import FireCircleConfig, CircleSize, FailureMode

BENIGN_PROMPT = "Please explain the concept of recursion in programming."

async def test_with_full_capture():
    """Run Round 3 and capture full response."""

    config = FireCircleConfig(
        models=["anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku"],
        circle_size=CircleSize.SMALL,
        max_rounds=3,
        failure_mode=FailureMode.RESILIENT,  # Continue even on error
        provider="openrouter"
    )

    evaluator = LLMEvaluator(config)

    # Monkey-patch _parse_response to log full response before parsing
    original_parse = evaluator.fire_circle._parse_response

    def logging_parse(response, model, round_num):
        if model == "anthropic/claude-3-haiku" and round_num >= 2:
            print(f"\n{'='*80}")
            print(f"FULL RESPONSE FROM {model} Round {round_num}:")
            print(f"{'='*80}")
            print(f"Length: {len(response)} characters")
            print(f"Response:\n{response}")
            print(f"{'='*80}")
            print(f"Response as repr:\n{repr(response)}")
            print(f"{'='*80}\n")
        return original_parse(response, model, round_num)

    evaluator.fire_circle._parse_response = logging_parse

    try:
        result = await evaluator.evaluate_layer(
            layer_content=BENIGN_PROMPT,
            context=BENIGN_PROMPT,
            evaluation_prompt="Evaluate this for reciprocity violations"
        )
        print(f"✅ Completed with {len(result)} evaluations")
    except Exception as e:
        print(f"❌ Failed: {e}")


if __name__ == "__main__":
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set")
        exit(1)

    asyncio.run(test_with_full_capture())
