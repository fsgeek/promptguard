"""Test Gemini response format."""
import asyncio
from promptguard.evaluation.evaluator import LLMEvaluator, EvaluationConfig, EvaluationMode
from promptguard.evaluation.prompts import NeutrosophicEvaluationPrompt

async def main():
    print("Testing Gemini Pro 1.5...\n")

    config = EvaluationConfig(
        mode=EvaluationMode.SINGLE,
        models=["google/gemini-pro-1.5"],
        provider="openrouter"
    )
    evaluator = LLMEvaluator(config)

    try:
        result = await evaluator.evaluate_layer(
            layer_content="Hello, how are you?",
            context="prompt: Hello, how are you?",
            evaluation_prompt=NeutrosophicEvaluationPrompt.ayni_relational()
        )

        print(f"✓ Gemini Pro 1.5 - T={result[0].truth:.2f}, I={result[0].indeterminacy:.2f}, F={result[0].falsehood:.2f}")
        print(f"  Reasoning: {result[0].reasoning[:100]}")

    except Exception as e:
        print(f"✗ ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
