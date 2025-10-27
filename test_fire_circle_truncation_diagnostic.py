#!/usr/bin/env python3
"""
Fire Circle Truncation Diagnostic

Minimal test to capture full prompt/response data when Hermes-4-405b and
Mistral-Medium-3.1 truncate in Round 2.

Purpose: Understand why models with 131K context windows truncate at ~155 chars
despite max_tokens=8192.

Run with logging enabled to capture diagnostic data:
    python -u test_fire_circle_truncation_diagnostic.py 2>&1 | tee /tmp/fire_circle_diagnostic.log

Then grep logs for:
    - "prompt_sent" - full Round 2 prompt that triggers truncation
    - "response_received" - full truncated response
    - "parse_failure_full_response" - complete error context
"""

import asyncio
import logging
import os
from promptguard.evaluation.evaluator import LLMEvaluator
from promptguard.evaluation.fire_circle import FireCircleConfig, CircleSize

# Enable DEBUG logging to capture full prompts/responses
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Models that truncate in Round 2
TRUNCATING_MODELS = [
    "nousresearch/hermes-4-405b",
    "mistralai/mistral-medium-3.1"
]

# Simple test case
TEST_PROMPT = "Hello, how are you?"
TEST_RESPONSE = "I'm doing well, thank you for asking!"

async def test_truncation():
    """Run minimal Fire Circle with truncating models to capture diagnostic data."""

    config = FireCircleConfig(
        models=TRUNCATING_MODELS,
        circle_size=CircleSize.SMALL,
        max_rounds=3,
        provider="openrouter",
        api_key=os.environ.get('OPENROUTER_API_KEY')
    )

    evaluator = LLMEvaluator(config)

    # Evaluate simple exchange
    layer_content = f"""USER REQUEST:
{TEST_PROMPT}

LLM RESPONSE:
{TEST_RESPONSE}"""

    context = """Evaluate this exchange between a user and an LLM.
Determine reciprocity: High T, Low F = reciprocal; Low T, High F = extractive."""

    evaluation_prompt = "Evaluate the reciprocity of this exchange."

    print("Starting Fire Circle diagnostic test")
    print(f"Models: {TRUNCATING_MODELS}")
    print(f"Max rounds: 3")
    print()

    try:
        result = await evaluator.fire_circle.evaluate(
            layer_content=layer_content,
            context=context,
            evaluation_prompt=evaluation_prompt
        )

        print("SUCCESS: Fire Circle completed without truncation")
        print(f"Consensus F-score: {result.consensus.falsehood}")
        print(f"Final active models: {result.metadata.get('final_active_models', [])}")

    except Exception as e:
        print(f"TRUNCATION OCCURRED: {e}")
        print()
        print("Check logs for diagnostic data:")
        print("  - grep 'prompt_sent' for full Round 2 prompt")
        print("  - grep 'response_received' for full truncated response")
        print("  - grep 'parse_failure_full_response' for error context")

if __name__ == '__main__':
    asyncio.run(test_truncation())
