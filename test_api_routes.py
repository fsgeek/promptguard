#!/usr/bin/env python3
"""
Test models via OpenRouter vs native APIs to diagnose Fire Circle failures.

Validates:
1. Which models work via OpenRouter
2. Which models work via native APIs
3. Root cause of KeyError issues from earlier Fire Circle run
4. JSON brace handling in prompts
"""

import asyncio
import httpx
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Tuple


# Test configuration
MODELS_TO_TEST = [
    "anthropic/claude-sonnet-4.5",
    "google/gemini-pro-1.5",
    "meta-llama/llama-3.3-70b-instruct",
    "openai/gpt-4o",
    "x-ai/grok-4"
]

# Test prompts - minimal and with JSON braces
PROMPTS = {
    "minimal": "Respond with a single word: hello",
    "json_unescaped": 'Evaluate this JSON: {"test": "value"}',
    "json_escaped": 'Evaluate this JSON: {{"test": "value"}}'
}


class TestResult:
    """Single test result."""
    def __init__(self, model: str, route: str, prompt_type: str):
        self.model = model
        self.route = route
        self.prompt_type = prompt_type
        self.success = False
        self.response = None
        self.error = None
        self.latency_ms = 0
        self.cost = 0.0

    def to_dict(self) -> dict:
        return {
            "model": self.model,
            "route": self.route,
            "prompt_type": self.prompt_type,
            "success": self.success,
            "response": self.response,
            "error": self.error,
            "latency_ms": self.latency_ms,
            "cost": self.cost
        }


async def test_openrouter(
    model: str,
    prompt: str,
    api_key: str
) -> Tuple[bool, Optional[str], Optional[str], int]:
    """
    Test model via OpenRouter.

    Returns: (success, response, error, latency_ms)
    """
    start = asyncio.get_event_loop().time()

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "HTTP-Referer": "https://github.com/tonyapsu/promptguard",
                    "X-Title": "PromptGuard API Test"
                },
                json={
                    "model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100,
                    "temperature": 0.7
                }
            )

            latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return True, content, None, latency_ms
            else:
                return False, None, f"HTTP {response.status_code}: {response.text}", latency_ms

    except Exception as e:
        latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)
        return False, None, str(e), latency_ms


async def test_anthropic_native(
    model: str,
    prompt: str,
    api_key: str
) -> Tuple[bool, Optional[str], Optional[str], int]:
    """
    Test Anthropic model via native API.

    Returns: (success, response, error, latency_ms)
    """
    start = asyncio.get_event_loop().time()

    # Map OpenRouter model name to native API name
    native_model = model.replace("anthropic/", "")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json"
                },
                json={
                    "model": native_model,
                    "max_tokens": 100,
                    "messages": [{"role": "user", "content": prompt}]
                }
            )

            latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)

            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [{}])[0].get("text", "")
                return True, content, None, latency_ms
            else:
                return False, None, f"HTTP {response.status_code}: {response.text}", latency_ms

    except Exception as e:
        latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)
        return False, None, str(e), latency_ms


async def test_openai_native(
    model: str,
    prompt: str,
    api_key: str
) -> Tuple[bool, Optional[str], Optional[str], int]:
    """
    Test OpenAI model via native API.

    Returns: (success, response, error, latency_ms)
    """
    start = asyncio.get_event_loop().time()

    # Map OpenRouter model name to native API name
    native_model = model.replace("openai/", "")

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": native_model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 100,
                    "temperature": 0.7
                }
            )

            latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)

            if response.status_code == 200:
                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                return True, content, None, latency_ms
            else:
                return False, None, f"HTTP {response.status_code}: {response.text}", latency_ms

    except Exception as e:
        latency_ms = int((asyncio.get_event_loop().time() - start) * 1000)
        return False, None, str(e), latency_ms


async def run_tests() -> List[TestResult]:
    """Run all test combinations."""
    results = []

    # Get API keys
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    anthropic_key = os.getenv("ANTHROPIC_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if not openrouter_key:
        print("ERROR: OPENROUTER_API_KEY not found")
        return results

    total_tests = 0
    for model in MODELS_TO_TEST:
        for prompt_type, prompt in PROMPTS.items():
            total_tests += 1  # OpenRouter test

            # Add native API tests
            if model.startswith("anthropic/") and anthropic_key:
                total_tests += 1
            elif model.startswith("openai/") and openai_key:
                total_tests += 1

    print(f"Running {total_tests} tests...")
    test_num = 0

    # Test each model with each prompt type
    for model in MODELS_TO_TEST:
        print(f"\n{'='*80}")
        print(f"Testing: {model}")
        print(f"{'='*80}")

        for prompt_type, prompt in PROMPTS.items():
            # Test via OpenRouter
            test_num += 1
            print(f"\n[{test_num}/{total_tests}] OpenRouter + {prompt_type}")
            result = TestResult(model, "openrouter", prompt_type)

            success, response, error, latency = await test_openrouter(
                model, prompt, openrouter_key
            )

            result.success = success
            result.response = response[:100] if response else None  # Truncate
            result.error = error
            result.latency_ms = latency

            print(f"  Success: {success}")
            if success:
                print(f"  Latency: {latency}ms")
                print(f"  Response: {response[:80]}...")
            else:
                print(f"  Error: {error}")

            results.append(result)

            # Test via native API if available
            native_tested = False

            if model.startswith("anthropic/") and anthropic_key:
                test_num += 1
                print(f"\n[{test_num}/{total_tests}] Anthropic Native + {prompt_type}")
                result = TestResult(model, "anthropic_native", prompt_type)

                success, response, error, latency = await test_anthropic_native(
                    model, prompt, anthropic_key
                )

                result.success = success
                result.response = response[:100] if response else None
                result.error = error
                result.latency_ms = latency

                print(f"  Success: {success}")
                if success:
                    print(f"  Latency: {latency}ms")
                    print(f"  Response: {response[:80]}...")
                else:
                    print(f"  Error: {error}")

                results.append(result)
                native_tested = True

            elif model.startswith("openai/") and openai_key:
                test_num += 1
                print(f"\n[{test_num}/{total_tests}] OpenAI Native + {prompt_type}")
                result = TestResult(model, "openai_native", prompt_type)

                success, response, error, latency = await test_openai_native(
                    model, prompt, openai_key
                )

                result.success = success
                result.response = response[:100] if response else None
                result.error = error
                result.latency_ms = latency

                print(f"  Success: {success}")
                if success:
                    print(f"  Latency: {latency}ms")
                    print(f"  Response: {response[:80]}...")
                else:
                    print(f"  Error: {error}")

                results.append(result)
                native_tested = True

            if not native_tested:
                print(f"  (Native API not available or no API key)")

            # Rate limiting
            await asyncio.sleep(1)

    return results


def analyze_results(results: List[TestResult]) -> dict:
    """Analyze test results and generate report."""

    # Count successes by route
    openrouter_success = sum(1 for r in results if r.route == "openrouter" and r.success)
    openrouter_total = sum(1 for r in results if r.route == "openrouter")

    native_success = sum(1 for r in results if r.route != "openrouter" and r.success)
    native_total = sum(1 for r in results if r.route != "openrouter")

    # Models that work via OpenRouter
    openrouter_models = set()
    for r in results:
        if r.route == "openrouter" and r.success:
            openrouter_models.add(r.model)

    # Models that work via native but fail via OpenRouter
    native_but_not_openrouter = set()
    for model in MODELS_TO_TEST:
        or_tests = [r for r in results if r.model == model and r.route == "openrouter"]
        native_tests = [r for r in results if r.model == model and r.route != "openrouter"]

        or_success = any(r.success for r in or_tests)
        native_success = any(r.success for r in native_tests)

        if native_success and not or_success:
            native_but_not_openrouter.add(model)

    # JSON brace handling
    json_unescaped_failures = [r for r in results if r.prompt_type == "json_unescaped" and not r.success]
    json_escaped_failures = [r for r in results if r.prompt_type == "json_escaped" and not r.success]

    # Check for KeyError specifically
    keyerror_cases = [r for r in results if r.error and "KeyError" in r.error]

    # Diagnosis
    diagnosis = []

    if keyerror_cases:
        diagnosis.append("KeyError detected in responses - likely OpenRouter parsing bug")
        diagnosis.append(f"Affected models: {set(r.model for r in keyerror_cases)}")

    if len(json_unescaped_failures) > len(json_escaped_failures):
        diagnosis.append("Unescaped JSON braces cause more failures than escaped braces")
    elif len(json_escaped_failures) > len(json_unescaped_failures):
        diagnosis.append("Escaped JSON braces cause more failures than unescaped braces")
    else:
        diagnosis.append("JSON brace escaping does not affect failure rates")

    if native_but_not_openrouter:
        diagnosis.append("Some models work via native API but fail via OpenRouter - federation issue")

    # Recommendations
    recommendations = []

    if openrouter_success / max(openrouter_total, 1) < 0.6:
        recommendations.append("OpenRouter reliability is poor (<60% success rate)")
        recommendations.append("Consider using native APIs where available")
    else:
        recommendations.append("OpenRouter reliability is acceptable for Fire Circle")

    if native_but_not_openrouter:
        recommendations.append(f"Use native APIs for: {', '.join(native_but_not_openrouter)}")

    return {
        "summary": {
            "openrouter_success_rate": f"{openrouter_success}/{openrouter_total}",
            "native_success_rate": f"{native_success}/{native_total}" if native_total > 0 else "N/A",
            "models_working_openrouter": len(openrouter_models),
            "models_working_native_only": len(native_but_not_openrouter)
        },
        "diagnosis": diagnosis,
        "recommendations": recommendations,
        "keyerror_cases": len(keyerror_cases),
        "json_unescaped_failures": len(json_unescaped_failures),
        "json_escaped_failures": len(json_escaped_failures)
    }


async def main():
    """Run tests and save results."""
    print("Starting API validation tests...")
    print(f"Time: {datetime.now().isoformat()}")

    # Run tests
    results = await run_tests()

    # Analyze
    analysis = analyze_results(results)

    # Save results
    output = {
        "timestamp": datetime.now().isoformat(),
        "test_results": [r.to_dict() for r in results],
        "analysis": analysis
    }

    output_path = "/home/tony/projects/promptguard/data/experiment_01_reanalysis/q2_api_validation.json"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n{'='*80}")
    print("RESULTS SAVED")
    print(f"{'='*80}")
    print(f"Output: {output_path}")

    # Print summary
    print(f"\n{'='*80}")
    print("SUMMARY")
    print(f"{'='*80}")
    for key, value in analysis["summary"].items():
        print(f"{key}: {value}")

    print(f"\nDIAGNOSIS:")
    for item in analysis["diagnosis"]:
        print(f"  - {item}")

    print(f"\nRECOMMENDATIONS:")
    for item in analysis["recommendations"]:
        print(f"  - {item}")

    print(f"\nTotal tests: {len(results)}")
    print(f"Successful: {sum(1 for r in results if r.success)}")
    print(f"Failed: {sum(1 for r in results if not r.success)}")


if __name__ == "__main__":
    asyncio.run(main())
