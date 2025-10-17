"""
Test parsing edge cases to validate all parsing fixes.

Tests:
1. Plain JSON (no fences)
2. JSON with markdown fences (```json)
3. JSON with text before fence (Gemini behavior)
4. JSON with extra text after (Haiku behavior)
5. JSON with double braces (Gemini Round 3)
"""

import sys
import json
from promptguard.evaluation.fire_circle import FireCircleEvaluator, FireCircleConfig, CircleSize


def test_parse_response(test_name: str, response: str, expected_truth: float) -> bool:
    """Test parsing a specific response format."""
    # Create minimal config (need 2 models for SMALL circle)
    config = FireCircleConfig(
        models=["test/model1", "test/model2"],
        circle_size=CircleSize.SMALL,
        provider="openrouter",
        api_key="dummy"
    )

    # Create evaluator with dummy LLM caller
    async def dummy_llm_caller(model, messages):
        return "", None

    evaluator = FireCircleEvaluator(config, dummy_llm_caller)

    try:
        evaluation = evaluator._parse_response(response, "test/model", 1)

        # Check parsed values
        if abs(evaluation.truth - expected_truth) < 0.01:
            print(f"✅ {test_name}: PASS")
            return True
        else:
            print(f"❌ {test_name}: FAIL - Expected truth={expected_truth}, got {evaluation.truth}")
            return False

    except Exception as e:
        print(f"❌ {test_name}: FAIL - {e}")
        return False


def main():
    """Run all parsing edge case tests."""
    print("="*80)
    print("PARSING EDGE CASE VALIDATION")
    print("="*80)
    print()

    tests_passed = 0
    tests_total = 0

    # Test 1: Plain JSON (no fences)
    tests_total += 1
    if test_parse_response(
        "Plain JSON",
        '{"truth": 0.8, "indeterminacy": 0.1, "falsehood": 0.1, "reasoning": "Test"}',
        0.8
    ):
        tests_passed += 1

    # Test 2: JSON with markdown fences
    tests_total += 1
    if test_parse_response(
        "JSON with markdown fences",
        '```json\n{"truth": 0.7, "indeterminacy": 0.2, "falsehood": 0.1, "reasoning": "Test"}\n```',
        0.7
    ):
        tests_passed += 1

    # Test 3: JSON with text before fence (Gemini)
    tests_total += 1
    if test_parse_response(
        "Text before fence (Gemini)",
        'Here is the JSON response:\n\n```json\n{"truth": 0.6, "indeterminacy": 0.2, "falsehood": 0.2, "reasoning": "Test"}\n```',
        0.6
    ):
        tests_passed += 1

    # Test 4: JSON with extra text after (Haiku)
    tests_total += 1
    if test_parse_response(
        "Extra text after JSON (Haiku)",
        '{"truth": 0.9, "indeterminacy": 0.1, "falsehood": 0.0, "reasoning": "Test"}\n\nThe concept of recursion in programming refers to...',
        0.9
    ):
        tests_passed += 1

    # Test 5: JSON with double braces (Gemini Round 3)
    tests_total += 1
    if test_parse_response(
        "Double braces (Gemini Round 3)",
        '{{\n    "truth": 0.5,\n    "indeterminacy": 0.3,\n    "falsehood": 0.2,\n    "reasoning": "Test"\n}}',
        0.5
    ):
        tests_passed += 1

    # Test 6: Combined: text before fence + extra text after
    tests_total += 1
    if test_parse_response(
        "Combined edge cases",
        'Response:\n```json\n{"truth": 1.0, "indeterminacy": 0.0, "falsehood": 0.0, "reasoning": "Test"}\n```\nAdditional explanation here...',
        1.0
    ):
        tests_passed += 1

    # Test 7: Nested braces in JSON (shouldn't break brace counting)
    tests_total += 1
    if test_parse_response(
        "Nested braces in JSON",
        '{"truth": 0.8, "indeterminacy": 0.1, "falsehood": 0.1, "reasoning": "Test with {nested} braces"}\nExtra text after',
        0.8
    ):
        tests_passed += 1

    print()
    print("="*80)
    print("RESULTS")
    print("="*80)
    print(f"Tests passed: {tests_passed}/{tests_total}")

    if tests_passed == tests_total:
        print("\n✅ All parsing edge cases handled correctly!")
        return 0
    else:
        print(f"\n❌ {tests_total - tests_passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(main())
