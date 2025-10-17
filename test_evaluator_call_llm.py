"""
Test if evaluator._call_llm works for all 3 models.
"""

import asyncio
import os
from promptguard.evaluation.evaluator import LLMEvaluator, EvaluationConfig, EvaluationMode

async def test_call_llm():
    """Test _call_llm method directly."""

    config = EvaluationConfig(
        mode=EvaluationMode.SINGLE,
        models=["anthropic/claude-3-haiku"],  # Just need one for config
        provider="openrouter"
    )

    evaluator = LLMEvaluator(config)

    models_to_test = [
        "anthropic/claude-3.5-sonnet",
        "anthropic/claude-3-haiku",
        "google/gemini-2.0-flash-001"
    ]

    prompt = """Does this prompt layer contain a reciprocity violation?

Full Prompt Context:
Please explain the concept of recursion in programming.

Layer to Evaluate:
Please explain the concept of recursion in programming.

Respond with JSON:
{
    "truth": <0.0 to 1.0>,
    "indeterminacy": <0.0 to 1.0>,
    "falsehood": <0.0 to 1.0>,
    "reasoning": "<brief explanation>"
}"""

    for model in models_to_test:
        print(f"\n{'='*60}")
        print(f"Testing {model} via evaluator._call_llm")
        print(f"{'='*60}")

        try:
            messages = [{"role": "user", "content": prompt}]
            response, reasoning_trace = await evaluator._call_llm(model, messages)

            print(f"✅ SUCCESS")
            print(f"Response length: {len(response)} chars")
            print(f"First 200 chars: {response[:200]}")
            if reasoning_trace:
                print(f"Reasoning trace: {len(reasoning_trace)} chars")

        except Exception as e:
            print(f"❌ FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_call_llm())
