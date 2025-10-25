#!/usr/bin/env python3
"""
Test Fire Circle model availability and pricing via OpenRouter API.
Minimal test prompts to verify connectivity and capture pricing data.
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional
import httpx

OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# Tony's specified Fire Circle models (2025-10-24)
FIRE_CIRCLE_MODELS = [
    "openai/gpt-5",
    "nousresearch/hermes-4-405b",
    "moonshotai/kimi-k2-0905",
    "x-ai/grok-4",
    "anthropic/claude-opus-4.1",
    "google/gemini-2.5-pro",
    "deepseek/deepseek-v3.1-terminus",
    "cohere/command-a",
    "mistralai/mistral-medium-3.1",
    "meta-llama/llama-4-maverick",
    "alibaba/tongyi-deepresearch-30b-a3b",
    "tencent/hunyuan-a13b-instruct",
    "inclusionai/ling-1t",
]

# Minimal test prompt - just need to verify API works
TEST_PROMPT = "What is 2+2? Reply with just the number."

async def get_model_pricing(model_id: str) -> Optional[Dict[str, Any]]:
    """Query OpenRouter models endpoint for pricing data."""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{OPENROUTER_BASE_URL}/models",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                },
                timeout=30.0
            )

            if response.status_code == 200:
                models_data = response.json()
                for model in models_data.get("data", []):
                    if model["id"] == model_id:
                        return {
                            "id": model_id,
                            "name": model.get("name", model_id),
                            "context_length": model.get("context_length", 0),
                            "pricing": model.get("pricing", {}),
                        }
            return None
    except Exception as e:
        print(f"  Pricing lookup failed: {e}")
        return None

async def test_model(model_id: str) -> Dict[str, Any]:
    """Test a single model with minimal prompt."""
    print(f"\nTesting {model_id}...")

    result = {
        "id": model_id,
        "status": "unavailable",
        "error": None,
        "pricing": None,
        "estimated_cost_per_fc_eval": None,
        "notes": "",
    }

    try:
        # First try to get pricing info
        pricing_info = await get_model_pricing(model_id)
        if pricing_info:
            pricing = pricing_info.get("pricing", {})
            input_price = float(pricing.get("prompt", 0))  # per token
            output_price = float(pricing.get("completion", 0))  # per token

            # Convert to per-million-tokens
            result["pricing"] = {
                "input_per_mtok": input_price * 1_000_000,
                "output_per_mtok": output_price * 1_000_000,
            }

            # Estimate Fire Circle cost: 3 rounds × (2K input + 1K output) per model
            input_tokens = 2000 * 3
            output_tokens = 1000 * 3
            cost = (input_tokens * input_price) + (output_tokens * output_price)
            result["estimated_cost_per_fc_eval"] = round(cost, 6)

            print(f"  Pricing: ${result['pricing']['input_per_mtok']:.2f}/Mtok in, "
                  f"${result['pricing']['output_per_mtok']:.2f}/Mtok out")
            print(f"  Estimated FC cost: ${result['estimated_cost_per_fc_eval']:.6f}")

        # Now test actual availability with minimal prompt
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{OPENROUTER_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "user", "content": TEST_PROMPT}
                    ],
                    "max_tokens": 10,  # Minimal to save cost
                    "temperature": 0,
                },
                timeout=60.0
            )

            if response.status_code == 200:
                result["status"] = "available"
                result["notes"] = "Model responded successfully"
                print(f"  Status: ✓ AVAILABLE")
            else:
                error_data = response.json()
                result["error"] = f"HTTP {response.status_code}: {error_data.get('error', {}).get('message', 'Unknown error')}"
                result["notes"] = f"API returned error: {result['error']}"
                print(f"  Status: ✗ FAILED - {result['error']}")

    except httpx.TimeoutException:
        result["error"] = "Request timeout (60s)"
        result["notes"] = "Model may be overloaded or unavailable"
        print(f"  Status: ✗ TIMEOUT")
    except Exception as e:
        result["error"] = str(e)
        result["notes"] = f"Unexpected error: {type(e).__name__}"
        print(f"  Status: ✗ ERROR - {e}")

    return result

async def test_all_models():
    """Test all Fire Circle models."""
    print(f"Testing {len(FIRE_CIRCLE_MODELS)} Fire Circle models...")
    print(f"API Key: {OPENROUTER_API_KEY[:10]}..." if OPENROUTER_API_KEY else "No API key!")

    results = []
    for model_id in FIRE_CIRCLE_MODELS:
        result = await test_model(model_id)
        results.append(result)
        # Small delay to avoid rate limits
        await asyncio.sleep(1)

    return results

def analyze_results(results: list) -> Dict[str, Any]:
    """Analyze test results and generate recommendations."""
    available = [r for r in results if r["status"] == "available"]
    unavailable = [r for r in results if r["status"] == "unavailable"]

    # Sort available by cost
    available_with_cost = [r for r in available if r["estimated_cost_per_fc_eval"]]
    available_with_cost.sort(key=lambda x: x["estimated_cost_per_fc_eval"])

    # Recommend sets
    small_set = []
    medium_set = []

    if len(available_with_cost) >= 3:
        # Small: 3 diverse models (cheapest, mid, premium)
        small_set = [
            available_with_cost[0]["id"],  # Cheapest
            available_with_cost[len(available_with_cost)//2]["id"],  # Mid
            available_with_cost[-1]["id"],  # Most expensive (presumably best)
        ]

        # Medium: 5-7 models spanning cost spectrum
        if len(available_with_cost) >= 7:
            indices = [0, 2, 4, 6, -3, -2, -1]
            medium_set = [available_with_cost[i]["id"] for i in indices if i < len(available_with_cost)]
        elif len(available_with_cost) >= 5:
            indices = [0, 1, 2, -2, -1]
            medium_set = [available_with_cost[i]["id"] for i in indices]

    # Calculate total costs
    small_cost = sum(
        next((r["estimated_cost_per_fc_eval"] for r in results if r["id"] == model_id), 0)
        for model_id in small_set
    )
    medium_cost = sum(
        next((r["estimated_cost_per_fc_eval"] for r in results if r["id"] == model_id), 0)
        for model_id in medium_set
    )
    large_cost = sum(
        r["estimated_cost_per_fc_eval"] for r in available_with_cost
    )

    return {
        "last_updated": datetime.now().strftime("%Y-%m-%d"),
        "source": "Tony's specification for current frontier models",
        "test_summary": {
            "total_tested": len(results),
            "available": len(available),
            "unavailable": len(unavailable),
        },
        "models": results,
        "recommended_sets": {
            "small": {
                "description": "3 diverse models (budget, mid, premium) for basic Fire Circle",
                "models": small_set,
                "total_cost_per_eval": round(small_cost, 6),
            },
            "medium": {
                "description": "5-7 models spanning cost spectrum for robust consensus",
                "models": medium_set,
                "total_cost_per_eval": round(medium_cost, 6),
            },
            "large": {
                "description": "All available models for comprehensive analysis",
                "models": [r["id"] for r in available_with_cost],
                "total_cost_per_eval": round(large_cost, 6),
            },
        },
        "failures": [
            {
                "id": r["id"],
                "error": r["error"],
                "notes": r["notes"],
            }
            for r in unavailable
        ],
    }

async def main():
    if not OPENROUTER_API_KEY:
        print("ERROR: OPENROUTER_API_KEY environment variable not set")
        return

    # Test all models
    results = await test_all_models()

    # Analyze and generate config
    config = analyze_results(results)

    # Write to file
    output_path = "/home/tony/projects/promptguard/config/fire_circle_models.json"
    with open(output_path, "w") as f:
        json.dump(config, f, indent=2)

    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"Models tested: {config['test_summary']['total_tested']}")
    print(f"Available: {config['test_summary']['available']}")
    print(f"Unavailable: {config['test_summary']['unavailable']}")
    print()
    print("Recommended configurations:")
    for size, info in config["recommended_sets"].items():
        print(f"  {size.upper()}: {len(info['models'])} models, ${info['total_cost_per_eval']:.6f} per evaluation")
    print()
    if config["failures"]:
        print("Failed models:")
        for failure in config["failures"]:
            print(f"  {failure['id']}: {failure['error']}")
    print()
    print(f"Configuration written to: {output_path}")

if __name__ == "__main__":
    asyncio.run(main())
