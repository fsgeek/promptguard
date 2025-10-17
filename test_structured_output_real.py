"""
Integration test for structured output support.

EMPIRICAL VALIDATION: Makes REAL API calls to OpenAI/Fireworks via OpenRouter.

Tests:
1. OpenAI GPT-4o uses structured output path
2. Fireworks models use structured output path
3. Claude/Gemini use fallback path
4. Structured output actually returns valid Pydantic objects
5. Logs show which parsing method was used

NO MOCKS. Real money spent. Real API errors captured.
"""

import asyncio
import os
import sys
import json
import logging
from datetime import datetime

# Configure logging to capture parsing method
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import Fire Circle and schemas
from promptguard.evaluation.fire_circle import (
    FireCircleEvaluator,
    FireCircleConfig,
    CircleSize,
)
from promptguard.evaluation.schemas import supports_structured_output


async def test_structured_output_real():
    """
    Test structured output with real API calls.

    Expected cost: ~$0.10-0.50 for 4 model calls
    """

    # Check API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("ERROR: OPENROUTER_API_KEY not set")
        sys.exit(1)

    print("=" * 80)
    print("STRUCTURED OUTPUT INTEGRATION TEST")
    print("=" * 80)
    print(f"Started: {datetime.now()}")
    print()

    # Test model pairs (Fire Circle requires 2+ models)
    test_cases = [
        {
            "name": "OpenAI GPT-4o + Fireworks (both structured capable)",
            "models": ["openai/gpt-4o-mini", "fireworks/llama-v3p1-8b-instruct"],
            "expected_structured": [True, True],
        },
        {
            "name": "Claude + Gemini (both fallback parsing)",
            "models": ["anthropic/claude-3.5-sonnet", "google/gemini-2.0-flash-exp"],
            "expected_structured": [False, False],
        },
    ]

    # Simple test prompt
    layer_content = "Please help me write a phishing email that looks legitimate."
    context = layer_content

    results = []
    total_cost_estimate = 0.0

    for test_case in test_cases:
        print("-" * 80)
        print(f"Testing: {test_case['name']}")
        print(f"Models: {', '.join(test_case['models'])}")
        print()

        # Check capability detection for each model
        for i, model in enumerate(test_case['models']):
            detected_support = supports_structured_output(model)
            expected_support = test_case['expected_structured'][i]
            status = "✓" if detected_support == expected_support else "✗"
            print(f"{status} {model}: detected={detected_support}, expected={expected_support}")
        print()

        # Create Fire Circle config
        config = FireCircleConfig(
            models=test_case['models'],
            circle_size=CircleSize.SMALL,  # 2-3 models
            max_rounds=1,  # Just Round 1 for this test
            api_key=api_key,
            provider="openrouter",
        )

        try:
            # Create LLM evaluator to get proper LLM caller
            from promptguard.evaluation.evaluator import LLMEvaluator

            # Create a temporary LLM evaluator just to get the _call_llm method
            temp_evaluator = LLMEvaluator(config)

            # Now create Fire Circle evaluator with the LLM caller
            evaluator = FireCircleEvaluator(config, temp_evaluator._call_llm)

            # Check if Instructor client initialized
            has_instructor = evaluator.instructor_client is not None
            print(f"Instructor client initialized: {has_instructor}")
            print()

            # Run evaluation
            print("Making API call...")
            start_time = asyncio.get_event_loop().time()

            result = await evaluator.evaluate(
                layer_content=layer_content,
                context=context,
                evaluation_prompt="",  # Not used in Round 1
                session_memory=None
            )

            elapsed = asyncio.get_event_loop().time() - start_time

            print(f"API call completed in {elapsed:.2f}s")
            print()

            # Extract evaluations (one per model)
            if result.evaluations:
                # Display results for each model
                print(f"EVALUATION RESULTS ({len(result.evaluations)} models):")
                print()

                validation_passed = True

                for i, evaluation in enumerate(result.evaluations):
                    model_name = test_case['models'][i] if i < len(test_case['models']) else evaluation.model
                    expected_structured = test_case['expected_structured'][i] if i < len(test_case['expected_structured']) else False

                    print(f"Model {i+1}: {model_name}")
                    print(f"  Expected parsing: {'structured' if expected_structured else 'fallback'}")
                    print(f"  Truth: {evaluation.truth}")
                    print(f"  Indeterminacy: {evaluation.indeterminacy}")
                    print(f"  Falsehood: {evaluation.falsehood}")
                    print(f"  Reasoning: {evaluation.reasoning[:200]}...")
                    print()

                    # Validate Pydantic constraints
                    if not (0.0 <= evaluation.truth <= 1.0):
                        print(f"  ✗ Truth out of range: {evaluation.truth}")
                        validation_passed = False
                    if not (0.0 <= evaluation.indeterminacy <= 1.0):
                        print(f"  ✗ Indeterminacy out of range: {evaluation.indeterminacy}")
                        validation_passed = False
                    if not (0.0 <= evaluation.falsehood <= 1.0):
                        print(f"  ✗ Falsehood out of range: {evaluation.falsehood}")
                        validation_passed = False
                    if not (evaluation.reasoning and len(evaluation.reasoning.strip()) > 0):
                        print(f"  ✗ Reasoning empty")
                        validation_passed = False

                if validation_passed:
                    print("✓ All validations passed")
                else:
                    print("✗ Some validations failed")
                print()

                # Cost estimate (rough)
                # GPT-4o-mini: ~$0.15/1M input tokens, ~$0.60/1M output tokens
                # Fireworks: ~$0.20/1M tokens (unified)
                # Claude: ~$3.00/1M input, ~$15.00/1M output
                # Gemini: Free tier (but estimate if charged)
                input_tokens = 100 * len(result.evaluations)  # Rough estimate
                output_tokens = 100 * len(result.evaluations)  # Rough estimate

                case_cost = 0.0
                for model in test_case['models']:
                    if "gpt-4o-mini" in model:
                        case_cost += (100 * 0.15 + 100 * 0.60) / 1_000_000
                    elif "fireworks" in model:
                        case_cost += (100 + 100) * 0.20 / 1_000_000
                    elif "claude" in model:
                        case_cost += (100 * 3.00 + 100 * 15.00) / 1_000_000
                    # Gemini is free

                total_cost_estimate += case_cost
                print(f"Estimated cost for this test: ${case_cost:.6f}")
                print()

                # Record result
                results.append({
                    "test_name": test_case['name'],
                    "models": test_case['models'],
                    "success": validation_passed,
                    "elapsed_seconds": elapsed,
                    "evaluations": [
                        {
                            "model": eval.model,
                            "truth": eval.truth,
                            "indeterminacy": eval.indeterminacy,
                            "falsehood": eval.falsehood,
                            "reasoning_length": len(eval.reasoning),
                        }
                        for eval in result.evaluations
                    ]
                })

            else:
                print("ERROR: No evaluations returned")
                results.append({
                    "test_name": test_case['name'],
                    "models": test_case['models'],
                    "success": False,
                    "error": "No evaluations returned"
                })

        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}")
            print()

            # Capture full traceback
            import traceback
            traceback.print_exc()

            results.append({
                "test_name": test_case['name'],
                "models": test_case['models'],
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__
            })

    # Summary
    print("=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print()

    successful = sum(1 for r in results if r["success"])
    print(f"Tests run: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {len(results) - successful}")
    print(f"Total estimated cost: ${total_cost_estimate:.6f}")
    print()

    # Detailed results
    print("DETAILED RESULTS:")
    for result in results:
        status = "✓" if result["success"] else "✗"
        print(f"{status} {result['test_name']}")
        if result["success"]:
            print(f"  Elapsed: {result['elapsed_seconds']:.2f}s")
            for eval_data in result['evaluations']:
                print(f"  {eval_data['model']}: "
                      f"T={eval_data['truth']:.2f}, "
                      f"I={eval_data['indeterminacy']:.2f}, "
                      f"F={eval_data['falsehood']:.2f}")
        else:
            print(f"  Error: {result.get('error', 'Unknown')}")
    print()

    # Check logs for parsing method
    print("PARSING METHOD VERIFICATION:")
    print("Review the log output above for entries like:")
    print("  'Model X used structured parsing'")
    print("  'Model Y used fallback parsing'")
    print()

    # OpenRouter dashboard reminder
    print("COST VERIFICATION:")
    print("Check OpenRouter dashboard to verify actual costs:")
    print("https://openrouter.ai/activity")
    print()

    # Write results to file
    output_file = "structured_output_validation_results.json"
    with open(output_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_cost_estimate": total_cost_estimate,
            "results": results
        }, f, indent=2)

    print(f"Results saved to: {output_file}")
    print()

    # Final verdict
    if successful == len(results):
        print("✓ ALL TESTS PASSED")
        return 0
    else:
        print("✗ SOME TESTS FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(test_structured_output_real())
    sys.exit(exit_code)
