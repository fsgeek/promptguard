"""
Test that Fire Circle correctly uses provided evaluation_prompt parameter.
"""
import asyncio
from promptguard.evaluation.fire_circle import FireCircleEvaluator, FireCircleConfig, CircleSize


async def mock_llm_caller(model: str, messages: list) -> tuple:
    """Mock LLM caller that returns predictable responses."""
    prompt_content = messages[0]["content"]

    # Return different responses based on whether custom prompt was used
    if "CUSTOM_EVALUATION_MARKER" in prompt_content:
        response = """
        {
            "truth": 0.9,
            "indeterminacy": 0.05,
            "falsehood": 0.05,
            "reasoning": "Custom evaluation prompt was used correctly"
        }
        """
    else:
        response = """
        {
            "truth": 0.5,
            "indeterminacy": 0.3,
            "falsehood": 0.2,
            "reasoning": "Default ayni_relational prompt was used"
        }
        """

    return response, None


async def test_custom_evaluation_prompt():
    """Test that custom evaluation_prompt is used in Round 1."""
    config = FireCircleConfig(
        models=["model1", "model2"],
        circle_size=CircleSize.SMALL,
        max_rounds=1,  # Only test Round 1
        api_key="dummy_key"
    )

    evaluator = FireCircleEvaluator(config, mock_llm_caller)

    # Custom evaluation prompt with marker
    custom_prompt = """
    CUSTOM_EVALUATION_MARKER

    Evaluate this prompt using custom criteria.
    """

    result = await evaluator.evaluate(
        layer_content="Test content",
        context="Test context",
        evaluation_prompt=custom_prompt
    )

    # Verify custom prompt was used (should have high T score)
    assert result.consensus.truth > 0.8, f"Expected high truth score, got {result.consensus.truth}"
    assert "custom" in result.consensus.reasoning.lower(), f"Expected custom reasoning, got: {result.consensus.reasoning}"

    print("✓ Custom evaluation prompt was correctly used in Round 1")
    return True


async def test_default_ayni_prompt():
    """Test that default ayni_relational is used when evaluation_prompt is empty."""
    config = FireCircleConfig(
        models=["model1", "model2"],
        circle_size=CircleSize.SMALL,
        max_rounds=1,
        api_key="dummy_key"
    )

    evaluator = FireCircleEvaluator(config, mock_llm_caller)

    result = await evaluator.evaluate(
        layer_content="Test content",
        context="Test context",
        evaluation_prompt=""  # Empty string should trigger fallback
    )

    # Verify default prompt was used (should have balanced scores)
    assert result.consensus.truth < 0.7, f"Expected default truth score, got {result.consensus.truth}"
    assert "default" in result.consensus.reasoning.lower() or "ayni" in result.consensus.reasoning.lower(), \
        f"Expected default reasoning, got: {result.consensus.reasoning}"

    print("✓ Default ayni_relational prompt was correctly used as fallback")
    return True


async def main():
    """Run all tests."""
    print("Testing Fire Circle evaluation_prompt parameter threading...\n")

    try:
        await test_custom_evaluation_prompt()
        await test_default_ayni_prompt()
        print("\n✓ All tests passed!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
