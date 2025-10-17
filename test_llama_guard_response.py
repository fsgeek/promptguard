"""Test LlamaGuard response format."""
import asyncio
from promptguard.evaluation.evaluator import LLMEvaluator, EvaluationConfig, EvaluationMode
from promptguard.evaluation.prompts import NeutrosophicEvaluationPrompt

async def main():
    print("Testing LlamaGuard response format...\n")

    config = EvaluationConfig(
        mode=EvaluationMode.SINGLE,
        models=["meta-llama/llama-guard-4-12b"],
        provider="openrouter"
    )
    evaluator = LLMEvaluator(config)

    try:
        # Call directly to see raw response
        messages = [{
            "role": "user",
            "content": evaluator._format_evaluation_request(
                layer_content="Hello, how are you?",
                context="prompt: Hello, how are you?",
                evaluation_prompt=NeutrosophicEvaluationPrompt.ayni_relational()
            )
        }]

        response, reasoning = await evaluator._call_llm(
            "meta-llama/llama-guard-4-12b",
            messages
        )

        print("Raw response:")
        print("="*60)
        print(response)
        print("="*60)

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
