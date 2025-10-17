"""
Minimal Fire Circle debugging test.

Tests Round 1 vs Round 2 vs Round 3 separately to isolate failure mode.
"""

import asyncio
import os
import sys
from promptguard.evaluation.evaluator import LLMEvaluator
from promptguard.evaluation.fire_circle import FireCircleConfig, CircleSize, FailureMode

BENIGN_PROMPT = "Please explain the concept of recursion in programming."

async def test_round_1_only():
    """Test Round 1 only (no dialogue context)."""
    print("\n" + "=" * 80)
    print("TEST 1: Round 1 only (independent baseline)")
    print("=" * 80)

    config = FireCircleConfig(
        models=["anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku"],  # Minimum 2 models
        circle_size=CircleSize.SMALL,
        max_rounds=1,  # Only Round 1
        failure_mode=FailureMode.STRICT,
        provider="openrouter"
    )

    evaluator = LLMEvaluator(config)

    try:
        result = await evaluator.evaluate_layer(
            layer_content=BENIGN_PROMPT,
            context=BENIGN_PROMPT,
            evaluation_prompt="Evaluate this for reciprocity violations"
        )
        print(f"✅ Round 1 succeeded")
        print(f"F-score: {result[0].falsehood:.2f}")
        print(f"Reasoning: {result[0].reasoning[:150]}...")
        return True
    except Exception as e:
        print(f"❌ Round 1 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_round_2_with_dialogue():
    """Test Round 2 with dialogue context from Round 1."""
    print("\n" + "=" * 80)
    print("TEST 2: Round 2 with dialogue context")
    print("=" * 80)

    config = FireCircleConfig(
        models=["anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku"],
        circle_size=CircleSize.SMALL,
        max_rounds=2,  # Round 1 + 2
        failure_mode=FailureMode.STRICT,
        provider="openrouter"
    )

    evaluator = LLMEvaluator(config)

    try:
        result = await evaluator.evaluate_layer(
            layer_content=BENIGN_PROMPT,
            context=BENIGN_PROMPT,
            evaluation_prompt="Evaluate this for reciprocity violations"
        )
        print(f"✅ Round 2 succeeded")
        print(f"Evaluations: {len(result)}")
        for i, r in enumerate(result, 1):
            print(f"  Eval {i}: F={r.falsehood:.2f}")
        return True
    except Exception as e:
        print(f"❌ Round 2 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_round_3_full_dialogue():
    """Test full 3-round dialogue."""
    print("\n" + "=" * 80)
    print("TEST 3: Full 3-round dialogue")
    print("=" * 80)

    config = FireCircleConfig(
        models=["anthropic/claude-3.5-sonnet", "anthropic/claude-3-haiku"],
        circle_size=CircleSize.SMALL,
        max_rounds=3,
        failure_mode=FailureMode.STRICT,
        provider="openrouter"
    )

    evaluator = LLMEvaluator(config)

    try:
        result = await evaluator.evaluate_layer(
            layer_content=BENIGN_PROMPT,
            context=BENIGN_PROMPT,
            evaluation_prompt="Evaluate this for reciprocity violations"
        )
        print(f"✅ Round 3 succeeded")
        print(f"Evaluations: {len(result)}")
        for i, r in enumerate(result, 1):
            print(f"  Eval {i}: F={r.falsehood:.2f}")
        return True
    except Exception as e:
        print(f"❌ Round 3 failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all three tests sequentially."""
    print("=" * 80)
    print("FIRE CIRCLE MINIMAL DEBUG TEST")
    print("=" * 80)
    print(f"Prompt: {BENIGN_PROMPT}")
    print(f"Models: anthropic/claude-3.5-sonnet, anthropic/claude-3-haiku")
    print()

    # Test each round level
    r1_ok = await test_round_1_only()
    r2_ok = await test_round_2_with_dialogue()
    r3_ok = await test_round_3_full_dialogue()

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Round 1 (no dialogue):    {'✅ PASS' if r1_ok else '❌ FAIL'}")
    print(f"Round 2 (with dialogue):  {'✅ PASS' if r2_ok else '❌ FAIL'}")
    print(f"Round 3 (full dialogue):  {'✅ PASS' if r3_ok else '❌ FAIL'}")

    if r1_ok and not r2_ok:
        print("\n🔍 DIAGNOSIS: Dialogue context construction is the problem")
    elif not r1_ok:
        print("\n🔍 DIAGNOSIS: Round 1 baseline evaluation is failing")
    elif r1_ok and r2_ok and not r3_ok:
        print("\n🔍 DIAGNOSIS: Round 3 consensus synthesis is the problem")
    elif r1_ok and r2_ok and r3_ok:
        print("\n✅ All rounds work with single model")


if __name__ == "__main__":
    if not os.getenv("OPENROUTER_API_KEY"):
        print("❌ OPENROUTER_API_KEY not set")
        exit(1)

    asyncio.run(main())
