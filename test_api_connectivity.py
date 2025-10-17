"""Quick test of API connectivity with all 4 models."""
import asyncio
from promptguard.evaluation.evaluator import LLMEvaluator, EvaluationConfig, EvaluationMode
from promptguard.evaluation.prompts import NeutrosophicEvaluationPrompt

MODELS = [
    "anthropic/claude-sonnet-4.5",
    "moonshotai/kimi-k2-0905",
    "deepseek/deepseek-v3.1-terminus",
    "openai/gpt-4o"
]

async def test_model(model: str):
    """Test a single model with a simple prompt."""
    print(f"Testing {model}...")
    try:
        config = EvaluationConfig(
            mode=EvaluationMode.SINGLE,
            models=[model],
            provider="openrouter"
        )
        evaluator = LLMEvaluator(config)

        result = await evaluator.evaluate_layer(
            layer_content="Hello, how are you?",
            context="prompt: Hello, how are you?",
            evaluation_prompt=NeutrosophicEvaluationPrompt.ayni_relational()
        )

        print(f"  ✓ {model} - F={result[0].falsehood:.2f}")
        return True
    except Exception as e:
        print(f"  ✗ {model} - ERROR: {str(e)[:100]}")
        return False

async def main():
    print("Testing API connectivity with 4 models...\n")
    results = []
    for model in MODELS:
        success = await test_model(model)
        results.append((model, success))

    print("\n" + "="*60)
    print("Results:")
    success_count = sum(1 for _, s in results if s)
    print(f"{success_count}/{len(MODELS)} models responded successfully")

    if success_count == len(MODELS):
        print("\n✅ All models working - proceeding with full calibration")
    else:
        print("\n⚠️ Some models failed - check OpenRouter API key and model availability")

if __name__ == "__main__":
    asyncio.run(main())
