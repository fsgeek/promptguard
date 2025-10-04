"""Quick test of trust_trajectory integration."""
import asyncio
from promptguard.promptguard import PromptGuard, PromptGuardConfig


async def main():
    print("Testing trust_trajectory integration...")

    # Test 1: Can we load the prompt?
    print("\n1. Testing prompt registration...")
    try:
        from promptguard.evaluation.prompts import NeutrosophicEvaluationPrompt
        prompt = NeutrosophicEvaluationPrompt.get_prompt("trust_trajectory")
        print(f"✓ trust_trajectory prompt loaded ({len(prompt)} chars)")
    except Exception as e:
        print(f"✗ Failed to load trust_trajectory prompt: {e}")
        return

    # Test 2: Can we create a 3-dimension config?
    print("\n2. Testing 3-dimension ensemble config...")
    try:
        config = PromptGuardConfig(
            models=["x-ai/grok-4-fast:free"],  # Model that worked this morning
            evaluation_type=["ayni_relational", "relational_structure", "trust_trajectory"]
        )
        guard = PromptGuard(config)
        print(f"✓ Created PromptGuard with {len(guard.evaluation_prompts)} prompts")
        print(f"  Prompts: {guard.evaluation_types}")
    except Exception as e:
        print(f"✗ Failed to create config: {e}")
        return

    # Test 3: Evaluate a simple prompt
    print("\n3. Testing evaluation with trust_trajectory...")
    try:
        result = await guard.evaluate(
            prompt="Can you help me understand how neural networks work?"
        )
        print(f"✓ Evaluation completed:")
        print(f"  Balance: {result.ayni_balance:.3f}")
        print(f"  Exchange type: {result.exchange_type.value}")
    except Exception as e:
        print(f"✗ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n✓ All tests passed! Trust trajectory is integrated.")


if __name__ == "__main__":
    asyncio.run(main())
